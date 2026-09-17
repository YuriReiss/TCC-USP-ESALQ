/* eslint-disable @typescript-eslint/no-require-imports */
require('dotenv').config();
const { OpenAI } = require('openai');
// Ajuste este caminho relativo para onde está o seu mcpClient.js
const { conectarMotorQuantitativo } = require('../mcp_client/mcpClient.js'); 

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY, 
});

const historicoSessoes = {};
const LIMITE_MENSAGENS = 12; // Aumentei um pouco para acomodar as chamadas de ferramentas

// Variável global para manter a conexão MCP viva entre as requisições
let mcpClient = null;

// Função auxiliar para traduzir o padrão do MCP para o padrão de ferramentas da OpenAI
function mapearFerramentasMcpParaOpenAI(mcpTools) {
  return mcpTools.map(tool => ({
    type: "function",
    function: {
      name: tool.name,
      description: tool.description,
      parameters: tool.inputSchema
    }
  }));
}

const processarChat = async (req, res) => {
  const { mensagem, userId = 'usuario_padrao' } = req.body;

  if (!mensagem) {
    return res.status(400).json({ error: 'A mensagem do usuário é obrigatória.' });
  }

  try {
    // 1. Garante que o cliente MCP está conectado ao servidor Python
    if (!mcpClient) {
      mcpClient = await conectarMotorQuantitativo();
    }

    // 2. Busca as ferramentas disponíveis no Python e mapeia para a IA
    const mcpToolsResponse = await mcpClient.listTools();
    const openAiTools = mapearFerramentasMcpParaOpenAI(mcpToolsResponse.tools);

    // Inicia histórico se não existir
    if (!historicoSessoes[userId]) {
      historicoSessoes[userId] = [];
    }

    historicoSessoes[userId].push({ role: "user", content: mensagem });

    // 3. Primeira chamada para a IA
    const systemPrompt = "Você é o EconomicAI, um assistente quantitativo focado na B3 e na estruturação de portfólios. Você tem acesso a ferramentas matemáticas reais construídas para o TCC da USP/Esalq. Sempre que o usuário pedir análises de risco, VaR, Beta ou otimização de carteira de Markowitz, chame a ferramenta apropriada e explique os resultados de forma analítica e clara.";

    let completion = await openai.chat.completions.create({
      model: "gpt-4o-mini", // Recomendo o 4o-mini: é muito melhor para usar ferramentas e mais barato que o 3.5
      messages: [
        { role: "system", content: systemPrompt },
        ...historicoSessoes[userId]
      ],
      tools: openAiTools,
      tool_choice: "auto", 
      temperature: 0.2, // Temperatura baixa deixa a IA mais lógica e menos "criativa" (ideal para números)
    });

    let mensagemAssistente = completion.choices[0].message;

    // 4. Verifica se a IA decidiu que precisa acionar o Python
    if (mensagemAssistente.tool_calls) {
      console.log("IA decidiu usar ferramentas:", mensagemAssistente.tool_calls.map(t => t.function.name));
      
      // Salva a intenção de chamada da ferramenta no histórico (obrigatório pela OpenAI)
      historicoSessoes[userId].push(mensagemAssistente);

      // 5. O Node executa todas as funções solicitadas chamando o servidor MCP
      for (const toolCall of mensagemAssistente.tool_calls) {
        const args = JSON.parse(toolCall.function.arguments);
        
        const resultadoMcp = await mcpClient.callTool({
          name: toolCall.function.name,
          arguments: args
        });

        // Adiciona a resposta bruta (JSON do Python) no histórico para a IA ler
        historicoSessoes[userId].push({
          role: "tool",
          tool_call_id: toolCall.id,
          content: resultadoMcp.content[0].text
        });
      }

      // 6. Segunda chamada: a IA lê os números do Python e gera o texto final
      const segundaChamada = await openai.chat.completions.create({
        model: "gpt-4o-mini",
        messages: [
          { role: "system", content: systemPrompt },
          ...historicoSessoes[userId]
        ],
      });

      mensagemAssistente = segundaChamada.choices[0].message;
    }

    // 7. Salva a resposta final de texto no histórico
    historicoSessoes[userId].push({ role: "assistant", content: mensagemAssistente.content });

    // Mantém o limite de memória para não estourar os tokens
    if (historicoSessoes[userId].length > LIMITE_MENSAGENS) {
      historicoSessoes[userId] = historicoSessoes[userId].slice(-LIMITE_MENSAGENS);
    }

    res.status(200).json({
      resposta: mensagemAssistente.content
    });

  } catch (error) {
    console.error('Erro ao conectar com OpenAI ou MCP:', error);
    res.status(500).json({ error: 'Erro interno ao processar a requisição com o agente.' });
  }
};

module.exports = {
  processarChat
};