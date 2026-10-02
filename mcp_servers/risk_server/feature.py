import pandas as pd
import numpy as np
from scipy.stats import skew, kurtosis
from sklearn.cluster import KMeans
import warnings

# Suprime avisos do scikit-learn sobre vazamento de memória em Windows com KMeans
warnings.filterwarnings("ignore", category=UserWarning)

class EngenhariaDeFeatures:
    def __init__(self, df_janela: pd.DataFrame):
        """
        Recebe estritamente o DataFrame fatiado da janela de treino (ex: 252 dias).
        Garante que a IA e o modelo de ML não enxerguem o futuro.
        """
        self.df = df_janela
        
        # Separa macroeconomia das ações corporativas
        colunas_macro = ['^BVSP', 'USDBRL=X', 'IFIX.SA']
        self.colunas_presentes_macro = [col for col in colunas_macro if col in self.df.columns]
        
        self.df_acoes = self.df.drop(columns=self.colunas_presentes_macro, errors='ignore')
        self.df_macro = self.df[self.colunas_presentes_macro]

    def extrair_features_acoes(self) -> pd.DataFrame:
        """
        Calcula os momentos estatísticos e indicadores de tendência para cada ação.
        """
        features = []
        retornos_diarios = self.df_acoes.pct_change().dropna()
        
        for ativo in self.df_acoes.columns:
            # 1. Momentum (Retorno Acumulado na janela)
            preco_inicial = self.df_acoes[ativo].iloc[0]
            preco_final = self.df_acoes[ativo].iloc[-1]
            momentum = (preco_final / preco_inicial) - 1
            
            # 2. Volatilidade Anualizada
            volatilidade = retornos_diarios[ativo].std() * np.sqrt(252)
            
            # 3. Skewness (Assimetria: risco de quedas abruptas se negativo)
            assimetria = skew(retornos_diarios[ativo].dropna())
            
            # 4. Kurtosis (Risco de cauda/cisnes negros se muito alto)
            curtose = kurtosis(retornos_diarios[ativo].dropna())
            
            features.append({
                'Ativo': ativo,
                'Momentum_12M': float(round(momentum, 4)),
                'Volatilidade_Anual': float(round(volatilidade, 4)),
                'Skewness': float(round(assimetria, 4)),
                'Kurtosis': float(round(curtose, 4))
            })
            
        df_features = pd.DataFrame(features).set_index('Ativo')
        return df_features

    def detectar_regime_kmeans(self) -> dict:
        """
        Aplica Clusterização Não-Supervisionada (K-Means) para identificar 
        se o mercado atual está em estado de Calmaria ou Turbulência.
        """
        if '^BVSP' not in self.df_macro.columns or 'USDBRL=X' not in self.df_macro.columns:
            return {"status": "erro", "mensagem": "Indicadores macro insuficientes para K-Means."}
            
        retornos_macro = self.df_macro.pct_change().dropna()
        
        # Cria features contínuas baseadas em janelas rolantes curtas dentro do ano
        # Isso ensina ao algoritmo a "sensação" recente do mercado
        volatilidade_ibov_rolante = retornos_macro['^BVSP'].rolling(window=21).std() * np.sqrt(252)
        retorno_dolar_rolante = retornos_macro['USDBRL=X'].rolling(window=21).mean() * 252
        
        df_ml = pd.DataFrame({
            'Volatilidade_BVSP': volatilidade_ibov_rolante,
            'Tendencia_Dolar': retorno_dolar_rolante
        }).dropna()
        
        if len(df_ml) < 21:
            return {"status": "erro", "mensagem": "Dados insuficientes pós-rolagem para K-Means."}
            
        # Treina o K-Means para encontrar 2 regimes macroeconômicos (k=2)
        kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
        kmeans.fit(df_ml)
        
        # Identifica a posição dos centroides para nomear os regimes
        centroides = kmeans.cluster_centers_
        # O cluster com maior volatilidade média do IBOV (coluna 0) será a "Turbulência"
        idx_turbulencia = np.argmax(centroides[:, 0])
        idx_calmaria = np.argmin(centroides[:, 0])
        
        # Pega a leitura exata do ÚLTIMO dia da janela (o "hoje" para o LLM)
        estado_hoje = df_ml.iloc[-1:]
        cluster_atual = kmeans.predict(estado_hoje)[0]
        
        nome_regime = "Turbulência (Alta Volatilidade/Risco Acumulado)" if cluster_atual == idx_turbulencia else "Calmaria (Baixa Volatilidade/Tendência de Alta)"
        
        return {
            "status": "sucesso",
            "regime_atual": nome_regime,
            "metricas_hoje": {
                "volatilidade_ibov_21d": float(round(estado_hoje['Volatilidade_BVSP'].iloc[0], 4)),
                "tendencia_dolar_anualizada": float(round(estado_hoje['Tendencia_Dolar'].iloc[0], 4))
            }
        }

    def gerar_contexto_llm(self) -> dict:
        """
        Consolida a engenharia de dados em um dicionário estruturado para injeção de Prompt.
        """
        features_acoes = self.extrair_features_acoes()
        regime = self.detectar_regime_kmeans()
        
        return {
            "cenario_macro": regime,
            "features_micro": features_acoes.to_dict(orient='index')
        }


if __name__ == "__main__":
    df_completo = pd.read_csv('../data_server/cotacoes_b3_fechamentos.csv', parse_dates=['Date']).set_index('Date')
    df_janela_exemplo = df_completo.iloc[:252]  # Simula a primeira janela do backtest
    
    engenharia = EngenhariaDeFeatures(df_janela_exemplo)
    contexto_para_agentes = engenharia.gerar_contexto_llm()
    
    print("REGIME DE MERCADO DETECTADO (K-MEANS):")
    print(contexto_para_agentes['cenario_macro'])
    
    print("\nFEATURES AVANÇADAS EXTRAÍDAS (Amostra de 3 ativos):")
    # Pega os 3 primeiros ativos do dicionário para visualização
    for ativo, stats in list(contexto_para_agentes['features_micro'].items())[:3]:
        print(f"{ativo}: {stats}")