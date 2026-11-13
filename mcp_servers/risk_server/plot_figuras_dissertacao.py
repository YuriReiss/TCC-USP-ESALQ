# -*- coding: utf-8 -*-
"""
Regera as figuras de resultado com eixo de datas legível para 168 janelas.
As versões herdadas foram desenhadas para 24 janelas e tornaram-se ilegíveis.

figura_capital.png    evolução do capital das quatro carteiras, escala logarítmica
figura_drawdown.png   queda acumulada em relação ao topo, comparando três carteiras
figura_var_beta.png   VaR 95% e Beta apurados a cada rebalanceamento
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

from estilo_figuras import aplicar

aplicar()

COR_HIBRIDO = '#1F4E79'
COR_MARKOWITZ = '#27AE60'
COR_UNIVERSO = '#E67E22'
COR_IBOV = '#7F8C8D'
CAPITAL_INICIAL = 100_000.0

SERIES = pd.read_csv('resultado_series_por_janela.csv', parse_dates=['Data_Rebalanceamento'])
DATAS = SERIES['Data_Rebalanceamento']


def eixo_datas(ax):
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_minor_locator(mdates.YearLocator(1))


def reais(valor, _=None):
    return f'{valor:,.0f}'.replace(',', '.')


def figura_capital():
    arranjo = [
        ('Bruto_Hibrido (IA + Markowitz)', 'Híbrida (agentes + Markowitz)', COR_HIBRIDO, '-', 2.0),
        ('Bruto_Markowitz isolado', 'Markowitz isolado (sem agentes)', COR_MARKOWITZ, '-', 1.6),
        ('Bruto_Universo 1/10', 'As 10 ações em peso igual', COR_UNIVERSO, '-', 1.6),
        ('Retorno_IBOV', 'IBOVESPA', COR_IBOV, '--', 1.6),
    ]
    fig, ax = plt.subplots(figsize=(10, 5.2))
    for coluna, rotulo, cor, traco, largura in arranjo:
        capital = CAPITAL_INICIAL * np.cumprod(1 + SERIES[coluna].values)
        ax.plot(DATAS, capital, color=cor, linestyle=traco, linewidth=largura,
                label=f'{rotulo} — R$ {reais(capital[-1])}')
    ax.set_yscale('log')
    ax.yaxis.set_major_formatter(FuncFormatter(reais))
    ax.set_yticks([100_000, 200_000, 500_000, 1_000_000, 2_000_000])
    eixo_datas(ax)
    ax.set_xlabel('Janela de rebalanceamento')
    ax.set_ylabel('Capital acumulado (R$, escala logarítmica)')
    ax.set_title('Evolução do capital de R$ 100.000,00 em 168 janelas de 21 pregões\n'
                 'Retorno bruto, sem custos de transação; escala logarítmica, em que '
                 'inclinações iguais representam taxas de crescimento iguais',
                 fontsize=11, loc='left')
    ax.legend(loc='upper left', fontsize=9, frameon=True)
    fig.tight_layout()
    fig.savefig('figura_capital.png', dpi=200)
    plt.close(fig)
    for coluna, rotulo, *_ in arranjo:
        capital = CAPITAL_INICIAL * np.cumprod(1 + SERIES[coluna].values)
        print(f'  {rotulo:38s} R$ {capital[-1]:,.2f}')


def figura_drawdown():
    arranjo = [
        ('Bruto_Hibrido (IA + Markowitz)', 'Híbrida (agentes + Markowitz)', COR_HIBRIDO),
        ('Bruto_Universo 1/10', 'As 10 ações em peso igual', COR_UNIVERSO),
        ('Retorno_IBOV', 'IBOVESPA', COR_IBOV),
    ]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    for coluna, rotulo, cor in arranjo:
        capital = np.cumprod(1 + SERIES[coluna].values)
        queda = (capital / np.maximum.accumulate(capital) - 1) * 100
        ax.plot(DATAS, queda, color=cor, linewidth=1.6,
                label=f'{rotulo} — pior queda {queda.min():.2f}%'.replace('.', ','))
        if coluna.startswith('Bruto_Hibrido'):
            ax.fill_between(DATAS, queda, 0, color=cor, alpha=0.18)
    ax.axhline(0, color='black', linewidth=0.8)
    eixo_datas(ax)
    ax.set_xlabel('Janela de rebalanceamento')
    ax.set_ylabel('Queda em relação ao topo anterior (%)')
    ax.set_title('Queda acumulada em relação ao topo anterior\n'
                 'Mede quanto o capital recuou do melhor momento já atingido',
                 fontsize=11, loc='left')
    ax.legend(loc='lower left', fontsize=9, frameon=True)
    fig.tight_layout()
    fig.savefig('figura_drawdown.png', dpi=200)
    plt.close(fig)
    for coluna, rotulo, _ in arranjo:
        capital = np.cumprod(1 + SERIES[coluna].values)
        queda = (capital / np.maximum.accumulate(capital) - 1) * 100
        print(f'  {rotulo:38s} pior queda {queda.min():.2f}%')


def figura_var_beta():
    bt = pd.read_csv('resultado_backtest_economicAI_KMEANS_EXPANSIVO.csv',
                     parse_dates=['Data_Rebalanceamento'])
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6.4), sharex=True)

    ax1.bar(bt['Data_Rebalanceamento'], bt['VaR_95'], width=18,
            color='#A93226', alpha=0.85)
    # O VaR é apurado sobre nocional fixo de R$ 100.000,00 (server.py), e não sobre o
    # capital acumulado da janela: os valores variam por mudança de volatilidade e de
    # cesta, nunca por crescimento do patrimônio.
    ax1.set_ylabel('VaR 95% em R$ por R$ 100.000\n(perda máxima diária esperada)')
    ax1.set_title('Balizas de risco apuradas pelo motor determinístico a cada rebalanceamento\n'
                  'Painel superior: perda diária máxima esperada em 95% dos casos, '
                  'sobre nocional fixo de R$ 100.000,00',
                  fontsize=11, loc='left')

    ax2.plot(bt['Data_Rebalanceamento'], bt['Beta'], color='#6C3483',
             linewidth=1.5, marker='o', markersize=2.6)
    ax2.axhline(1.0, color='black', linestyle='--', linewidth=1.2,
                label='Beta = 1: mesma sensibilidade do índice')
    ax2.axhline(bt['Beta'].mean(), color='#1F4E79', linestyle=':', linewidth=1.6,
                label=f'Beta médio da carteira = {bt["Beta"].mean():.3f}'.replace('.', ','))
    ax2.set_ylabel('Beta da carteira\n(sensibilidade ao índice)')
    ax2.set_xlabel('Janela de rebalanceamento')
    ax2.legend(loc='upper left', fontsize=9, frameon=True)
    eixo_datas(ax2)

    fig.tight_layout()
    fig.savefig('figura_var_beta.png', dpi=200)
    plt.close(fig)
    print(f'  VaR 95% médio R$ {bt["VaR_95"].mean():,.2f} | '
          f'Beta ex-ante médio {bt["Beta"].mean():.4f} | '
          f'abaixo de 1 em {(bt["Beta"] < 1).mean() * 100:.1f}% das janelas')


if __name__ == '__main__':
    print('figura_capital.png'); figura_capital()
    print('figura_drawdown.png'); figura_drawdown()
    print('figura_var_beta.png'); figura_var_beta()
