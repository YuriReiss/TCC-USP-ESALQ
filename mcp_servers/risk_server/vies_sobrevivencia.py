"""
Quanto do resultado vem de ter escolhido as 10 acoes sabendo quem sobreviveu.

POR QUE ESTE E O TESTE MAIS IMPORTANTE DO TRABALHO
A decomposicao do excesso atribui 8,77% a.a. ao efeito do UNIVERSO, com p = 0,0000. E o
unico resultado com significancia forte, e ele e inteiramente uma propriedade das 10
acoes escolhidas — nao da camada de IA nem do otimizador. Essas 10 foram selecionadas em
2025/2026 sem regra documentada, e todas as 10 estao vivas e liquidas depois de 14 anos.
Se a escolha retrospectiva explica o excesso, o resultado principal cai.

O TESTE
Duas perguntas, respondidas sobre o universo ampliado (acoes de alta liquidez
negociaveis em 2011, incluindo as que depois colapsaram):

  1. ONDE AS 10 CAEM NA DISTRIBUICAO? Sorteiam-se milhares de carteiras de 10 acoes do
     universo ampliado, com peso igual e rebalanceamento nas mesmas datas. O percentil
     das 10 escolhidas nessa distribuicao e a medida direta do vies: percentil 50
     significaria escolha neutra; percentil 95 significaria que a escolha capturou o que
     so se sabia depois.

  2. O QUE SOBRA DO EXCESSO? O efeito do universo e recalculado trocando o benchmark das
     10 sobreviventes pelo universo ampliado inteiro em peso igual. O que resta e o
     excesso que nao vem da selecao retrospectiva.

TRATAMENTO DE DESLISTAGEM
Quando uma acao para de ser negociada no meio de uma janela, a posicao nao desaparece: e
liquidada no ultimo preco disponivel e o capital vai para as demais acoes da carteira. E
a hipotese mais favoravel possivel ao investidor (supoe saida sem desconto de
liquidez), logo o vies medido aqui e um PISO: o vies real e pelo menos este.

O que o Yahoo nao devolveu (empresas totalmente deslistadas, como OGXP3 e MMXM3) fica
fora da amostra e precisa ser declarado: o universo ampliado tem vies residual, menor e
conhecido, mas nao nulo.
"""

import numpy as np
import pandas as pd
from scipy import stats

CAMINHO_AMPLIADO = '../data_server/cotacoes_universo_ampliado.csv'
# Deste arquivo só se aproveitam as datas das janelas, que vêm do calendário de pregões e
# não da decisão dos agentes. Por isso aponta para o backup: ele é estável enquanto o
# backtest reescreve o arquivo corrente, e as datas são as mesmas nas duas execuções.
CAMINHO_RESULTADOS = 'resultado_backtest_economicAI_KMEANS_JANELA252.csv'
TICKERS_ESTUDO = ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'WEGE3.SA', 'BBAS3.SA',
                  'BBDC4.SA', 'LREN3.SA', 'ABEV3.SA', 'SBSP3.SA', 'CMIG4.SA']
JANELAS_ANO = 252 / 21
N_SORTEIOS = 5_000
SEMENTE = 42
# Minimo de pregoes com cotacao para um ativo entrar nos sorteios. Uma serie que comeca
# em 2014 nao pode compor uma carteira de 2012, e tratar isso como ausencia de dados
# faria o sorteio comparar periodos diferentes.
MIN_COBERTURA_INICIAL = 200


def carregar():
    px = (pd.read_csv(CAMINHO_AMPLIADO, parse_dates=['Date'])
          .set_index('Date').sort_index())
    res = pd.read_csv(CAMINHO_RESULTADOS,
                      parse_dates=['Data_Rebalanceamento', 'Data_Apuracao'])
    return px, res


def retorno_carteira_igual(px: pd.DataFrame, tickers: list, ini, fim) -> float:
    """
    Retorno de uma carteira de peso igual entre duas datas, com liquidacao de deslistados.

    Para cada acao, o retorno e medido do primeiro ao ultimo preco DISPONIVEL dentro da
    janela. Uma acao que deixa de ser cotada no meio do caminho contribui com o retorno
    realizado ate a ultima cotacao; a alternativa (descartar o ativo) apagaria justamente
    a perda que o vies de sobrevivencia esconde.
    """
    trecho = px.loc[ini:fim, tickers]
    if len(trecho) < 2:
        return np.nan

    retornos = []
    for t in tickers:
        s = trecho[t].dropna()
        # Sem preco no inicio da janela: a acao nao era investivel, nao entra.
        if len(s) < 2 or s.index[0] > trecho.index[min(4, len(trecho) - 1)]:
            continue
        retornos.append(s.iloc[-1] / s.iloc[0] - 1)

    return float(np.mean(retornos)) if retornos else np.nan


def serie_de_janelas(px: pd.DataFrame, tickers: list, res: pd.DataFrame) -> pd.Series:
    return pd.Series([
        retorno_carteira_igual(px, tickers, ini, fim)
        for ini, fim in zip(res.Data_Rebalanceamento, res.Data_Apuracao)
    ])


def metricas(r: pd.Series) -> dict:
    r = r.fillna(0.0)
    cap = (1 + r).cumprod()
    anos = len(r) / JANELAS_ANO
    return {
        'total': cap.iloc[-1] - 1,
        'cagr': cap.iloc[-1] ** (1 / anos) - 1,
        'vol': r.std() * np.sqrt(JANELAS_ANO),
        'mdd': (cap / cap.cummax() - 1).min(),
        'media_janela': r.mean(),
    }


def executar():
    px, res = carregar()
    ibov = res.Retorno_IBOV.reset_index(drop=True)
    inicio = res.Data_Rebalanceamento.min()

    candidatos = [c for c in px.columns if c != '^BVSP']
    cobertura_inicial = px.loc[:inicio, candidatos].notna().sum()
    investiveis = [c for c in candidatos if cobertura_inicial[c] >= MIN_COBERTURA_INICIAL]
    ausentes_estudo = [t for t in TICKERS_ESTUDO if t not in investiveis]

    print('=' * 86)
    print('VIES DE SOBREVIVENCIA NA ESCOLHA DO UNIVERSO')
    print('=' * 86)
    print(f'Universo ampliado coletado: {len(candidatos)} acoes')
    print(f'Investiveis em {inicio.date()} (>= {MIN_COBERTURA_INICIAL} pregoes antes): '
          f'{len(investiveis)}')
    excluidos = sorted(set(candidatos) - set(investiveis))
    if excluidos:
        print(f'Excluidas por historico curto ({len(excluidos)}): {", ".join(excluidos)}')
    if ausentes_estudo:
        print(f'[ATENCAO] acoes do estudo fora dos investiveis: {ausentes_estudo}')
    print(f'Janelas: {len(res)} ({inicio.date()} a {res.Data_Apuracao.max().date()})')

    # Quantas series morrem no meio da amostra: a materia-prima do vies.
    ultimo = px[investiveis].apply(lambda s: s.last_valid_index())
    mortas = ultimo[ultimo < px.index.max() - pd.Timedelta(days=30)]
    print('-' * 86)
    print(f'Series interrompidas antes do fim da amostra: {len(mortas)}/{len(investiveis)}')
    for t, d in mortas.sort_values().items():
        print(f'  {t:<12} ultimo pregao {d.date()}')
    if len(mortas) == 0:
        print('  Nenhuma. O universo ampliado ainda e majoritariamente de sobreviventes:')
        print('  o vies medido abaixo e um piso bastante otimista.')

    estudo = serie_de_janelas(px, TICKERS_ESTUDO, res)
    ampliado = serie_de_janelas(px, investiveis, res)

    print('-' * 86)
    print('DESEMPENHO EM PESO IGUAL, MESMAS JANELAS')
    print(f'{"Carteira":<34}{"Total":>12}{"CAGR":>9}{"Vol":>9}{"MaxDD":>10}')
    for rotulo, serie in [('10 do estudo (1/10)', estudo),
                          (f'Universo ampliado (1/{len(investiveis)})', ampliado),
                          ('IBOVESPA', ibov)]:
        m = metricas(serie)
        print(f'{rotulo:<34}{m["total"]*100:>11.1f}%{m["cagr"]*100:>8.2f}%'
              f'{m["vol"]*100:>8.2f}%{m["mdd"]*100:>9.2f}%')

    # 1. Percentil das 10 escolhidas numa distribuicao de carteiras aleatorias de 10.
    rng = np.random.default_rng(SEMENTE)
    cagrs, excessos_ibov = [], []
    for _ in range(N_SORTEIOS):
        sorteio = list(rng.choice(investiveis, size=len(TICKERS_ESTUDO), replace=False))
        serie = serie_de_janelas(px, sorteio, res)
        cagrs.append(metricas(serie)['cagr'])
        excessos_ibov.append((serie.fillna(0.0) - ibov).mean() * JANELAS_ANO)

    cagrs = np.array(cagrs)
    excessos_ibov = np.array(excessos_ibov)
    cagr_estudo = metricas(estudo)['cagr']
    excesso_estudo = (estudo.fillna(0.0) - ibov).mean() * JANELAS_ANO
    percentil_cagr = (cagrs < cagr_estudo).mean() * 100
    percentil_excesso = (excessos_ibov < excesso_estudo).mean() * 100

    print('-' * 86)
    print(f'TESTE 1 - AS 10 ESCOLHIDAS CONTRA {N_SORTEIOS} CARTEIRAS ALEATORIAS DE 10')
    print(f'{"Metrica":<26}{"Escolhidas":>13}{"Mediana":>11}{"p5":>10}{"p95":>10}{"Percentil":>12}')
    print(f'{"CAGR":<26}{cagr_estudo*100:>12.2f}%{np.median(cagrs)*100:>10.2f}%'
          f'{np.percentile(cagrs, 5)*100:>9.2f}%{np.percentile(cagrs, 95)*100:>9.2f}%'
          f'{percentil_cagr:>11.1f}%')
    print(f'{"Excesso s/ IBOV a.a.":<26}{excesso_estudo*100:>12.2f}%'
          f'{np.median(excessos_ibov)*100:>10.2f}%{np.percentile(excessos_ibov, 5)*100:>9.2f}%'
          f'{np.percentile(excessos_ibov, 95)*100:>9.2f}%{percentil_excesso:>11.1f}%')
    print()
    if percentil_cagr >= 90:
        print('-> As 10 estao no decil superior do que era sorteavel. A escolha do universo')
        print('   capturou desempenho que nao estava disponivel ex ante: o vies e material e')
        print('   o efeito de universo NAO pode ser apresentado como resultado do metodo.')
    elif percentil_cagr >= 70:
        print('-> As 10 estao acima da mediana de forma relevante. Parte do efeito de universo')
        print('   e selecao retrospectiva e precisa ser declarada como limitacao.')
    else:
        print('-> As 10 nao se destacam do que era sorteavel: o efeito de universo sobrevive')
        print('   ao controle de sobrevivencia, o que fortalece bastante o resultado.')

    # 2. Efeito do universo medido contra o ampliado, nao contra o IBOV.
    dif_vs_ibov = estudo.fillna(0.0) - ibov
    dif_vs_ampliado = estudo.fillna(0.0) - ampliado.fillna(0.0)
    t_ibov, p_ibov = stats.ttest_1samp(dif_vs_ibov, 0)
    t_amp, p_amp = stats.ttest_1samp(dif_vs_ampliado, 0)

    print('-' * 86)
    print('TESTE 2 - EFEITO DO UNIVERSO COM E SEM CONTROLE DE SOBREVIVENCIA')
    print(f'{"Comparacao":<44}{"Efeito a.a.":>13}{"t":>9}{"p":>9}')
    print(f'{"10 do estudo vs IBOVESPA (como estava)":<44}'
          f'{dif_vs_ibov.mean()*JANELAS_ANO*100:>12.2f}%{t_ibov:>9.3f}{p_ibov:>9.4f}')
    print(f'{"10 do estudo vs universo ampliado":<44}'
          f'{dif_vs_ampliado.mean()*JANELAS_ANO*100:>12.2f}%{t_amp:>9.3f}{p_amp:>9.4f}')
    print(f'{"Universo ampliado vs IBOVESPA":<44}'
          f'{(ampliado.fillna(0.0)-ibov).mean()*JANELAS_ANO*100:>12.2f}%')
    print()
    print('A primeira linha e o efeito de universo publicado. A segunda e o que sobra dele')
    print('depois de trocar o benchmark por um universo montado sem olhar quem sobreviveu.')

    pd.DataFrame({'CAGR_Sorteio': cagrs, 'Excesso_IBOV_Sorteio': excessos_ibov}) \
        .to_csv('resultado_vies_sorteios.csv', index=False)
    pd.DataFrame({'Data_Rebalanceamento': res.Data_Rebalanceamento,
                  'Retorno_10_Estudo': estudo, 'Retorno_Universo_Ampliado': ampliado,
                  'Retorno_IBOV': ibov}).to_csv('resultado_vies_sobrevivencia.csv', index=False)
    print('=' * 86)
    print("Salvos: resultado_vies_sorteios.csv, resultado_vies_sobrevivencia.csv")


if __name__ == '__main__':
    executar()
