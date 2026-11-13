# -*- coding: utf-8 -*-
"""
Desenha a figura de arquitetura do sistema.

Os três fluxogramas do texto original (pipeline de anonimização, orquestração
multiagente e otimização determinística) eram objetos de desenho do Word e não
puderam ser recuperados do arquivo. Esta figura os consolida em um único
diagrama, separando por cor a camada heurística da camada determinística.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Patch

plt.rcParams.update({'font.family': 'Arial', 'axes.unicode_minus': False})

AZUL, AZUL_CLARO = '#1F4E79', '#D9E6F2'
VERMELHO, VERMELHO_CLARO = '#A93226', '#F7DDD9'
VERDE, VERDE_CLARO = '#1E6F50', '#D7EFE4'
CINZA = '#566573'


def caixa(ax, x, y, largura, altura, titulo, corpo, cor, fundo, fonte_corpo=8.0):
    ax.add_patch(FancyBboxPatch((x, y), largura, altura,
                                boxstyle='round,pad=0.008,rounding_size=0.015',
                                linewidth=1.6, edgecolor=cor, facecolor=fundo, zorder=2))
    ax.text(x + largura / 2, y + altura - 0.030, titulo, ha='center', va='top',
            fontsize=9.4, fontweight='bold', color=cor, zorder=3)
    ax.text(x + largura / 2, y + altura / 2 - 0.028, corpo, ha='center', va='center',
            fontsize=fonte_corpo, color='#17202A', linespacing=1.55, zorder=3)


def seta(ax, origem, destino, cor, curvatura=0.0, traco='-'):
    ax.add_patch(FancyArrowPatch(origem, destino, arrowstyle='-|>', mutation_scale=14,
                                 linewidth=1.6, color=cor, linestyle=traco, zorder=1,
                                 connectionstyle=f'arc3,rad={curvatura}'))


fig, ax = plt.subplots(figsize=(10.5, 7.2))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

L, A = 0.275, 0.215
X1, X2, X3 = 0.075, 0.3625, 0.650
Y1, Y2, Y3 = 0.715, 0.440, 0.165

caixa(ax, X1, Y1, L, A, '1. Coleta e corte temporal',
      'Preços da B3 e demonstrações\nfinanceiras da CVM.\n\nNa data da decisão a série é\ncortada: nenhum dado\nposterior entra no sistema.',
      AZUL, AZUL_CLARO)

caixa(ax, X2, Y1, L, A, '2. Atributos e regime',
      'Momentum, volatilidade,\nassimetria, curtose e\nindicadores fundamentalistas.\n\nK-Means com janela expansiva:\ncalmaria ou turbulência.',
      AZUL, AZUL_CLARO)

caixa(ax, X3, Y1, L, A, '3. Câmara cega',
      'Os códigos reais são\nmascarados: VALE3 → Ativo_1.\n\nO modelo de linguagem recebe\napenas números, sem saber\nde que empresa se trata.',
      VERMELHO, VERMELHO_CLARO)

caixa(ax, X1, Y2, 0.850, 0.190, '4. Debate entre agentes',
      'Três personas analisam a lista anônima: Value, Growth e Macro. Regra de consenso rígida — o ativo\n'
      'avança para a etapa seguinte apenas se obtiver dois votos ou mais. Nenhum peso, preço ou métrica\n'
      'de risco é calculado aqui: os agentes apenas selecionam.',
      VERMELHO, VERMELHO_CLARO, fonte_corpo=8.2)

caixa(ax, X1, Y3, 0.470, A, '5. Otimização determinística',
      'A máscara é revertida somente dentro\ndo servidor. Sobre a cesta aprovada,\no motor resolve a fronteira eficiente\npela maximização do índice de Sharpe\ne apura VaR 95% e Beta, em ordem fixa\nde ativos para garantir reprodutibilidade.',
      VERDE, VERDE_CLARO, fonte_corpo=8.0)

caixa(ax, 0.580, Y3, 0.345, A, '6. Apuração fora da amostra',
      'Os pesos permanecem imóveis\npor 21 pregões.\n\nO retorno apurado não realimenta\na decisão: a janela avança e\no ciclo recomeça.',
      VERDE, VERDE_CLARO)

seta(ax, (X1 + L, Y1 + A / 2), (X2, Y1 + A / 2), AZUL)
seta(ax, (X2 + L, Y1 + A / 2), (X3, Y1 + A / 2), AZUL)
seta(ax, (X3 + L / 2, Y1), (X3 + L / 2, Y2 + 0.190), VERMELHO)
seta(ax, (X1 + 0.425, Y2), (X1 + 0.235, Y3 + A), VERDE, curvatura=0.0)
seta(ax, (X1 + 0.470, Y3 + A / 2), (0.580, Y3 + A / 2), VERDE)

# Ciclo de retorno: sobe pela esquerda do diagrama
ax.add_patch(FancyArrowPatch((0.752, Y3), (X1 + L / 2, Y1), arrowstyle='-|>',
                             mutation_scale=14, linewidth=1.6, color=CINZA,
                             linestyle='--', zorder=0,
                             connectionstyle='arc3,rad=0.42'))
ax.text(0.400, 0.072, 'O ciclo completo repetiu-se 168 vezes, de janeiro de 2012 a abril de 2026',
        fontsize=8.4, color=CINZA, style='italic', ha='center')

ax.legend(handles=[
    Patch(facecolor=AZUL_CLARO, edgecolor=AZUL, label='Preparação dos dados (determinística)'),
    Patch(facecolor=VERMELHO_CLARO, edgecolor=VERMELHO, label='Seleção pelos agentes (heurística, com modelo de linguagem)'),
    Patch(facecolor=VERDE_CLARO, edgecolor=VERDE, label='Cálculo e apuração (determinística)')],
    loc='lower center', bbox_to_anchor=(0.5, -0.045), ncol=3, fontsize=8.2,
    frameon=False, handlelength=1.5)

fig.savefig('figura_arquitetura.png', dpi=200, bbox_inches='tight')
plt.close(fig)
print('figura_arquitetura.png gerada')
