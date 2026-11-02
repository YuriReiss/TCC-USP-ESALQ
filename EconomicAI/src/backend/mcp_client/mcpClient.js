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
    
    return mcpClient;
  } catch (error) {
    console.error("❌ Erro ao conectar no MCP via HTTP:", error);
  }
}

module.exports = { conectarMotorQuantitativo };