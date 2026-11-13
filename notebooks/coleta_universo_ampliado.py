"""
Universo ampliado de 2011, para medir o vies de sobrevivencia.

PROBLEMA QUE ESTE SCRIPT ATACA
As 10 acoes do estudo foram escolhidas em 2025/2026 sem regra documentada de selecao.
Todas as 10 existem e sao liquidas hoje, depois de 14 anos. Isso significa que a escolha
embute informacao que ninguem tinha em janeiro de 2012: a de que essas empresas
sobreviveriam. O problema nao e academico. A decomposicao do excesso mostra que o efeito
do UNIVERSO responde por 8,77% a.a. dos 12,07% a.a. de excesso sobre o IBOVESPA, com
p = 0,0000 — e o unico resultado do trabalho com significancia forte e exatamente aquele
que o vies contamina. Sem medir o vies, o resultado principal nao e defensavel.

O QUE A COLETA FAZ
Monta uma lista de acoes de alta liquidez negociaveis na B3 em janeiro de 2011,
DELIBERADAMENTE incluindo nomes que depois colapsaram, foram incorporados ou sairam do
indice. Com essa base e possivel comparar, no mesmo periodo e com o mesmo criterio de
peso igual, o universo de 10 sobreviventes contra um universo montado ex ante.

O QUE A COLETA NAO E
Esta lista NAO e a composicao oficial do Ibovespa de 2012 e nao deve ser descrita como
tal no texto. E uma amostra de grandes nomes do periodo. A carteira teorica historica do
indice e publicada pela B3 e seria a fonte correta para uma replicacao exata; aqui o
objetivo e dimensionar a ordem de grandeza do vies, nao reproduzir o indice.

VIES RESIDUAL
Empresas totalmente deslistadas, como OGXP3 e MMXM3, costumam nao ter mais serie no
Yahoo. O que o script nao conseguir baixar fica registrado em 'universo_ampliado_faltantes.csv'
e precisa ser declarado: mesmo o universo ampliado continua com vies de sobrevivencia
residual, so que menor e agora conhecido.
"""

import json
import os
import time
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

import pandas as pd

DESTINO = '../mcp_servers/data_server'
DATA_INICIO = '2011-01-01'
DATA_FIM = '2026-06-01'
ESPERA_ENTRE_ATIVOS = 3
TENTATIVAS = 4

# Os 10 do estudo, para que o arquivo ampliado seja autossuficiente na comparacao.
TICKERS_ESTUDO = ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'WEGE3.SA', 'BBAS3.SA',
                  'BBDC4.SA', 'LREN3.SA', 'ABEV3.SA', 'SBSP3.SA', 'CMIG4.SA']

# Grandes nomes do periodo que NAO estao no estudo. A lista inclui de proposito os
# desastres (PDGR3, GFSA3, RSID3, OGXP3, MMXM3) e as empresas que deixaram de existir
# como ticker (FIBR3, NATU3, CIEL3, BTOW3, HGTX3): sao justamente esses casos que a
# escolha retrospectiva de 10 sobreviventes elimina da amostra.
TICKERS_AMPLIACAO = [
    # Materiais basicos e siderurgia
    'CSNA3.SA', 'USIM5.SA', 'GGBR4.SA', 'GOAU4.SA', 'BRKM5.SA', 'FIBR3.SA', 'SUZB3.SA',
    # Energia eletrica e saneamento
    'ELET3.SA', 'ELET6.SA', 'CPLE6.SA', 'CPFE3.SA', 'ENBR3.SA', 'LIGT3.SA', 'TRPL4.SA',
    'CESP6.SA', 'ELPL4.SA',
    # Petroleo e gas
    'PETR3.SA', 'CSAN3.SA', 'OGXP3.SA',
    # Construcao e imobiliario (o setor que concentrou as perdas do periodo)
    'PDGR3.SA', 'GFSA3.SA', 'CYRE3.SA', 'MRVE3.SA', 'RSID3.SA', 'BRML3.SA',
    # Mineracao e logistica
    'MMXM3.SA', 'CCRO3.SA', 'RAIL3.SA', 'EMBR3.SA', 'GOLL4.SA',
    # Consumo e varejo
    'PCAR3.SA', 'LAME4.SA', 'BTOW3.SA', 'HGTX3.SA', 'NATU3.SA', 'MRFG3.SA', 'BRFS3.SA',
    'JBSS3.SA', 'SMTO3.SA',
    # Financeiro, saude e telecom
    'ITSA4.SA', 'SANB11.SA', 'BBSE3.SA', 'B3SA3.SA', 'CIEL3.SA', 'HYPE3.SA', 'VIVT3.SA',
    'RADL3.SA', 'KLBN11.SA',
]


def baixar(ticker: str) -> pd.Series:
    """
    Fechamento ajustado via endpoint de chart do Yahoo.

    Nao usa yfinance: neste ambiente o cookie/crumb falha na verificacao de certificado
    e a biblioteca devolve DataFrame vazio, indistinguivel de ticker inexistente. O
    urllib direto funciona, e o ajuste por adjclose/close replica o auto_adjust=True.
    """
    p1 = int(pd.Timestamp(DATA_INICIO, tz='UTC').timestamp())
    p2 = int(pd.Timestamp(DATA_FIM, tz='UTC').timestamp())
    url = (f'https://query1.finance.yahoo.com/v8/finance/chart/{quote(ticker)}'
           f'?period1={p1}&period2={p2}&interval=1d')

    with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=45) as r:
        resultado = json.load(r)['chart']['result'][0]

    if 'timestamp' not in resultado:
        return pd.Series(dtype=float)

    indice = pd.to_datetime(resultado['timestamp'], unit='s', utc=True).tz_localize(None).normalize()
    fechamento = pd.Series(resultado['indicators']['quote'][0]['close'], index=indice)
    ajustado = resultado['indicators'].get('adjclose', [{}])[0].get('adjclose')
    if ajustado is not None:
        fechamento = pd.Series(ajustado, index=indice)
    return fechamento.dropna()


def baixar_com_backoff(ticker: str) -> tuple:
    """
    Devolve (serie, motivo_da_falha). O 404 do Yahoo e ambiguo: aparece tanto para
    ticker que nunca existiu como para excesso de requisicoes. Sem backoff, um bloqueio
    temporario seria registrado como empresa deslistada — e o vies de sobrevivencia que
    este script pretende medir voltaria pela porta dos fundos.
    """
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            serie = baixar(ticker)
            return (serie, '') if not serie.empty else (None, 'sem serie no Yahoo')
        except HTTPError as e:
            if e.code == 404 and tentativa < TENTATIVAS:
                espera = 10 * (2 ** (tentativa - 1))
                print(f'    404 (ambiguo) na tentativa {tentativa}; aguardando {espera}s')
                time.sleep(espera)
                continue
            return None, f'HTTP {e.code}'
        except Exception as e:
            if tentativa < TENTATIVAS:
                time.sleep(10)
                continue
            return None, type(e).__name__
    return None, 'esgotou tentativas (404 persistente)'


def coletar():
    todos = TICKERS_ESTUDO + TICKERS_AMPLIACAO + ['^BVSP']
    series, faltantes = {}, []

    print(f'Coletando {len(todos)} ativos ({DATA_INICIO} a {DATA_FIM})...')
    for i, ticker in enumerate(todos, 1):
        serie, motivo = baixar_com_backoff(ticker)
        if serie is None:
            print(f'[{i:2d}/{len(todos)}] {ticker:<12} FALHOU: {motivo}')
            faltantes.append({'Ticker': ticker, 'Motivo': motivo,
                              'No_Estudo': ticker in TICKERS_ESTUDO})
        else:
            series[ticker] = serie
            print(f'[{i:2d}/{len(todos)}] {ticker:<12} {len(serie):5d} obs  '
                  f'{serie.index.min().date()} a {serie.index.max().date()}')
        time.sleep(ESPERA_ENTRE_ATIVOS)

    if '^BVSP' not in series:
        raise RuntimeError('Sem ^BVSP nao ha calendario de pregao nem benchmark.')

    # Calendario do pregao, igual ao da base original.
    df = pd.DataFrame(series).reindex(series['^BVSP'].index)
    df.index.name = 'Date'

    # Sem dropna() nas colunas: um ativo que para de ser negociado em 2016 TEM de ficar
    # com NaN a partir dali. Preencher ou descartar reintroduziria o vies — o fim da
    # serie e justamente o evento que precisa ser observado.
    os.makedirs(DESTINO, exist_ok=True)
    caminho = f'{DESTINO}/cotacoes_universo_ampliado.csv'
    df.to_csv(caminho)

    cobertura = df.notna().sum()
    fim = df.apply(lambda s: s.last_valid_index())
    interrompidos = fim[fim < df.index.max() - pd.Timedelta(days=30)].sort_values()

    print(f'\n{len(df.columns)} series, {len(df)} pregoes '
          f'({df.index.min().date()} a {df.index.max().date()})')
    print(f'Cobertura mediana: {cobertura.median():.0f} pregoes')
    print(f'\nSeries que terminam antes do fim da amostra ({len(interrompidos)}):')
    for ticker, data in interrompidos.items():
        print(f'  {ticker:<12} ultimo pregao {data.date()}')

    if faltantes:
        pd.DataFrame(faltantes).to_csv(f'{DESTINO}/universo_ampliado_faltantes.csv', index=False)
        print(f'\n{len(faltantes)} ativos nao obtidos (ver universo_ampliado_faltantes.csv):')
        for f in faltantes:
            print(f'  {f["Ticker"]:<12} {f["Motivo"]}')
        print('Estes ausentes sao o vies residual: precisam ser declarados no texto.')

    print(f"\nSalvo em '{caminho}'.")


if __name__ == '__main__':
    coletar()
