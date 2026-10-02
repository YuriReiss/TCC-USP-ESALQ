import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Importa o motor matemático do arquivo calculators.py
# Certifique-se de que calculators.py está no mesmo diretório ou ajuste o import
from calculators import IndicadoresRiscoB3

def calcular_max_drawdown(retornos_diarios):
    """Calcula a queda percentual máxima registrada (Drawdown)"""
    retorno_acumulado = (1 + retornos_diarios).cumprod()
    pico_historico = retorno_acumulado.cummax()
    drawdown = (retorno_acumulado / pico_historico) - 1
    return drawdown.min()

def executar_backtest():
    print("Iniciando Backtesting de Portfólio (Janelas Deslizantes)...")
    
    # 1. Carrega a base de dados multidimensional limpa
    caminho_csv = '../data_server/cotacoes_b3_fechamentos.csv'
    if not os.path.exists(caminho_csv):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_csv}")
        
    df_completo = pd.read_csv(caminho_csv, parse_dates=['Date']).set_index('Date')
    
    # 2. Configurações da Janela Deslizante
    JANELA_TREINO = 252  # ~1 ano de histórico para o Markowitz calcular o risco
    JANELA_TESTE = 21    # ~1 mês de manutenção da carteira antes do rebalanceamento
    
    # Instancia o motor quantitativo
    motor = IndicadoresRiscoB3(caminho_csv=caminho_csv)
    
    retornos_portfolio_out_of_sample = []
    retornos_benchmark_out_of_sample = []
    datas_out_of_sample = []
    
    # 3. Loop do Backtesting (Walk-Forward)
    for inicio_teste in range(JANELA_TREINO, len(df_completo), JANELA_TESTE):
        fim_teste = inicio_teste + JANELA_TESTE
        
        # Garante que não ultrapassamos o limite do dataframe
        if fim_teste > len(df_completo):
            fim_teste = len(df_completo)
            
        # Define os períodos exatos
        df_treino = df_completo.iloc[inicio_teste - JANELA_TREINO : inicio_teste]
        df_teste = df_completo.iloc[inicio_teste : fim_teste]
        
        # Extrai os retornos diários do período de teste
        retornos_teste_acoes = df_teste.drop(columns=['^BVSP', 'USDBRL=X', 'IFIX.SA'], errors='ignore').pct_change().dropna()
        retornos_teste_bench = df_teste['^BVSP'].pct_change().dropna()
        
        # 4. Injeta os dados de treino no motor e otimiza
        # Substituímos dinamicamente os dados dentro do motor para forçar o cálculo na janela específica
        motor.df_acoes = df_treino.drop(columns=['^BVSP', 'USDBRL=X', 'IFIX.SA'], errors='ignore')
        otimizacao = motor.otimizar_carteira_markowitz()
        
        if otimizacao['status'] == 'sucesso':
            pesos = otimizacao['pesos_otimizados']
            
            # Alinha os ativos da matriz de pesos com os retornos do período de teste
            pesos_array = np.array([pesos.get(ativo, 0.0) for ativo in retornos_teste_acoes.columns])
            
            # 5. Calcula o retorno diário da carteira no mês seguinte (Out-of-sample)
            # Retorno do portfólio = Soma(Retorno do Ativo * Peso do Ativo) para cada dia
            retornos_diarios_carteira = retornos_teste_acoes.dot(pesos_array)
            
            retornos_portfolio_out_of_sample.extend(retornos_diarios_carteira.values)
            retornos_benchmark_out_of_sample.extend(retornos_teste_bench.values)
            datas_out_of_sample.extend(retornos_diarios_carteira.index)
        else:
            print(f"Falha na otimização para a janela terminada em {df_treino.index[-1].date()}: {otimizacao['mensagem']}")
            
    # 6. Consolidação e Validação de Métricas
    serie_retornos_port = pd.Series(retornos_portfolio_out_of_sample, index=datas_out_of_sample)
    serie_retornos_bench = pd.Series(retornos_benchmark_out_of_sample, index=datas_out_of_sample)
    
    # Rentabilidade Acumulada
    acumulado_port = (1 + serie_retornos_port).cumprod()
    acumulado_bench = (1 + serie_retornos_bench).cumprod()
    
    rentabilidade_final_port = (acumulado_port.iloc[-1] - 1) * 100
    rentabilidade_final_bench = (acumulado_bench.iloc[-1] - 1) * 100
    
    # Volatilidade Anualizada
    volatilidade_port = serie_retornos_port.std() * np.sqrt(252) * 100
    volatilidade_bench = serie_retornos_bench.std() * np.sqrt(252) * 100
    
    # Drawdown Máximo
    drawdown_port = calcular_max_drawdown(serie_retornos_port) * 100
    drawdown_bench = calcular_max_drawdown(serie_retornos_bench) * 100

    print("\n" + "="*50)
    print("RESULTADOS DO BACKTESTING (OUT-OF-SAMPLE)")
    print("="*50)
    print(f"Período Testado: {datas_out_of_sample[0].date()} a {datas_out_of_sample[-1].date()}")
    print("-" * 50)
    print(f"{'Métrica':<25} | {'Carteira IA':<10} | {'IBOVESPA':<10}")
    print("-" * 50)
    print(f"{'Rentabilidade Acumulada':<25} | {rentabilidade_final_port:>8.2f}% | {rentabilidade_final_bench:>8.2f}%")
    print(f"{'Volatilidade Anualizada':<25} | {volatilidade_port:>8.2f}% | {volatilidade_bench:>8.2f}%")
    print(f"{'Drawdown Máximo':<25} | {drawdown_port:>8.2f}% | {drawdown_bench:>8.2f}%")
    print("="*50)

    # 7. Plotagem da Curva de Capital
    plt.figure(figsize=(14, 7))
    plt.plot(acumulado_port.index, acumulado_port.values * 100, label='Carteira Otimizada (Markowitz)', color='blue', linewidth=2)
    plt.plot(acumulado_bench.index, acumulado_bench.values * 100, label='IBOVESPA (Benchmark)', color='black', linewidth=2, linestyle='--')
    
    plt.title('Backtesting Walk-Forward: Evolução do Capital (Base 100)')
    plt.xlabel('Data')
    plt.ylabel('Crescimento do Capital (%)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    executar_backtest()