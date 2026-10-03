import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

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
    
    # 3. Índice de Sharpe (Assumindo Selic média de ~10.5% ao ano -> ~0.83% ao mês/janela)
    taxa_livre_risco_janela = 0.0083 
    excesso_retorno = df['Retorno_Carteira'] - taxa_livre_risco_janela
    sharpe_ratio = (excesso_retorno.mean() / df['Retorno_Carteira'].std()) * np.sqrt(12) # Anualizado (aprox 12 janelas de 21 dias/ano)
    
    # 4. Teste T de Student Pareado (Estratégia vs IBOVESPA)
    # Hipótese Nula (H0): Não há diferença significativa entre a média de retornos da IA e do IBOV
    t_stat, p_value = stats.ttest_rel(df['Retorno_Carteira'], df['Retorno_IBOV'])
    
    # 5. Simulação de Monte Carlo
    print(f"Iniciando Simulação de Monte Carlo com {simulacoes_mc} cenários...")
    mu = df['Retorno_Carteira'].mean()
    sigma = df['Retorno_Carteira'].std()
    passos = len(df)
    
    # Gera matriz de retornos aleatórios baseados na distribuição normal da carteira
    retornos_aleatorios = np.random.normal(mu, sigma, (passos, simulacoes_mc))
    
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
    print(f"Índice de Sharpe:       {sharpe_ratio:.2f}")
    print("-"*50)
    print("TESTE DE HIPÓTESES (T-Student Pareado)")
    print(f"Estatística T:          {t_stat:.4f}")
    print(f"P-Value:                {p_value:.4f}")
    if p_value < 0.05:
         print("-> Resultado: ESTATISTICAMENTE SIGNIFICANTE. A IA gera alpha comprovado.")
    else:
         print("-> Resultado: Não significante a 95% de confiança.")
    print("-"*50)
    print("MONTE CARLO (10.000 Trajetórias)")
    print(f"Capital Final Médio:    R$ {capital_final_mc.mean():.2f}")
    print(f"Pior Cenário (VaR 95%): R$ {risco_ruina:.2f}")
    print("="*50)
    
    # ================= Geração de Gráficos (Alta Resolução) =================
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # Gráfico 1: Curva de Capital (IA vs IBOV)
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    ax1.plot(df['Data_Apuracao'], df['Capital_Estrategia'], label='Multiagente AI (Estratégia)', color='blue', linewidth=2)
    ax1.plot(df['Data_Apuracao'], df['Capital_IBOV'], label='IBOVESPA (Benchmark)', color='orange', linewidth=2, linestyle='--')
    ax1.set_title('Evolução do Capital: Inteligência Artificial vs Mercado Passivo', fontsize=14)
    ax1.set_ylabel('Capital Acumulado (R$)', fontsize=12)
    ax1.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('grafico_curva_capital.png', dpi=300)
    
    # Gráfico 2: Simulação de Monte Carlo
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    ax2.plot(caminhos_capital[:, :100], color='gray', alpha=0.1) # Plota apenas 100 para não pesar o render
    ax2.plot(caminhos_capital.mean(axis=1), color='red', linewidth=2, label='Trajetória Média (Esperança Matemática)')
    ax2.plot(np.percentile(caminhos_capital, 5, axis=1), color='blue', linewidth=2, linestyle='--', label='VaR 95% (Cenário Pessimista)')
    ax2.set_title('Simulação de Monte Carlo: Robustez a Longo Prazo', fontsize=14)
    ax2.set_ylabel('Capital Simulado (R$)', fontsize=12)
    ax2.set_xlabel('Janelas de Rebalanceamento (21 dias)', fontsize=12)
    ax2.legend()
    plt.tight_layout()
    plt.savefig('grafico_monte_carlo.png', dpi=300)
    
    print("\nGráficos 'grafico_curva_capital.png' e 'grafico_monte_carlo.png' salvos com sucesso na pasta atual!")

if __name__ == "__main__":
    executar_analise_completa()