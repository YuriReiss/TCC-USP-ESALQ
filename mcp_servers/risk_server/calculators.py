import os
import pandas as pd
import numpy as np
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns

class IndicadoresRiscoB3:
    def __init__(self, caminho_csv: str = "../../data/raw/cotacoes_b3_historico.csv"):
        """
        Classe responsável pelos cálculos matemáticos determinísticos do TCC.
        Carrega a base histórica local gerada na etapa de ingestão.
        """
        # Validação do caminho do arquivo CSV
        if not os.path.exists(caminho_csv):
            caminho_csv = os.path.join(os.path.dirname(__file__), '../../data/raw/cotacoes_b3_historico.csv')
            
        if not os.path.exists(caminho_csv):
            raise FileNotFoundError(f"Arquivo histórico não encontrado no caminho: {caminho_csv}")
            
        self.df = pd.read_csv(caminho_csv, parse_dates=['Date']).set_index('Date')
        
        # Separa o Benchmark (IBOVESPA) das Ações
        self.benchmark_ticker = '^BVSP'
        if self.benchmark_ticker in self.df.columns:
            self.df_acoes = self.df.drop(columns=[self.benchmark_ticker])
            self.df_bench = self.df[self.benchmark_ticker]
        else:
            self.df_acoes = self.df
            self.df_bench = None

    def calcular_beta(self, ticker: str) -> float:
        """Calcula o risco sistemático (Beta) de um ativo contra o IBOVESPA"""
        if self.df_bench is None or ticker not in self.df_acoes.columns:
            return 1.0
        
        # Retornos diários
        retornos_ativo = self.df_acoes[ticker].pct_change().dropna()
        retornos_bench = self.df_bench.pct_change().dropna()
        
        # Alinha as datas
        dados_alinhados = pd.concat([retornos_ativo, retornos_bench], axis=1).dropna()
        
        # Matriz de covariância
        cov_matrix = np.cov(dados_alinhados.iloc[:, 0], dados_alinhados.iloc[:, 1])
        cov_ativo_bench = cov_matrix[0, 1]
        var_bench = cov_matrix[1, 1]
        
        beta = cov_ativo_bench / var_bench
        return float(round(beta, 4))

    def otimizar_carteira_markowitz(self) -> dict:
        """
        Aplica a Teoria Moderna de Portfólios para achar os pesos ideais 
        que maximizam o Índice de Sharpe (Fronteira Eficiente).
        """
        try:
            # Calcula retornos esperados históricos anualizados e matriz de covariância shrinkage
            mu = expected_returns.mean_historical_return(self.df_acoes)
            S = risk_models.CovarianceShrinkage(self.df_acoes).ledoit_wolf()
            
            # Otimiza para o Sharpe Máximo
            ef = EfficientFrontier(mu, S)
            pesos_crus = ef.max_sharpe(risk_free_rate=0.0)
            pesos_limpos = ef.clean_weights()
            
            # Mapeia métricas esperadas da carteira otimizada
            retorno_esp, volat_esp, sharpe_esp = ef.portfolio_performance(risk_free_rate=0.0)
            
            return {
                "status": "sucesso",
                "pesos_otimizados": dict(pesos_limpos),
                "metricas_esperadas": {
                    "retorno_anual": float(round(retorno_esp, 4)),
                    "volatilidade_anual": float(round(volat_esp, 4)),
                    "indice_sharpe": float(round(sharpe_esp, 4))
                }
            }
        except Exception as e:
            return {"status": "erro", "mensagem": str(e)}

    def calcular_var_parametrico(self, pesos: dict, patrimonio_total: float, confianca: float = 0.95) -> float:
        """
        Calcula o Value at Risk (VaR) paramétrico diário para o portfólio especificado.
        pesos: dicionário contendo {'TICKER': proporção} (Ex: {'PETR4.SA': 0.5, 'VALE3.SA': 0.5})
        """
        retornos_acoes = self.df_acoes[list(pesos.keys())].pct_change().dropna()
        vetor_pesos = np.array(list(pesos.values()))
        
        # Matriz de covariância dos retornos diários
        cov_matrix_diaria = retornos_acoes.cov()
        
        # Volatilidade diária do portfólio combinado
        variancia_portfolio = np.dot(vetor_pesos.T, np.dot(cov_matrix_diaria, vetor_pesos))
        volatilidade_diaria_portfolio = np.sqrt(variancia_portfolio)
        
        # Z-score para a distribuição normal
        import scipy.stats as st
        z_score = st.norm.ppf(confianca)
        
        # Cálculo do VaR financeiro diário
        var_porcentagem = volatilidade_diaria_portfolio * z_score
        var_financeiro = patrimonio_total * var_porcentagem
        
        return float(round(var_financeiro, 2))

# Teste rápido de validação local do motor quantitativo
if __name__ == "__main__":
    print("Testando Motor Quantitativo localmente...")
    motor = IndicadoresRiscoB3()
    
    # 1. Teste Markowitz
    otimizacao = motor.otimizar_carteira_markowitz()
    print("\n1. Resultados da Otimização de Markowitz:")
    print(otimizacao)
    
    # 2. Teste Beta
    # Pega o primeiro ativo disponível que não seja o benchmark para testar o Beta
    ativo_teste = [col for col in motor.df_acoes.columns if col != '^BVSP'][0]
    if ativo_teste:
        beta_ativo = motor.calcular_beta(ativo_teste)
        print(f"\n2. Coeficiente Beta do {ativo_teste}: {beta_ativo}")
        
        # 3. Teste VaR usando os pesos gerados pelo Markowitz
        if otimizacao["status"] == "sucesso":
            pesos_gerados = otimizacao["pesos_otimizados"]
            var_financeiro = motor.calcular_var_parametrico(pesos_gerados, patrimonio_total=100000)
            print(f"\n3. VaR Paramétrico Diário (95% conf. para R$ 100k investidos): R$ {var_financeiro}")