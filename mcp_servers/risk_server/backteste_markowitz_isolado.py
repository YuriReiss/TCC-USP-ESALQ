import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pypfopt import expected_returns, risk_models
from pypfopt.efficient_frontier import EfficientFrontier
import warnings

warnings.filterwarnings("ignore")

def executar_markowitz_isolado(caminho_cotacoes='../data_server/cotacoes_b3_fechamentos.csv', 
                               caminho_resultados='resultado_backtest_economicAI.csv', 
                               capital_inicial=100000.0):
    
    print("A carregar dados históricos e resultados do multiagente...")
    df_cotacoes = pd.read_csv(caminho_cotacoes, parse_dates=['Date']).set_index('Date').sort_index()
    df_resultados = pd.read_csv(caminho_resultados)
    
    # Isolar apenas as ações (remover índices e moedas)
    colunas_macro = ['^BVSP', 'USDBRL=X', 'IFIX.SA']
    df_acoes = df_cotacoes.drop(columns=[col for col in colunas_macro if col in df_cotacoes.columns], errors='ignore')
    
    retornos_markowitz = []
    
    print("A executar motor de Markowitz Puro (Controlo Estrito)...")
    
    for index, row in df_resultados.iterrows():
        data_treino_fim = row['Data_Rebalanceamento']
        data_teste_fim = row['Data_Apuracao']
        
        # 1. Janela de Treino (252 dias antes da data de rebalanceamento)
        df_treino = df_acoes.loc[:data_treino_fim].tail(252)
        
        try:
            # 2. Matemática Pura de Markowitz (Sem filtro de IA)
            mu = expected_returns.mean_historical_return(df_treino)
            S = risk_models.sample_cov(df_treino)
            
            ef = EfficientFrontier(mu, S)
            # Adiciona pequeno regularizador para evitar que a matemática se perca com matrizes singulares
            ef.add_objective(objective=lambda w: 0.01 * np.sum(w ** 2)) 
            pesos_brutos = ef.max_sharpe()
            pesos = ef.clean_weights()
            
        except Exception as e:
            print(f"Erro matemático na janela {data_treino_fim}. A alocar em pesos iguais (1/N).")
            n_ativos = len(df_treino.columns)
            pesos = {ativo: 1.0/n_ativos for ativo in df_treino.columns}
            
        # 3. Apuração no mercado real (Janela de Teste)
        df_teste = df_acoes.loc[data_treino_fim:data_teste_fim]
        if len(df_teste) >= 2:
            retorno_ativos = (df_teste.iloc[-1] / df_teste.iloc[0]) - 1
            retorno_janela = sum(peso * retorno_ativos.get(ticker, 0) for ticker, peso in pesos.items())
        else:
            retorno_janela = 0
            
        retornos_markowitz.append(retorno_janela)
        print(f"Janela {data_treino_fim}: Retorno Markowitz Isolado = {retorno_janela*100:+.2f}%")

    # Atualizar o DataFrame e calcular o capital composto
    df_resultados['Retorno_Markowitz_Isolado'] = retornos_markowitz
    df_resultados['Capital_Markowitz'] = capital_inicial * (1 + df_resultados['Retorno_Markowitz_Isolado']).cumprod()
    
    # Salvar o CSV atualizado
    df_resultados.to_csv(caminho_resultados, index=False)
    
    rentabilidade_ia = ((df_resultados['Capital_Acumulado'].iloc[-1] / capital_inicial) - 1) * 100
    rentabilidade_mark = ((df_resultados['Capital_Markowitz'].iloc[-1] / capital_inicial) - 1) * 100
    rentabilidade_ibov = ((df_resultados['Capital_IBOV'].iloc[-1] if 'Capital_IBOV' in df_resultados else 
                          (capital_inicial * (1 + df_resultados['Retorno_IBOV']).cumprod()).iloc[-1] / capital_inicial) - 1) * 100
    
    print("\n" + "="*50)
    print("RESULTADOS DO TESTE DE CONTROLO")
    print("="*50)
    print(f"1. Estratégia Híbrida (IA + Markowitz): {rentabilidade_ia:.2f}%")
    print(f"2. Markowitz Isolado (Matemática Pura): {rentabilidade_mark:.2f}%")
    print(f"3. IBOVESPA (Benchmark Passivo):        {rentabilidade_ibov:.2f}%")
    print("="*50)

    # ================= Geração da Figura 2 (Comparativo Triplo) =================
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(df_resultados['Data_Apuracao'], df_resultados['Capital_Acumulado'], label='Multiagente AI + Markowitz', color='blue', linewidth=2.5)
    ax.plot(df_resultados['Data_Apuracao'], df_resultados['Capital_Markowitz'], label='Markowitz Isolado (Sem IA)', color='green', linewidth=2)
    
    # Garantir que o capital do IBOV está calculado para o plot
    cap_ibov = capital_inicial * (1 + df_resultados['Retorno_IBOV']).cumprod()
    ax.plot(df_resultados['Data_Apuracao'], cap_ibov, label='IBOVESPA (Benchmark)', color='orange', linewidth=2, linestyle='--')
    
    ax.set_title('Evolução do Capital: Estratégia Multiagente vs Matemática Isolada vs Mercado', fontsize=14)
    ax.set_ylabel('Capital Acumulado (R$)', fontsize=12)
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('figura2_curva_capital_tripla.png', dpi=300)
    
    print("\nGráfico 'figura2_curva_capital_tripla.png' gerado com sucesso!")

if __name__ == "__main__":
    executar_markowitz_isolado()