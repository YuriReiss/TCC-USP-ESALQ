import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

from estilo_figuras import aplicar

CAMINHO_CDI = '../data_server/cdi_diario.csv'


def taxa_livre_risco_por_janela(df: pd.DataFrame) -> pd.Series:
    """
    CDI efetivo capitalizado dentro de cada janela de apuração.

    Substitui a premissa anterior de Selic fixa em 10,5% a.a. para todo o período. Num
    estudo que cobre 2012 a 2026 a taxa constante distorce o Sharpe nas duas pontas: o
    CDI acumulou 2,76% em 2020 e 14,32% em 2025. Com taxa fixa, o excesso de retorno
    ficava subestimado nos anos de juro baixo e superestimado nos de juro alto.
    """
    cdi = pd.read_csv(CAMINHO_CDI, parse_dates=['Date']).set_index('Date').CDI_Dia.sort_index()
    inicio = pd.to_datetime(df['Data_Rebalanceamento'])
    fim = pd.to_datetime(df['Data_Apuracao'])
    # iloc[1:] exclui o dia do rebalanceamento: o capital só rende a partir do dia seguinte.
    return pd.Series([(1 + cdi.loc[i:f].iloc[1:]).prod() - 1 for i, f in zip(inicio, fim)],
                     index=df.index)


def executar_analise_completa(caminho_csv='resultado_backtest_economicAI.csv', capital_inicial=100000.0, simulacoes_mc=10000):
    print("Carregando resultados do backtest...")
    df = pd.read_csv(caminho_csv)

    # 1. Preparação dos Retornos e Curva de Capital
    df['Retorno_Carteira'] = df['Retorno_Carteira'].astype(float)
    df['Retorno_IBOV'] = df['Retorno_IBOV'].astype(float)
    
    # Capitalização composta
    df['Capital_Estrategia'] = capital_inicial * (1 + df['Retorno_Carteira']).cumprod()
    df['Capital_IBOV'] = capital_inicial * (1 + df['Retorno_IBOV']).cumprod()
    
    # 2. Maximum Drawdown (Maior queda do topo ao fundo)
    df['Pico_Estrategia'] = df['Capital_Estrategia'].cummax()
    df['Drawdown_Estrategia'] = (df['Capital_Estrategia'] / df['Pico_Estrategia']) - 1
    max_dd = df['Drawdown_Estrategia'].min()
    
    # 3. Índice de Sharpe com CDI efetivo de cada janela
    taxa_livre_risco_janela = taxa_livre_risco_por_janela(df)
    excesso_retorno = df['Retorno_Carteira'] - taxa_livre_risco_janela
    janelas_por_ano = 252 / 21
    sharpe_ratio = (excesso_retorno.mean() / df['Retorno_Carteira'].std()) * np.sqrt(janelas_por_ano)
    
    # 4. Teste T de Student Pareado (Estratégia vs IBOVESPA)
    # Hipótese Nula (H0): Não há diferença significativa entre a média de retornos da IA e do IBOV
    t_stat, p_value = stats.ttest_rel(df['Retorno_Carteira'], df['Retorno_IBOV'])
    
    # 5. Simulação de Monte Carlo
    print(f"Iniciando Simulação de Monte Carlo com {simulacoes_mc} cenários...")
    mu = df['Retorno_Carteira'].mean()
    sigma = df['Retorno_Carteira'].std()
    passos = len(df)
    
    # Semente fixa: sem ela os números de Monte Carlo citados no trabalho não são reproduzíveis.
    rng = np.random.default_rng(42)
    retornos_aleatorios = rng.normal(mu, sigma, (passos, simulacoes_mc))
    
    # Calcula os caminhos de capital
    caminhos_capital = capital_inicial * np.ones((passos + 1, simulacoes_mc))
    for t in range(1, passos + 1):
        caminhos_capital[t] = caminhos_capital[t - 1] * (1 + retornos_aleatorios[t - 1])
        
    capital_final_mc = caminhos_capital[-1]
    risco_ruina = np.percentile(capital_final_mc, 5) # VaR 95% do capital final
    
    # ================= Exibição de Resultados no Terminal =================
    print("\n" + "="*50)
    print("RELATÓRIO ESTATÍSTICO - ECONOMIC AI")
    print("="*50)
    print(f"Retorno Total Carteira: {((df['Capital_Estrategia'].iloc[-1] / capital_inicial) - 1)*100:.2f}%")
    print(f"Retorno Total IBOV:     {((df['Capital_IBOV'].iloc[-1] / capital_inicial) - 1)*100:.2f}%")
    print(f"Maximum Drawdown:       {max_dd*100:.2f}%")
    print(f"Índice de Sharpe:       {sharpe_ratio:.2f}  "
          f"(CDI médio no período: {taxa_livre_risco_janela.mean()*janelas_por_ano*100:.2f}% a.a.)")
    print("-"*50)
    print("TESTE DE HIPÓTESES (T-Student Pareado)")
    print(f"Estatística T:          {t_stat:.4f}")
    print(f"P-Value:                {p_value:.4f}")
    # O teste compara a carteira com o IBOVESPA, então ele mede o efeito conjunto de
    # universo, seleção e otimizador. Atribuir a diferença à IA exigiria a decomposição
    # feita separadamente, que mostra o universo respondendo por quase todo o excesso.
    if p_value < 0.05:
         print("-> Resultado: diferença significante a 95% contra o IBOVESPA.")
         print("   Atenção: o teste não isola a contribuição da IA; ver a decomposição")
         print("   por universo, seleção e otimizador antes de falar em alpha.")
    else:
         print("-> Resultado: Não significante a 95% de confiança.")
    print("-"*50)
    print("MONTE CARLO (10.000 Trajetórias)")
    print(f"Capital Final Médio:    R$ {capital_final_mc.mean():.2f}")
    print(f"Pior Cenário (VaR 95%): R$ {risco_ruina:.2f}")
    print("="*50)
    
# ================= Geração de Gráficos (Alta Resolução) =================
    aplicar()
    
    # FIGURA 2: Curva de Capital
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    ax2.plot(df['Data_Apuracao'], df['Capital_Estrategia'], label='Multiagente AI + Markowitz', color='blue', linewidth=2)
    ax2.plot(df['Data_Apuracao'], df['Capital_IBOV'], label='IBOVESPA (Benchmark)', color='orange', linewidth=2, linestyle='--')
    ax2.set_title('Evolução do Capital: Estratégia vs Mercado Passivo', fontsize=14)
    ax2.set_ylabel('Capital Acumulado (R$)', fontsize=12)
    ax2.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('figura2_curva_capital.png', dpi=300)

    # FIGURA 3: Risco (VaR e Beta) em Subplots
    fig3, (ax3a, ax3b) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    # Subplot VaR
    ax3a.bar(df['Data_Apuracao'], df['VaR_95'], color='darkred', alpha=0.7)
    ax3a.set_title('Monitoramento de Risco (Rebalanceamentos a cada 21 dias)', fontsize=14)
    ax3a.set_ylabel('Value at Risk (95%) em R$', fontsize=11)
    
    # Subplot Beta
    ax3b.plot(df['Data_Apuracao'], df['Beta'], color='purple', marker='o', linewidth=2)
    ax3b.axhline(y=1.0, color='gray', linestyle='--', label='Risco de Mercado (Beta = 1)')
    ax3b.set_ylabel('Coeficiente Beta da Carteira', fontsize=11)
    ax3b.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('figura3_var_beta.png', dpi=300)

    # FIGURA 4: Underwater Plot (Drawdown)
    fig4, ax4 = plt.subplots(figsize=(12, 5))
    ax4.fill_between(df['Data_Apuracao'], df['Drawdown_Estrategia'] * 100, 0, color='red', alpha=0.4)
    ax4.plot(df['Data_Apuracao'], df['Drawdown_Estrategia'] * 100, color='darkred', linewidth=1)
    ax4.set_title('Underwater Plot: Maximum Drawdown da Estratégia', fontsize=14)
    ax4.set_ylabel('Queda em Relação ao Topo (%)', fontsize=12)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('figura4_drawdown.png', dpi=300)

    # FIGURA 5: Simulação de Monte Carlo
    fig5, ax5 = plt.subplots(figsize=(12, 6))
    ax5.plot(caminhos_capital[:, :100], color='gray', alpha=0.1)
    ax5.plot(caminhos_capital.mean(axis=1), color='red', linewidth=2, label='Trajetória Média Esperada')
    ax5.plot(np.percentile(caminhos_capital, 5, axis=1), color='blue', linewidth=2, linestyle='--', label='VaR 95% (Cenário Pessimista)')
    ax5.set_title('Simulação de Monte Carlo: robustez a longo prazo (10.000 trajetórias)', fontsize=13, loc='left')
    ax5.set_ylabel('Capital simulado (R$)', fontsize=12)
    ax5.set_xlabel('Janelas de rebalanceamento', fontsize=12)
    # A notação científica do eixo ("1e7") é ilegível num texto em reais.
    ax5.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda v, _: f'{v:,.0f}'.replace(',', '.')))
    ax5.legend()
    plt.tight_layout()
    plt.savefig('figura5_monte_carlo.png', dpi=300)
    
    print("\nAs Figuras 2, 3, 4 e 5 foram geradas e guardadas na pasta atual!")

if __name__ == "__main__":
    executar_analise_completa()