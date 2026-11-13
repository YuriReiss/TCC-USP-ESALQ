"""
Custos de transacao: o teste que decide se a estrategia existe fora do papel.

O backtest apura retorno bruto. Com rebalanceamento a cada 21 dias e carteiras de 2 a 4
ativos, o giro e alto, e a pergunta obvia de qualquer avaliador com vivencia de mercado e
se o excesso sobrevive ao custo. Este script responde com numeros.

Metodo:
  1. Os pesos no fim da janela nao sao os do inicio: eles derivam com os retornos dos
     ativos. Comparar os pesos novos com os pesos ALVO anteriores superestimaria o giro,
     porque parte do ajuste o mercado ja fez. Por isso a derivacao e reconstruida.
  2. Giro de uma ponta = 0,5 * soma(|peso_novo - peso_derivado|).
     O custo incide sobre as duas pontas, logo custo = soma(|delta|) * taxa_por_ordem.
  3. O custo entra como reducao do retorno da janela, antes da capitalizacao composta.

A taxa de referencia de 10 bps por ordem cobre emolumentos e liquidacao da B3 (~3,25 bps)
mais corretagem institucional e deslizamento em blue chips de alta liquidez. A tabela de
sensibilidade vai de 5 a 50 bps porque a premissa e discutivel e o resultado depende dela.
"""

import numpy as np
import pandas as pd
from scipy import stats

CAMINHO_RESULTADOS = 'resultado_backtest_economicAI.csv'
CAMINHO_COTACOES = '../data_server/cotacoes_b3_fechamentos.csv'
COLUNAS_MACRO = ['^BVSP', 'USDBRL=X', 'IFIX.SA']
JANELAS_ANO = 252 / 21
TAXAS_BPS = [0, 5, 10, 20, 50]
TAXA_REFERENCIA_BPS = 10


def ler_pesos(texto: str) -> dict:
    if not isinstance(texto, str) or not texto:
        return {}
    return {par.split('=')[0]: float(par.split('=')[1]) for par in texto.split(';') if '=' in par}


def carregar():
    res = pd.read_csv(CAMINHO_RESULTADOS, parse_dates=['Data_Rebalanceamento', 'Data_Apuracao'])
    px = pd.read_csv(CAMINHO_COTACOES, parse_dates=['Date']).set_index('Date').sort_index()
    acoes = px.drop(columns=[c for c in COLUNAS_MACRO if c in px.columns], errors='ignore')
    return res, acoes


def retornos_por_janela(res: pd.DataFrame, acoes: pd.DataFrame) -> list:
    """Retorno de cada ativo em cada janela de apuracao."""
    saida = []
    for _, linha in res.iterrows():
        trecho = acoes.loc[linha.Data_Rebalanceamento:linha.Data_Apuracao]
        saida.append((trecho.iloc[-1] / trecho.iloc[0] - 1) if len(trecho) >= 2 else None)
    return saida


def simular(pesos_por_janela: list, retornos: list, taxa_bps: float):
    """
    Retorno liquido por janela e giro, dada uma sequencia de carteiras-alvo.

    Devolve (retornos_liquidos, giros_uma_ponta).
    """
    taxa = taxa_bps / 10_000
    liquidos, giros = [], []
    derivados = {}

    for alvo, ret in zip(pesos_por_janela, retornos):
        if ret is None or not alvo:
            liquidos.append(0.0)
            giros.append(0.0)
            continue

        tickers = set(alvo) | set(derivados)
        negociado = sum(abs(alvo.get(t, 0.0) - derivados.get(t, 0.0)) for t in tickers)
        custo = negociado * taxa

        bruto = sum(p * ret.get(t, 0.0) for t, p in alvo.items())
        liquidos.append(bruto - custo)
        giros.append(negociado / 2)

        # Deriva os pesos com o mercado: e daqui que parte o proximo rebalanceamento.
        if bruto <= -1:
            derivados = {}
        else:
            derivados = {t: p * (1 + ret.get(t, 0.0)) / (1 + bruto) for t, p in alvo.items()}

    return pd.Series(liquidos), pd.Series(giros)


def metricas(r: pd.Series) -> dict:
    cap = (1 + r).cumprod()
    anos = len(r) / JANELAS_ANO
    return {
        'total': cap.iloc[-1] - 1,
        'cagr': cap.iloc[-1] ** (1 / anos) - 1,
        'sharpe': r.mean() / r.std() * np.sqrt(JANELAS_ANO),
        'mdd': (cap / cap.cummax() - 1).min(),
    }


def executar():
    res, acoes = carregar()
    retornos = retornos_por_janela(res, acoes)
    universo = list(acoes.columns)

    # Tres bracos, todos rebalanceados nas mesmas datas:
    #   hibrido  = pesos de Markowitz sobre o consenso dos agentes
    #   ia_1n    = pesos iguais sobre o consenso (isola a selecao do otimizador)
    #   passivo  = 1/10 fixo sobre o universo (giro vem so da derivacao)
    bracos = {
        'Hibrido (IA + Markowitz)': [ler_pesos(p) for p in res.Pesos],
        'IA + 1/N': [
            {t: 1 / len(sel) for t in sel}
            for sel in ([a for a in str(s).split(';') if a in universo] or [universo]
                        for s in res.Ativos_Selecionados)
        ],
        'Universo 1/10': [{t: 1 / len(universo) for t in universo}] * len(res),
    }

    print('=' * 78)
    print('IMPACTO DOS CUSTOS DE TRANSACAO')
    print('=' * 78)
    print(f'Janelas: {len(res)}  |  rebalanceamento a cada 21 pregoes  |  '
          f'{len(res) / JANELAS_ANO:.1f} anos')
    print()

    giro_ref = {}
    for nome, pesos in bracos.items():
        _, giros = simular(pesos, retornos, 0)
        giro_ref[nome] = giros
        print(f'{nome:<26} giro medio por rebalanceamento: {giros.mean()*100:6.2f}%  '
              f'(anualizado {giros.mean()*JANELAS_ANO*100:7.1f}%)')

    print()
    print('-' * 78)
    print(f'{"Taxa/ordem":<12}{"Braco":<26}{"Retorno total":>16}{"CAGR":>9}{"Sharpe":>9}{"MaxDD":>9}')
    print('-' * 78)
    guardados = {}
    for taxa in TAXAS_BPS:
        for nome, pesos in bracos.items():
            liq, _ = simular(pesos, retornos, taxa)
            m = metricas(liq)
            rotulo = f'{taxa} bps' if nome == list(bracos)[0] else ''
            print(f'{rotulo:<12}{nome:<26}{m["total"]*100:>15.1f}%{m["cagr"]*100:>8.2f}%'
                  f'{m["sharpe"]:>9.2f}{m["mdd"]*100:>8.2f}%')
            if taxa == TAXA_REFERENCIA_BPS:
                guardados[nome] = liq
        print()

    ibov = res.Retorno_IBOV
    print('-' * 78)
    print(f'TESTE CONTRA O IBOVESPA A {TAXA_REFERENCIA_BPS} BPS POR ORDEM')
    for nome, liq in guardados.items():
        t, p = stats.ttest_rel(liq, ibov)
        print(f'  {nome:<26} excesso {(liq-ibov).mean()*JANELAS_ANO*100:+7.2f}%/ano   '
              f't={t:+.3f}  p={p:.4f}')

    print('-' * 78)
    print('CUSTO DE EQUILIBRIO (taxa que anula o excesso sobre o IBOVESPA)')
    for nome, pesos in bracos.items():
        bruto, giros = simular(pesos, retornos, 0)
        excesso = (bruto - ibov).mean()
        custo_por_bps = giros.mean() * 2 / 10_000
        breakeven = excesso / custo_por_bps if custo_por_bps > 0 else np.inf
        alcance = 'inalcancavel (giro nulo)' if np.isinf(breakeven) else f'{breakeven:7.0f} bps por ordem'
        print(f'  {nome:<26} {alcance}')

    detalhe = pd.DataFrame({'Data_Rebalanceamento': res.Data_Rebalanceamento,
                            'Retorno_Bruto': res.Retorno_Carteira,
                            'Retorno_IBOV': ibov})
    for nome, liq in guardados.items():
        detalhe[f'Liquido_{nome.split()[0]}'] = liq
        detalhe[f'Giro_{nome.split()[0]}'] = giro_ref[nome]
    detalhe.to_csv('resultado_custos_transacao.csv', index=False)
    print('=' * 78)
    print("Detalhe por janela salvo em 'resultado_custos_transacao.csv'.")


if __name__ == '__main__':
    executar()
