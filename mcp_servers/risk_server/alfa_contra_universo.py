"""
Re-mede o alfa trocando o benchmark do IBOVESPA pelo universo ampliado em peso igual.

POR QUE ISTO E NECESSARIO
O teste de vies de sobrevivencia mostrou que as 10 acoes do estudo estao no percentil
99,6% de 5.000 carteiras aleatorias de 10 sorteadas do universo investivel em 2012. Logo
o "efeito de universo" (+8,5% a.a., p = 0,0001) nao e resultado do metodo: e o retorno de
uma escolha feita sabendo quem sobreviveu 14 anos.

O problema e que esse artefato esta DENTRO do alfa de Jensen contra o IBOVESPA. Dos
~14,5% a.a. de alfa do hibrido, uma parte grande e apenas a diferenca entre as 10 acoes
escolhidas e o indice — nada a ver com os agentes nem com o otimizador.

Trocar o benchmark resolve: contra o universo ampliado em peso igual (1/34), o alfa passa
a medir o que a arquitetura acrescenta DEPOIS de dado o universo, que e exatamente a
pergunta do trabalho ("o que cada camada acrescenta"). O universo ampliado e o benchmark
honesto porque e montado sem olhar o resultado — entram todas as acoes com historico
suficiente em 2012, sobreviventes ou nao.

RESSALVA QUE PRECISA IR PARA O TEXTO
O universo ampliado ainda e majoritariamente de sobreviventes: das 56 acoes da lista, 21
nao foram obtidas (HTTP 404), e entre elas estao justamente as deslistadas (OGXP3, MMXM3,
ELPL4, CESP6, BRML3, HGTX3). Com elas, o benchmark renderia menos e o alfa contra ele
seria MAIOR. Ou seja, o alfa calculado aqui e um piso conservador, e o vies medido no
outro teste e um piso otimista.
"""

import numpy as np
import pandas as pd

from inferencia_consolidada import JANELAS_ANO, jensen, poder, taxa_livre_risco
from vies_sobrevivencia import (CAMINHO_AMPLIADO, MIN_COBERTURA_INICIAL,
                                metricas, serie_de_janelas)

CAMINHO_RESULTADOS = 'resultado_backtest_economicAI.csv'
CAMINHO_COTACOES = '../data_server/cotacoes_b3_fechamentos.csv'
TICKERS_ESTUDO = ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'WEGE3.SA', 'BBAS3.SA',
                  'BBDC4.SA', 'LREN3.SA', 'ABEV3.SA', 'SBSP3.SA', 'CMIG4.SA']
TAXA_BPS = 10


def pesos_por_janela(res: pd.DataFrame) -> list:
    """Le a coluna Pesos, no formato 'TICKER=peso;TICKER=peso'."""
    saida = []
    for valor in res['Pesos']:
        if not isinstance(valor, str) or not valor.strip():
            saida.append({})
            continue
        d = {}
        for par in valor.split(';'):
            if '=' in par:
                t, p = par.split('=')
                d[t.strip()] = float(p)
        saida.append(d)
    return saida


def retorno_igual_estudo(acoes: pd.DataFrame, res: pd.DataFrame) -> pd.Series:
    """Universo do estudo em peso igual (1/10), nas janelas do backtest."""
    saida = []
    for _, linha in res.iterrows():
        trecho = acoes.loc[linha.Data_Rebalanceamento:linha.Data_Apuracao, TICKERS_ESTUDO]
        saida.append(float((trecho.iloc[-1] / trecho.iloc[0] - 1).mean()))
    return pd.Series(saida, index=res.index)


def retorno_ia_igual(acoes: pd.DataFrame, res: pd.DataFrame) -> pd.Series:
    """Cesta escolhida pelos agentes, em peso igual (remove o efeito do otimizador)."""
    saida = []
    for _, linha in res.iterrows():
        tickers = [t.strip() for t in str(linha.Ativos_Selecionados).split(';') if t.strip()]
        tickers = [t for t in tickers if t in acoes.columns]
        if not tickers:
            saida.append(np.nan)
            continue
        trecho = acoes.loc[linha.Data_Rebalanceamento:linha.Data_Apuracao, tickers]
        saida.append(float((trecho.iloc[-1] / trecho.iloc[0] - 1).mean()))
    return pd.Series(saida, index=res.index)


def executar():
    res = pd.read_csv(CAMINHO_RESULTADOS,
                      parse_dates=['Data_Rebalanceamento', 'Data_Apuracao'])
    acoes = (pd.read_csv(CAMINHO_COTACOES, parse_dates=['Date'])
             .set_index('Date').sort_index())
    px = (pd.read_csv(CAMINHO_AMPLIADO, parse_dates=['Date'])
          .set_index('Date').sort_index())

    inicio = res.Data_Rebalanceamento.iloc[0]
    investiveis = [c for c in px.columns if c != '^BVSP'
                   and px.loc[:inicio, c].dropna().shape[0] >= MIN_COBERTURA_INICIAL]

    rf = taxa_livre_risco(res)
    ampliado = serie_de_janelas(px, investiveis, res).fillna(0.0)
    ibov = res.Retorno_IBOV.astype(float)

    bracos = {
        'Hibrido (IA + Markowitz)': res.Retorno_Carteira.astype(float),
        'IA + 1/N': retorno_ia_igual(acoes, res),
        'Universo 1/10': retorno_igual_estudo(acoes, res),
    }
    if 'Retorno_Markowitz_Isolado' in res.columns:
        bracos['Markowitz isolado'] = res.Retorno_Markowitz_Isolado.astype(float)

    print('=' * 92)
    print('ALFA CONTRA O UNIVERSO AMPLIADO (benchmark sem vies de sobrevivencia na escolha)')
    print('=' * 92)
    print(f'{len(res)} janelas | {len(investiveis)} acoes no universo ampliado | '
          f'CDI medio {rf.mean()*JANELAS_ANO*100:.2f}% a.a.')

    m_amp, m_ibov = metricas(ampliado), metricas(ibov)
    print(f'\nBenchmark ampliado (1/{len(investiveis)}): total {m_amp["total"]*100:.1f}%, '
          f'CAGR {m_amp["cagr"]*100:.2f}%, vol {m_amp["vol"]*100:.2f}%')
    print(f'IBOVESPA:                total {m_ibov["total"]*100:.1f}%, '
          f'CAGR {m_ibov["cagr"]*100:.2f}%, vol {m_ibov["vol"]*100:.2f}%')

    linhas = []
    for nome_bench, bench in [('IBOVESPA', ibov),
                              (f'Universo ampliado 1/{len(investiveis)}', ampliado)]:
        print('\n' + '-' * 92)
        print(f'BENCHMARK: {nome_bench}')
        print('-' * 92)
        print(f'{"Braco":<30}{"Alfa a.a.":>12}{"EP":>9}{"t":>8}{"p":>9}'
              f'{"Beta":>8}{"t(b=1)":>9}{"p(b=1)":>9}{"R2":>7}')
        for nome, serie in bracos.items():
            s = serie.astype(float)
            mask = s.notna() & bench.notna()
            j = jensen((s - rf)[mask].values, (bench - rf)[mask].values)
            print(f'{nome:<30}{j["alfa_ano"]*100:>11.2f}%{j["ep_alfa_ano"]*100:>8.2f}%'
                  f'{j["t_alfa"]:>8.2f}{j["p_alfa"]:>9.4f}{j["beta"]:>8.3f}'
                  f'{j["t_beta_vs_1"]:>9.2f}{j["p_beta_vs_1"]:>9.4f}{j["r2"]:>7.2f}')
            linhas.append({'benchmark': nome_bench, 'braco': nome, **j})

    print('\n' + '-' * 92)
    print('PODER: BRACOS CONTRA O UNIVERSO AMPLIADO')
    print('-' * 92)
    print(f'{"Comparacao":<46}{"Efeito a.a.":>13}{"MDE a.a.":>11}{"n":>6}{"n necess.":>11}')
    for nome, serie in bracos.items():
        s = serie.astype(float)
        mask = s.notna() & ampliado.notna()
        p = poder((s - ampliado)[mask])
        print(f'{nome + " vs ampliado":<46}{p["efeito_ano"]*100:>12.2f}%'
              f'{p["mde_ano"]*100:>10.2f}%{p["n"]:>6}{p["n_necessario"]:>11.0f}')

    pd.DataFrame(linhas).to_csv('resultado_alfa_contra_universo.csv', index=False)
    print('\nSalvo: resultado_alfa_contra_universo.csv')


if __name__ == '__main__':
    executar()
