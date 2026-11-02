/* eslint-disable @typescript-eslint/no-require-imports */
const { OpenAI } = require('openai');
require('dotenv').config();

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

// System Prompts com formatação JSON estrita e instrução para usar as identidades anonimizadas
const PROMPTS_AGENTES = {
  Value: `És um gestor quantitativo focado em Value Investing e Proteção de Capital.
Regras: Prioriza ativos com Skewness positiva e baixa Volatilidade Anual. Rejeita Kurtosis alta.
Retorna APENAS um objeto JSON com a chave "ativos" contendo 5 ativos (ex: {"ativos": ["Ativo_1", "Ativo_3", "Ativo_5", "Ativo_7", "Ativo_9"]}).`,
  
  Growth: `És um gestor agressivo focado em Growth e Momentum.
Regras: Maximiza o Momentum_12M. Se o cenário for 'Calmaria', ignora a volatilidade. Se 'Turbulência', reduz a exposição.
Retorna APENAS um objeto JSON com a chave "ativos" contendo 5 ativos (ex: {"ativos": ["Ativo_2", "Ativo_4", "Ativo_6", "Ativo_8", "Ativo_10"]}).`,
  
  Macro: `És um estrategista Macro focado em Risco Sistémico.
Regras: Analisa o Regime Atual. Se 'Calmaria', escolhe ativos cíclicos. Se 'Turbulência', protege o capital com mínima volatilidade.
Retorna APENAS um objeto JSON com a chave "ativos" contendo 5 ativos (ex: {"ativos": ["Ativo_1", "Ativo_2", "Ativo_3", "Ativo_4", "Ativo_5"]}).`
};

/**
 * Orquestra o debate dos agentes LLM e envia o consenso para o motor quantitativo.
 * Recebe o mcpClient já conectado pelo controlador para evitar duplicidade de rede.
 */
async function orquestrarPortfolio(contextoMacroMicro, mcpClient) {
  // A IA recebe apenas as estatísticas e os nomes genéricos (Ativo_1, Ativo_2...)
  const dadosContexto = JSON.stringify(contextoMacroMicro, null, 2);

  console.log("Iniciando debate simultâneo na mesa de operações (LLMs)...");

  // 1. Executa chamadas paralelas reais à API da OpenAI
  const promessasAgentes = Object.entries(PROMPTS_AGENTES).map(async ([nome, promptBase]) => {
    try {
      const completion = await openai.chat.completions.create({
        model: "gpt-4o-mini",
        temperature: 0.1, // Quase determinístico para rigor científico
        response_format: { type: "json_object" }, // Força o retorno estruturado
        messages: [
          { role: "system", content: promptBase },
          { role: "user", content: `Contexto do Mercado (Anonimizado):\n${dadosContexto}` }
        ]
      });
      
      const respostaJson = JSON.parse(completion.choices[0].message.content);
      return { nome, votos: respostaJson.ativos || [] };
      
    } catch (erro) {
      console.error(`[Aviso] Falha ao consultar agente ${nome}: ${erro.message}`);
      return { nome, votos: [] };
    }
  });

  const resultadosAgentes = await Promise.all(promessasAgentes);

  // 2. Classificador de Votação (Ensemble Voting)
  const contagemVotos = {};
  resultadosAgentes.forEach(agente => {
    agente.votos.forEach(ticker => {
      contagemVotos[ticker] = (contagemVotos[ticker] || 0) + 1;
    });
  });

  // Regra de Consenso: Aprova apenas os ativos selecionados por 2 ou mais agentes
  const ativosAprovados = Object.keys(contagemVotos).filter(ticker => contagemVotos[ticker] >= 2);

  if (ativosAprovados.length === 0) {
    throw new Error("Não houve consenso entre os agentes para a formação da carteira (ou os LLMs falharam por falta de saldo).");
  }

  console.log(`Consenso alcançado: ${ativosAprovados.length} ativos aprovados.`);

  // 3. Envia o consenso anonimizado para a ferramenta Markowitz no servidor Python
  // O Python, internamente, usará a MEMORIA_GABARITO para traduzir "Ativo_X" para o Ticker real
  const resultadoMcp = await mcpClient.callTool({
    name: "otimizar_markowitz_selecao",
    arguments: { ativos: ativosAprovados }
  });

  return {
    detalhes_votacao: resultadosAgentes,
    ativos_consenso_anonimos: ativosAprovados, // O que a IA decidiu cegamente
    alocacao_final_markowitz: JSON.parse(resultadoMcp.content[0].text) // O que a Matemática calculou (com nomes reais)
  };
}

module.exports = {
  orquestrarPortfolio
};