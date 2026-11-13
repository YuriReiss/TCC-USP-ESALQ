# -*- coding: utf-8 -*-
"""
Gera as duas figuras que faltavam para a dissertação.

figura7_vies_sorteios.png     distribuição do retorno anual composto de 5.000 carteiras
                              aleatórias de 10 ações sorteadas do universo investível em
                              2012, com a posição das 10 ações do estudo. Quantifica o
                              viés de sobrevivência.

figura8_controle_universo.png o resultado de risco que sobrevive ao controle de universo.
                              O painel A usa retornos acima do CDI, de modo que a
                              inclinação desenhada é exatamente o Beta da regressão de
                              Jensen reportada no texto (0,7085 e 1,0608).
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from estilo_figuras import aplicar

aplicar()

COR_ESTUDO = '#C0392B'
COR_SORTEIO = '#95A5A6'
COR_HIBRIDO = '#1F4E79'
COR_UNIVERSO = '#E67E22'
COR_IBOV = '#7F8C8D'

CAGR_ESTUDO = 17.84  # 10 ações do estudo em peso igual, medido em vies_sobrevivencia.py


def figura_vies():
    cagr = pd.read_csv('resultado_vies_sorteios.csv')['CAGR_Sorteio'].dropna().values * 100
    mediana, p95 = np.median(cagr), np.percentile(cagr, 95)
    percentil = (cagr < CAGR_ESTUDO).mean() * 100

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(cagr, bins=60, color=COR_SORTEIO, edgecolor='white', linewidth=0.4,
            label=f'5.000 carteiras aleatórias de 10 ações (mediana {mediana:.2f}% a.a.)')
    ax.axvline(p95, color='#34495E', linestyle=':', linewidth=1.8,
               label=f'Percentil 95 dos sorteios ({p95:.2f}% a.a.)')
    ax.axvline(CAGR_ESTUDO, color=COR_ESTUDO, linestyle='--', linewidth=2.2,
               label=f'10 ações do estudo: {CAGR_ESTUDO:.2f}% a.a. (percentil {percentil:.1f}%)')

    ax.set_xlabel('Retorno anual composto da carteira em peso igual (% a.a.)')
    ax.set_ylabel('Número de carteiras sorteadas')
    ax.set_title('Posição do universo do estudo na distribuição de carteiras aleatórias\n'
                 'Período 2012–2026, sorteio sem reposição do universo investível em 2012',
                 fontsize=11, loc='left')
    ax.legend(loc='upper left', frameon=True, fontsize=9)
    fig.tight_layout()
    fig.savefig('figura7_vies_sorteios.png', dpi=200)
    plt.close(fig)
    print(f'figura7_vies_sorteios.png     | mediana {mediana:.2f}% | p95 {p95:.2f}% '
          f'| estudo {CAGR_ESTUDO:.2f}% | percentil {percentil:.2f}%')


def figura_controle_universo():
    df = pd.read_csv('resultado_series_por_janela.csv')
    rf = df['RF_Janela'].values
    # Retornos acima do CDI: é a base da regressão de Jensen, então a reta desenhada
    # tem exatamente a inclinação (Beta) reportada no texto.
    ibov = (df['Retorno_IBOV'].values - rf) * 100
    hib = (df['Bruto_Hibrido (IA + Markowitz)'].values - rf) * 100
    uni = (df['Bruto_Universo 1/10'].values - rf) * 100

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))

    ax1.scatter(ibov, uni, s=20, color=COR_UNIVERSO, alpha=0.55,
                label='As 10 ações em peso igual')
    ax1.scatter(ibov, hib, s=20, color=COR_HIBRIDO, alpha=0.65, label='Carteira híbrida')
    grade = np.linspace(ibov.min(), ibov.max(), 50)
    for serie, cor in ((uni, COR_UNIVERSO), (hib, COR_HIBRIDO)):
        a, b = np.polyfit(ibov, serie, 1)
        ax1.plot(grade, a * grade + b, color=cor, linewidth=2.2)
    ax1.plot(grade, grade, color=COR_IBOV, linestyle=':', linewidth=1.5,
             label='Reta de 45°: acompanha o índice')
    ax1.axhline(0, color='black', linewidth=0.6)
    ax1.axvline(0, color='black', linewidth=0.6)
    ax1.set_xlabel('Retorno do IBOVESPA acima do CDI na janela (p.p.)')
    ax1.set_ylabel('Retorno da carteira acima do CDI na janela (p.p.)')
    ax1.set_title('A) Sensibilidade ao índice (Beta)\n'
                  'Híbrida 0,709 (p = 0,0006); 10 ações 1,061 (p = 0,1010)',
                  fontsize=10, loc='left')
    ax1.legend(loc='upper left', fontsize=8.5, frameon=True)

    # O painel B usa retorno nominal, não o excesso sobre o CDI: a janela de queda do
    # índice é definida pelo IBOVESPA negativo, que é o recorte das 73 janelas testadas.
    ibov_n = df['Retorno_IBOV'].values * 100
    hib_n = df['Bruto_Hibrido (IA + Markowitz)'].values * 100
    uni_n = df['Bruto_Universo 1/10'].values * 100

    queda = ibov_n < 0
    rotulos = ['IBOVESPA', 'As 10 ações\nem peso igual', 'Carteira\nhíbrida']
    medias = [ibov_n[queda].mean(), uni_n[queda].mean(), hib_n[queda].mean()]
    barras = ax2.bar(rotulos, medias, color=[COR_IBOV, COR_UNIVERSO, COR_HIBRIDO],
                     width=0.55, edgecolor='white')
    for barra, valor in zip(barras, medias):
        ax2.text(barra.get_x() + barra.get_width() / 2, valor - 0.22,
                 f'{valor:+.2f} p.p.'.replace('.', ','), ha='center', va='top',
                 fontsize=9.5, fontweight='bold')
    ax2.axhline(0, color='black', linewidth=0.8)
    ax2.set_ylabel('Retorno nominal médio por janela (%)')
    ax2.set_title(f'B) Média das {int(queda.sum())} janelas de queda do índice\n'
                  'Híbrida menos 10 ações: +2,24 p.p. (t = 3,290; p = 0,0016)',
                  fontsize=10, loc='left')
    ax2.set_ylim(min(medias) * 1.30, 0.6)

    fig.tight_layout()
    fig.savefig('figura8_controle_universo.png', dpi=200)
    plt.close(fig)
    print(f'figura8_controle_universo.png | janelas de queda {int(queda.sum())} '
          f'| IBOV {medias[0]:+.3f} | universo {medias[1]:+.3f} | híbrido {medias[2]:+.3f} '
          f'| diferença {medias[2] - medias[1]:+.3f} p.p.')


if __name__ == '__main__':
    figura_vies()
    figura_controle_universo()
