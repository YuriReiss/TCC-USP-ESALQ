"""
Teste de permutação exato sobre a seleção de ativos dos agentes LLM.

O teste T pareado de retorno compara carteiras que atravessam o mesmo mercado, então
quase toda a variância do par vem de choques macro comuns aos dois braços. Com
tracking error de 12,6% a.a., o efeito mínimo detectável em 168 janelas é ~9,5% a.a.,
muito acima de qualquer alpha plausível.

Aqui a comparação é feita dentro de cada janela, contra TODOS os subconjuntos do mesmo
tamanho que a IA poderia ter escolhido. Como todos vivem exatamente o mesmo mês, a
variância de mercado se cancela por construção e sobra apenas a habilidade de seleção.
Sob a hipótese nula de escolha aleatória, o percentil da IA é Uniforme(0,1).

Pesos iguais em todos os subconjuntos, inclusive o da IA: isola a seleção do efeito do
otimizador, que é testado separadamente no controle Markowitz Isolado.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations
from scipy import stats

CAMINHO_COTACOES = '../data_server/cotacoes_b3_fechamentos.csv'
CAMINHO_RESULTADOS = 'resultado_backtest_economicAI.csv'
COLUNAS_MACRO = ['^BVSP', 'USDBRL=X', 'IFIX.SA']


def executar_teste_permutacao():
    df_cotacoes = pd.read_csv(CAMINHO_COTACOES, parse_dates=['Date']).set_index('Date').sort_index()
    df_acoes = df_cotacoes.drop(columns=[c for c in COLUNAS_MACRO if c in df_cotacoes.columns],
                                errors='ignore')
    universo = list(df_acoes.columns)

    df_res = pd.read_csv(CAMINHO_RESULTADOS)

    registros = []

    for _, linha in df_res.iterrows():
        selecionados = [a for a in str(linha['Ativos_Selecionados']).split(';') if a in universo]
        if not selecionados:
            continue

        df_teste = df_acoes.loc[linha['Data_Rebalanceamento']:linha['Data_Apuracao']]
        if len(df_teste) < 2:
            continue

        retorno_ativo = (df_teste.iloc[-1] / df_teste.iloc[0]) - 1

        k = len(selecionados)
        retornos_subconjuntos = np.array([retorno_ativo[list(c)].mean()
                                          for c in combinations(universo, k)])
        retorno_ia = retorno_ativo[selecionados].mean()

        # Midrank: com C(10,2)=45 subconjuntos os empates são possíveis e ignorá-los
        # enviesaria o percentil para cima.
        abaixo = (retornos_subconjuntos < retorno_ia).sum()
        iguais = (retornos_subconjuntos == retorno_ia).sum()
        percentil = (abaixo + 0.5 * iguais) / len(retornos_subconjuntos)

        registros.append({
            'Data_Rebalanceamento': linha['Data_Rebalanceamento'],
            'k': k,
            'n_subconjuntos': len(retornos_subconjuntos),
            'Retorno_IA_1N': retorno_ia,
            'Retorno_Mediano_Subconjuntos': np.median(retornos_subconjuntos),
            'Retorno_Universo_1N': retorno_ativo.mean(),
            'Melhor_Subconjunto': retornos_subconjuntos.max(),
            'Pior_Subconjunto': retornos_subconjuntos.min(),
            'Percentil': percentil
        })

    df = pd.DataFrame(registros)
    p = df['Percentil']
    n = len(df)

    t_stat, p_valor = stats.ttest_1samp(p, 0.5)
    w_stat, p_wilcoxon = stats.wilcoxon(p - 0.5)
    acima = int((p > 0.5).sum())
    p_binomial = stats.binomtest(acima, n, 0.5).pvalue
    ic = stats.t.interval(0.95, n - 1, loc=p.mean(), scale=stats.sem(p))

    # Poder: sob H0 o percentil é Uniforme(0,1), logo sd = 1/sqrt(12) = 0.2887.
    mde = 2.802 * (1 / np.sqrt(12)) / np.sqrt(n)

    excesso = df['Retorno_IA_1N'] - df['Retorno_Mediano_Subconjuntos']
    t_exc, p_exc = stats.ttest_1samp(excesso, 0.0)

    print("=" * 62)
    print("TESTE DE PERMUTACAO - HABILIDADE DE SELECAO DOS AGENTES LLM")
    print("=" * 62)
    print(f"Janelas avaliadas:            {n}")
    print(f"Universo:                     {len(universo)} acoes")
    print(f"Tamanho medio da selecao:     {df['k'].mean():.2f} ativos")
    print(f"Subconjuntos por janela:      {df['n_subconjuntos'].min()} a {df['n_subconjuntos'].max()}")
    print("-" * 62)
    print(f"Percentil medio da IA:        {p.mean():.4f}  (H0 = 0.5000)")
    print(f"IC 95%:                       [{ic[0]:.4f}, {ic[1]:.4f}]")
    print(f"Percentil mediano:            {p.median():.4f}")
    print(f"Janelas acima da mediana:     {acima}/{n} ({acima/n*100:.1f}%)")
    print("-" * 62)
    print(f"Teste T (1 amostra vs 0.5):   t = {t_stat:+.4f}   p = {p_valor:.4f}")
    print(f"Wilcoxon (sinais):            W = {w_stat:.1f}   p = {p_wilcoxon:.4f}")
    print(f"Binomial exato:                            p = {p_binomial:.4f}")
    print(f"Efeito minimo detectavel (80% poder): {mde:.4f} de percentil")
    print(f"  -> detecta um percentil medio a partir de {0.5 + mde:.4f}")
    print("-" * 62)
    print("RETORNO 1/N POR JANELA (media)")
    print(f"Selecao da IA:                {df['Retorno_IA_1N'].mean()*100:+.3f}%")
    print(f"Mediana dos subconjuntos:     {df['Retorno_Mediano_Subconjuntos'].mean()*100:+.3f}%")
    print(f"Universo completo (1/10):     {df['Retorno_Universo_1N'].mean()*100:+.3f}%")
    print(f"Melhor subconjunto possivel:  {df['Melhor_Subconjunto'].mean()*100:+.3f}%")
    print(f"Pior subconjunto possivel:    {df['Pior_Subconjunto'].mean()*100:+.3f}%")
    print(f"Excesso IA vs mediana:        {excesso.mean()*100:+.3f} p.p.  t = {t_exc:+.4f}  p = {p_exc:.4f}")
    print("=" * 62)

    if p_valor < 0.05:
        direcao = "ACIMA" if p.mean() > 0.5 else "ABAIXO"
        print(f"Veredito: selecao significativamente {direcao} do acaso (95% de confianca).")
    else:
        print("Veredito: selecao indistinguivel de escolha aleatoria a 95% de confianca.")
    print("=" * 62)

    df.to_csv('resultado_teste_permutacao.csv', index=False)

    plt.style.use('seaborn-v0_8-darkgrid')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.hist(p, bins=20, range=(0, 1), color='steelblue', edgecolor='white')
    ax1.axhline(n / 20, color='gray', linestyle=':', linewidth=2, label='Distribuicao sob H0 (uniforme)')
    ax1.axvline(p.mean(), color='darkred', linestyle='--', linewidth=2,
                label=f'Media observada = {p.mean():.3f}')
    ax1.axvline(0.5, color='black', linewidth=1.5, label='Acaso = 0.500')
    ax1.set_title('Percentil da selecao da IA entre todos os subconjuntos', fontsize=12)
    ax1.set_xlabel('Percentil na janela')
    ax1.set_ylabel('Numero de janelas')
    ax1.legend(fontsize=9)

    media_movel = p.rolling(12).mean()
    ax2.plot(pd.to_datetime(df['Data_Rebalanceamento']), media_movel,
             color='darkblue', linewidth=2, label='Media movel de 12 janelas')
    ax2.axhline(0.5, color='black', linestyle='--', linewidth=1.5, label='Acaso = 0.500')
    ax2.set_title('Estabilidade da habilidade de selecao ao longo do tempo', fontsize=12)
    ax2.set_ylabel('Percentil medio')
    ax2.set_ylim(0, 1)
    ax2.legend(fontsize=9)
    plt.setp(ax2.get_xticklabels(), rotation=45)

    plt.tight_layout()
    plt.savefig('figura6_teste_permutacao.png', dpi=300)
    print("\nFigura 'figura6_teste_permutacao.png' e 'resultado_teste_permutacao.csv' gerados.")


if __name__ == "__main__":
    executar_teste_permutacao()
