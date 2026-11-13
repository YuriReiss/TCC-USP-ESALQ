import yfinance as yf
import pandas as pd
import os
import matplotlib.pyplot as plt
import time
import json
from urllib.parse import quote
from urllib.request import Request, urlopen

# 1. Garantir que a pasta de destino existe
# Grava direto onde o pipeline lê (data_server), em vez de uma pasta avulsa.
DESTINO = '../mcp_servers/data_server'
os.makedirs(DESTINO, exist_ok=True)

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
# Janela de ~15 anos: a análise de poder mostrou que a comparação contra o
# Markowitz isolado (tracking error de 4,96% a.a.) precisa de ~180 janelas de
# 21 dias para detectar o efeito observado. Com 24 janelas o efeito mínimo
# detectável era de 25% ao ano, ou seja, o teste era cego.
data_inicio = '2011-01-01'
data_fim = '2026-06-01'

print(f"Iniciando extração sequencial ({data_inicio} a {data_fim})...")

dfs = []
ativos_com_erro = []

def baixar_via_chart_api(ticker):
    """
    Lê o endpoint público de chart do Yahoo e replica o auto_adjust=True do yfinance.

    Necessário onde fc.yahoo.com (de onde o yfinance tira o cookie/crumb) é
    interceptado por proxy: sem crumb o yfinance cai num caminho que o Yahoo limita
    por rate e devolve DataFrame vazio, indistinguível de ticker inexistente.
    """
    p1 = int(pd.Timestamp(data_inicio, tz='UTC').timestamp())
    p2 = int(pd.Timestamp(data_fim, tz='UTC').timestamp())
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(ticker)}"
           f"?period1={p1}&period2={p2}&interval=1d")

    with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30) as resposta:
        resultado = json.load(resposta)['chart']['result'][0]

    # Ticker sem série no Yahoo (caso do IFIX.SA): devolve vazio para o chamador
    # tratar como ativo ignorado, em vez de estourar KeyError.
    if 'timestamp' not in resultado:
        return pd.DataFrame()

    # O nome 'Date' precisa sobreviver até o CSV: todo o pipeline lê parse_dates=['Date'].
    indice = pd.to_datetime(resultado['timestamp'], unit='s', utc=True).tz_localize(None).normalize()
    indice.name = 'Date'
    cotacoes = resultado['indicators']['quote'][0]
    df = pd.DataFrame({campo.capitalize(): cotacoes[campo]
                       for campo in ['open', 'high', 'low', 'close', 'volume']}, index=indice)

    # Mesmo ajuste do auto_adjust: escala OHLC pela razão adjclose/close (splits e proventos).
    ajustado = resultado['indicators'].get('adjclose', [{}])[0].get('adjclose')
    if ajustado is not None:
        fator = pd.Series(ajustado, index=indice) / df['Close']
        for campo in ['Open', 'High', 'Low', 'Close']:
            df[campo] = df[campo] * fator

    return df.dropna(how='all')


def baixar_com_retry(ticker, tentativas=2):
    """
    O yfinance devolve um DataFrame vazio tanto para ticker inexistente como para
    HTTP 429, mascarando rate limit como 'possibly delisted'. Sem backoff, um
    bloqueio temporário do Yahoo é lido como ativo sem dados e a série some da base
    silenciosamente. Esgotadas as tentativas, cai no endpoint de chart direto.
    """
    for tentativa in range(1, tentativas + 1):
        df = yf.download(ticker, start=data_inicio, end=data_fim,
                         progress=False, auto_adjust=True)
        if not df.empty:
            return df
        if tentativa < tentativas:
            espera = 15 * (2 ** (tentativa - 1))
            print(f"  [retry {tentativa}/{tentativas - 1}] {ticker} vazio; aguardando {espera}s...")
            time.sleep(espera)

    print(f"  [fallback] {ticker} via endpoint de chart direto.")
    return baixar_via_chart_api(ticker)


# 3. Executar o download sequencial sem sessão estática (Anti-Bloqueio)
for ticker in tickers:
    try:
        df_temp = baixar_com_retry(ticker)

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

    time.sleep(8)

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

    # Diagnóstico do ativo limitante: o dropna() abaixo corta a base inteira até o
    # ativo que começa mais tarde. Sem este relatório a perda de anos é silenciosa.
    primeiros = fechamentos_limpos.apply(lambda s: s.first_valid_index())
    print("\nPrimeiro pregão disponível por ativo:")
    for ticker, data in primeiros.sort_values(ascending=False).items():
        print(f"  {ticker:<12} {str(data.date()) if pd.notna(data) else 'sem dados'}")
    limitante = primeiros.idxmax()
    print(f"\n-> Base comum comeca em {primeiros.max().date()}, limitada por {limitante}.")

    # Calendário mestre da B3: a estratégia negocia ações brasileiras, então o índice
    # tem de ser o do pregão. O USDBRL=X traz barras de sábado e domingo (o câmbio abre
    # domingo à noite) e, pela união do concat, elas entrariam como pregões falsos com
    # retorno zero nas ações — diluindo volatilidade, VaR e Beta, e encurtando a janela
    # de 252 dias para menos de um ano de mercado real.
    if '^BVSP' in ativos_validos:
        calendario_b3 = fechamentos_limpos['^BVSP'].dropna().index
        descartadas = len(df_b3.index.difference(calendario_b3))
        df_b3 = df_b3.reindex(calendario_b3)
        print(f"-> Calendario alinhado ao ^BVSP: {descartadas} datas fora do pregao descartadas.")

    # Alinhamento de Feriados (B3 vs USD):
    # Propaga o último preço válido (forward fill), depois remove os NaNs residuais no início da série
    df_b3 = df_b3.ffill().dropna()

    janelas = (len(df_b3) - 252) // 21
    print(f"-> {len(df_b3)} pregoes apos alinhamento, o que da {janelas} janelas de rebalanceamento.")

    if not df_b3.empty:
        print("\nPrimeiras linhas da matriz de Fechamento (Close):")
        print(df_b3['Close'].head())
        
        # 5. Salvar arquivos
        caminho_parquet = f'{DESTINO}/cotacoes_b3_multidimensional.parquet'
        df_b3.to_parquet(caminho_parquet)
        print(f"\nBase tridimensional gerada em: {caminho_parquet}")

        caminho_csv = f'{DESTINO}/cotacoes_b3_fechamentos.csv'
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
        # savefig em vez de show: o script roda sem travar esperando a janela fechar.
        plt.savefig('../images/Resultados_Preliminares_EVOLUCAO_AJUSTADA_ATIVOS_IBOVESPA.png', dpi=300)
        print("Grafico de evolucao atualizado em images/.")

    else:
        print("\nErro: A tabela ficou vazia após o alinhamento de feriados e remoção de valores nulos.")
else:
    print("\nErro crítico: Nenhum dado pôde ser processado.")