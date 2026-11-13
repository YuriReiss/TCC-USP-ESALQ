"""
Inferencia consolidada: as tabelas que vao para a dissertacao.

Centraliza tudo o que e afirmacao estatistica, para que o texto nao tenha numeros vindos
de scripts diferentes com premissas diferentes. Tres decisoes metodologicas estao aqui:

1. TAXA LIVRE DE RISCO REAL. O CDI diario (BCB/SGS 12) e capitalizado dentro de cada
   janela de apuracao. A premissa anterior de Selic fixa em 10,5% a.a. subestimava o
   excesso em 2020 (CDI 2,76%) e superestimava em 2025 (CDI 14,32%).

2. ALFA DE JENSEN EM VEZ DE TESTE T PAREADO. O teste pareado contra o IBOVESPA
   compara retornos sem descontar a exposicao ao mercado, o que equivale a assumir
   beta = 1. O beta da carteira esta perto de 0,6: o teste pareado cobra da estrategia a
   variancia de um risco de mercado que ela nao carrega, e por isso tem pouco poder. A
   regressao R_p - rf = alfa + beta(R_m - rf) + e remove essa variancia, e o erro padrao
   do alfa fica menor que o da diferenca bruta. Com rebalanceamento a cada 21 pregoes as
   janelas nao se sobrepoem, mas os residuos ainda podem ter autocorrelacao de ordem 1
   por efeito de calendario, por isso o erro padrao e Newey-West (Bartlett, 1 lag).

3. BETA TESTADO CONTRA 1, NAO CONTRA 0. A hipotese interessante nao e "a carteira tem
   exposicao ao mercado" (tem, obviamente), e sim "a carteira carrega menos risco
   sistemico que o indice". Logo t = (beta - 1) / EP(beta).

A decomposicao separa o que vem do universo, o que vem da selecao dos agentes e o que
vem do otimizador. E a unica forma honesta de responder o que a camada de IA contribuiu:
comparar a carteira final com o IBOVESPA mede os tres efeitos somados.
"""

import numpy as np
import pandas as pd
from scipy import stats

from custos_transacao import (JANELAS_ANO, TAXA_REFERENCIA_BPS, carregar, ler_pesos,
                              retornos_por_janela, simular)

CAMINHO_CDI = '../data_server/cdi_diario.csv'


def taxa_livre_risco(res: pd.DataFrame) -> pd.Series:
    """CDI capitalizado dentro de cada janela de apuracao."""
    cdi = pd.read_csv(CAMINHO_CDI, parse_dates=['Date']).set_index('Date').CDI_Dia.sort_index()
    return pd.Series([
        (1 + cdi.loc[ini:fim].iloc[1:]).prod() - 1
        for ini, fim in zip(res.Data_Rebalanceamento, res.Data_Apuracao)
    ])


def jensen(excesso_carteira: np.ndarray, excesso_mercado: np.ndarray) -> dict:
    """
    OLS de alfa e beta com erro padrao Newey-West (Bartlett, 1 lag).

    Feito a mao porque statsmodels nao esta no ambiente. A matriz robusta e
    V = (X'X)^-1 S (X'X)^-1 com S = X'diag(e^2)X + 0.5(G + G'), onde G e a
    autocovariancia de ordem 1 dos momentos.
    """
    n = len(excesso_carteira)
    X = np.column_stack([np.ones(n), excesso_mercado])
    beta_hat = np.linalg.lstsq(X, excesso_carteira, rcond=None)[0]
    residuo = excesso_carteira - X @ beta_hat

    momentos = X * residuo[:, None]
    S = momentos.T @ momentos
    G = momentos[1:].T @ momentos[:-1]
    S = S + 0.5 * (G + G.T)

    XtX_inv = np.linalg.inv(X.T @ X)
    V = XtX_inv @ S @ XtX_inv
    ep = np.sqrt(np.diag(V))
    gl = n - 2

    alfa, beta = beta_hat
    t_alfa = alfa / ep[0]
    t_beta_um = (beta - 1) / ep[1]
    critico = stats.t.ppf(0.975, gl)

    return {
        'alfa_janela': alfa,
        'alfa_ano': alfa * JANELAS_ANO,
        'ep_alfa_ano': ep[0] * JANELAS_ANO,
        't_alfa': t_alfa,
        'p_alfa': 2 * (1 - stats.t.cdf(abs(t_alfa), gl)),
        'beta': beta,
        'ep_beta': ep[1],
        't_beta_vs_1': t_beta_um,
        'p_beta_vs_1': 2 * (1 - stats.t.cdf(abs(t_beta_um), gl)),
        'ic_beta': (beta - critico * ep[1], beta + critico * ep[1]),
        'r2': 1 - residuo.var() / excesso_carteira.var(),
    }


def descritivas(r: pd.Series, rf: pd.Series) -> dict:
    cap = (1 + r).cumprod()
    anos = len(r) / JANELAS_ANO
    excesso = r - rf
    baixo = r[r < 0]
    return {
        'total': cap.iloc[-1] - 1,
        'cagr': cap.iloc[-1] ** (1 / anos) - 1,
        'vol': r.std() * np.sqrt(JANELAS_ANO),
        'sharpe': excesso.mean() / r.std() * np.sqrt(JANELAS_ANO),
        'semivol': baixo.std() * np.sqrt(JANELAS_ANO) if len(baixo) > 1 else np.nan,
        'sortino': excesso.mean() / baixo.std() * np.sqrt(JANELAS_ANO) if len(baixo) > 1 else np.nan,
        'mdd': (cap / cap.cummax() - 1).min(),
        'positivas': (r > 0).mean(),
        'var95': np.percentile(r, 5),
        'cvar95': r[r <= np.percentile(r, 5)].mean(),
    }


def assimetria(r: pd.Series, mercado: pd.Series) -> dict:
    """Quanto a carteira acompanha o indice na alta e quanto escapa dele na baixa."""
    alta, baixa = mercado > 0, mercado < 0
    captura_alta = r[alta].mean() / mercado[alta].mean()
    captura_baixa = r[baixa].mean() / mercado[baixa].mean()
    t_baixa, p_baixa = stats.ttest_rel(r[baixa], mercado[baixa])
    return {
        'n_alta': int(alta.sum()),
        'n_baixa': int(baixa.sum()),
        'captura_alta': captura_alta,
        'captura_baixa': captura_baixa,
        'razao': captura_alta / captura_baixa if captura_baixa else np.nan,
        't_baixa': t_baixa,
        'p_baixa': p_baixa,
    }


def poder(diferenca: pd.Series) -> dict:
    """
    Efeito minimo detectavel e tamanho de amostra necessario, a 95% com poder de 80%.

    MDE = 2,8 * sd / raiz(n); n_necessario = (2,8 * sd / media)^2. Serve para separar
    "nao ha efeito" de "o teste nao consegue ver o efeito que ha".
    """
    n, sd, media = len(diferenca), diferenca.std(), diferenca.mean()
    mde = 2.8 * sd / np.sqrt(n)
    return {
        'n': n,
        'efeito_ano': media * JANELAS_ANO,
        'mde_ano': mde * JANELAS_ANO,
        'n_necessario': (2.8 * sd / media) ** 2 if media else np.inf,
    }


def montar_bracos(res: pd.DataFrame, acoes: pd.DataFrame) -> dict:
    universo = list(acoes.columns)
    return {
        'Hibrido (IA + Markowitz)': [ler_pesos(p) for p in res.Pesos],
        'IA + 1/N': [
            {t: 1 / len(sel) for t in sel}
            for sel in ([a for a in str(s).split(';') if a in universo] or [universo]
                        for s in res.Ativos_Selecionados)
        ],
        'Universo 1/10': [{t: 1 / len(universo) for t in universo}] * len(res),
    }


def executar():
    res, acoes = carregar()
    retornos = retornos_por_janela(res, acoes)
    rf = taxa_livre_risco(res)
    ibov = res.Retorno_IBOV.reset_index(drop=True)
    pesos_bracos = montar_bracos(res, acoes)

    brutos, liquidos = {}, {}
    for nome, pesos in pesos_bracos.items():
        brutos[nome] = simular(pesos, retornos, 0)[0]
        liquidos[nome] = simular(pesos, retornos, TAXA_REFERENCIA_BPS)[0]

    # Markowitz isolado nao tem pesos registrados no CSV, logo nao entra na simulacao de
    # custos. Entra bruto, e isso favorece o controle — vale dizer no texto.
    if 'Retorno_Markowitz_Isolado' in res:
        brutos['Markowitz isolado'] = res.Retorno_Markowitz_Isolado.reset_index(drop=True)
    brutos['IBOVESPA'] = ibov

    anos = len(res) / JANELAS_ANO
    print('=' * 92)
    print('INFERENCIA CONSOLIDADA')
    print('=' * 92)
    print(f'{len(res)} janelas de 21 pregoes ({anos:.1f} anos), '
          f'{res.Data_Rebalanceamento.min().date()} a {res.Data_Apuracao.max().date()}')
    print(f'Taxa livre de risco: CDI diario capitalizado por janela '
          f'(media {rf.mean()*JANELAS_ANO*100:.2f}% a.a.)')
    print(f'Custo de transacao liquido: {TAXA_REFERENCIA_BPS} bps por ordem')

    print('\n' + '-' * 92)
    print('TABELA 1 - DESEMPENHO E RISCO (bruto)')
    print('-' * 92)
    cab = (f'{"Braco":<26}{"Total":>10}{"CAGR":>8}{"Vol":>8}{"Sharpe":>8}'
           f'{"Sortino":>9}{"MaxDD":>9}{"VaR95":>8}{"CVaR95":>8}')
    print(cab)
    for nome, r in brutos.items():
        m = descritivas(r, rf)
        print(f'{nome:<26}{m["total"]*100:>9.1f}%{m["cagr"]*100:>7.2f}%{m["vol"]*100:>7.2f}%'
              f'{m["sharpe"]:>8.2f}{m["sortino"]:>9.2f}{m["mdd"]*100:>8.2f}%'
              f'{m["var95"]*100:>7.2f}%{m["cvar95"]*100:>7.2f}%')

    print('\n' + '-' * 92)
    print(f'TABELA 2 - DESEMPENHO LIQUIDO DE CUSTOS ({TAXA_REFERENCIA_BPS} bps/ordem)')
    print('-' * 92)
    print(cab)
    for nome, r in liquidos.items():
        m = descritivas(r, rf)
        print(f'{nome:<26}{m["total"]*100:>9.1f}%{m["cagr"]*100:>7.2f}%{m["vol"]*100:>7.2f}%'
              f'{m["sharpe"]:>8.2f}{m["sortino"]:>9.2f}{m["mdd"]*100:>8.2f}%'
              f'{m["var95"]*100:>7.2f}%{m["cvar95"]*100:>7.2f}%')

    print('\n' + '-' * 92)
    print('TABELA 3 - ALFA DE JENSEN CONTRA O IBOVESPA (EP Newey-West, 1 lag)')
    print('-' * 92)
    print(f'{"Braco":<36}{"Alfa a.a.":>12}{"EP":>8}{"t":>8}{"p":>9}'
          f'{"Beta":>8}{"t(b=1)":>9}{"p(b=1)":>9}{"R2":>7}')
    linhas_jensen = []
    for rotulo, serie in [(f'{n} (bruto)', r) for n, r in brutos.items() if n != 'IBOVESPA'] + \
                         [(f'{n} (liquido)', r) for n, r in liquidos.items()]:
        j = jensen((serie - rf).to_numpy(), (ibov - rf).to_numpy())
        print(f'{rotulo:<36}{j["alfa_ano"]*100:>11.2f}%{j["ep_alfa_ano"]*100:>7.2f}%'
              f'{j["t_alfa"]:>8.2f}{j["p_alfa"]:>9.4f}{j["beta"]:>8.3f}'
              f'{j["t_beta_vs_1"]:>9.2f}{j["p_beta_vs_1"]:>9.4f}{j["r2"]:>7.2f}')
        linhas_jensen.append({'Braco': rotulo, **{k: v for k, v in j.items() if k != 'ic_beta'},
                              'IC95_beta_inf': j['ic_beta'][0], 'IC95_beta_sup': j['ic_beta'][1]})

    print('\n' + '-' * 92)
    print('TABELA 4 - ASSIMETRIA: CAPTURA DE ALTA E DE BAIXA DO IBOVESPA')
    print('-' * 92)
    print(f'{"Braco":<26}{"Alta":>7}{"Baixa":>7}{"Capt.alta":>11}{"Capt.baixa":>12}'
          f'{"Razao":>8}{"t(baixa)":>10}{"p(baixa)":>10}')
    for nome, r in brutos.items():
        if nome == 'IBOVESPA':
            continue
        a = assimetria(r, ibov)
        print(f'{nome:<26}{a["n_alta"]:>7}{a["n_baixa"]:>7}{a["captura_alta"]:>11.2f}'
              f'{a["captura_baixa"]:>12.2f}{a["razao"]:>8.2f}{a["t_baixa"]:>10.3f}'
              f'{a["p_baixa"]:>10.4f}')
    print('Capt.alta = retorno medio da carteira / do indice nas janelas de indice positivo.')
    print('Capt.baixa idem nas janelas negativas: quanto MENOR, mais a carteira protege.')

    print('\n' + '-' * 92)
    print('TABELA 5 - DECOMPOSICAO DO EXCESSO (bruto, a.a.)')
    print('-' * 92)
    etapas = [
        ('Universo (10 acoes 1/N vs IBOV)', brutos['Universo 1/10'], ibov),
        ('Selecao dos agentes (IA 1/N vs universo)', brutos['IA + 1/N'], brutos['Universo 1/10']),
        ('Otimizador (hibrido vs IA 1/N)', brutos['Hibrido (IA + Markowitz)'], brutos['IA + 1/N']),
    ]
    print(f'{"Etapa":<44}{"Efeito a.a.":>13}{"t":>9}{"p":>9}{"MDE a.a.":>11}{"n necess.":>11}')
    linhas_decomp = []
    for rotulo, tratamento, controle in etapas:
        dif = tratamento - controle
        t, p = stats.ttest_1samp(dif, 0)
        pw = poder(dif)
        n_nec = '  >10.000' if pw['n_necessario'] > 10_000 else f'{pw["n_necessario"]:>11.0f}'
        print(f'{rotulo:<44}{pw["efeito_ano"]*100:>12.2f}%{t:>9.3f}{p:>9.4f}'
              f'{pw["mde_ano"]*100:>10.2f}%{n_nec}')
        linhas_decomp.append({'Etapa': rotulo, 'Efeito_ano': pw['efeito_ano'], 't': t,
                              'p': p, 'MDE_ano': pw['mde_ano'], 'n_necessario': pw['n_necessario']})
    soma = sum(l['Efeito_ano'] for l in linhas_decomp)
    excesso_total = (brutos['Hibrido (IA + Markowitz)'] - ibov).mean() * JANELAS_ANO
    print(f'{"Soma das etapas":<44}{soma*100:>12.2f}%')
    print(f'{"Excesso do hibrido sobre o IBOV":<44}{excesso_total*100:>12.2f}%')

    print('\n' + '-' * 92)
    print('TABELA 6 - PODER DOS TESTES DE SUPERIORIDADE')
    print('-' * 92)
    print(f'{"Comparacao":<44}{"Efeito a.a.":>13}{"MDE a.a.":>11}{"n":>6}{"n necess.":>11}')
    comparacoes = [('Hibrido bruto vs IBOVESPA', brutos['Hibrido (IA + Markowitz)'], ibov),
                   ('IA 1/N liquido vs IBOVESPA', liquidos['IA + 1/N'], ibov)]
    if 'Markowitz isolado' in brutos:
        comparacoes.append(('Hibrido vs Markowitz isolado',
                            brutos['Hibrido (IA + Markowitz)'], brutos['Markowitz isolado']))
    linhas_poder = []
    for rotulo, tratamento, controle in comparacoes:
        pw = poder(tratamento - controle)
        n_nec = '  >10.000' if pw['n_necessario'] > 10_000 else f'{pw["n_necessario"]:>11.0f}'
        print(f'{rotulo:<44}{pw["efeito_ano"]*100:>12.2f}%{pw["mde_ano"]*100:>10.2f}%'
              f'{pw["n"]:>6}{n_nec}')
        linhas_poder.append({'Comparacao': rotulo, **pw})
    print('MDE = efeito minimo que este n consegue detectar a 95% com poder de 80%.')
    print('Efeito abaixo do MDE significa teste cego, nao ausencia de efeito.')

    pd.DataFrame(linhas_jensen).to_csv('resultado_jensen.csv', index=False)
    pd.DataFrame(linhas_decomp).to_csv('resultado_decomposicao.csv', index=False)
    pd.DataFrame(linhas_poder).to_csv('resultado_poder.csv', index=False)
    pd.DataFrame({'Data_Rebalanceamento': res.Data_Rebalanceamento, 'RF_Janela': rf,
                  'Retorno_IBOV': ibov,
                  **{f'Bruto_{n}': r for n, r in brutos.items()},
                  **{f'Liquido_{n}': r for n, r in liquidos.items()}}
                 ).to_csv('resultado_series_por_janela.csv', index=False)

    print('\n' + '=' * 92)
    print("Salvos: resultado_jensen.csv, resultado_decomposicao.csv, resultado_poder.csv,")
    print("        resultado_series_por_janela.csv")


if __name__ == '__main__':
    executar()
