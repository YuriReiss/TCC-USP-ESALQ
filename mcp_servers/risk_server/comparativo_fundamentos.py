"""
Efeito de dar fundamentos point-in-time aos agentes.

Os dois backtests percorrem as MESMAS janelas, com o mesmo universo, o mesmo otimizador
e o mesmo benchmark. A unica diferenca e o payload entregue ao LLM: o arquivo
SEM_FUNDAMENTOS so tinha estatisticas de preco; o atual acrescenta ROE, Margem_Liquida,
Crescimento_Receita, Crescimento_Lucro e Alavancagem do ultimo balanco publico.

Por isso o teste pareado aqui isola a contribuicao da informacao fundamentalista, coisa
que a comparacao contra o IBOVESPA nao faz.
"""

import numpy as np
import pandas as pd
from scipy import stats

COM = 'resultado_backtest_economicAI.csv'
SEM = 'resultado_backtest_economicAI_SEM_FUNDAMENTOS.csv'
CAPITAL = 100_000.0
JANELAS_ANO = 252 / 21


def metricas(retornos: pd.Series) -> dict:
    capital = CAPITAL * (1 + retornos).cumprod()
    anos = len(retornos) / JANELAS_ANO
    pico = capital.cummax()
    return {
        'Retorno_Total': capital.iloc[-1] / CAPITAL - 1,
        'CAGR': (capital.iloc[-1] / CAPITAL) ** (1 / anos) - 1,
        'Volatilidade': retornos.std() * np.sqrt(JANELAS_ANO),
        'Sharpe': (retornos.mean() / retornos.std()) * np.sqrt(JANELAS_ANO),
        'Max_Drawdown': (capital / pico - 1).min(),
        'Janelas_Positivas': (retornos > 0).mean(),
    }


def jaccard(a: str, b: str) -> float:
    """Sobreposicao entre as duas cestas da mesma janela."""
    sa, sb = set(str(a).split(';')), set(str(b).split(';'))
    return len(sa & sb) / len(sa | sb) if sa | sb else np.nan


def comparar():
    com = pd.read_csv(COM, parse_dates=['Data_Rebalanceamento'])
    sem = pd.read_csv(SEM, parse_dates=['Data_Rebalanceamento'])

    # O backtest com fundamentos pode estar incompleto; compara-se so o trecho comum,
    # senao a diferenca viraria efeito de periodo em vez de efeito de informacao.
    par = com.merge(sem, on='Data_Rebalanceamento', suffixes=('_com', '_sem'))

    m_com = metricas(par.Retorno_Carteira_com)
    m_sem = metricas(par.Retorno_Carteira_sem)
    m_ibov = metricas(par.Retorno_IBOV_com)

    t_stat, p_value = stats.ttest_rel(par.Retorno_Carteira_com, par.Retorno_Carteira_sem)
    sobreposicao = par.apply(
        lambda l: jaccard(l.Ativos_Selecionados_com, l.Ativos_Selecionados_sem), axis=1)
    n_com = par.Ativos_Selecionados_com.str.count(';').add(1)
    n_sem = par.Ativos_Selecionados_sem.str.count(';').add(1)

    print('=' * 72)
    print('EFEITO DOS FUNDAMENTOS POINT-IN-TIME NA SELECAO DOS AGENTES')
    print('=' * 72)
    print(f'Janelas comparadas: {len(par)} '
          f'({par.Data_Rebalanceamento.min().date()} a {par.Data_Rebalanceamento.max().date()})')
    if len(com) != len(sem):
        print(f'  [aviso] backtest com fundamentos tem {len(com)} janelas; '
              f'baseline tem {len(sem)}.')
    print('-' * 72)
    print(f'{"Metrica":<22}{"COM fund.":>16}{"SEM fund.":>16}{"IBOVESPA":>16}')
    for chave, rotulo in [('Retorno_Total', 'Retorno acumulado'), ('CAGR', 'CAGR'),
                          ('Volatilidade', 'Volatilidade anual'),
                          ('Max_Drawdown', 'Max drawdown'),
                          ('Janelas_Positivas', 'Janelas positivas')]:
        print(f'{rotulo:<22}{m_com[chave]*100:>15.2f}%{m_sem[chave]*100:>15.2f}%'
              f'{m_ibov[chave]*100:>15.2f}%')
    print(f'{"Sharpe (rf=0)":<22}{m_com["Sharpe"]:>16.2f}{m_sem["Sharpe"]:>16.2f}'
          f'{m_ibov["Sharpe"]:>16.2f}')
    print('-' * 72)
    print('TESTE T PAREADO: COM fundamentos vs SEM fundamentos')
    print(f'Retorno medio por janela: {par.Retorno_Carteira_com.mean()*100:.3f}% vs '
          f'{par.Retorno_Carteira_sem.mean()*100:.3f}%')
    print(f'Estatistica T: {t_stat:.4f}   p-value: {p_value:.4f}')
    if p_value < 0.05:
        print('-> A informacao fundamentalista mudou o retorno de forma significante a 95%.')
    else:
        print('-> Diferenca nao significante a 95%: com estas 10 acoes e este otimizador,')
        print('   o fundamento nao se traduziu em retorno distinguivel de ruido.')
    print('-' * 72)
    print('QUANTO A SELECAO MUDOU')
    print(f'Jaccard medio entre as cestas: {sobreposicao.mean():.3f} '
          f'(mediana {sobreposicao.median():.3f})')
    print(f'Janelas com cesta identica:   {(sobreposicao == 1).sum()}/{len(par)}')
    print(f'Janelas sem ativo em comum:   {(sobreposicao == 0).sum()}/{len(par)}')
    print(f'Tamanho medio da cesta:       {n_com.mean():.2f} com vs {n_sem.mean():.2f} sem')
    print('=' * 72)

    par.assign(Jaccard=sobreposicao).to_csv('resultado_comparativo_fundamentos.csv', index=False)
    print("Detalhe por janela salvo em 'resultado_comparativo_fundamentos.csv'.")


if __name__ == '__main__':
    comparar()
