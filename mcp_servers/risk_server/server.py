from mcp.server.mcpserver import MCPServer
from calculators import IndicadoresRiscoB3
import json

# Inicializa o servidor usando a classe atualizada
mcp = MCPServer("RiskServer")
motor = IndicadoresRiscoB3()

@mcp.tool()
def otimizar_carteira_markowitz() -> str:
    """Otimiza a carteira usando a Teoria Moderna de Portfólios."""
    resultado = motor.otimizar_carteira_markowitz()
    return json.dumps(resultado)

@mcp.tool()
def calcular_beta_ativo(ticker: str) -> str:
    """Calcula o risco sistemático (Beta) de um ativo contra o IBOVESPA."""
    resultado = motor.calcular_beta(ticker)
    return json.dumps({"ticker": ticker, "beta": resultado})

@mcp.tool()
def calcular_var(pesos: dict, patrimonio_total: float, confianca: float = 0.95) -> str:
    """Calcula o Value at Risk (VaR) paramétrico diário."""
    resultado = motor.calcular_var_parametrico(pesos, patrimonio_total, confianca)
    return json.dumps({"var_financeiro": resultado})

if __name__ == "__main__":
    # Define o transporte para o novo padrão HTTP (Streamable HTTP)
    mcp.run(transport='streamable-http', host="0.0.0.0", port=8000)