"""
Quanto as correcoes do K-Means mudam a classificacao de regime.

Duas falhas foram corrigidas, e este script separa o efeito de cada uma rodando os tres
metodos nas mesmas datas de rebalanceamento:

  A) ORIGINAL — ajuste dentro da janela de 252 pregoes, sem padronizar. Os centroides
     eram recalculados a cada rebalanceamento sobre um unico ano, logo "Turbulencia"
     significava apenas volatilidade alta PARA AQUELE ANO e o rotulo nao era comparavel
     entre janelas.
  B) EXPANSIVO — ajuste sobre todo o historico ate a data, ainda sem padronizar. Isola o
     efeito da janela.
  C) FINAL — expansivo e padronizado. Sem padronizar, a distancia euclidiana e dominada
     pela tendencia do dolar, que varia numa escala muito maior que a volatilidade; o
     metodo chegava a rotular como Calmaria janelas cuja volatilidade estava acima do
     proprio centroide turbulento.

Sem estes numeros a correcao seria uma afirmacao sem evidencia — e o backtest publicado
foi rodado com o metodo A, logo o texto precisa declarar o tamanho do problema que ficou
para tras.

Nao consome API: so recalcula os clusters sobre precos.
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from feature import (MIN_OBS_REGIME, EngenhariaDeFeatures, ajustar_clusters_regime,
                     carregar_cotacoes)

CAMINHO_RESULTADOS = 'resultado_backtest_economicAI.csv'
JANELA_TREINO = 252


def rotular_cru(df_ml: pd.DataFrame) -> tuple:
    """Metodo sem padronizacao, como estava antes. Rotulo e limiar de volatilidade."""
    kmeans = KMeans(n_clusters=2, random_state=42, n_init=10).fit(df_ml)
    idx = int(np.argmax(kmeans.cluster_centers_[:, 0]))
    atual = kmeans.predict(df_ml.iloc[-1:])[0]
    return ('Turbulencia' if atual == idx else 'Calmaria',
            float(kmeans.cluster_centers_[idx, 0]))


def rotular_padronizado(df_ml: pd.DataFrame) -> tuple:
    kmeans, escala, idx = ajustar_clusters_regime(df_ml)
    atual = kmeans.predict(escala.transform(df_ml.iloc[-1:]))[0]
    limiar = escala.inverse_transform(kmeans.cluster_centers_)[idx, 0]
    return ('Turbulencia' if atual == idx else 'Calmaria', float(limiar))


def executar():
    res = pd.read_csv(CAMINHO_RESULTADOS, parse_dates=['Data_Rebalanceamento'])
    precos = carregar_cotacoes()[['^BVSP', 'USDBRL=X']]
    features = EngenhariaDeFeatures._features_regime

    linhas = []
    for data in res.Data_Rebalanceamento:
        ate_data = precos.loc[:data]
        janela = ate_data.iloc[-JANELA_TREINO:]

        ml_janela = features(janela)
        ml_expansiva = features(ate_data)
        if len(ml_janela) < 21 or len(ml_expansiva) < MIN_OBS_REGIME:
            continue

        regime_a, limiar_a = rotular_cru(ml_janela)
        regime_b, limiar_b = rotular_cru(ml_expansiva)
        regime_c, limiar_c = rotular_padronizado(ml_expansiva)
        vol = float(ml_expansiva.Volatilidade_BVSP.iloc[-1])
        linhas.append({
            'Data_Rebalanceamento': data,
            'Regime_A_Original': regime_a,
            'Regime_B_Expansivo': regime_b,
            'Regime_C_Final': regime_c,
            'Limiar_A': round(limiar_a, 4),
            'Limiar_B': round(limiar_b, 4),
            'Limiar_C': round(limiar_c, 4),
            'Vol_IBOV_21d': round(vol, 4),
            # Incoerencia interna: rotulo contradiz o proprio limiar de volatilidade.
            'Incoerente_A': (regime_a == 'Turbulencia') != (vol >= limiar_a),
            'Incoerente_C': (regime_c == 'Turbulencia') != (vol >= limiar_c),
            'Obs_Expansivo': len(ml_expansiva),
        })

    d = pd.DataFrame(linhas)
    metodos = [('Regime_A_Original', 'Limiar_A', 'A) original (252, cru)'),
               ('Regime_B_Expansivo', 'Limiar_B', 'B) expansivo, cru'),
               ('Regime_C_Final', 'Limiar_C', 'C) expansivo, padronizado')]

    print('=' * 88)
    print('DIAGNOSTICO DAS CORRECOES NO K-MEANS DE REGIME')
    print('=' * 88)
    print(f'Datas avaliadas: {len(d)} '
          f'({d.Data_Rebalanceamento.min().date()} a {d.Data_Rebalanceamento.max().date()})')

    print('-' * 88)
    print('CONCORDANCIA ENTRE METODOS')
    for (ca, _, ra), (cb, _, rb) in [(metodos[0], metodos[1]), (metodos[1], metodos[2]),
                                     (metodos[0], metodos[2])]:
        igual = d[ca] == d[cb]
        print(f'  {ra:<28} vs {rb:<28} {igual.mean()*100:5.1f}% '
              f'({igual.sum()}/{len(d)})')

    print('-' * 88)
    print('FREQUENCIA DO ROTULO "TURBULENCIA"')
    for coluna, _, rotulo in metodos:
        print(f'  {rotulo:<28} {(d[coluna] == "Turbulencia").mean()*100:5.1f}%')

    print('-' * 88)
    print('ESTABILIDADE DO LIMIAR (volatilidade do centroide turbulento)')
    print('Se o limiar varia muito entre janelas, o rotulo nao e comparavel no tempo.')
    for _, coluna, rotulo in metodos:
        s = d[coluna]
        print(f'  {rotulo:<28} min {s.min()*100:5.1f}%  mediana {s.median()*100:5.1f}%  '
              f'max {s.max()*100:5.1f}%  amplitude {(s.max()-s.min())*100:5.1f} p.p.')

    print('-' * 88)
    print('COERENCIA INTERNA (rotulo de acordo com o proprio limiar de volatilidade)')
    print(f'  A) original                  {d.Incoerente_A.sum():3d}/{len(d)} janelas incoerentes'
          f'  ({d.Incoerente_A.mean()*100:.1f}%)')
    print(f'  C) expansivo, padronizado    {d.Incoerente_C.sum():3d}/{len(d)} janelas incoerentes'
          f'  ({d.Incoerente_C.mean()*100:.1f}%)')
    print('  A incoerencia residual em C nao e defeito: a regra e bidimensional e o limiar')
    print('  acima e so a projecao dela na volatilidade. Janelas proximas da fronteira podem')
    print('  ser decididas pela tendencia do dolar. Em A a incoerencia era de escala.')

    divergentes = d[d.Regime_A_Original != d.Regime_C_Final]
    print('-' * 88)
    print(f'JANELAS EM QUE O ROTULO MUDOU DE A PARA C ({len(divergentes)} no total, 15 primeiras)')
    print(f'{"Data":<12}{"A":>13}{"C":>13}{"Vol 21d":>10}{"Limiar A":>11}{"Limiar C":>11}')
    for _, l in divergentes.head(15).iterrows():
        print(f'{str(l.Data_Rebalanceamento.date()):<12}{l.Regime_A_Original:>13}'
              f'{l.Regime_C_Final:>13}{l.Vol_IBOV_21d*100:>9.1f}%'
              f'{l.Limiar_A*100:>10.1f}%{l.Limiar_C*100:>10.1f}%')

    d.to_csv('resultado_diagnostico_regime.csv', index=False)
    print('=' * 88)
    print("Detalhe por janela salvo em 'resultado_diagnostico_regime.csv'.")


if __name__ == '__main__':
    executar()
