# TCC-USP-ESALQ: Sistemas Multiagentes e Protocolo MCP na Otimização de Portfólios e Gestão de Risco na B3 

Este repositório contém o código-fonte e os experimentos do Trabalho de Conclusão de Curso (TCC) desenvolvido para o MBA em Data Science e Analytics da **USP/Esalq**.

O projeto propõe uma arquitetura inovadora que une Inteligência Artificial Generativa e finanças quantitativas, utilizando **Sistemas Multiagentes** e o **Model Context Protocol (MCP)** para automatizar a otimização de portfólios de ativos da B3 e a gestão de risco.

---

## Objetivo do Projeto

O mercado de capitais brasileiro exige métodos analíticos avançados para lidar com sua acentuada volatilidade. Embora os *Large Language Models* (LLMs) sejam excelentes na interpretação de cenários, eles sofrem com alucinações em cálculos aritméticos rigorosos. 

O objetivo deste projeto é demonstrar que a dissociação estrutural entre a camada de raciocínio linguístico da IA e os módulos quantitativos viabiliza recomendações de investimento precisas. Para isso, o sistema delega cálculos estatísticos determinísticos (como Fronteira de Markowitz, VaR e Índice de Sharpe) para servidores MCP especializados, garantindo fidedignidade analítica.

---

## Arquitetura e Fluxo Multiagente

O sistema é construído **inteiramente em Python** e orquestra os seguintes componentes:

1. **Agente Analista:** Responsável pela triagem de ativos da B3, extração de fatores macroeconômicos e interpretação de fundamentos.
2. **Agente Gestor de Risco:** Avalia restrições, analisa o cenário e define pesos para o portfólio.
3. **Servidores MCP (Model Context Protocol):** Atuam como ferramentas (*tools*) determinísticas isoladas do LLM, executando:
   - Coleta de dados via APIs públicas (Yahoo Finance / Alpha Vantage).
   - Otimização de portfólio (Teoria de Markowitz).
   - Cálculo de *Value at Risk* (VaR), Beta e Índice de Sharpe.

---

## Tecnologias Utilizadas

* **Linguagem:** Python 3.14+
* **Orquestração de Agentes:** LangChain
* **Protocolo de Integração:** MCP SDK (Python)
* **Ciência de Dados & Finanças:** `pandas`, `numpy`, `PyPortfolioOpt`, `yfinance`
* **Avaliação:** Backtesting engine (comparação contra o IBOVESPA)

---

## 📂 Estrutura Sugerida do Repositório

```text
TCC-USP-ESALQ
 ┣ agents               # Definição dos agentes (Analista e Gestor)
 ┣ mcp_servers          # Servidores MCP contendo as ferramentas determinísticas
 ┃ ┣ data_fetcher.py    # Integração com APIs financeiras (yfinance, etc.)
 ┃ ┗ risk_metrics.py    # Cálculos de VaR, Sharpe, Markowitz (PyPortfolioOpt)
 ┣ data                 # Datasets históricos ou extrações temporárias
 ┣ notebooks            # Jupyter Notebooks para EDA e testes de backtesting
 ┣ main.py              # Ponto de entrada para execução do sistema
 ┣ requirements.txt     # Dependências do projeto
 ┣ .env.example         # Variáveis de ambiente (Chaves de API, etc.)
 ┗ README.md            # Documentação principal
