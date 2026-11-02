/* eslint-disable @typescript-eslint/no-require-imports */
const { orquestrarPortfolio } = require('../services/ensembleService.js');
const { conectarMotorQuantitativo } = require('../mcp_client/mcpClient.js');

// Variável global para manter a conexão MCP viva e evitar o erro "Already connected"
let mcpClientInstance = null;

const gerarPortfolioOtimizado = async (req, res) => {
  try {
    const { data_referencia } = req.body;

    if (!data_referencia) {
      return res.status(400).json({ sucesso: false, error: "A 'data_referencia' é obrigatória no payload." });
    }

    // 1. Conecta apenas se a linha ainda não estiver aberta
    if (!mcpClientInstance) {
        mcpClientInstance = await conectarMotorQuantitativo();
    }
    
    // 2. Passa a data limite para o Python não espreitar o futuro
    const contextoBruto = await mcpClientInstance.callTool({
      name: "gerar_contexto_janela_atual", 
      arguments: { data_limite: data_referencia } 
    });
    
    const contextoMacroMicro = JSON.parse(contextoBruto.content[0].text);

    if (contextoMacroMicro.status === "erro") {
       return res.status(500).json({ sucesso: false, error: contextoMacroMicro.mensagem });
    }

    // 3. Repassamos o cliente já conectado para o serviço orquestrar
    const resultadoFinal = await orquestrarPortfolio(contextoMacroMicro, mcpClientInstance);

    res.status(200).json({
      sucesso: true,
      data: resultadoFinal
    });

  } catch (error) {
    console.error('Erro no ciclo multiagente:', error);
    res.status(500).json({ 
      sucesso: false, 
      error: 'Erro interno ao processar a requisição da mesa de operações.' 
    });
  }
};

module.exports = {
  gerarPortfolioOtimizado
};