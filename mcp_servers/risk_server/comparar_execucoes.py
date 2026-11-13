"""
Compara execucoes do backtest em dois eixos independentes.

EIXO 1 - EFEITO DA CORRECAO DO K-MEANS
Confronta a serie publicada (clusters ajustados em janela movel de 252 dias, sem
padronizacao das features) com a serie corrigida (janela expansiva + StandardScaler).
Mede quanto a cesta mudou por janela, via indice de Jaccard, e quanto disso chegou ao
retorno acumulado. Serve para responder se a correcao mudou o resultado ou apenas o rotulo.

EIXO 2 - DETERMINISMO DA CAMADA DE LLM
Confronta replicas da MESMA especificacao: mesmo codigo, mesma base, temperature 0 e
seed 42. Em teoria as cestas deveriam ser identicas. Este eixo mede a dispersao que
sobra, e e a evidencia empirica que o titulo da dissertacao exige na palavra
"deterministica" — o seed por si nao basta, porque a OpenAI nao mantem o backend fixo
(os tres agentes recebem system_fingerprint diferentes na mesma chamada).

Nenhum dos dois eixos consome API: tudo sai dos CSV ja gravados.
"""

import glob
import os

import numpy as np
import pandas as pd

JANELAS_ANO = 252 / 21
CAMINHO_PUBLICADO = 'resultado_backtest_economicAI_KMEANS_JANELA252.csv'
CAMINHO_CORRIGIDO = 'resultado_backtest_economicAI_KMEANS_EXPANSIVO.csv'
PADRAO_REPLICAS = 'resultado_replica_*.csv'


def ler(caminho: str) -> pd.DataFrame:
    df = pd.read_csv(caminho, parse_dates=['Data_Rebalanceamento', 'Data_Apuracao'])
    return df.set_index('Data_Rebalanceamento').sort_index()


def cesta(linha) -> set:
    """Conjunto de tickers de uma janela. Campo vazio devolve conjunto vazio, nao NaN."""
    valor = linha.get('Ativos_Selecionados')
    if not isinstance(valor, str) or not valor.strip():
        return set()
    return {t.strip() for t in valor.split(';') if t.strip()}


def jaccard(a: set, b: set) -> float:
    """Indice de Jaccard. Duas cestas vazias contam como identicas, nao como 0/0."""
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def metricas(retornos: pd.Series) -> dict:
    r = retornos.dropna()
    total = (1 + r).prod() - 1
    anos = len(r) / JANELAS_ANO
    capital = (1 + r).cumprod()
    return {
        'janelas': len(r),
        'total': total,
        'cagr': (1 + total) ** (1 / anos) - 1,
        'vol': r.std() * np.sqrt(JANELAS_ANO),
        'mdd': (capital / capital.cummax() - 1).min(),
    }


def comparar_par(rotulo_a: str, a: pd.DataFrame, rotulo_b: str, b: pd.DataFrame) -> dict:
    """Compara duas execucoes apenas nas janelas que existem nas duas."""
    comuns = a.index.intersection(b.index)
    js = [jaccard(cesta(a.loc[d]), cesta(b.loc[d])) for d in comuns]
    identicas = sum(1 for j in js if j == 1.0)
    ma, mb = metricas(a.Retorno_Carteira), metricas(b.Retorno_Carteira)
    return {
        'par': f'{rotulo_a} vs {rotulo_b}',
        'janelas_comuns': len(comuns),
        'so_em_a': len(a.index.difference(b.index)),
        'so_em_b': len(b.index.difference(a.index)),
        'jaccard_medio': float(np.mean(js)) if js else np.nan,
        'jaccard_mediano': float(np.median(js)) if js else np.nan,
        'cestas_identicas': identicas,
        'pct_identicas': 100 * identicas / len(comuns) if len(comuns) else np.nan,
        'total_a': ma['total'], 'total_b': mb['total'],
        'cagr_a': ma['cagr'], 'cagr_b': mb['cagr'],
    }


def executar():
    print('=' * 88)
    print('COMPARACAO DE EXECUCOES DO BACKTEST')
    print('=' * 88)

    # ---------------- Eixo 1: efeito da correcao do K-Means ----------------
    if os.path.exists(CAMINHO_PUBLICADO) and os.path.exists(CAMINHO_CORRIGIDO):
        pub, cor = ler(CAMINHO_PUBLICADO), ler(CAMINHO_CORRIGIDO)
        r = comparar_par('publicado (movel 252)', pub, 'corrigido (expansivo)', cor)

        print('\n' + '-' * 88)
        print('EIXO 1 - EFEITO DA CORRECAO DO K-MEANS')
        print('-' * 88)
        print(f'Janelas comuns:            {r["janelas_comuns"]}')
        print(f'So na serie publicada:     {r["so_em_a"]}  (descartadas na corrigida)')
        print(f'So na serie corrigida:     {r["so_em_b"]}')
        print(f'Jaccard medio das cestas:  {r["jaccard_medio"]:.3f}')
        print(f'Jaccard mediano:           {r["jaccard_mediano"]:.3f}')
        print(f'Cestas identicas:          {r["cestas_identicas"]} de {r["janelas_comuns"]} '
              f'({r["pct_identicas"]:.1f}%)')
        print(f'Retorno total publicado:   {r["total_a"]*100:.1f}%  (CAGR {r["cagr_a"]*100:.2f}%)')
        print(f'Retorno total corrigido:   {r["total_b"]*100:.1f}%  (CAGR {r["cagr_b"]*100:.2f}%)')

        # Comparacao pareada nas janelas comuns: a diferenca de retorno e sistematica ou ruido?
        comuns = pub.index.intersection(cor.index)
        dif = (cor.loc[comuns, 'Retorno_Carteira'] - pub.loc[comuns, 'Retorno_Carteira']).dropna()
        from scipy import stats
        t, p = stats.ttest_1samp(dif, 0.0)
        print(f'Diferenca media por janela: {dif.mean()*100:+.3f} p.p. '
              f'({dif.mean()*JANELAS_ANO*100:+.2f}% a.a.)')
        print(f'Teste pareado:             t = {t:.3f}, p = {p:.4f}')
        if p >= 0.05:
            print('  -> A melhora do retorno acumulado NAO e estatisticamente distinguivel')
            print('     de ruido janela a janela. O ganho no acumulado vem da capitalizacao')
            print('     de diferencas pequenas, e nao pode ser declarado como efeito medido')
            print('     da correcao. A justificativa da correcao e metodologica (coerencia')
            print('     interna do rotulo), nao de desempenho.')
        else:
            print('  -> Diferenca sistematica detectada. Ainda assim a correcao se justifica')
            print('     a priori, pela coerencia do rotulo, e nao pelo retorno.')
    else:
        print('\n[Eixo 1 ignorado: faltam os CSV das duas series.]')

    # ---------------- Eixo 2: dispersao entre replicas ----------------
    arquivos = sorted(glob.glob(PADRAO_REPLICAS))
    if os.path.exists(CAMINHO_CORRIGIDO):
        arquivos = [CAMINHO_CORRIGIDO] + arquivos

    print('\n' + '-' * 88)
    print('EIXO 2 - DETERMINISMO: REPLICAS DA MESMA ESPECIFICACAO (seed 42, temperature 0)')
    print('-' * 88)

    if len(arquivos) < 2:
        print('Menos de duas execucoes disponiveis; dispersao nao calculavel.')
        return

    execucoes = {os.path.basename(a).replace('resultado_', '').replace('.csv', ''): ler(a)
                 for a in arquivos}
    rotulos = list(execucoes)

    print(f'{"Execucao":<38}{"Janelas":>9}{"Total":>12}{"CAGR":>9}{"Vol":>9}{"MaxDD":>10}')
    totais, cagrs = [], []
    for rot in rotulos:
        m = metricas(execucoes[rot].Retorno_Carteira)
        totais.append(m['total'])
        cagrs.append(m['cagr'])
        print(f'{rot:<38}{m["janelas"]:>9}{m["total"]*100:>11.1f}%{m["cagr"]*100:>8.2f}%'
              f'{m["vol"]*100:>8.2f}%{m["mdd"]*100:>9.2f}%')

    totais, cagrs = np.array(totais), np.array(cagrs)
    print(f'\nRetorno total: min {totais.min()*100:.1f}% | max {totais.max()*100:.1f}% | '
          f'amplitude {(totais.max()-totais.min())*100:.1f} p.p.')
    print(f'CAGR:          min {cagrs.min()*100:.2f}% | max {cagrs.max()*100:.2f}% | '
          f'amplitude {(cagrs.max()-cagrs.min())*100:.2f} p.p. | '
          f'desvio-padrao {cagrs.std(ddof=1)*100:.2f} p.p.')

    print('\nJaccard entre pares de execucoes:')
    linhas = []
    for i in range(len(rotulos)):
        for j in range(i + 1, len(rotulos)):
            r = comparar_par(rotulos[i], execucoes[rotulos[i]],
                             rotulos[j], execucoes[rotulos[j]])
            linhas.append(r)
            print(f'  {rotulos[i]:<30} x {rotulos[j]:<30} '
                  f'Jaccard {r["jaccard_medio"]:.3f} | '
                  f'identicas {r["pct_identicas"]:.1f}%')

    jm = np.array([l['jaccard_medio'] for l in linhas])
    pct = np.array([l['pct_identicas'] for l in linhas])
    print(f'\nJaccard medio entre replicas: {jm.mean():.3f} '
          f'(min {jm.min():.3f}, max {jm.max():.3f})')
    print(f'Cestas identicas entre replicas: {pct.mean():.1f}% em media')

    print('\nLeitura para o texto:')
    if jm.min() >= 0.999 and (cagrs.max() - cagrs.min()) < 0.0005:
        print('  Reproducao exata. Com temperature 0 e seed fixo as cestas nao variaram')
        print('  entre execucoes, logo a camada de LLM e deterministica na pratica.')
    else:
        print('  A reproducao NAO e exata. Com a mesma especificacao as cestas variam entre')
        print('  execucoes, e o retorno acumulado varia na amplitude acima. O trabalho nao')
        print('  pode afirmar determinismo da camada de LLM; o que se pode afirmar e que a')
        print('  camada matematica e deterministica e que a camada de LLM foi fixada no')
        print('  maximo que a API permite (temperature 0, seed 42), com a dispersao residual')
        print('  medida e declarada. Os resultados principais devem ser reportados com essa')
        print('  amplitude, nao como ponto unico.')

    pd.DataFrame(linhas).to_csv('resultado_comparacao_execucoes.csv', index=False)
    print('\nSalvo: resultado_comparacao_execucoes.csv')


if __name__ == '__main__':
    executar()
