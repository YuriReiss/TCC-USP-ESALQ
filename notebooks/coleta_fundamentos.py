"""
Coleta fundamentos point-in-time dos dados abertos da CVM (ITR trimestral + DFP anual).

Por que a CVM e nao o yfinance: as APIs de fundamentos devolvem o balanco COMO ELE E HOJE,
ja reapresentado. Usar isso num backtest de 2013 injeta numeros que so existiram anos depois.
A CVM publica a data de recebimento (DT_RECEB) de cada documento, o que permite reconstruir
exatamente o que era publico em cada data de rebalanceamento.

Duas decisoes que preservam o point-in-time:
  1. Quando ha varias versoes do mesmo trimestre, fica a PRIMEIRA entregue. Reapresentacoes
     posteriores corrigem o passado e nao estavam disponiveis na epoca.
  2. Todo indicador carrega o DT_RECEB da ultima demonstracao usada para calcula-lo. O
     consumidor filtra por DT_RECEB <= data_limite; nada entra antes de ser publico.

Nenhum indicador usa preco. P/L e P/VP exigiriam o preco NAO ajustado, porque o lucro por
acao da CVM esta em acoes da epoca, enquanto a serie de cotacoes foi baixada com
auto_adjust=True e ja incorpora desdobramentos e proventos. Dividir um pelo outro
descasaria nos splits (o de BBAS3 em 2024, por exemplo, dobraria o P/L retroativo). Os
cinco indicadores escolhidos sao razoes contabeis, invariantes a desdobramento.
"""

import io
import os
import re
import unicodedata
import zipfile

import numpy as np
import pandas as pd
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ANO_INICIAL = 2010  # 2010 entra so para fechar o TTM das janelas de 2011
ANO_FINAL = 2026
CACHE = '../mcp_servers/data_server/cvm/extratos'
DESTINO = '../mcp_servers/data_server/fundamentos_cvm.csv'

# AMBEV trocou de companhia em 2013: a serie antiga (18112) cobre ate 2013, a nova (23264)
# assume depois. As duas alimentam o mesmo ticker.
TICKERS_CVM = {
    'PETR4.SA': [9512],
    'VALE3.SA': [4170],
    'ITUB4.SA': [19348],
    'WEGE3.SA': [5410],
    'BBAS3.SA': [1023],
    'BBDC4.SA': [906],
    'LREN3.SA': [8133],
    'ABEV3.SA': [23264, 18112],
    'SBSP3.SA': [14443],
    'CMIG4.SA': [2453],
}
CODIGOS = {cd for lista in TICKERS_CVM.values() for cd in lista}

# Nem o lucro nem o patrimonio liquido tem codigo fixo: o lucro fecha em 3.09, 3.11 ou 3.13
# e o patrimonio aparece em 2.03, 2.05, 2.07 ou 2.08, conforme o emissor seja banco ou nao e
# conforme o layout do ano. Casar pela descricao, entre as contas de primeiro nivel, e o que
# sobrevive aos dois eixos de variacao.
PADRAO_LUCRO = re.compile(r'lucro.*(periodo|exercicio)')
# "antes das participacoes" e um subtotal pre-PLR; as demais sao aberturas do proprio lucro.
RUIDO_LUCRO = re.compile(r'antes|descontinuad|atribuid|por acao|acionista|basico|diluido')
PADRAO_PL = re.compile(r'^patrimonio liquido')
CONTA_RECEITA = '3.01'
CONTA_ATIVO = '1'


def normalizar(serie):
    """Minuscula sem acento: as descricoes da CVM variam na acentuacao entre layouts."""
    sem_acento = (serie.fillna('').astype(str)
                  .map(lambda s: unicodedata.normalize('NFKD', s)
                       .encode('ascii', 'ignore').decode('ascii')))
    return sem_acento.str.lower().str.strip()


def baixar_zip(tipo, ano):
    """
    Abre o pacote anual da CVM em memoria. Devolve None para ano ainda nao publicado.

    O zip nao vai para o disco: sao ~35 MB por ano e so algumas dezenas de linhas
    interessam. O cache e feito depois, sobre o extrato ja filtrado.
    """
    nome = f'{tipo.lower()}_cia_aberta_{ano}.zip'
    url = f'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/{tipo}/DADOS/{nome}'
    try:
        with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=300) as r:
            conteudo = r.read()
    except HTTPError as e:
        if e.code == 404:
            print(f'  [skip] {tipo} {ano} ainda nao publicado.')
            return None
        raise
    print(f'  [lido] {nome} ({len(conteudo)/1e6:.1f} MB)')
    return zipfile.ZipFile(io.BytesIO(conteudo))


def ler_membro(z, nome):
    if nome not in z.namelist():
        return pd.DataFrame()
    df = pd.read_csv(z.open(nome), sep=';', encoding='latin-1', low_memory=False)
    return df[df.CD_CVM.isin(CODIGOS)]


def ler_demonstracao(z, tipo, grupo, ano):
    """
    Empilha as versoes consolidada e individual, marcando a origem.

    Banco do Brasil e Bradesco nao publicam demonstracao consolidada em varios trimestres
    da amostra; sem o fallback para 'ind' esses tickers sairiam da base. A escolha entre as
    duas e feita por trimestre, e nao por empresa: um emissor pode ter consolidado num ano
    e nao no seguinte.
    """
    partes = []
    for origem in ['con', 'ind']:
        parte = ler_membro(z, f'{tipo.lower()}_cia_aberta_{grupo}_{origem}_{ano}.csv')
        if not parte.empty:
            partes.append(parte.assign(ORIGEM=origem))
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()


def recortar(df, cd_cvm, dt_refer, versao):
    """Linhas de um documento especifico, preferindo o consolidado quando ele existe."""
    if df.empty:
        return df
    d = df[(df.CD_CVM == cd_cvm) & (df.DT_REFER == dt_refer)
           & (df.VERSAO == versao) & (df.ORDEM_EXERC == 'ÚLTIMO')]
    if d.empty:
        return d
    return d[d.ORIGEM == ('con' if (d.ORIGEM == 'con').any() else 'ind')]


def escala(serie_valor, serie_escala):
    """VL_CONTA vem em MIL na maioria das contas da CVM."""
    fator = np.where(serie_escala.str.upper().str.strip() == 'MIL', 1000.0, 1.0)
    return serie_valor * fator


def primeiro(serie):
    return float(serie.iloc[0]) if len(serie) else np.nan


def extrair_ano(tipo, ano):
    # O extrato filtrado tem poucos KB; so ele fica em disco, e uma reexecucao nao
    # rebaixa os ~600 MB de pacotes anuais.
    cache = os.path.join(CACHE, f'{tipo}_{ano}.csv')
    if os.path.exists(cache):
        return pd.read_csv(cache, parse_dates=['DT_REFER', 'DT_RECEB'])

    z = baixar_zip(tipo, ano)
    if z is None:
        return pd.DataFrame()

    cabecalho = ler_membro(z, f'{tipo.lower()}_cia_aberta_{ano}.csv')
    if cabecalho.empty:
        return pd.DataFrame()

    # Todas as versoes, da mais antiga para a mais nova. O pacote anual nem sempre traz as
    # linhas da versao 1: a CVM descarta o detalhe das versoes substituidas. Quando isso
    # acontece, vale a versao mais antiga que AINDA tem linhas, com a DT_RECEB dela — nunca
    # a data da versao 1 com os numeros da 2, que seria reapresentacao disfarcada de original.
    recebimento = (cabecalho[['CD_CVM', 'DT_REFER', 'VERSAO', 'DT_RECEB']]
                   .drop_duplicates()
                   .sort_values(['CD_CVM', 'DT_REFER', 'DT_RECEB']))

    dre = ler_demonstracao(z, tipo, 'DRE', ano)
    bpp = ler_demonstracao(z, tipo, 'BPP', ano)
    bpa = ler_demonstracao(z, tipo, 'BPA', ano)
    if dre.empty:
        return pd.DataFrame()

    registros = []
    vistos = set()
    for _, chave in recebimento.iterrows():
        if (chave.CD_CVM, chave.DT_REFER) in vistos:
            continue

        d = recortar(dre, chave.CD_CVM, chave.DT_REFER, chave.VERSAO)
        if d.empty:
            continue

        # Acumulado do exercicio: comeca em 1 de janeiro. As linhas de 3 meses existem para
        # alguns emissores, mas o acumulado e o unico presente em todos eles.
        inicio_ano = f'{pd.to_datetime(chave.DT_REFER).year}-01-01'
        ytd = d[d.DT_INI_EXERC == inicio_ano]
        if ytd.empty:
            continue

        vistos.add((chave.CD_CVM, chave.DT_REFER))

        ytd = ytd.assign(VALOR=escala(ytd.VL_CONTA, ytd.ESCALA_MOEDA),
                         DESC=normalizar(ytd.DS_CONTA))

        # Entre as contas de primeiro nivel, o lucro liquido e a de MAIOR codigo que fala de
        # resultado do periodo: as anteriores sao subtotais que ainda nao descontaram tudo.
        nivel1 = ytd[ytd.CD_CONTA.str.fullmatch(r'3\.\d\d') & (ytd.CD_CONTA != '3.99')]
        lucro = nivel1[nivel1.DESC.str.contains(PADRAO_LUCRO)
                       & ~nivel1.DESC.str.contains(RUIDO_LUCRO)].sort_values('CD_CONTA')
        receita = ytd[ytd.CD_CONTA == CONTA_RECEITA]

        b = recortar(bpp, chave.CD_CVM, chave.DT_REFER, chave.VERSAO)
        patrimonio = pd.DataFrame()
        if not b.empty:
            b = b.assign(VALOR=escala(b.VL_CONTA, b.ESCALA_MOEDA), DESC=normalizar(b.DS_CONTA))
            patrimonio = b[b.CD_CONTA.str.fullmatch(r'2\.\d\d') & b.DESC.str.contains(PADRAO_PL)]

        a = recortar(bpa, chave.CD_CVM, chave.DT_REFER, chave.VERSAO)
        ativo = pd.DataFrame()
        if not a.empty:
            ativo = a[a.CD_CONTA == CONTA_ATIVO].assign(
                VALOR=lambda x: escala(x.VL_CONTA, x.ESCALA_MOEDA))

        registros.append({
            'CD_CVM': chave.CD_CVM,
            'DT_REFER': pd.to_datetime(chave.DT_REFER),
            'DT_RECEB': pd.to_datetime(chave.DT_RECEB),
            'Lucro_YTD': float(lucro.VALOR.iloc[-1]) if len(lucro) else np.nan,
            'Conta_Lucro': lucro.CD_CONTA.iloc[-1] if len(lucro) else '',
            'Receita_YTD': primeiro(receita.VALOR),
            'Patrimonio_Liquido': primeiro(patrimonio.VALOR) if len(patrimonio) else np.nan,
            'Ativo_Total': primeiro(ativo.VALOR) if len(ativo) else np.nan,
        })

    extrato = pd.DataFrame(registros)
    if not extrato.empty:
        extrato.to_csv(cache, index=False)
    return extrato


def ytd_para_trimestre(df):
    """
    Converte acumulado do exercicio em valor do trimestre.

    O 4o trimestre so aparece na DFP, que e anual: Q4 = ano inteiro menos o acumulado ate
    setembro. Diferenciar dentro do mesmo exercicio evita somar periodos sobrepostos.
    """
    df = df.sort_values(['CD_CVM', 'DT_REFER']).copy()
    df['Ano'] = df.DT_REFER.dt.year

    for coluna in ['Lucro', 'Receita']:
        anterior = df.groupby(['CD_CVM', 'Ano'])[f'{coluna}_YTD'].shift(1).fillna(0.0)
        df[f'{coluna}_Tri'] = df[f'{coluna}_YTD'] - anterior

    return df


def montar_base():
    os.makedirs(CACHE, exist_ok=True)

    partes = []
    for ano in range(ANO_INICIAL, ANO_FINAL + 1):
        print(f'Processando {ano}...')
        for tipo in ['ITR', 'DFP']:
            parte = extrair_ano(tipo, ano)
            if not parte.empty:
                partes.append(parte)

    bruto = pd.concat(partes, ignore_index=True)
    # Um mesmo DT_REFER pode vir no ITR e na DFP (4o tri): fica o primeiro publicado.
    bruto = (bruto.sort_values('DT_RECEB')
             .drop_duplicates(subset=['CD_CVM', 'DT_REFER'], keep='first'))

    trimestral = ytd_para_trimestre(bruto)

    # TTM: soma dos 4 trimestres mais recentes. min_periods=4 descarta os primeiros
    # trimestres de cada empresa, onde a soma cobriria menos de um ano.
    g = trimestral.groupby('CD_CVM')
    for coluna in ['Lucro', 'Receita']:
        trimestral[f'{coluna}_TTM'] = (g[f'{coluna}_Tri']
                                       .rolling(4, min_periods=4).sum()
                                       .reset_index(level=0, drop=True))
    for coluna in ['Lucro', 'Receita']:
        trimestral[f'{coluna}_TTM_Anterior'] = trimestral.groupby('CD_CVM')[f'{coluna}_TTM'].shift(4)

    linhas = []
    for ticker, codigos in TICKERS_CVM.items():
        sub = trimestral[trimestral.CD_CVM.isin(codigos)].copy()
        sub['Ticker'] = ticker
        linhas.append(sub)

    # A AMBEV se sobrepoe nos dois codigos CVM durante a transicao de 2013; fica a
    # divulgacao mais antiga de cada trimestre, que e a que o mercado viu primeiro.
    final = (pd.concat(linhas, ignore_index=True)
             .sort_values(['Ticker', 'DT_REFER', 'DT_RECEB'])
             .drop_duplicates(subset=['Ticker', 'DT_REFER'], keep='first')
             .sort_values(['Ticker', 'DT_RECEB']))

    final['ROE'] = final.Lucro_TTM / final.Patrimonio_Liquido.replace(0, np.nan)
    final['Margem_Liquida'] = final.Lucro_TTM / final.Receita_TTM.replace(0, np.nan)
    final['Crescimento_Receita'] = (final.Receita_TTM / final.Receita_TTM_Anterior.abs().replace(0, np.nan)) - 1
    final['Crescimento_Lucro'] = (final.Lucro_TTM - final.Lucro_TTM_Anterior) / final.Lucro_TTM_Anterior.abs().replace(0, np.nan)
    # Ativo/PL em vez de divida/PL: a divida bruta nao tem conta comparavel entre banco e
    # industria, e a alavancagem patrimonial tem.
    final['Alavancagem'] = final.Ativo_Total / final.Patrimonio_Liquido.replace(0, np.nan)

    colunas = ['Ticker', 'CD_CVM', 'DT_REFER', 'DT_RECEB', 'Conta_Lucro', 'Lucro_TTM',
               'Receita_TTM', 'Patrimonio_Liquido', 'Ativo_Total', 'ROE', 'Margem_Liquida',
               'Crescimento_Receita', 'Crescimento_Lucro', 'Alavancagem']
    final = final[colunas].dropna(subset=['DT_RECEB'])
    final.to_csv(DESTINO, index=False)

    indicadores = ['ROE', 'Margem_Liquida', 'Crescimento_Receita', 'Crescimento_Lucro', 'Alavancagem']
    print(f'\nBase gravada em {DESTINO}: {len(final)} linhas.')
    print('\nCobertura por ticker (trimestres com o indicador preenchido):')
    cabecalho = ' '.join(f'{i[:10]:>10}' for i in indicadores)
    print(f'  {"Ticker":<10} {"Tri":>4} {cabecalho}   Periodo de publicacao')
    for ticker, sub in final.groupby('Ticker'):
        contagem = ' '.join(f'{sub[i].notna().sum():>10}' for i in indicadores)
        print(f'  {ticker:<10} {len(sub):>4} {contagem}   '
              f'{sub.DT_RECEB.min().date()} a {sub.DT_RECEB.max().date()}')

    # A defasagem entre o fim do trimestre e a publicacao e o que separa este desenho de
    # um backtest com look-ahead; imprimir obriga o resultado a ser auditado.
    defasagem = (final.DT_RECEB - final.DT_REFER).dt.days
    print(f'\nDefasagem DT_REFER -> DT_RECEB: mediana {defasagem.median():.0f} dias, '
          f'min {defasagem.min():.0f}, max {defasagem.max():.0f}')


if __name__ == '__main__':
    montar_base()
