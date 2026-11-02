import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

# Carregar dados brutos
df = pd.read_csv('../data_server/cotacoes_b3_fechamentos.csv', parse_dates=['Date']).set_index('Date')
df = df.dropna()

# 1. Feature Engineering
# Volatilidade rolante do IBOV (21 dias)
volatilidade_ibov = df['^BVSP'].pct_change().rolling(window=21).std() * np.sqrt(252)
# Retorno do Dólar (21 dias)
retorno_dolar = df['USDBRL=X'].pct_change(periods=21)

df_features = pd.DataFrame({'Volatilidade_IBOV': volatilidade_ibov, 'Variacao_Dolar': retorno_dolar}).dropna()

# 2. Modelo K-Means
kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
df_features['Cluster'] = kmeans.fit_predict(df_features)

# Identificar qual cluster é a Turbulência (o que tem maior volatilidade média)
media_vol = df_features.groupby('Cluster')['Volatilidade_IBOV'].mean()
cluster_turbulencia = media_vol.idxmax()
df_features['Regime'] = np.where(df_features['Cluster'] == cluster_turbulencia, 'Turbulência', 'Calmaria')

# 3. Plotagem
plt.style.use('seaborn-v0_8-darkgrid')
fig, ax = plt.subplots(figsize=(10, 6))

cores = {'Calmaria': 'blue', 'Turbulência': 'red'}
for regime, cor in cores.items():
    subset = df_features[df_features['Regime'] == regime]
    ax.scatter(subset['Volatilidade_IBOV'], subset['Variacao_Dolar'], label=regime, c=cor, alpha=0.6, edgecolors='k')

ax.set_title('Regimes de Mercado (K-Means): Volatilidade vs Variação Cambial', fontsize=14)
ax.set_xlabel('Volatilidade Anualizada do IBOVESPA', fontsize=12)
ax.set_ylabel('Variação do Dólar (USDBRL)', fontsize=12)
ax.legend()
plt.tight_layout()
plt.savefig('figura1_kmeans.png', dpi=300)
print("Figura 1 gerada com sucesso!")