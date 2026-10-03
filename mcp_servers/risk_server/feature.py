import pandas as pd
import numpy as np
from scipy.stats import skew, kurtosis
from sklearn.cluster import KMeans
import warnings

# Suprime avisos do scikit-learn sobre vazamento de memória em Windows com KMeans
warnings.filterwarnings("ignore", category=UserWarning)

class EngenhariaDeFeatures:
    def __init__(self, df_janela: pd.DataFrame):
        self.df = df_janela
        
        colunas_macro = ['^BVSP', 'USDBRL=X', 'IFIX.SA']
        self.colunas_presentes_macro = [col for col in colunas_macro if col in self.df.columns]
        
        self.df_acoes = self.df.drop(columns=self.colunas_presentes_macro, errors='ignore')
        self.df_macro = self.df[self.colunas_presentes_macro]

    def extrair_features_acoes(self) -> pd.DataFrame:
        features = []
        retornos_diarios = self.df_acoes.pct_change().dropna()
        
        for ativo in self.df_acoes.columns:
            preco_inicial = self.df_acoes[ativo].iloc[0]
            preco_final = self.df_acoes[ativo].iloc[-1]
            momentum = (preco_final / preco_inicial) - 1
            
            volatilidade = retornos_diarios[ativo].std() * np.sqrt(252)
            assimetria = skew(retornos_diarios[ativo].dropna())
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
        if '^BVSP' not in self.df_macro.columns or 'USDBRL=X' not in self.df_macro.columns:
            return {"status": "erro", "mensagem": "Indicadores macro insuficientes para K-Means."}
            
        retornos_macro = self.df_macro.pct_change().dropna()
        
        volatilidade_ibov_rolante = retornos_macro['^BVSP'].rolling(window=21).std() * np.sqrt(252)
        retorno_dolar_rolante = retornos_macro['USDBRL=X'].rolling(window=21).mean() * 252
        
        df_ml = pd.DataFrame({
            'Volatilidade_BVSP': volatilidade_ibov_rolante,
            'Tendencia_Dolar': retorno_dolar_rolante
        }).dropna()
        
        if len(df_ml) < 21:
            return {"status": "erro", "mensagem": "Dados insuficientes pós-rolagem para K-Means."}
            
        kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
        kmeans.fit(df_ml)
        
        centroides = kmeans.cluster_centers_
        idx_turbulencia = np.argmax(centroides[:, 0])
        idx_calmaria = np.argmin(centroides[:, 0])
        
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
        features_acoes = self.extrair_features_acoes()
        regime = self.detectar_regime_kmeans()
        
        # Início da Lógica de Mascaramento (Anonimização)
        dicionario_features = features_acoes.to_dict(orient='index')
        features_anonimas = {}
        gabarito = {}
        
        for i, (ativo_real, stats) in enumerate(dicionario_features.items(), start=1):
            nome_anonimo = f"Ativo_{i}"
            gabarito[nome_anonimo] = ativo_real
            
            # Remove o nome real de dentro das métricas, se existir
            stats_copia = stats.copy()
            if 'Ativo' in stats_copia:
                stats_copia['Ativo'] = nome_anonimo
                
            features_anonimas[nome_anonimo] = stats_copia
            
        return {
            "cenario_macro": regime,
            "features_micro": features_anonimas,
            "gabarito_ativos": gabarito # Será capturado e ocultado pelo server.py
        }