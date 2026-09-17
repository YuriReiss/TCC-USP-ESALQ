/* eslint-disable @typescript-eslint/no-require-imports */
const { Client } = require("@modelcontextprotocol/sdk/client/index.js");
const { StreamableHTTPClientTransport } = require("@modelcontextprotocol/sdk/client/streamableHttp.js");

const mcpClient = new Client(
  { name: "economic-ai-client", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

async function conectarMotorQuantitativo() {
  try {
    // Aponta para a raiz do servidor /mcp em vez de /sse
    const transport = new StreamableHTTPClientTransport(new URL("http://localhost:8000/mcp"));
    
    await mcpClient.connect(transport);
    console.log("✅ Conectado ao Servidor MCP de Risco via Streamable HTTP!");

    const resultado = await mcpClient.callTool({
      name: "otimizar_carteira_markowitz",
      arguments: {}
    });

    console.log("Resultado bruto recebido via rede:", resultado.content[0].text);
    return mcpClient;
  } catch (error) {
    console.error("❌ Erro ao conectar no MCP via HTTP:", error);
  }
}

module.exports = { conectarMotorQuantitativo };