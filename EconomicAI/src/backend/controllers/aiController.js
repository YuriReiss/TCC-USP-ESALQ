/* eslint-disable @typescript-eslint/no-require-imports */
require('dotenv').config();
const { OpenAI } = require('openai');

// Inicializa o cliente da OpenAI usando variável de ambiente (Segurança em 1º lugar!)
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY, 
});

// Objeto para guardar o histórico na memória (chave: ID do usuário, valor: array de mensagens)
// NOTA: Em produção (servidores que reiniciam ou escalam), use um Banco de Dados ou Redis.
const historicoSessoes = {};

// Limite de mensagens a serem lembradas (8 mensagens = 4 perguntas e 4 respostas)
const LIMITE_MENSAGENS = 8; 

const processarChat = async (req, res) => {
  // Para diferenciar os usuários, é ideal receber um userId. 
  // Se não vier, usamos um padrão para testes.
  const { mensagem, userId = 'usuario_padrao' } = req.body;

  if (!mensagem) {
    return res.status(400).json({ error: 'A mensagem do usuário é obrigatória.' });
  }

  // Se o usuário ainda não tem histórico, cria um array vazio
  if (!historicoSessoes[userId]) {
    historicoSessoes[userId] = [];
  }

  // 1. Adiciona a nova mensagem do usuário ao histórico
  historicoSessoes[userId].push({ role: "user", content: mensagem });

  // 2. Garante que o histórico não passe do limite de 8 mensagens
  if (historicoSessoes[userId].length > LIMITE_MENSAGENS) {
    historicoSessoes[userId] = historicoSessoes[userId].slice(-LIMITE_MENSAGENS);
  }

  try {
    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        { 
          role: "system", 
          content: "Você é o EconomicAI, um assistente especializado no mercado financeiro e na B3. Forneça respostas analíticas, curtas e diretas sobre investimentos e economia." 
        },
        // 3. Despeja (spread) o histórico salvo logo após o system prompt
        ...historicoSessoes[userId]
      ],
      temperature: 0.3,
    });

    const respostaAssistente = completion.choices[0].message.content;

    // 4. Salva a resposta do assistente no histórico para a próxima rodada
    historicoSessoes[userId].push({ role: "assistant", content: respostaAssistente });

    // Garante o limite novamente (opcional aqui, mas é uma boa prática de segurança)
    if (historicoSessoes[userId].length > LIMITE_MENSAGENS) {
        historicoSessoes[userId] = historicoSessoes[userId].slice(-LIMITE_MENSAGENS);
    }

    res.status(200).json({
      resposta: respostaAssistente
    });
  } catch (error) {
    console.error('Erro ao conectar com OpenAI:', error);
    res.status(500).json({ error: 'Erro interno ao processar a requisição com o agente.' });
  }
};

module.exports = {
  processarChat
};