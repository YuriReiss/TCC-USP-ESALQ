# -*- coding: utf-8 -*-
"""
Estilo unico das figuras da dissertacao.

A Tabela 8 do Manual de Normas do MBA USP/ESALQ exige graficos sem linhas de grade e
sem preenchimento de fundo. Os estilos 'seaborn-v0_8-whitegrid' e '-darkgrid' usados
antes violavam os dois pontos.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PARAMETROS = {
    'font.family': 'Arial',
    'font.size': 10,
    'axes.unicode_minus': False,
    'axes.grid': False,
    'axes.facecolor': 'white',
    'axes.edgecolor': '#333333',
    'axes.linewidth': 0.8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.facecolor': 'white',
    'savefig.facecolor': 'white',
    'legend.frameon': False,
    'xtick.direction': 'out',
    'ytick.direction': 'out',
}


def aplicar():
    plt.rcParams.update(matplotlib.rcParamsDefault)
    plt.rcParams.update(PARAMETROS)
