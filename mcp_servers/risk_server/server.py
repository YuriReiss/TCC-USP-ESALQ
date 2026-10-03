import json
import pandas as pd
from mcp.server.mcpserver import MCPServer
from calculators import IndicadoresRiscoB3
from feature import EngenhariaDeFeatures

mcp = MCPServer("RiskServer")

# Variável global de estado para guardar o mapeamento da janela atual na memória do servidor
MEMORIA_GABARITO = {}

@mcp.tool()
def gerar_contexto_janela_atual(data_limite: str) -> str:
    global MEMORIA_GABARITO
    try:
        df_completo = pd.read_csv('../data_server/cotacoes_b3_fechamentos.csv', parse_dates=['Date']).set_index('Date')
        df_completo = df_completo.sort_index()
        
        df_historia_permitida = df_completo.loc[:data_limite]
        df_janela = df_historia_permitida.iloc[-252:] 
        
        if len(df_janela) < 21:
             return json.dumps({"status": "erro", "mensagem": f"Histórico insuficiente até a data {data_limite}."})
        
        engenharia = EngenhariaDeFeatures(df_janela)
        contexto_completo = engenharia.gerar_contexto_llm()
        
        # Salva o gabarito na memória e retira-o do dicionário antes de enviar para o Node/LLM
        MEMORIA_GABARITO = contexto_completo.pop("gabarito_ativos", {})
        
        # Retorna apenas cenário macro e as features anonimizadas ("Ativo_1", "Ativo_2")
        return json.dumps(contexto_completo)
    except Exception as e:
        return json.dumps({"status": "erro", "mensagem": str(e)})

@mcp.tool()
def otimizar_markowitz_selecao(ativos: list) -> str:
    global MEMORIA_GABARITO
    motor = IndicadoresRiscoB3()
    
    # Desmascara os ativos: traduz ["Ativo_3", "Ativo_8"] de volta para ["ITUB4.SA", "VALE3.SA"]
    ativos_reais = [MEMORIA_GABARITO[anonimo] for anonimo in ativos if anonimo in MEMORIA_GABARITO]
    
    ativos_validos = [ativo for ativo in ativos_reais if ativo in motor.df_acoes.columns]
    
    if not ativos_validos:
        return json.dumps({"status": "erro", "mensagem": "Nenhum ativo correspondente na base de dados após tradução."})
        
    motor.df_acoes = motor.df_acoes[ativos_validos]
    resultado = motor.otimizar_carteira_markowitz()
    
    if resultado["status"] == "sucesso":
        pesos = resultado["pesos_otimizados"]
        var_projetado = motor.calcular_var_parametrico(pesos, patrimonio_total=100000)
        beta_carteira = sum(motor.calcular_beta(ticker) * peso for ticker, peso in pesos.items())
        
        pacote_completo = {
            "status": "sucesso",
            "pesos_otimizados": pesos, # Retorna os tickers reais para o relatório final
            "metricas_esperadas": resultado["metricas_esperadas"],
            "risco_projetado": {
                "var_diario_95": var_projetado,
                "beta_carteira": round(beta_carteira, 4)
            }
        }
        return json.dumps(pacote_completo)
        
    return json.dumps(resultado)

if __name__ == "__main__":
    mcp.run(transport='streamable-http', host="0.0.0.0", port=8000)