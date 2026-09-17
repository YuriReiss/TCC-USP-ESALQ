/* eslint-disable @typescript-eslint/no-require-imports */
const { conectarMotorQuantitativo } = require('./mcpClient.js');

async function rodarTeste() {
    console.log("Iniciando teste de conexão MCP...");
    await conectarMotorQuantitativo();
    console.log("Teste finalizado!");
    process.exit(0);
}

rodarTeste();