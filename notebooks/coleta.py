import yfinance as yf
import pandas as pd
import os
import matplotlib.pyplot as plt
import requests

# 1. Garantir que a pasta de destino existe
os.makedirs('../data/raw', exist_ok=True)

# Configura o cache de timezone local
yf.set_tz_cache_location(os.path.join(os.getcwd(), '.cache'))

# 2. Definir os ativos com o sufixo correto da B3 e o Benchmark
tickers = ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'WEGE3.SA', 'ELET3.SA', '^BVSP'] 
data_inicio = '2023-06-14'
data_fim = '2026-06-01'

print(f"Iniciando download em lote via Yahoo Finance ({data_inicio} a {data_fim})...")

# 3. Criar a sessão HTTP protegida para evitar bloqueios
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
})

# 4. Executar o download em lote
try:
    df_raw = yf.download(
        tickers, 
        start=data_inicio, 
        end=data_fim, 
        progress=True, 
        auto_adjust=True, 
        session=session
    )
    
    # Extrai a matriz de fechamentos
    if isinstance(df_raw.columns, pd.MultiIndex):
        dados_b3 = df_raw['Close']
    else:
        dados_b3 = df_raw

    # PASSO CRÍTICO: Remove primeiro as COLUNAS que falharam 100% (ex: ELET3.SA se vier toda NaN)
    colunas_antes = set(dados_b3.columns)
    dados_b3 = dados_b3.dropna(axis=1, how='all')
    colunas_depois = set(dados_b3.columns)
    
    colunas_removidas = colunas_antes - colunas_depois
    if colunas_removidas:
        print(f"\nAtenção: Os seguintes ativos falharam e foram descartados da análise: {list(colunas_removidas)}")

    # Agora sim, remove linhas com dados faltantes (feriados) nos ativos que restaram com sucesso
    dados_b3 = dados_b3.dropna()
    
    if not dados_b3.empty:
        print("\nPrimeiras linhas da tabela final alinhada:")
        print(dados_b3.head())
        
        # 5. Salvar o arquivo CSV final para o projeto
        caminho_arquivo = '../data/raw/cotacoes_b3_historico.csv'
        dados_b3.to_csv(caminho_arquivo)
        print(f"\nBase de dados gerada com sucesso em: {caminho_arquivo}")
        
        # 6. Plotar o gráfico de Resultados Preliminares
        dados_normalizados = (dados_b3 / dados_b3.iloc[0]) * 100
        
        plt.figure(figsize=(12, 6))
        for coluna in dados_normalizados.columns:
            if coluna == '^BVSP':
                plt.plot(dados_normalizados.index, dados_normalizados[coluna], label='IBOVESPA (Benchmark)', linewidth=3, color='black')
            else:
                plt.plot(dados_normalizados.index, dados_normalizados[coluna], label=coluna, alpha=0.7)
                
        plt.title('Resultados Preliminares: Evolução Ajustada dos Ativos vs IBOVESPA (Base 100)')
        plt.xlabel('Data')
        plt.ylabel('Crescimento Acumulado (%)')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.show()
        
    else:
        print("\nErro: O alinhamento resultou em uma tabela sem nenhuma linha válida.")
        
except Exception as e:
    print(f"\nErro crítico durante o download: {e}")
