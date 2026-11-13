"""
Verifica o determinismo da CAMADA MATEMATICA, que e o que o titulo da dissertacao afirma:
"multiagentes e modelagem matematica deterministica" — os multiagentes usam LLM, e a
modelagem matematica (Markowitz, VaR, beta, K-Means, Monte Carlo) e deterministica.

A afirmacao de determinismo nao se demonstra lendo o codigo: ela se demonstra mostrando
que a mesma entrada economica produz a mesma saida. Sao quatro testes, nenhum deles
consome API.

TESTE 1 - REPETIBILIDADE
A mesma cesta na mesma data, repetida N vezes, tem de devolver pesos, VaR e beta
identicos bit a bit. Falha aqui significaria solver com estado aleatorio nao fixado.

TESTE 2 - INVARIANCIA A ORDEM DOS ATIVOS
Este e o teste que importa. Os agentes votam em ordens diferentes a cada janela:
["Ativo_8","Ativo_7"] e ["Ativo_7","Ativo_8"] sao a MESMA cesta economica. Se o
otimizador devolver pesos diferentes para as duas, o determinismo vale apenas para uma
ordem arbitraria de entrada, e o resultado do backtest passa a depender da ordem em que
os LLMs listaram os ativos — ou seja, a camada matematica herdaria a variabilidade da
camada de IA justamente onde o titulo promete o contrario.

TESTE 3 - K-MEANS
A mesma data de referencia tem de devolver o mesmo rotulo de regime, o mesmo limiar de
turbulencia e os mesmos centroides. Com `random_state` fixo e a janela expansiva isto
deve valer; o teste existe porque o K-Means e o unico componente com inicializacao
aleatoria.

TESTE 4 - MONTE CARLO
A simulacao com `default_rng(42)` tem de reproduzir os mesmos percentis. E o numero
citado no texto como cenario pessimista, logo precisa ser reproduzivel por terceiros.
"""

import itertools
import json

import numpy as np
import pandas as pd

from calculators import IndicadoresRiscoB3
from feature import EngenhariaDeFeatures, ajustar_clusters_regime, carregar_cotacoes

JANELA_TREINO = 252
REPETICOES = 10
N_PERMUTACOES = 12
SEMENTE_MC = 42

# Datas escolhidas a priori por representarem regimes distintos, nao por resultado:
# fundo da crise de 2015-2016, choque da covid e um periodo calmo recente.
# Todas sao datas de rebalanceamento efetivas da serie: uma data inventada nao tem cesta
# real associada e o teste 2 passaria a avaliar o solver, nao o caminho do backtest.
DATAS_TESTE = ['2016-02-11', '2020-04-06', '2024-03-27', '2026-04-02']


def otimizar(ativos: list, data_limite: str) -> dict:
    """Reproduz exatamente o caminho do servidor MCP, sem passar por Node nem pela LLM."""
    motor = IndicadoresRiscoB3()
    validos = [a for a in ativos if a in motor.df_acoes.columns]
    motor.aplicar_janela(data_limite=data_limite, janela=JANELA_TREINO, ativos=validos)
    resultado = motor.otimizar_carteira_markowitz()
    if resultado['status'] != 'sucesso':
        return {'status': 'erro', 'mensagem': resultado.get('mensagem', '')}
    pesos = resultado['pesos_otimizados']
    return {
        'status': 'sucesso',
        'pesos': pesos,
        'var': motor.calcular_var_parametrico(pesos, patrimonio_total=100000),
        # sorted() replica a correcao feita no servidor: soma em ordem canonica, para que a
        # saida nao dependa da ordem em que os agentes listaram os ativos.
        'beta': sum(motor.calcular_beta(t) * pesos[t] for t in sorted(pesos)),
        'metricas': resultado['metricas_esperadas'],
    }


def assinatura(r: dict) -> str:
    """
    Assinatura canonica de um resultado: pesos ORDENADOS por ticker com precisao total.
    A ordenacao e de proposito — compara-se a carteira, nao a ordem do dicionario.
    """
    if r['status'] != 'sucesso':
        return f"erro:{r['mensagem']}"
    pesos = ';'.join(f'{t}={r["pesos"][t]!r}' for t in sorted(r['pesos']))
    return f'{pesos}|var={r["var"]!r}|beta={r["beta"]!r}'


def teste_repetibilidade(cestas: dict) -> list:
    print('-' * 88)
    print(f'TESTE 1 - REPETIBILIDADE ({REPETICOES} execucoes identicas por data)')
    print('-' * 88)
    linhas = []
    for data, ativos in cestas.items():
        assinaturas = {assinatura(otimizar(ativos, data)) for _ in range(REPETICOES)}
        ok = len(assinaturas) == 1
        print(f'  {data}  {len(ativos)} ativos  ->  '
              f'{"IDENTICO" if ok else f"DIVERGE ({len(assinaturas)} saidas distintas)"}')
        linhas.append({'teste': 'repetibilidade', 'data': data, 'n': REPETICOES,
                       'saidas_distintas': len(assinaturas), 'deterministico': ok})
    return linhas


def teste_ordem(cestas: dict) -> list:
    print('-' * 88)
    print(f'TESTE 2 - INVARIANCIA A ORDEM (ate {N_PERMUTACOES} permutacoes da mesma cesta)')
    print('-' * 88)
    linhas = []
    for data, ativos in cestas.items():
        todas = list(itertools.permutations(ativos))
        rng = np.random.default_rng(SEMENTE_MC)
        if len(todas) > N_PERMUTACOES:
            idx = rng.choice(len(todas), size=N_PERMUTACOES, replace=False)
            perms = [todas[i] for i in idx]
        else:
            perms = todas
        # A ordem original entra sempre, para que a comparacao inclua o caso real.
        perms = [tuple(ativos)] + [p for p in perms if p != tuple(ativos)]

        vistos = {}
        for p in perms:
            vistos.setdefault(assinatura(otimizar(list(p), data)), []).append(p)

        ok = len(vistos) == 1
        # Se as assinaturas diferem, e preciso separar duas coisas que nao sao a mesma:
        # uma carteira diferente (falha metodologica) e o mesmo resultado com residuo de
        # ponto flutuante (irrelevante, mas que nao deve ser escondido). O critério é a
        # carteira: pesos e VaR iguais com beta divergindo em menos de 1e-9 é residuo.
        residuo = False
        if not ok:
            carteiras = {a.split('|var=')[0] + '|var=' + a.split('|var=')[1].split('|')[0]
                         for a in vistos}
            betas = [float(a.split('beta=')[1]) for a in vistos if 'beta=' in a]
            residuo = len(carteiras) == 1 and (max(betas) - min(betas)) < 1e-9

        rotulo = ('INVARIANTE' if ok else
                  f'INVARIANTE na carteira, residuo de float no beta '
                  f'({len(vistos)} assinaturas)' if residuo else
                  f'SENSIVEL A ORDEM ({len(vistos)} saidas distintas)')
        print(f'  {data}  {len(ativos)} ativos, {len(perms)} ordens  ->  {rotulo}')
        if not ok:
            for i, (ass, ordens) in enumerate(vistos.items(), 1):
                exemplo = ', '.join(ordens[0])
                print(f'      saida {i} ({len(ordens)} ordens), ex.: [{exemplo}]')
                print(f'        {ass[:150]}')
        linhas.append({'teste': 'invariancia_ordem', 'data': data, 'n': len(perms),
                       'saidas_distintas': len(vistos),
                       'residuo_float': residuo, 'deterministico': ok or residuo})
    return linhas


def teste_kmeans() -> list:
    print('-' * 88)
    print(f'TESTE 3 - K-MEANS ({REPETICOES} execucoes identicas por data)')
    print('-' * 88)
    # Mesmo caminho de gerar_contexto_janela_atual no servidor MCP: a janela de 252 pregoes
    # recortada do historico completo, com as colunas macro ainda presentes.
    historico = carregar_cotacoes()
    linhas = []
    for data in DATAS_TESTE:
        janela = historico.loc[:data].iloc[-JANELA_TREINO:]
        assinaturas = set()
        rotulo = limiar = None
        for _ in range(REPETICOES):
            eng = EngenhariaDeFeatures(janela)
            r = eng.detectar_regime_kmeans()
            if r['status'] != 'sucesso':
                assinaturas.add('erro:' + r.get('mensagem', ''))
                continue
            rotulo = r['regime_atual'].split(' ')[0]
            limiar = r['ajuste_clusters']['limiar_turbulencia_vol']
            assinaturas.add(f'{r["regime_atual"]}|{limiar!r}|'
                            f'{r["ajuste_clusters"]["observacoes"]}')
        ok = len(assinaturas) == 1
        print(f'  {data}  regime {rotulo}, limiar {limiar}  ->  '
              f'{"IDENTICO" if ok else f"DIVERGE ({len(assinaturas)} saidas)"}')
        linhas.append({'teste': 'kmeans', 'data': data, 'n': REPETICOES,
                       'saidas_distintas': len(assinaturas), 'deterministico': ok})
    return linhas


def teste_monte_carlo() -> list:
    print('-' * 88)
    print(f'TESTE 4 - MONTE CARLO (default_rng({SEMENTE_MC}), 2 execucoes independentes)')
    print('-' * 88)
    df = pd.read_csv('resultado_backtest_economicAI.csv')
    mu, sigma, passos = (df.Retorno_Carteira.mean(), df.Retorno_Carteira.std(), len(df))
    percentis = []
    for _ in range(2):
        rng = np.random.default_rng(SEMENTE_MC)
        r = rng.normal(mu, sigma, (passos, 10_000))
        final = 100000.0 * np.prod(1 + r, axis=0)
        percentis.append((float(final.mean()), float(np.percentile(final, 5))))
    ok = percentis[0] == percentis[1]
    print(f'  media R$ {percentis[0][0]:,.2f} | VaR95 R$ {percentis[0][1]:,.2f}  ->  '
          f'{"IDENTICO" if ok else "DIVERGE"}')
    return [{'teste': 'monte_carlo', 'data': 'serie completa', 'n': 2,
             'saidas_distintas': 1 if ok else 2, 'deterministico': ok}]


def cestas_reais() -> dict:
    """
    Usa as cestas que os agentes efetivamente escolheram nas datas de teste. Inventar uma
    cesta testaria o solver, nao o sistema: o que precisa ser deterministico e o caminho
    que o backtest percorreu.
    """
    df = pd.read_csv('resultado_backtest_economicAI.csv')
    df = df.set_index('Data_Rebalanceamento')
    cestas = {}
    for data in DATAS_TESTE:
        if data in df.index:
            cestas[data] = [t.strip() for t in df.loc[data, 'Ativos_Selecionados'].split(';')]
    return cestas


def executar():
    print('=' * 88)
    print('DETERMINISMO DA CAMADA MATEMATICA')
    print('=' * 88)
    cestas = cestas_reais()
    print(f'Cestas reais do backtest em {len(cestas)} datas:')
    for d, a in cestas.items():
        print(f'  {d}: {", ".join(a)}')
    print()

    linhas = (teste_repetibilidade(cestas) + teste_ordem(cestas)
              + teste_kmeans() + teste_monte_carlo())

    res = pd.DataFrame(linhas)
    res.to_csv('resultado_determinismo_matematico.csv', index=False)

    print('=' * 88)
    falhas = res[~res.deterministico]
    if falhas.empty:
        print('CONCLUSAO: a camada matematica e deterministica em todos os testes.')
        print('A afirmacao do titulo ("modelagem matematica deterministica") se sustenta:')
        print('mesma entrada economica, mesma saida, inclusive sob permutacao da ordem dos')
        print('ativos e com o K-Means reajustado a cada chamada.')
    else:
        print('CONCLUSAO: ha componentes NAO deterministicos. Nao afirmar determinismo')
        print('sem qualificar. Falhas:')
        for _, f in falhas.iterrows():
            print(f'  - {f.teste} em {f.data}: {f.saidas_distintas} saidas distintas')
    print('Salvo: resultado_determinismo_matematico.csv')


if __name__ == '__main__':
    executar()
