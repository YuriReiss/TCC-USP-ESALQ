// Conteúdo textual da dissertação. Separado do gerador para que o texto possa ser
// revisado sem mexer na formatação.
//
// Marcação aceita dentro dos parágrafos:
//   *texto*  -> negrito
//   "texto"  -> mantido como está (aspas são o recurso do autor para estrangeirismos,
//               já que as normas reservam o itálico a nomes científicos)

const RESUMO = `O mercado de capitais brasileiro exigiu métodos analíticos avançados para lidar com a sua acentuada volatilidade, fundamentando-se historicamente em modelos matemáticos complexos. A Inteligência Artificial [IA] Generativa e os "Large Language Models" [LLMs] despontaram como ferramentas promissoras para a interpretação de cenários econômicos, mas a sua adoção em finanças quantitativas esbarrou na natureza estocástica e no Viés de Retrospectiva Implícito ("Implicit Look-Ahead Bias"). O estudo desenvolveu um "framework" integrado ao "Model Context Protocol" [MCP], que isolou o raciocínio heurístico de um "ensemble" de agentes LLM da execução de algoritmos matemáticos exatos, e avaliou se a arquitetura modificou o perfil de risco de uma carteira de ações da B3. A validação percorreu 168 janelas não sobrepostas de 21 pregões entre janeiro de 2012 e maio de 2026, sob anonimização estrita dos ativos e corte dos indicadores fundamentalistas pela data de recebimento na Comissão de Valores Mobiliários. O controle decisivo confrontou a carteira híbrida com as mesmas dez ações mantidas em peso igual. O coeficiente Beta da carteira híbrida alcançou 0,709, ante 1,061 do universo em peso igual, com rejeição da igualdade entre ambos (t = -3,85; p = 0,0002), enquanto a captura de queda recuou de 0,89 para 0,42. Nas 73 janelas de recuo do índice, a diferença média por janela atingiu +2,24 pontos percentuais (p = 0,0016). A camada matemática devolveu saídas idênticas sob repetição e sob permutação da ordem dos ativos. O excesso de retorno acumulado, em contrapartida, mostrou-se atribuível à seleção retrospectiva do universo de ativos.`;

const ABSTRACT = `The Brazilian capital market required advanced analytical methods to cope with its pronounced volatility, historically relying on complex mathematical models. Generative Artificial Intelligence and Large Language Models emerged as promising tools for the interpretation of economic scenarios, yet their adoption in quantitative finance was hindered by their stochastic nature and by implicit look-ahead bias. This study developed a framework built on the Model Context Protocol, which isolated the heuristic reasoning of an ensemble of LLM agents from the execution of exact mathematical algorithms, and assessed whether the architecture modified the risk profile of a Brazilian equity portfolio. Validation spanned 168 non-overlapping windows of 21 trading sessions between January 2012 and May 2026, under strict asset anonymisation and with fundamental indicators truncated by their filing date at the Brazilian Securities Commission. The decisive control compared the hybrid portfolio against the same ten stocks held at equal weight. The hybrid portfolio reached a beta of 0.709, against 1.061 for the equally weighted universe, with equality between them rejected (t = -3.85; p = 0.0002), while downside capture fell from 0.89 to 0.42. Across the 73 windows in which the index declined, the mean difference per window reached +2.24 percentage points (p = 0.0016). The mathematical layer returned identical outputs under repetition and under permutation of asset ordering. Cumulative excess return, by contrast, proved attributable to the retrospective selection of the asset universe.`;

// Palavras-chave preservadas do texto original. Nenhuma delas repete termo do título.
const PALAVRAS_CHAVE = 'Inteligência artificial; Finanças quantitativas; Teoria de Markowitz; "Walk-Forward"; "Model Context Protocol".';
const KEYWORDS = 'Artificial intelligence; Quantitative finance; Markowitz theory; Walk-forward; Model Context Protocol.';

const TITULO = 'Alocação de ativos e gestão de risco na B3: multiagentes e modelagem matemática determinística';
const TITULO_EN = 'Asset allocation and risk management on the B3 exchange: multi-agent systems and deterministic mathematical modelling';

const AUTORES = 'Yuri dos Reis de Oliveira¹*; Adâmara Santos Gonçalves Felício²';
const ENDERECOS = [
  '¹* Bacharel. Universidade de São Paulo (USP/Esalq). E-mail autor correspondente: yurireisoliveira@usp.br',
  '² Doutora. Universidade de São Paulo (USP/Esalq). E-mail: adamara.felicio@usp.br'
];
const CABECALHO = 'Trabalho de Conclusão de Curso apresentado para obtenção do título de especialista em Data Science e Analytics – 2027';

// ---------------------------------------------------------------------------
// INTRODUÇÃO — preservada do texto original; alterado apenas o parágrafo final,
// em que o objetivo foi reorientado, e acrescentadas as hipóteses exigidas pelas
// normas. Verbos convertidos para o pretérito perfeito do indicativo.
// ---------------------------------------------------------------------------
const INTRODUCAO = [
  `O mercado de capitais brasileiro, estruturado operacionalmente pela B3 (Brasil, Bolsa, Balcão), caracterizou-se por uma dinâmica de acentuada volatilidade e forte exposição a choques macroeconômicos globais e domésticos. Neste ambiente de incerteza, a alocação eficiente de capital e a gestão rigorosa de risco constituíram desafios que transcenderam a mera intuição humana, exigindo o escrutínio de imensos volumes de dados. Historicamente, a construção de portfólios eficientes fundamentou-se na Teoria Moderna de Portfólios, que demonstrou matematicamente como a diversificação estratégica pôde maximizar o retorno esperado para um dado nível de risco (Markowitz, 1952). A formulação matemática clássica buscou minimizar a variância do portfólio, sujeita a restrições orçamentais e de retorno alvo, e consolidou-se como o alicerce da diversificação (Markowitz, 1959). Contudo, a execução analítica destas metodologias sobre fluxos massivos de dados financeiros gerou severos gargalos práticos. A otimização baseada em variância, quando exposta à totalidade dos ativos de uma bolsa, sofreu frequentemente da Maldição da Dimensionalidade. A presença de ruído estatístico no histórico de preços gerou matrizes instáveis, o que exigiu filtros qualitativos rigorosos antes da submissão dos dados aos modelos (Guo, 2022; Prado, 2018).`,
  `Com o advento da Inteligência Artificial [IA] Generativa, especificamente os "Large Language Models" [LLMs], emergiu a possibilidade de introduzir raciocínio semântico e análise lógica no processo inicial de triagem financeira (Handler et al., 2024). O estado da arte expandiu rapidamente o uso de comandos textuais para a estruturação de Sistemas Multiagentes, nos quais diferentes personas de inteligência artificial colaboraram e debateram, atuando como um mecanismo para a redução de variância na tomada de decisão qualitativa (Saha et al., 2025; Xi et al., 2023). Autores como Cheng et al. (2026) e Devi et al. (2026) demonstraram que a alocação de capital se beneficiou destes modelos de debate especialista. No entanto, a transposição direta de LLMs para as finanças quantitativas esbarrou em limitações críticas. Primeiramente, as redes neurais generativas possuíram uma natureza estocástica focada na previsão semântica, o que as tornou imprecisas e propensas a alucinações na execução de cálculos aritméticos exatos (Wu et al., 2023). Em segundo lugar, os LLMs sofreram de um grave Viés de Retrospectiva Implícito ("Implicit Look-Ahead Bias"). Como estes modelos foram pré-treinados com vastos volumes de dados históricos, retiveram nos seus pesos conhecimento sobre o desempenho posterior das empresas. A contaminação da simulação por informação indisponível na data da decisão retira validade fora da amostra ao resultado apurado, conforme demonstraram Bailey et al. (2014) a propósito do sobreajuste de estratégias a séries passadas. Conforme alertaram Lumer et al. (2025), sincronizar o contexto abstrato destas IAs com ferramentas de cálculo exato exigiu protocolos padronizados de comunicação para evitar a degradação aritmética.`,
  `Para contornar estas barreiras, o presente estudo introduziu uma arquitetura de engenharia de software estruturada sob o "Model Context Protocol" [MCP], que padronizou a interoperabilidade entre agentes cognitivos e infraestruturas de dados isoladas (Venkiteela, 2025). O MCP atuou como um paradigma que permitiu isolar a camada de raciocínio lógico da camada de cálculo determinístico. O objetivo central desta pesquisa consistiu em desenvolver, testar e avaliar a robustez deste "framework" quantitativo, verificando se a dissociação arquitetural providenciada pelo MCP, aliada a algoritmos de anonimização estrita e a uma camada matemática determinística, alterou de forma mensurável o perfil de risco de uma carteira de ações da B3. A formulação do objetivo nestes termos decorreu de uma exigência de desenho experimental: um "backtest" que compara uma carteira ativa apenas com um índice de mercado confunde o efeito da arquitetura com o efeito da escolha prévia do universo de ativos, razão pela qual a avaliação adotou como referência o próprio conjunto de ações que originou a carteira.`,
  `Duas hipóteses orientaram a investigação. A primeira estabeleceu que o coeficiente Beta da carteira construída pela arquitetura difere do coeficiente Beta do seu próprio universo de ativos mantido em peso igual, de modo que a redução de sensibilidade ao mercado não decorra da composição do universo. A segunda estabeleceu que a camada de cálculo produz saídas idênticas sob repetição da execução e sob permutação da ordem de apresentação dos ativos, condição sem a qual o termo determinístico não se sustenta. A hipótese nula associada a cada uma delas pressupôs, respetivamente, a igualdade dos coeficientes e a existência de divergência numérica entre execuções.`
];

// ---------------------------------------------------------------------------
// METODOLOGIA
// ---------------------------------------------------------------------------
const MET_ABERTURA = [
  `A pesquisa caracterizou-se como de natureza aplicada. Quanto aos objetivos, classificou-se como exploratória; quanto à abordagem dos dados, como quantitativa; quanto ao delineamento, como implementação de algoritmo de "Machine Learning"; e quanto às técnicas e instrumentos de coleta, como levantamento de dados secundários combinado a pesquisa documental. O planejamento estatístico contemplou estatística descritiva das séries de retorno, regressão linear com erros-padrão corrigidos para autocorrelação e heterocedasticidade, testes de hipótese sobre médias pareadas e sobre coeficientes angulares, análise de poder estatístico e simulação estocástica. Toda a análise correu em Python 3.12.`,
  `Com o intuito de assegurar a total transparência e a reprodutibilidade metodológica desta pesquisa, adotaram-se as diretrizes de Ciência Aberta. Todo o código-fonte do motor quantitativo, a lógica de orquestração dos agentes, a arquitetura dos servidores MCP e a base de dados histórica foram integralmente disponibilizados em repositório público no GitHub (https://github.com/YuriReiss/TCC-USP-ESALQ). A Figura 1 sistematiza a arquitetura implementada e delimita a fronteira entre a camada heurística, conduzida por modelos de linguagem, e a camada determinística, conduzida por algoritmos matemáticos exatos.`
];

const MET_COLETA = [
  `A base de dados primária de preços foi extraída mediante a API pública do "Yahoo Finance". A amostra compreendeu o período de 03 jan. 2011 a 06 maio 2026, do qual os três primeiros semestres serviram exclusivamente à formação da primeira janela de treino, de modo que a apuração de desempenho se iniciou em 06 jan. 2012. Esta janela de catorze anos de apuração abrangeu a crise cambial de 2015, a recessão de 2015 e 2016, o choque da pandemia em 2020 e o ciclo de aperto monetário subsequente, o que garantiu densidade estatística para capturar múltiplos regimes econômicos. A seleção englobou dez ativos de renda variável e dois indicadores macroeconômicos, estruturados para maximizar o potencial de diversificação:`,
];

const MET_ATIVOS = [
  `Commodities e Materiais Básicos (PETR4, VALE3): ativos de elevada liquidez, com forte correlação à demanda global e à variação cambial.`,
  `Setor Financeiro (ITUB4, BBAS3, BBDC4): instituições sensíveis à política monetária e ao crédito.`,
  `Utilidade Pública e Saneamento (SBSP3, CMIG4): pilares defensivos com fluxos de caixa previsíveis, fundamentais para a redução do "Value at Risk" (VaR).`,
  `Consumo e Bens Industriais (WEGE3, ABEV3, LREN3): cobriu desde crescimento e consumo não-cíclico até ao varejo cíclico dependente da inflação.`,
  `Variáveis de Controle e "benchmark": a variação cambial (USDBRL) atuou como termômetro de risco país, enquanto o Índice Bovespa (^BVSP) serviu como base para o Coeficiente Beta e referência passiva.`
];

const MET_COLETA_FIM = [
  `Para assegurar a integridade estatística, aplicou-se o descarte programático de pregões inexistentes ou feriados e utilizou-se estritamente a variável de Preço de Fechamento Ajustado ("Adj Close"). A taxa livre de risco adotada em todas as métricas de excesso correspondeu ao Certificado de Depósito Interbancário [CDI] apurado na própria janela, cuja média geométrica no período alcançou 9,81% ao ano.`,
  `A definição deste conjunto de dez ativos precedeu a construção do modelo e não obedeceu a uma regra de seleção documentada, o que configurou um viés de sobrevivência cuja magnitude foi posteriormente medida e reportada na seção de resultados, e não tratada como ressalva genérica.`
];

const MET_FUNDAMENTOS = [
  `Aos atributos de preço somaram-se indicadores fundamentalistas extraídos dos formulários de demonstrações financeiras padronizadas divulgados pela Comissão de Valores Mobiliários [CVM]: retorno sobre o patrimônio líquido, margem líquida, alavancagem, crescimento de receita e crescimento de lucro. A incorporação destes indicadores impôs um cuidado temporal distinto daquele exigido pelas séries de preço. Uma demonstração referente ao primeiro trimestre descreveu um período já encerrado, mas tornou-se informação pública apenas na data em que a CVM a recebeu, em média trinta e nove dias depois do encerramento do trimestre.`,
  `O corte temporal dos fundamentos utilizou, por conseguinte, a data de recebimento do documento pela CVM, e não a data de referência do trimestre. Qualquer demonstração cuja data de recebimento foi posterior à data da decisão permaneceu invisível ao sistema, ainda que o trimestre a que se referia já tivesse terminado. Estabeleceu-se ainda uma defasagem máxima de quatrocentos dias, de forma a descartar demonstrações antigas que permaneceriam no conjunto por ausência de divulgação mais recente.`
];

const MET_KMEANS = [
  `A aplicação de métodos não supervisionados em finanças permitiu a extração de regimes sem interferência do viés humano (Prado, 2018). Antes da inferência dos agentes, o motor em Python executou a extração de atributos de "Momentum" (12 meses), Volatilidade Anualizada, "Skewness" e Kurtosis. Simultaneamente, implementou-se o algoritmo de agrupamento K-Means, que processou a volatilidade rolante do IBOVESPA e a variação do par USD/BRL e classificou estritamente o mercado em regimes de Calmaria ou Turbulência, conforme demonstrado na Figura 2.`,
  `O painel A da Figura 2 dispôs as 168 datas de decisão no plano dos dois atributos, atribuída a cada ponto a cor do rótulo que vigorou naquela data. A fronteira daí resultante não se formou de maneira vertical: os dois atributos repartiram entre si a separação, e a tendência cambial revelou-se o eixo mais discriminante dos dois. Tomada isoladamente, a tendência do dólar reproduziu 92,3% dos rótulos, contra 79,8% da volatilidade do índice, e 36 das 47 janelas de Turbulência situaram-se abaixo da volatilidade observada na janela de Calmaria mais volátil. A Turbulência caracterizou-se, por conseguinte, pela conjugação de volatilidade elevada com depreciação acelerada do real, com médias de 27,6% e de +68,4% ao ano, contra 18,0% e -14,9% nas janelas de Calmaria.`,
  `O ajuste deste agrupamento exigiu duas decisões de desenho que afetaram diretamente a comparabilidade entre janelas. A primeira consistiu na padronização prévia dos atributos, sem a qual a volatilidade e a variação cambial entraram na distância euclidiana em escalas incompatíveis e o agrupamento passou a refletir sobretudo a variável de maior amplitude. A segunda consistiu na adoção de uma janela expansiva, em que cada reajuste do algoritmo utilizou toda a história disponível até à data da decisão, em substituição a uma janela móvel de 252 dias.`,
  `A janela móvel produziu um defeito de coerência interna: como o algoritmo foi reajustado a cada rebalanceamento sobre um conjunto de observações distinto, o limiar que separou Calmaria de Turbulência oscilou ao longo do tempo e o mesmo nível de volatilidade recebeu rótulos opostos em janelas diferentes. A janela expansiva preservou integralmente o desenho "point-in-time", uma vez que nenhuma observação posterior à data da decisão entrou no ajuste, e eliminou a incomparabilidade do rótulo.`,
  `O painel B da Figura 2 documenta este reajuste. O limiar de volatilidade que separou os dois regimes foi reestimado em cada uma das 168 datas, sempre a partir de observações anteriores à data da decisão, e percorreu a faixa de 26,6% a 34,5% ao longo do período, numa amplitude de 7,9 pontos percentuais. Sob a janela móvel de 252 dias, o mesmo limiar percorrera 61,5 pontos percentuais. Registre-se que este limiar constituiu apenas a projeção unidimensional de uma regra que operou em duas dimensões, razão pela qual 19,6% das janelas receberam rótulo que a volatilidade isolada não explicaria, decididas que foram pela tendência cambial.`
];

const MET_CAMARA = [
  `O Viés de Retrospectiva ("Look-Ahead Bias") constituiu a principal causa de fracasso na transposição de simulações para o mercado real (Bailey et al., 2014). Para erradicar esta falha, a ferramenta atuou como uma câmara cega, mecanismo que correspondeu à etapa 3 da Figura 1. O orquestrador requisitou uma data específica do passado. O servidor em Python fatiou o histórico rigorosamente até esse dia. Os códigos de negociação reais, como VALE3.SA, foram mascarados para identificadores abstratos, como Ativo_1. O conteúdo recebido pela API da OpenAI continha exclusivamente métricas numéricas puras.`,
  `A reversão da máscara ocorreu somente dentro do servidor determinístico, depois de concluída a votação, de maneira que em nenhum momento o modelo de linguagem teve acesso à identidade das empresas analisadas. O mascaramento impediu que o modelo recorresse ao desempenho futuro que memorizou durante o pré-treino, ao passo que o fatiamento temporal impediu o acesso a qualquer dado posterior à data da decisão. Os dois mecanismos atuaram sobre fontes distintas de contaminação e revelaram-se complementares.`
];

const MET_AGENTES = [
  `No servidor central, implementou-se um modelo de "Ensemble Voting" que utilizou a API da OpenAI, com o modelo gpt-4o-mini. Três personas foram instanciadas: Agente Value, orientado a retorno sobre o patrimônio líquido, margem líquida e alavancagem; Agente Growth, orientado ao crescimento de receita e de lucro confirmado pelo "Momentum"; e Agente Macro, orientado ao regime identificado pelo K-Means e ao endividamento. Aprovou-se uma regra de consenso rígida: um ativo anonimizado apenas avançou para a otimização caso obtivesse a aprovação de, no mínimo, dois agentes.`,
  `Os parâmetros de amostragem da API foram fixados em "temperature" igual a zero e semente igual a 42, em substituição ao valor de 0,1 adotado em versão anterior do sistema. O rebaixamento da temperatura para zero reduziu a aleatoriedade da amostragem de tokens ao mínimo permitido pela interface, mas não a eliminou: durante a execução, os três agentes receberam identificadores de infraestrutura distintos na mesma chamada, o que evidenciou que o provedor não manteve o mesmo "backend" de inferência. A variabilidade residual daí decorrente foi tratada como limitação declarada e submetida a teste de réplica, descrito adiante.`,
  `Nenhum valor numérico da carteira resultou do modelo de linguagem. Os agentes exerceram exclusivamente a função de seleção: indicaram quais ativos anônimos deveriam avançar, sem atribuir pesos, estimar retornos ou calcular métricas de risco.`
];

const MET_OTIMIZACAO = [
  `A sub-lista anonimizada foi reenviada ao MCP. Após reverter a anonimização, o motor calculou a Fronteira Eficiente focada na Maximização do Índice Sharpe (Brînză et al., 2023). Foram apuradas, também, métricas exatas de defesa: o "Value at Risk" paramétrico a 95% (Orlova e Sayakhetdinov, 2023) e o Coeficiente Beta ponderado (Skorupski, 2023). O motor restringiu a estimação da matriz de covariância e do Beta à mesma janela de treino de 252 pregões, com o ativo e o índice de referência fatiados em conjunto, pois o fatiamento de apenas um deles faria o Beta comparar a janela de treino com o histórico completo do índice.`,
  `A exigência de determinismo imposta pelo título do trabalho obrigou a uma correção específica no somatório ponderado do Beta. O cálculo percorria os ativos na ordem de inserção do dicionário que os armazenava e, como a soma de números de ponto flutuante não é associativa, duas execuções que apresentassem os mesmos ativos em ordens diferentes devolviam valores divergentes na décima casa decimal. A correção consistiu em percorrer os ativos em ordem alfabética fixa, e não em arredondar o resultado, de modo que a igualdade bit a bit entre execuções passou a decorrer da estrutura do cálculo e não de um truncamento posterior.`
];

const MET_VALIDACAO = [
  `O excesso de otimização em dados do passado ("in-sample") não garantiu previsibilidade futura (Pardo, 2011). Adotou-se o rigoroso enquadramento "Walk-Forward". Fixou-se uma janela de treino de 252 pregões e uma janela de apuração estrita de 21 pregões, sem sobreposição entre janelas de apuração consecutivas. O sistema simulou a exposição a mercado, avançou sobre os retornos sequencialmente e compôs os juros, o que totalizou 168 janelas válidas entre 06 jan. 2012 e 06 maio 2026. A ausência de sobreposição assegurou a independência exigida pelos testes pareados aplicados em seguida.`,
  `A avaliação do desempenho confrontou cinco construções distintas, todas apuradas sobre as mesmas janelas: a carteira híbrida, formada pela seleção dos agentes seguida da otimização de Markowitz; a seleção dos agentes mantida em peso igual, que isolou a contribuição do otimizador; a otimização de Markowitz aplicada diretamente aos dez ativos, sem filtragem dos agentes; o universo das dez ações mantido em peso igual; e o IBOVESPA. A adoção do peso igual como referência apoiou-se na evidência de que essa regra ingênua supera com frequência as carteiras obtidas por otimização em dados fora da amostra (DeMiguel et al., 2009). A quarta construção constituiu o controle decisivo do estudo, porque manteve fixa a escolha das ações e variou apenas a arquitetura, o que permitiu separar o efeito do método do efeito da seleção prévia do universo.`,
  `O excesso de retorno ajustado ao risco foi estimado por regressão do retorno em excesso de cada carteira sobre o retorno em excesso do índice, cujo intercepto correspondeu ao alfa e cujo coeficiente angular correspondeu ao Beta, segundo a formulação proposta por Jensen (1968). Os erros-padrão foram corrigidos pelo estimador consistente a heterocedasticidade e autocorrelação proposto por Newey e West (1987), com núcleo de Bartlett e uma defasagem. O coeficiente Beta foi testado contra a hipótese nula de igualdade à unidade, e não contra a hipótese de nulidade, uma vez que a questão relevante consistiu em saber se a carteira oscilou menos do que o mercado e não se oscilou com ele. A igualdade entre os coeficientes Beta de duas carteiras foi avaliada pela razão entre a diferença dos coeficientes e a raiz da soma dos quadrados dos respetivos erros-padrão.`,
  `A inferência foi complementada por uma análise de poder estatístico, em que se calculou o efeito mínimo detectável a 95% de confiança e 80% de poder, bem como o número de janelas necessário para detectar o efeito observado. Este procedimento evitou que a ausência de rejeição da hipótese nula fosse interpretada como ausência de efeito quando a amostra não dispunha de poder para o detectar.`,
  `A magnitude do viés de sobrevivência foi quantificada por reamostragem. Reconstituiu-se o conjunto de ações negociadas na B3 em 2012 com histórico disponível, sortearam-se 5.000 carteiras de dez ativos sem reposição e apurou-se o retorno anual composto de cada uma em peso igual ao longo do mesmo período, o que situou o universo do estudo numa distribuição de referência. Em complemento, construiu-se um universo ampliado de ações da mesma época, igualmente em peso igual, para servir de referência alternativa ao índice.`,
  `O determinismo da camada matemática foi submetido a quatro testes independentes, aplicados em quatro datas reais de rebalanceamento escolhidas em regimes distintos: repetibilidade, com dez execuções consecutivas da mesma chamada; invariância à permutação da ordem de apresentação dos ativos, teste central porque os agentes votaram em ordens diferentes a cada janela; estabilidade do agrupamento K-Means; e estabilidade da simulação de Monte Carlo sobre a série completa.`,
  `A sensibilidade do resultado à variabilidade residual do modelo de linguagem foi avaliada por réplica integral do "backtest" sob especificação idêntica, com os mesmos parâmetros de semente e temperatura. A comparação entre a execução original e a réplica recorreu ao índice de Jaccard para medir a coincidência das cestas selecionadas e repetiu todas as métricas de risco e de retorno. Como duas execuções não permitem estimar a dispersão de um agregado, a aferição da estabilidade das métricas de risco recaiu sobre as séries por janela: as 168 janelas foram emparelhadas entre as duas execuções e submetidas a teste t para amostras dependentes, com decomposição posterior da dispersão entre as janelas de cesta coincidente e as de cesta divergente.`,
  `A fricção operacional foi incorporada por um custo proporcional ao giro da carteira, aplicado às duas pontas de cada rebalanceamento. A taxa de referência de dez pontos-base por ordem cobriu emolumentos e liquidação da B3, corretagem institucional e deslizamento em ações de elevada liquidez, e a premissa foi submetida a análise de sensibilidade entre cinco e cinquenta pontos-base, além do cálculo do custo de equilíbrio que anularia o excesso sobre o índice.`,
  `Por fim, a avaliação de risco exigiu a extrapolação probabilística do passado (Glasserman, 2003). Simularam-se 10.000 trajetórias de Monte Carlo ao longo das mesmas 168 janelas, a partir de um capital inicial de R$ 100.000,00, sorteando-se o retorno de cada janela de uma distribuição normal independente, cuja média e cujo desvio-padrão foram estimados sobre os retornos efetivamente observados pela carteira híbrida. As premissas de normalidade e de independência delimitam o alcance do exercício: ele mede a dispersão implícita no histórico da própria carteira, mas não reproduz a autocorrelação nem as caudas pesadas da série original.`
];

// ---------------------------------------------------------------------------
// RESULTADOS E DISCUSSÃO
// ---------------------------------------------------------------------------
const RES_ABERTURA = [
  `A arquitetura concluiu o "backtest out-of-sample" ao longo de 168 janelas, com emissão de carteira rebalanceada em cada uma delas. Ao contrário de estudos que reportam falhas por contaminação temporal (Bailey et al., 2014), a governança da câmara cega assegurou um ambiente de teste isento de "Look-Ahead Bias", tanto na dimensão dos preços quanto na dimensão dos fundamentos. Os resultados que se seguem distinguem, deliberadamente, aquilo que a arquitetura produziu daquilo que a composição prévia do universo de ativos produziu, distinção que alterou de modo substantivo a leitura do desempenho agregado.`
];

const RES_DESEMPENHO = [
  `O algoritmo gerou uma rentabilidade absoluta que excedeu substancialmente o investimento passivo. A carteira híbrida acumulou 1.870,91% em catorze anos, equivalentes a 23,73% ao ano, contra 230,99% do IBOVESPA, equivalentes a 8,93% ao ano. A Tabela 1 reúne as métricas descritivas das cinco construções avaliadas.`,
  `A leitura isolada da primeira coluna da Tabela 1 sugeriria uma superioridade ampla da arquitetura. A quarta linha, contudo, introduz a ressalva decisiva: as mesmas dez ações mantidas em peso igual, sem qualquer intervenção dos agentes ou do otimizador, renderam 899,47%, ou 17,87% ao ano, mais do que o dobro do índice. Uma parcela substancial do excesso de retorno, portanto, já existia no universo de ativos antes de a arquitetura operar sobre ele, e a seção seguinte quantifica essa parcela.`,
  `A comparação entre a carteira híbrida e a otimização de Markowitz aplicada diretamente aos dez ativos produziu uma diferença de 3,60 pontos percentuais ao ano em favor da primeira. Esta diferença não alcançou significância estatística, e a análise de poder esclareceu a razão: com 168 janelas, o efeito mínimo detectável situou-se em 7,43 pontos percentuais ao ano e o número de janelas necessário para detectar um efeito desta magnitude ascendeu a 717, o equivalente a sessenta anos de dados. O resultado configurou, por conseguinte, um teste sem poder suficiente, e não a demonstração de ausência de efeito. A Figura 3 apresenta as trajetórias patrimoniais sobrepostas.`,
  `A Figura 3 expõe a fragilidade da otimização matemática pura quando não tratada, documentada na literatura como a maximização do erro de estimação (Guo, 2022). A submissão simultânea de todos os ativos gerou instabilidade e produziu matrizes mal condicionadas. A filtragem prévia pelos agentes saneou a base e permitiu a convergência do cálculo de otimização. Este ganho decorreu do protocolo MCP. A literatura contemporânea explorou o uso de modelos fundacionais como o "BloombergGPT" (Wu et al., 2023); contudo, a submissão de séries temporais para a inferência direta de pesos resultou em alucinações aritméticas (Saha et al., 2025). Ao adotar o MCP (Lumer et al., 2025; Venkiteela, 2025), o sistema blindou-se contra a imprecisão inerente aos LLMs.`
];

const RES_RISCO = [
  `A capacidade real de uma estratégia quantitativa avaliou-se nas suas fases de recuo patrimonial. A Figura 4 detalha a evolução das balizas de risco calculadas pelo motor determinístico em cada rebalanceamento.`,
  `Nas 47 janelas em que o K-Means sinalizou Turbulência, o painel comprimiu o Beta para níveis defensivos: a média recuou a 0,711, contra 0,789 nas 121 janelas de Calmaria, e o coeficiente permaneceu abaixo da unidade em 91,5% dos casos, contra 79,3%. O "Value at Risk" seguiu o sentido oposto, de R$ 2.628,17 na Calmaria para R$ 2.856,91 na Turbulência, resultado esperado, visto que o indicador paramétrico herda a volatilidade da própria janela e o motor não impôs teto absoluto de risco. A adaptação ao regime operou, por conseguinte, sobre a sensibilidade ao mercado, e não sobre o nível absoluto de risco. No conjunto das janelas, o coeficiente Beta apurado antes de cada rebalanceamento permaneceu abaixo da unidade em 82,7% dos casos, com média de 0,767. Esta adaptação estrutural corroborou os achados de Cheng et al. (2026) e de Devi et al. (2026), que postularam que sistemas multiagentes são mais eficazes do que comandos únicos na adaptação a choques. A consequência patrimonial desse amortecimento aparece na Figura 5.`,
  `A Figura 5 atesta a eficácia do amortecimento: a maior queda acumulada da carteira híbrida restringiu-se a 28,11%, contra 36,92% do universo em peso igual e 38,83% do índice. O Índice de Sharpe, apurado sobre o excesso em relação ao CDI, alcançou 0,567 para a carteira híbrida, contra 0,404 do universo em peso igual e 0,079 do índice.`
];

const RES_INFERENCIA = [
  `A Tabela 2 apresenta o alfa e o Beta de cada construção, com erros-padrão corrigidos por Newey e West (1987).`,
  `A quarta linha da Tabela 2 concentra o resultado mais importante do estudo. O universo das dez ações mantido em peso igual apresentou Beta de 1,061, cuja distância em relação à unidade não alcançou significância (p = 0,1010): em sensibilidade ao mercado, esse universo foi indistinguível do próprio mercado. A carteira híbrida, construída sobre exatamente as mesmas dez ações, apresentou Beta de 0,709, significativamente inferior à unidade (p = 0,0006). O teste direto da igualdade entre os dois coeficientes rejeitou a hipótese nula com t = -3,85 e p = 0,0002.`,
  `A redução de sensibilidade ao mercado, por conseguinte, não decorreu da composição do universo de ativos, visto que esse universo se comportou como o mercado. Decorreu da arquitetura. A Figura 6 representa graficamente este resultado.`,
  `O painel A da Figura 6 mostra as duas retas ajustadas sobre os mesmos 168 pontos de retorno do índice: a reta do universo em peso igual acompanhou a diagonal, ao passo que a reta da carteira híbrida apresentou inclinação visivelmente menor. O painel B traduz a mesma propriedade em termos patrimoniais. Nas 73 janelas em que o índice recuou, a carteira híbrida perdeu em média 1,97%, contra 4,21% do universo em peso igual e 4,74% do índice. A diferença média por janela entre a carteira híbrida e o universo atingiu +2,24 pontos percentuais, com t = +3,290 e p = 0,0016. A captura de queda, que mede a fração do recuo do índice transferida à carteira, recuou de 0,89 no universo em peso igual para 0,42 na carteira híbrida, enquanto a captura de alta se manteve em 0,99, o que resultou numa razão entre as duas de 2,38 contra 1,31.`,
  `A decomposição do excesso de retorno em três etapas, apresentada na Tabela 3, completa o diagnóstico e separa o que a arquitetura produziu do que a escolha do universo produziu.`,
  `A primeira linha da Tabela 3 isolou o efeito da composição do universo, que atingiu 8,52 pontos percentuais ao ano com p = 0,0001. A segunda linha isolou o efeito da seleção pelos agentes, de 6,59 pontos percentuais ao ano, que não alcançou significância, e cuja detecção exigiria 972 janelas. A terceira linha isolou o efeito do otimizador, negativo e sem significância. O excesso de retorno agregado, em suma, concentrou-se na etapa que antecedeu a arquitetura.`
];

const RES_VIES = [
  `A reamostragem quantificou a magnitude dessa etapa anterior. A Figura 7 posiciona o universo do estudo na distribuição dos retornos de 5.000 carteiras aleatórias de dez ações sorteadas do conjunto investível em 2012.`,
  `As dez ações do estudo, mantidas em peso igual, renderam 17,84% ao ano, contra uma mediana de 9,88% ao ano nas carteiras sorteadas e um percentil 95 de 15,88% ao ano. O universo situou-se, portanto, no percentil 99,6% da distribuição, e o excesso sobre o IBOVESPA situou-se no percentil 99,4%. A probabilidade de um sorteio aleatório reproduzir este universo aproximou-se de quatro em mil.`,
  `A construção de um universo ampliado confirmou o diagnóstico por via independente. Trinta e quatro ações da mesma época, mantidas em peso igual, renderam 8,89% ao ano, praticamente idênticos aos 8,62% ao ano do índice no mesmo recorte. A substituição do índice por essa referência ampliada, por conseguinte, não corrigiu o artefato: o alfa da carteira híbrida apenas recuou de 14,53% para 14,36% ao ano, porque o artefato residiu na própria série da estratégia, que negociou exclusivamente as dez ações selecionadas, e não na referência adotada.`,
  `O viés medido constituiu um piso, e não uma estimativa central. Das 56 ações que compunham a lista ampliada pretendida, 21 não puderam ser obtidas, e entre elas figuraram precisamente as empresas deslistadas ao longo do período, ao passo que nenhuma das 34 efetivamente obtidas apresentou série interrompida. A inclusão das deslistadas teria ampliado a distância medida.`,
  `Este resultado determinou a leitura de todo o desempenho de retorno reportado e impôs uma distinção que a literatura de "backtest overfitting" já antecipava (Bailey et al., 2014): o excesso de retorno acumulado pela arquitetura não constituiu evidência do método, ao passo que a alteração do perfil de risco, medida contra o mesmo universo, constituiu.`
];

const RES_DETERMINISMO = [
  `A Tabela 4 reúne o resultado dos quatro testes aplicados à camada matemática.`,
  `Os treze ensaios devolveram uma única saída distinta cada um, o que confirmou a propriedade afirmada pelo título do trabalho no que respeita à camada matemática. O teste de invariância à ordem assumiu relevância particular, uma vez que os agentes votaram em ordens diferentes a cada janela e, sem essa invariância, a mesma cesta produziria carteiras numericamente distintas conforme a sequência em que os ativos chegassem ao motor. A aprovação neste teste exigiu a correção descrita na metodologia, sem a qual duas permutações da mesma cesta devolviam 0,7928381259999999 e 0,792838126 para o mesmo Beta.`,
  `A propriedade verificada circunscreveu-se à camada matemática. A camada de linguagem não a apresentou, conforme a seção seguinte demonstra, e a palavra determinística, no título, qualificou a modelagem matemática e não o modelo de linguagem.`
];

const RES_REPLICA = [
  `A réplica integral do "backtest" sob especificação idêntica produziu o resultado que sustentou a interpretação de todo o trabalho. A Tabela 5 confronta os agregados das duas execuções; a aferição da estabilidade, contudo, não repousou sobre esse confronto, pelas razões expostas adiante.`,
  `O retorno acumulado variou 307 pontos percentuais entre as duas execuções, de 1.871,5% para 1.564,7%. Esta constatação bastou para caracterizar o retorno acumulado como realização instável, visto que a afirmação de instabilidade se satisfaz com uma única discrepância, e os 307 pontos percentuais constituíram piso, e não estimativa, dessa dispersão.`,
  `A afirmação simétrica a respeito das métricas de risco exigiu base empírica distinta, porquanto duas realizações agregadas não permitem estimar dispersão. As séries gravadas por janela tornaram disponível o emparelhamento integral das duas execuções, e foi sobre as 168 janelas emparelhadas que a estabilidade se aferiu. O coeficiente Beta apresentou diferença média de +0,0034 entre as execuções, com desvio-padrão de 0,0315 e t = 1,412 sobre 167 graus de liberdade. O "Value at Risk" apresentou diferença média de R$ 14,14 sobre média de R$ 2.692,16, com desvio-padrão de R$ 152,34 e t = 1,203. Nenhuma das duas se distinguiu de zero, de modo que a hipótese de igualdade das métricas de risco entre execuções não foi rejeitada em teste conduzido sobre 168 observações.`,
  `A decomposição dessa dispersão por origem esclareceu o mecanismo. As cestas selecionadas coincidiram integralmente em 148 das 168 janelas, correspondentes a 88,1%, com índice de Jaccard médio de 0,951. Nessas 148 janelas de cesta coincidente, o "Value at Risk" saiu idêntico em 135 e o Beta em 137; o resíduo decorreu da apresentação dos pesos em ordem distinta em 19 janelas e alcançou, no máximo, R$ 10,13 no "Value at Risk" e 0,0032 no Beta. A dispersão materialmente relevante concentrou-se, portanto, nas 20 janelas em que os agentes divergiram quanto à cesta, nas quais o desvio do Beta atingiu 0,218. A camada matemática mostrou-se reprodutível dada a cesta, e o risco apenas se deslocou quando a camada heurística mudou de decisão, em 11,9% das janelas e com efeito contido.`,
  `Deste contraste decorreram duas consequências. A primeira: a propriedade de risco constituiu característica estrutural da arquitetura e sobreviveu ao ruído residual do modelo de linguagem, o que afastou a objeção de que o resultado decorreria de uma execução afortunada. A segunda: o retorno acumulado constituiu uma realização instável e, como tal, exigiu reporte sob a forma de faixa e não de valor pontual. Registre-se que a primeira consequência se apoiou nas 168 comparações emparelhadas, e não nas duas realizações agregadas da Tabela 5, cuja função se restringiu a delimitar a amplitude observada.`,
  `A mesma régua aplicou-se à avaliação da correção do agrupamento K-Means descrita na metodologia. A correção elevou o retorno acumulado de 1.406,5% para 1.871,5%, mas a diferença média por janela entre as duas especificações alcançou apenas 0,206 pontos percentuais, com t = 1,014 e p = 0,3123. O deslocamento de 307 pontos percentuais observado entre réplicas da mesma especificação situou-se na mesma ordem de grandeza dos 465 pontos percentuais atribuíveis à correção, o que impediu a atribuição do ganho à mudança metodológica. A justificação da correção assentou, por conseguinte, exclusivamente na coerência interna do rótulo de regime, que apresentava incoerência em 43,5% das janelas sob a janela móvel, com o limiar a oscilar 61,5 pontos percentuais.`
];

const RES_CUSTOS = [
  `A incorporação da fricção operacional não comprometeu o resultado. À taxa de referência de dez pontos-base por ordem, o retorno acumulado da carteira híbrida recuou de 1.870,91% para 1.706,70%, o Índice de Sharpe de 0,567 para 0,544 e o alfa de 14,53% para 13,90% ao ano, mantida a significância (p = 0,0186). O giro médio por janela alcançou 28,54% do patrimônio.`,
  `A análise de sensibilidade percorreu o intervalo de cinco a cinquenta pontos-base sem alterar a ordenação entre as construções avaliadas. O custo de equilíbrio, isto é, a taxa por ordem que anularia integralmente o excesso sobre o índice, situou-se em 222 pontos-base, patamar cerca de vinte vezes superior à premissa de referência e incompatível com a negociação de ações de elevada liquidez na B3.`
];

const RES_MONTE_CARLO = [
  `A simulação de Monte Carlo com 10.000 trajetórias, apresentada na Figura 8, projetou um capital médio de R$ 3.288.388,94 ao fim das 168 janelas, a partir de R$ 100.000,00. No quinto percentil, correspondente ao VaR de 95%, o limite prudencial projetou um piso de R$ 363.704,20 (Orlova e Sayakhetdinov, 2023), valor que permaneceu acima do capital inicial e caracterizou preservação de capital no cenário pessimista. Esta projeção herdou, contudo, duas limitações. A primeira é a apontada na seção anterior: a série de retornos que a alimentou foi produzida por um universo de ativos situado no percentil 99,6% da distribuição de referência. A segunda decorre das premissas do próprio sorteio, pois sob retornos normais e independentes apenas 0,17% das trajetórias terminaram abaixo do capital inicial, proporção que a autocorrelação e as caudas pesadas da série real elevariam.`
];

const RES_LIMITACOES = [
  `O estudo exigiu o delineamento claro das premissas e dos "trade-offs" assumidos:`
];

const LIMITACOES = [
  `Viés de sobrevivência no universo de ativos: as dez ações foram definidas sem regra documentada de seleção e com conhecimento retrospectivo de quais sobreviveram ao período. O viés foi quantificado no percentil 99,6% de 5.000 carteiras aleatórias e constituiu um piso, dada a impossibilidade de obter as séries das empresas deslistadas. Esta limitação invalidou a leitura do excesso de retorno como resultado do método, mas não afetou o resultado de risco, aferido contra o próprio universo.`,
  `Variabilidade residual da camada de linguagem: com "temperature" igual a zero e semente fixa, os agentes receberam identificadores de infraestrutura distintos na mesma chamada, o que indicou que o provedor não manteve o "backend" de inferência fixo. A propriedade determinística afirmada no título qualificou a camada matemática, cuja verificação consta da Tabela 4, e não a camada de linguagem. Apenas duas execuções integrais estiveram disponíveis, pelo que a dispersão dos resultados agregados não foi estimada, e sim delimitada; a inferência sobre a estabilidade do risco apoiou-se no emparelhamento das 168 janelas entre as duas execuções, e a sua extensão a um número maior de réplicas permanece como verificação pendente.`,
  `Poder estatístico insuficiente para a comparação com o otimizador isolado: a detecção de um efeito da magnitude observada exigiria 717 janelas, o equivalente a sessenta anos de dados. Com dez ativos, esse número é inalcançável, e apenas a ampliação do universo permitiria conduzir o teste.`,
  `Omissão de covariância na fase heurística: ao delegar a filtragem aos LLMs, a metodologia abriu mão das potenciais sinergias de "hedge" perfeito. Os agentes, ao rejeitarem ativos preliminarmente, impuseram um limite de eficiência teórica à fronteira final, preço pago para suprimir o "overfitting" de dados (Prado, 2018).`,
  `Uma janela descartada: em 08 jan. 2016, a maximização do Índice Sharpe não admitiu solução viável, dado que nenhum ativo da cesta apresentou retorno esperado acima da taxa livre de risco. O descarte foi pareado, com remoção simultânea da janela correspondente do índice, e desfavoreceu a estratégia, que naquela janela rendeu +5,3% contra -3,19% do índice. Daí resultaram 168 janelas, e não 169.`,
  `Impacto tributário: o modelo não previu o recolhimento de Imposto de Renda sobre os ganhos apurados a cada rebalanceamento, cuja incidência reduziria o retorno líquido efetivo.`,
  `Divergência entre a taxa livre de risco do otimizador e a das métricas: a maximização do Índice Sharpe interna ao motor operou com taxa livre de risco nula, ao passo que as métricas reportadas utilizaram o CDI da janela. A divergência afetou a composição dos pesos, e não a apuração do desempenho.`
];

// ---------------------------------------------------------------------------
// CONSIDERAÇÕES FINAIS — sem citações, sem figuras, sem tabelas (norma)
// ---------------------------------------------------------------------------
const CONSIDERACOES = [
  `O mercado financeiro impôs desafios que tornaram arriscada a aplicação isolada de inteligência artificial generativa. Este estudo desenvolveu um "framework" híbrido e atestou que a ponte entre o processamento semântico de múltiplos agentes e o rigor do cálculo matemático encontrou viabilidade no "Model Context Protocol". A implementação da câmara cega revelou-se eficaz na eliminação do viés de retrospectiva, e a camada matemática satisfez integralmente a exigência de determinismo, inclusive sob permutação da ordem de apresentação dos ativos.`,
  `A contribuição central do trabalho não residiu, contudo, onde a formulação inicial a situava. O desenho experimental que confrontou a carteira construída pela arquitetura com o seu próprio universo de ativos revelou que o excesso de retorno acumulado decorreu da composição desse universo, escolhida com conhecimento retrospectivo, ao passo que a alteração do perfil de risco decorreu da arquitetura e sobreviveu a esse controle. A sensibilidade ao mercado caiu de um patamar indistinguível do índice para um patamar significativamente inferior, e a proteção nas janelas de recuo manteve-se estável, com as métricas de risco indistinguíveis em comparação emparelhada janela a janela entre réplicas que deslocaram o retorno acumulado em mais de trezentos pontos percentuais.`,
  `Dessa assimetria decorreu a lição metodológica mais transferível do trabalho: num sistema cuja camada heurística conserva variabilidade residual, uma propriedade só se qualifica como resultado da arquitetura quando permanece estável entre execuções e resiste ao controle pelo universo de ativos. O retorno acumulado não satisfez nenhuma das duas condições; o perfil de risco satisfez ambas.`,
  `Recomenda-se que trabalhos futuros ampliem o universo de ativos mediante regra de seleção documentada e aplicada no início do período, condição necessária tanto para eliminar o viés medido quanto para alcançar o poder estatístico exigido pela comparação com o otimizador isolado. Recomenda-se igualmente a expansão da prova de conceito para estratégias de "Paper Trading" conectadas a fluxo de dados em tempo real.`
];

// O Manual restringe a menção a nomes de pessoas nos agradecimentos; o nome próprio
// que constava do texto original foi suprimido, preservado o conteúdo.
const AGRADECIMENTOS = `À minha esposa e companheira, agradeço por incentivar o meu desenvolvimento e por ser a minha maior inspiração. À minha família, minha profunda gratidão pelo apoio incondicional aos meus estudos. A vocês, devo todas as minhas conquistas.`;

const REFERENCIAS = [
  `Bailey, D.H.; Borwein, J.M.; Prado, M.L. de; Zhu, Q.J. 2014. Pseudo-mathematics and financial charlatanism: the effects of backtest overfitting on out-of-sample performance. Notices of the American Mathematical Society 61(5): 458-471.`,
  `Brînză, A.; Ioan, V.; Lăzărescu, I. 2023. Critical analysis of the Sharpe ratio: assessing performance and risk in financial portfolio management. Ovidius University Annals, Economic Sciences Series 23(2): 633-639.`,
  `Cheng, E.Y.C.; Tseng, C.J.; Chu, H.T. 2026. Adaptive LLM-based multi-agent systems to enhance quantitative trading performance. PeerJ Computer Science 12: e3630.`,
  `DeMiguel, V.; Garlappi, L.; Uppal, R. 2009. Optimal versus naive diversification: how inefficient is the 1/N portfolio strategy? The Review of Financial Studies 22(5): 1915-1953.`,
  `Devi, S.R.; Harsavardhini, R.; Kaviya, S.; Monisha, M. 2026. Agentic tool-based decision agents for finance: a survey of sentiment, event, and risk integration. In: IEEE International Students' Conference on Electrical, Electronics and Computer Science (SCEECS), 2026, Bhopal, MP, Índia. Anais... p. 1-7.`,
  `Glasserman, P. 2003. Monte Carlo Methods in Financial Engineering. Springer, New York, NY, EUA.`,
  `Guo, Q. 2022. Review of research on Markowitz model in portfolios. In: International Conference on Social Sciences and Economic Development (ICSSED), 7., 2022, Wuhan, Hubei, China. Anais... p. 786-790.`,
  `Handler, A.; Larsen, K.R.; Hackathorn, R. 2024. Large language models present new questions for decision support. International Journal of Information Management 79: e102811.`,
  `Jensen, M.C. 1968. The performance of mutual funds in the period 1945-1964. The Journal of Finance 23(2): 389-416.`,
  `Lumer, E.; Gulati, A.; Subbiah, V.K.; Basavaraju, P.H.; Burke, J.A. 2025. Scalemcp: dynamic and auto-synchronizing model context protocol tools for llm agents. In: International Joint Conference on Computational Intelligence, 2025, Genebra, GE, Suíça. Anais... p. 23-42.`,
  `Markowitz, H. 1952. Portfolio selection. The Journal of Finance 7(1): 77-91.`,
  `Markowitz, H. 1959. Portfolio Selection: Efficient Diversification of Investments. Yale University Press, New Haven, CT, EUA.`,
  `Newey, W.K.; West, K.D. 1987. A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix. Econometrica 55(3): 703-708.`,
  `Orlova, L.N.; Sayakhetdinov, A.R. 2023. Methods for quantitative risk assessment based on VaR: comparative analysis. Intellect. Innovations. Investments (2): 63-74.`,
  `Pardo, R. 2011. The Evaluation and Optimization of Trading Strategies. 2ed. John Wiley & Sons, Hoboken, NJ, EUA.`,
  `Prado, M.L. de. 2018. Advances in Financial Machine Learning. John Wiley & Sons, Hoboken, NJ, EUA.`,
  `Saha, P.; Lyu, J.; Saxena, A.; Zhao, T.; Mehta, D. 2025. Large language model agents for investment management: foundations, benchmarks, and research frontiers. In: ACM International Conference on AI in Finance, 6., 2025, Singapura, Singapura. Anais... p. 736-744.`,
  `Skorupski, M. 2023. Market beta coefficient and enterprise risk management: a literature review. Research Papers in Economics and Finance 7(1): 67-88.`,
  `Venkiteela, P. 2025. The new interoperability paradigm model context protocol [MCP], APIs, and the future of agentic AI. Comput. Fraud Sec 8(1): 1259-1271.`,
  `Wu, S.; Irsoy, O.; Lu, S.; Dabravolski, V.; Dredze, M.; Gehrmann, S.; Kambadur, P.; Rosenberg, D.; Mann, G. 2023. BloombergGPT: a large language model for finance. arXiv preprint arXiv:2303.17564. Disponível em: <https://arxiv.org/abs/2303.17564>. Acesso em: 06 out. 2026.`,
  `Xi, Z.; Chen, W.; Guo, X.; He, W.; Ding, Y.; Hong, B.; Zhang, M.; Wang, J. 2023. The rise and potential of large language model based agents: a survey. arXiv preprint arXiv:2309.07864. Disponível em: <https://arxiv.org/abs/2309.07864>. Acesso em: 06 out. 2026.`
];

// ---------------------------------------------------------------------------
// TABELAS
// ---------------------------------------------------------------------------
const TABELA_1 = {
  titulo: 'Tabela 1. Desempenho das carteiras nas 168 janelas de apuração, de 06 jan. 2012 a 06 maio 2026',
  fonte: 'Fonte: Resultados originais da pesquisa',
  larguras: [2600, 1500, 1250, 1150, 1350, 1220],
  cabecalho: ['Carteira', 'Retorno acumulado (%)', 'Retorno anual (% a.a.)', 'Índice de Sharpe', 'Maior queda acumulada (%)', 'Coeficiente Beta'],
  linhas: [
    ['Híbrida (agentes + Markowitz)', '1.870,91', '23,73', '0,567', '-28,11', '0,709'],
    ['Agentes + peso igual', '2.317,04', '25,55', '0,642', '-28,90', '0,737'],
    ['Markowitz isolado (sem agentes)', '1.094,68', '19,38', '0,436', '-26,59', '0,677'],
    ['As 10 ações em peso igual', '899,47', '17,87', '0,404', '-36,92', '1,061'],
    ['IBOVESPA', '230,99', '8,93', '0,079', '-38,83', '1,000']
  ],
  nota: 'O Índice de Sharpe foi apurado sobre o excesso em relação ao CDI da própria janela. Os valores correspondem ao retorno bruto, sem custos de transação.'
};

const TABELA_2 = {
  titulo: 'Tabela 2. Alfa e coeficiente Beta contra o IBOVESPA, com erros-padrão corrigidos por Newey e West (1987)',
  fonte: 'Fonte: Resultados originais da pesquisa',
  larguras: [2700, 1300, 1050, 1150, 1500, 1370],
  cabecalho: ['Carteira', 'Alfa (% a.a.)', 'p (alfa)', 'Coeficiente Beta', 'p (Beta = 1)', 'R²'],
  linhas: [
    ['Híbrida (agentes + Markowitz)', '14,53', '0,0138', '0,709', '0,0006', '0,342'],
    ['Agentes + peso igual', '15,59', '0,0028', '0,737', '0,0002', '0,415'],
    ['Markowitz isolado (sem agentes)', '10,99', '0,0683', '0,677', '0,0010', '0,310'],
    ['As 10 ações em peso igual', '8,41', '0,0001', '1,061', '0,1010', '0,911']
  ],
  nota: 'O Beta foi testado contra a hipótese nula de igualdade à unidade. O teste direto da igualdade entre o Beta da carteira híbrida e o Beta do universo em peso igual devolveu t = -3,85 e p = 0,0002.'
};

const TABELA_3 = {
  titulo: 'Tabela 3. Decomposição do excesso de retorno anual e poder estatístico de cada etapa',
  fonte: 'Fonte: Resultados originais da pesquisa',
  larguras: [3000, 1300, 950, 1050, 1500, 1270],
  cabecalho: ['Etapa isolada', 'Efeito (% a.a.)', 'Estatística t', 'p', 'Efeito mínimo detectável (% a.a.)', 'Janelas necessárias'],
  linhas: [
    ['Universo (10 ações em peso igual contra o IBOVESPA)', '+8,52', '4,116', '0,0001', '5,80', '78'],
    ['Seleção pelos agentes (agentes em peso igual contra o universo)', '+6,59', '1,164', '0,2462', '15,86', '972'],
    ['Otimizador (carteira híbrida contra agentes em peso igual)', '-1,12', '-0,381', '0,7034', '8,19', '9.055']
  ],
  nota: 'O efeito mínimo detectável foi calculado a 95% de confiança e 80% de poder. O número de janelas necessárias refere-se à detecção do efeito efetivamente observado.'
};

const TABELA_4 = {
  titulo: 'Tabela 4. Testes de determinismo da camada matemática',
  fonte: 'Fonte: Resultados originais da pesquisa',
  larguras: [2700, 1250, 1900, 1550, 1670],
  cabecalho: ['Teste aplicado', 'Datas avaliadas', 'Execuções ou permutações', 'Saídas distintas obtidas', 'Resultado'],
  linhas: [
    ['Repetibilidade da mesma chamada', '4', '10 por data', '1', 'Determinístico'],
    ['Invariância à ordem dos ativos', '4', '2, 1, 6 e 13 permutações', '1', 'Determinístico'],
    ['Estabilidade do agrupamento K-Means', '4', '10 por data', '1', 'Determinístico'],
    ['Estabilidade da simulação de Monte Carlo', 'Série completa', '2', '1', 'Determinístico']
  ],
  nota: 'As quatro datas corresponderam a rebalanceamentos reais escolhidos em regimes distintos: 11 fev. 2016, 06 abr. 2020, 27 mar. 2024 e 02 abr. 2026.'
};

const TABELA_5 = {
  titulo: 'Tabela 5. Amplitude dos resultados agregados entre duas execuções da mesma especificação',
  fonte: 'Fonte: Resultados originais da pesquisa',
  larguras: [4300, 2350, 2420],
  cabecalho: ['Medida apurada', 'Execução original', 'Réplica'],
  linhas: [
    ['Retorno acumulado (%)', '1.871,5', '1.564,7'],
    ['Retorno anual composto (% a.a.)', '23,73', '22,25'],
    ['Alfa (% a.a.)', '14,53', '13,44'],
    ['Coeficiente Beta da carteira híbrida', '0,709', '0,702'],
    ['Coeficiente Beta do universo em peso igual', '1,061', '1,061'],
    ['p da igualdade entre os dois coeficientes Beta', '0,0002', '0,0002'],
    ['Captura de queda', '0,42', '0,42'],
    ['Diferença nas 73 janelas de queda (p.p. por janela)', '+2,241', '+2,229'],
    ['p dessa diferença', '0,0016', '0,0024']
  ],
  nota: 'As cestas selecionadas coincidiram integralmente em 148 das 168 janelas, correspondentes a 88,1%, com índice de Jaccard médio de 0,951. Com duas execuções, os agregados acima delimitam a amplitude observada, mas não estimam a dispersão; a estabilidade das métricas de risco foi aferida por comparação emparelhada janela a janela, reportada no texto.'
};

// ---------------------------------------------------------------------------
// FIGURAS
// ---------------------------------------------------------------------------
const DIR_FIG = '../mcp_servers/risk_server/';

const FIGURAS = {
  arquitetura: {
    arquivo: DIR_FIG + 'figura_arquitetura.png', razao: 0.701,
    legenda: 'Figura 1. Arquitetura do sistema e fronteira entre a camada heurística e a camada determinística',
    fonte: 'Fonte: Dados originais da pesquisa'
  },
  kmeans: {
    arquivo: DIR_FIG + 'figura1_kmeans.png', razao: 0.927,
    legenda: 'Figura 2. Classificação do regime de mercado pelo K-Means, com rótulo e limiar reestimados a cada data de decisão',
    fonte: 'Fonte: Dados originais da pesquisa'
  },
  capital: {
    arquivo: DIR_FIG + 'figura_capital.png', razao: 0.520,
    legenda: 'Figura 3. Evolução do capital acumulado sob quatro abordagens distintas',
    fonte: 'Fonte: Resultados originais da pesquisa'
  },
  varBeta: {
    arquivo: DIR_FIG + 'figura_var_beta.png', razao: 0.640,
    legenda: 'Figura 4. Value at Risk sobre nocional fixo e Coeficiente Beta apurados a cada rebalanceamento',
    fonte: 'Fonte: Resultados originais da pesquisa'
  },
  drawdown: {
    arquivo: DIR_FIG + 'figura_drawdown.png', razao: 0.460,
    legenda: 'Figura 5. Queda acumulada em relação ao topo anterior sob três abordagens',
    fonte: 'Fonte: Resultados originais da pesquisa'
  },
  controle: {
    arquivo: DIR_FIG + 'figura8_controle_universo.png', razao: 0.455,
    legenda: 'Figura 6. Sensibilidade ao índice e comportamento nas janelas de queda, com o universo de ativos mantido fixo',
    fonte: 'Fonte: Resultados originais da pesquisa'
  },
  vies: {
    arquivo: DIR_FIG + 'figura7_vies_sorteios.png', razao: 0.556,
    legenda: 'Figura 7. Posição do universo do estudo na distribuição de 5.000 carteiras aleatórias de dez ações',
    fonte: 'Fonte: Resultados originais da pesquisa'
  },
  monteCarlo: {
    arquivo: DIR_FIG + 'figura5_monte_carlo.png', razao: 0.500,
    legenda: 'Figura 8. Simulação de Monte Carlo para 10.000 trajetórias',
    fonte: 'Fonte: Resultados originais da pesquisa'
  }
};

module.exports = {
  TITULO, TITULO_EN, AUTORES, ENDERECOS, CABECALHO,
  PALAVRAS_CHAVE, KEYWORDS,
  RESUMO, ABSTRACT, INTRODUCAO,
  MET_ABERTURA, MET_COLETA, MET_ATIVOS, MET_COLETA_FIM, MET_FUNDAMENTOS,
  MET_KMEANS, MET_CAMARA, MET_AGENTES, MET_OTIMIZACAO, MET_VALIDACAO,
  RES_ABERTURA, RES_DESEMPENHO, RES_RISCO, RES_INFERENCIA, RES_VIES,
  RES_DETERMINISMO, RES_REPLICA, RES_CUSTOS, RES_MONTE_CARLO,
  RES_LIMITACOES, LIMITACOES,
  CONSIDERACOES, AGRADECIMENTOS, REFERENCIAS,
  TABELA_1, TABELA_2, TABELA_3, TABELA_4, TABELA_5, FIGURAS
};
