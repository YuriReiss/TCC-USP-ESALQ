import yfinance as yf
import pandas as pd
import os
import matplotlib.pyplot as plt
import time

# 1. Garantir que a pasta de destino existe
os.makedirs('../data/raw', exist_ok=True)

# 2. Definir os ativos ampliados e indicadores macroeconômicos
tickers = [
    'PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'WEGE3.SA', 
    'BBAS3.SA', 'BBDC4.SA',                         
    'LREN3.SA', 'ABEV3.SA',                         
    'SBSP3.SA', 'CMIG4.SA',                         
    'IFIX.SA',                                      
    'USDBRL=X',                                     
    '^BVSP'                                         
]
data_inicio = '2023-06-14'
data_fim = '2026-06-01'

print(f"Iniciando extração sequencial ({data_inicio} a {data_fim})...")

dfs = []
ativos_com_erro = []

# 3. Executar o download sequencial sem sessão estática (Anti-Bloqueio)
for ticker in tickers:
    try:
        df_temp = yf.download(
            ticker, 
            start=data_inicio, 
            end=data_fim, 
            progress=False, 
            auto_adjust=True
        )
        
        # Teste simplificado: verifica apenas se o DataFrame não está vazio
        if not df_temp.empty and len(df_temp) > 0:
            
            # Verifica se o yfinance já retornou um MultiIndex nativo. 
            # Se não, nós o criamos. Isso evita empilhar MultiIndex duplicados.
            if not isinstance(df_temp.columns, pd.MultiIndex):
                df_temp.columns = pd.MultiIndex.from_product([df_temp.columns, [ticker]])
            else:
                # Se já for MultiIndex, garante que o nome do ticker esteja no nível correto
                if ticker not in df_temp.columns.get_level_values(1):
                    df_temp.columns = pd.MultiIndex.from_product([df_temp.columns.get_level_values(0).unique(), [ticker]])

            dfs.append(df_temp)
            print(f"[OK] {ticker} baixado com sucesso.")
        else:
            print(f"[Falha] {ticker} retornou vazio e será ignorado.")
            ativos_com_erro.append(ticker)
            
    except Exception as e:
        print(f"[Erro] Falha ao extrair {ticker}: {e}")
        ativos_com_erro.append(ticker)
        
    # Pausa de 3 segundos entre requisições para evitar rate limit
    time.sleep(3)

# 4. Tratamento de Dados e Limpeza
if dfs:
    # Concatena todos os ativos extraídos
    df_raw = pd.concat(dfs, axis=1)
    
    # Isola temporariamente os fechamentos para checar se algum ativo veio majoritariamente nulo
    fechamentos = df_raw['Close']
    fechamentos_limpos = fechamentos.dropna(axis=1, how='all')
    ativos_validos = fechamentos_limpos.columns
    
    # Filtra o DataFrame original tridimensional apenas para os ativos que passaram no teste
    df_b3 = df_raw.loc[:, (slice(None), ativos_validos)]
    
    # Alinhamento de Feriados (B3 vs USD): 
    # Propaga o último preço válido (forward fill), depois remove os NaNs residuais no início da série
    df_b3 = df_b3.ffill().dropna()

    if not df_b3.empty:
        print("\nPrimeiras linhas da matriz de Fechamento (Close):")
        print(df_b3['Close'].head())
        
        # 5. Salvar arquivos
        caminho_parquet = '../data/raw/cotacoes_b3_multidimensional.parquet'
        df_b3.to_parquet(caminho_parquet)
        print(f"\nBase tridimensional gerada em: {caminho_parquet}")
        
        caminho_csv = '../data/raw/cotacoes_b3_fechamentos.csv'
        df_b3['Close'].to_csv(caminho_csv)
        print(f"Base de fechamentos gerada em: {caminho_csv}")
        
        # 6. Plotar o gráfico atualizado de Resultados Preliminares
        # Normalização na Base 100
        dados_normalizados = (df_b3['Close'] / df_b3['Close'].iloc[0]) * 100
        
        plt.figure(figsize=(14, 7))
        for coluna in dados_normalizados.columns:
            if coluna == '^BVSP':
                plt.plot(dados_normalizados.index, dados_normalizados[coluna], label='IBOVESPA (Benchmark)', linewidth=3, color='black')
            elif coluna == 'USDBRL=X':
                plt.plot(dados_normalizados.index, dados_normalizados[coluna], label='Dólar (USDBRL)', linewidth=2, linestyle='--', color='green')
            else:
                plt.plot(dados_normalizados.index, dados_normalizados[coluna], label=coluna, alpha=0.4)
                
        plt.title('Evolução Ajustada: Ativos Multisetoriais, IBOVESPA e Câmbio (Base 100)')
        plt.xlabel('Data')
        plt.ylabel('Crescimento Acumulado (%)')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.show()
        
    else:
        print("\nErro: A tabela ficou vazia após o alinhamento de feriados e remoção de valores nulos.")
else:
    print("\nErro crítico: Nenhum dado pôde ser processado.")