# -*- coding: utf-8 -*-
"""
Figura 2 da dissertacao: classificacao do regime de mercado pelo K-Means.

A versao anterior ajustava o K-Means uma unica vez sobre a amostra inteira
(kmeans.fit_predict sobre todos os pregoes) e colorava cada ponto com o rotulo daquele
ajuste. Isso contradizia a metodologia, que declara janela expansiva point-in-time, e
exibia na figura exatamente o vies de retrospectiva que o trabalho afirma eliminar.

Agora a figura usa os rotulos apurados em 'resultado_diagnostico_regime.csv', que
'diagnostico_regime.py' produz reajustando o algoritmo a cada data de decisao sobre a
historia disponivel somente ate aquela data.

Painel A  dispersao dos atributos nas datas de decisao, com a cor do rotulo vigente.
Painel B  limiar de volatilidade reestimado a cada janela, contra a volatilidade
          observada. Mostra que a fronteira se moveu com a historia acumulada.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

from estilo_figuras import aplicar
from feature import EngenhariaDeFeatures, carregar_cotacoes

aplicar()

COR_CALMARIA = '#1F4E79'
COR_TURBULENCIA = '#A93226'

diag = pd.read_csv('resultado_diagnostico_regime.csv',
                   parse_dates=['Data_Rebalanceamento']).set_index('Data_Rebalanceamento')

# As duas features sao janelas moveis para tras (retorno, desvio e media de 21 dias),
# logo o valor na data t nunca usa pregao posterior a t: calcular sobre a serie inteira
# e selecionar as datas de decisao equivale a recalcular a cada fatia.
precos = carregar_cotacoes()[['^BVSP', 'USDBRL=X']]
atributos = EngenhariaDeFeatures._features_regime(precos).reindex(diag.index).dropna()
diag = diag.loc[atributos.index]

# Empilhados, e nao lado a lado: na pagina A4 a figura ocupa 420 pt de largura, e em duas
# colunas os rotulos dos eixos ficam ilegiveis no impresso.
plt.rcParams.update({'font.size': 11})
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.2, 7.6))


def pct(valor, _=None):
    return f'{valor * 100:.0f}%'


# Duas janelas de 2020 ficam muito fora da nuvem e, em escala cheia, comprimem as
# demais 166 ate a ilegibilidade. Sao mantidas, desenhadas na borda e identificadas.
X_MAX, Y_MIN, Y_MAX = 0.60, -1.6, 1.8

for rotulo, cor, nome in (('Calmaria', COR_CALMARIA, 'Calmaria'),
                          ('Turbulencia', COR_TURBULENCIA, 'Turbulência')):
    corte = diag.Regime_C_Final == rotulo
    x = atributos.Volatilidade_BVSP[corte]
    y = atributos.Tendencia_Dolar[corte]
    fora = (x > X_MAX) | (y < Y_MIN) | (y > Y_MAX)
    ax1.scatter(x[~fora], y[~fora], s=34, color=cor, alpha=0.75,
                linewidths=0.5, edgecolors='white',
                label=f'{nome} — {int(corte.sum())} janelas')
    if fora.any():
        ax1.scatter(x[fora].clip(upper=X_MAX), y[fora].clip(lower=Y_MIN, upper=Y_MAX),
                    s=46, facecolors='none', edgecolors=cor, linewidths=1.4, marker='D')

ax1.set_xlim(0.06, X_MAX + 0.015)
ax1.set_ylim(Y_MIN - 0.05, Y_MAX + 0.05)
ax1.axhline(0, color='#AAAAAA', linewidth=0.7, zorder=0)
ax1.xaxis.set_major_formatter(FuncFormatter(pct))
ax1.yaxis.set_major_formatter(FuncFormatter(pct))
ax1.set_xlabel('Volatilidade anualizada do IBOVESPA (21 pregões)')
ax1.set_ylabel('Tendência anualizada do dólar (21 pregões)')
ax1.set_title(f'A) Atributos nas {len(diag)} datas de decisão\n'
              'Cor: rótulo vigente na data, apurado só com dados anteriores a ela',
              fontsize=10, loc='left')
ax1.legend(loc='lower right', fontsize=9)
ax1.text(0.015, 0.985, 'Losangos vazados: abril e junho de 2020, fora da escala',
         transform=ax1.transAxes, fontsize=7.6, color='#555555', va='top')

ax2.plot(diag.index, diag.Vol_IBOV_21d, color='#7F8C8D', linewidth=1.2,
         label='Volatilidade observada na data')
ax2.plot(diag.index, diag.Limiar_C, color='#A93226', linewidth=2.0,
         label='Limiar reestimado a cada janela')
ax2.fill_between(diag.index, diag.Limiar_C, diag.Vol_IBOV_21d,
                 where=diag.Vol_IBOV_21d >= diag.Limiar_C,
                 color=COR_TURBULENCIA, alpha=0.18, interpolate=True)
ax2.set_ylim(0.06, 0.62)
pico = diag.Vol_IBOV_21d.idxmax()
ax2.annotate(f'{diag.Vol_IBOV_21d.max() * 100:.0f}% em {pico.strftime("%m/%Y")}',
             xy=(pico, 0.60), xytext=(-96, -4), textcoords='offset points',
             fontsize=7.6, color='#555555')
ax2.yaxis.set_major_formatter(FuncFormatter(pct))
ax2.xaxis.set_major_locator(mdates.YearLocator(2))
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax2.set_xlabel('Data de rebalanceamento')
ax2.set_ylabel('Volatilidade anualizada do IBOVESPA')
ax2.set_title('B) Deslocamento da fronteira ao longo do tempo\n'
              'Área sombreada: volatilidade acima do limiar vigente',
              fontsize=10, loc='left')
ax2.legend(loc='lower left', fontsize=9)

fig.tight_layout()
fig.savefig('figura1_kmeans.png', dpi=300)
plt.close(fig)

turb = (diag.Regime_C_Final == 'Turbulencia')
print(f'figura1_kmeans.png | {len(diag)} datas | Turbulência em {turb.sum()} '
      f'({turb.mean() * 100:.1f}%) | limiar de {diag.Limiar_C.min() * 100:.1f}% '
      f'a {diag.Limiar_C.max() * 100:.1f}%')
