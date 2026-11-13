import pandas as pd
import requests
import warnings

# Suprime avisos do Pandas sobre fatiamento
warnings.filterwarnings("ignore")

URL_NODE = "http://localhost:3000/api/otimizar-portfolio"
CAMINHO_CSV = '../data_server/cotacoes_b3_fechamentos.csv'

VAZIO = (None, None, None, None, None)


def rodar_janela_ia(data_fim_treino: str):
    """Aciona a rede para deliberar a alocação de uma data específica do passado."""
    payload = {"data_referencia": data_fim_treino}
    try:
        resposta = requests.post(URL_NODE, json=payload)
        if resposta.status_code == 200:
            dados = resposta.json()['data']
            alocacao = dados['alocacao_final_markowitz']
            # Janela sem solução numérica no Markowitz: a otimização devolve
            # {"status": "erro"} sem pesos. Sem este tratamento uma única janela
            # ruim derruba a execução inteira do walk-forward.
            if 'pesos_otimizados' not in alocacao:
                print(f"Otimização falhou em {data_fim_treino}: {alocacao.get('mensagem', alocacao.get('status'))}")
                return VAZIO
            pesos = alocacao['pesos_otimizados']
            risco = alocacao['risco_projetado']
            janela = alocacao.get('janela_utilizada', {})
            return (pesos, risco['var_diario_95'], risco['beta_carteira'], janela,
                    dados.get('detalhes_votacao', []))
        else:
            print(f"Erro na API para {data_fim_treino}:", resposta.text)
            return VAZIO
    except requests.exceptions.ConnectionError:
        print("Erro: Falha de conexão com o Node.js.")
        return VAZIO

def executar_backtest(janela_treino=252, passo_rebalanceamento=21, capital_inicial=100000.0):
    print(f"Carregando base histórica de {CAMINHO_CSV}...")
    df_completo = pd.read_csv(CAMINHO_CSV, parse_dates=['Date']).set_index('Date').sort_index()
    
    # Isola ações e o benchmark
    colunas_macro = ['^BVSP', 'USDBRL=X', 'IFIX.SA']
    df_acoes = df_completo.drop(columns=[col for col in colunas_macro if col in df_completo.columns], errors='ignore')
    df_bench = df_completo['^BVSP'] if '^BVSP' in df_completo.columns else None

    datas_pregoes = df_completo.index
    if len(datas_pregoes) <= janela_treino:
        print("Erro: Histórico insuficiente para a janela de treino inicial.")
        return

    historico_portfolio = []
    janelas_descartadas = []
    capital_atual = capital_inicial

    print("\nIniciando Motor Walk-Forward...")
    print(f"Capital Inicial: R$ {capital_inicial:.2f}\n")
    print("-" * 60)

    # Avança no tempo aos saltos de 21 dias
    for i in range(janela_treino, len(datas_pregoes) - passo_rebalanceamento, passo_rebalanceamento):
        data_treino_fim = datas_pregoes[i]
        data_teste_fim = datas_pregoes[i + passo_rebalanceamento]
        
        str_treino_fim = data_treino_fim.strftime('%Y-%m-%d')
        str_teste_fim = data_teste_fim.strftime('%Y-%m-%d')
        
        print(f"[{str_treino_fim}] Solicitando consenso aos agentes LLM...")
        pesos, var, beta, janela, votacao = rodar_janela_ia(str_treino_fim)

        if not pesos:
            # A mensagem anterior atribuía todo descarte a "falta de consenso", o que é falso:
            # a causa predominante é o max_sharpe sem solução viável quando nenhum ativo da
            # cesta tem retorno esperado acima da taxa livre de risco (caso de 08/01/2016, no
            # fundo da crise). O motivo exato é impresso por rodar_janela_ia logo acima; aqui
            # só se registra que a janela saiu da série. O descarte é pareado — a janela é
            # removida também do IBOVESPA —, logo a comparação segue válida, mas o número de
            # janelas efetivas precisa ser declarado no texto.
            print("-> Janela removida da série (sem pesos; ver motivo na linha anterior).")
            janelas_descartadas.append(str_treino_fim)
            continue

        # A otimização não pode enxergar nada além da data de rebalanceamento.
        if janela and janela.get('ultimo_pregao', str_treino_fim) > str_treino_fim:
            raise RuntimeError(
                f"Look-ahead detectado em {str_treino_fim}: otimização usou dados até {janela['ultimo_pregao']}."
            )

        # Calcula rentabilidade real no mundo futuro invisível para a IA (próximos 21 dias)
        df_teste = df_acoes.loc[str_treino_fim:str_teste_fim]
        if len(df_teste) < 2:
            continue
            
        # Rentabilidade de cada ativo na janela (Preço Final / Preço Inicial - 1)
        retorno_ativos = (df_teste.iloc[-1] / df_teste.iloc[0]) - 1
        
        # Produto vetorial entre os pesos recomendados e os retornos reais
        retorno_carteira = sum(peso * retorno_ativos.get(ticker, 0) for ticker, peso in pesos.items())
        lucro_janela = capital_atual * retorno_carteira
        capital_atual += lucro_janela
        
        # Rentabilidade do Benchmark para a mesma janela
        retorno_bench = 0
        if df_bench is not None:
            bench_teste = df_bench.loc[str_treino_fim:str_teste_fim]
            if len(bench_teste) >= 2:
                retorno_bench = (bench_teste.iloc[-1] / bench_teste.iloc[0]) - 1

        print(f"-> Retorno 21d Carteira: {retorno_carteira*100:+.2f}% | IBOV: {retorno_bench*100:+.2f}%")
        print(f"-> Risco Alocado: VaR R$ {var} | Beta {beta}")
        print(f"-> Capital Atualizado: R$ {capital_atual:.2f}")
        print("-" * 60)
        
        historico_portfolio.append({
            'Data_Rebalanceamento': str_treino_fim,
            'Data_Apuracao': str_teste_fim,
            'Retorno_Carteira': round(retorno_carteira, 4),
            'Retorno_IBOV': round(retorno_bench, 4),
            'VaR_95': var,
            'Beta': beta,
            'Capital_Acumulado': round(capital_atual, 2),
            # Auditoria: permite reconstruir a carteira sem reexecutar as chamadas aos LLMs
            'Ativos_Selecionados': ';'.join(t for t, p in pesos.items() if p > 0),
            'Pesos': ';'.join(f"{t}={p:.5f}" for t, p in pesos.items() if p > 0),
            'Janela_Ultimo_Pregao': (janela or {}).get('ultimo_pregao', ''),
            # Voto de cada persona e o backend que respondeu. Sem o fingerprint não é
            # possível saber se uma divergência entre execuções veio da estocasticidade
            # do modelo ou de uma troca de infraestrutura pela OpenAI.
            'Votos_Por_Agente': '|'.join(
                f"{a.get('nome')}:{','.join(a.get('votos', []))}" for a in (votacao or [])),
            'System_Fingerprint': ';'.join(sorted({
                a.get('system_fingerprint', '') for a in (votacao or []) if a.get('system_fingerprint')
            }))
        })

        # Grava a cada janela: a execução leva horas (169 rodadas de LLM) e uma
        # falha na última janela não pode descartar todas as anteriores.
        pd.DataFrame(historico_portfolio).to_csv('resultado_backtest_economicAI.csv', index=False)

    # Compilação estatística final
    df_resultados = pd.DataFrame(historico_portfolio)
    df_resultados.to_csv('resultado_backtest_economicAI.csv', index=False)
    
    rentabilidade_total = (capital_atual / capital_inicial) - 1
    
    print("\n" + "=" * 60)
    print("BACKTEST CONCLUÍDO")
    print("=" * 60)
    print(f"Rentabilidade Total do Multiagente: {rentabilidade_total*100:.2f}%")
    print(f"Janelas efetivas: {len(df_resultados)} | descartadas: {len(janelas_descartadas)}")
    if janelas_descartadas:
        print(f"Datas descartadas: {', '.join(janelas_descartadas)}")
    print(f"Arquivo 'resultado_backtest_economicAI.csv' gerado com sucesso.")
    print("Pronto para plotagem da curva de capital e execução do Teste T de Student.")

if __name__ == "__main__":
    executar_backtest()