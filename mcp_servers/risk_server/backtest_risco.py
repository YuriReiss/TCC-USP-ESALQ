import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from calculators import IndicadoresRiscoB3

def executar_backtest_risco():
    print("Iniciando Backtesting de Risco (VaR e Beta)...")
    
    caminho_csv = '../data_server/cotacoes_b3_fechamentos.csv'
    
    if not os.path.exists(caminho_csv):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_csv}")
        
    df_completo = pd.read_csv(caminho_csv, parse_dates=['Date']).set_index('Date')
    motor = IndicadoresRiscoB3(caminho_csv=caminho_csv)
    
    JANELA_TREINO = 252
    JANELA_TESTE = 21
    CAPITAL_INICIAL = 100000.0  # R$ 100.000,00 para simulação financeira
    NIVEL_CONFIANCA = 0.95
    
    # Armazenamento de resultados
    resultados_pnl_diario = []
    limites_var_diario = []
    datas_out_of_sample = []
    historico_beta_carteira = []
    datas_rebalanceamento = []
    
    for inicio_teste in range(JANELA_TREINO, len(df_completo), JANELA_TESTE):
        fim_teste = inicio_teste + JANELA_TESTE
        if fim_teste > len(df_completo):
            fim_teste = len(df_completo)
            
        df_treino = df_completo.iloc[inicio_teste - JANELA_TREINO : inicio_teste]
        df_teste = df_completo.iloc[inicio_teste : fim_teste]
        
        # Injeta dados de treino no motor
        motor.df_acoes = df_treino.drop(columns=['^BVSP', 'USDBRL=X', 'IFIX.SA'], errors='ignore')
        
        otimizacao = motor.otimizar_carteira_markowitz()
        
        if otimizacao['status'] == 'sucesso':
            pesos = otimizacao['pesos_otimizados']
            
            # 1. Calcula o VaR Paramétrico da carteira otimizada (Treino)
            var_projetado = motor.calcular_var_parametrico(pesos, patrimonio_total=CAPITAL_INICIAL, confianca=NIVEL_CONFIANCA)
            
            # 2. Calcula o Beta ponderado da carteira
            beta_portfolio = 0.0
            for ticker, peso in pesos.items():
                if peso > 0:
                    beta_portfolio += motor.calcular_beta(ticker) * peso
                    
            historico_beta_carteira.append(beta_portfolio)
            datas_rebalanceamento.append(df_teste.index[0])
            
            # 3. Calcula o PnL (Lucro/Prejuízo) financeiro real no período de Teste
            retornos_teste_acoes = df_teste.drop(columns=['^BVSP', 'USDBRL=X', 'IFIX.SA'], errors='ignore').pct_change().dropna()
            pesos_array = np.array([pesos.get(ativo, 0.0) for ativo in retornos_teste_acoes.columns])
            
            retorno_percentual_diario = retornos_teste_acoes.dot(pesos_array)
            pnl_financeiro_diario = retorno_percentual_diario * CAPITAL_INICIAL
            
            resultados_pnl_diario.extend(pnl_financeiro_diario.values)
            
            # O VaR projetado no treino é a linha de limite para todos os dias deste teste
            limites_var_diario.extend([-var_projetado] * len(pnl_financeiro_diario))
            datas_out_of_sample.extend(pnl_financeiro_diario.index)
            
    # Consolidação das Métricas de Risco
    df_risco = pd.DataFrame({
        'PnL_Real': resultados_pnl_diario,
        'Limite_VaR': limites_var_diario
    }, index=datas_out_of_sample)
    
    # Conta quantas vezes a perda real foi pior que o VaR projetado
    violacoes = df_risco[df_risco['PnL_Real'] < df_risco['Limite_VaR']]
    total_dias = len(df_risco)
    taxa_violacao = (len(violacoes) / total_dias) * 100
    
    print("\n" + "="*50)
    print("RESULTADOS DO BACKTESTING DE RISCO (VaR e Beta)")
    print("="*50)
    print(f"Confiança do Modelo VaR: {NIVEL_CONFIANCA*100:.0f}% (Aceitável até {100 - NIVEL_CONFIANCA*100:.0f}% de falhas)")
    print(f"Total de Dias Testados: {total_dias}")
    print(f"Violações do VaR (Perdas extremas): {len(violacoes)} dias")
    print(f"Taxa de Falha Efetiva: {taxa_violacao:.2f}%")
    
    if taxa_violacao <= (100 - NIVEL_CONFIANCA*100) + 1:
        print("Veredito: O modelo VaR está CALIBRADO E EFICIENTE.")
    else:
        print("Veredito: O modelo VaR está SUBESTIMANDO O RISCO (Muitas violações).")
    print("="*50)

    # Plotagem 1: PnL vs Value at Risk
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [2, 1]})
    
    ax1.bar(df_risco.index, df_risco['PnL_Real'], color=np.where(df_risco['PnL_Real'] > 0, 'g', 'r'), alpha=0.6, label='PnL Diário (R$)')
    ax1.plot(df_risco.index, df_risco['Limite_VaR'], color='black', linewidth=2, linestyle='--', label=f'Limite VaR {NIVEL_CONFIANCA*100:.0f}%')
    ax1.scatter(violacoes.index, violacoes['PnL_Real'], color='darkred', s=50, zorder=5, label='Violação de VaR')
    
    ax1.set_title('Backtesting de Risco: Lucro/Prejuízo Diário vs Limite VaR (Base R$ 100k)')
    ax1.set_ylabel('Valor Financeiro (R$)')
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Plotagem 2: Evolução do Risco Sistemático (Beta)
    ax2.plot(datas_rebalanceamento, historico_beta_carteira, color='purple', marker='o', linewidth=2, label='Beta da Carteira')
    ax2.axhline(y=1.0, color='black', linestyle='-', alpha=0.5, label='Beta do Mercado (IBOVESPA = 1.0)')
    ax2.set_title('Evolução do Perfil de Risco (Coeficiente Beta)')
    ax2.set_ylabel('Beta Ponderado')
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    executar_backtest_risco()