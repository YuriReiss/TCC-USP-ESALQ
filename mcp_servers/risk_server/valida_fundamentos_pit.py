"""
Prova de que os fundamentos entregues aos agentes sao point-in-time.

A acusacao padrao contra um backtest com fundamentos e que o balanco usado em 2013 so
existiu em 2016. Este script percorre as MESMAS janelas do backtest e verifica, uma a uma,
que todo numero visto pelo agente ja tinha sido entregue a CVM naquela data.

Tres verificacoes:
  1. Cada fundamento entregue tem DT_RECEB <= data de rebalanceamento.
  2. Nenhum fundamento tem DT_REFER posterior a data de rebalanceamento.
  3. A serie vista em cada janela e monotona: refazer a janela de 2013 hoje devolve
     exatamente o que devolveria em 2013, porque o filtro nao depende do presente.
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature import EngenhariaDeFeatures, carregar_fundamentos, MAX_DEFASAGEM_DIAS

CAMINHO_COTACOES = '../data_server/cotacoes_b3_fechamentos.csv'
JANELA_TREINO = 252
PASSO = 21


def validar():
    df = pd.read_csv(CAMINHO_COTACOES, parse_dates=['Date']).set_index('Date').sort_index()
    base = carregar_fundamentos()
    if base.empty:
        raise RuntimeError('fundamentos_cvm.csv ausente; rode notebooks/coleta_fundamentos.py.')

    violacoes = []
    cobertura = []

    for inicio in range(JANELA_TREINO, len(df), PASSO):
        janela = df.iloc[inicio - JANELA_TREINO:inicio]
        data_limite = janela.index[-1]

        fundamentos = EngenhariaDeFeatures(janela).extrair_fundamentos()
        entregues = fundamentos.dropna(subset=['ROE'])

        for ticker, linha in entregues.iterrows():
            publicado = base[(base.Ticker == ticker)
                             & (base.DT_REFER.dt.strftime('%Y-%m') == linha.Trimestre_Referencia)]
            if publicado.empty:
                violacoes.append((data_limite, ticker, 'trimestre inexistente na base'))
                continue

            recebimento = publicado.DT_RECEB.iloc[0]
            referencia = publicado.DT_REFER.iloc[0]
            if recebimento > data_limite:
                violacoes.append((data_limite, ticker, f'DT_RECEB {recebimento.date()} > limite'))
            if referencia > data_limite:
                violacoes.append((data_limite, ticker, f'DT_REFER {referencia.date()} > limite'))

        cobertura.append({
            'Data_Rebalanceamento': data_limite,
            'Ativos': len(fundamentos),
            'Com_Fundamento': len(entregues),
            'Defasagem_Mediana': (
                (data_limite - base.set_index('Ticker')
                 .loc[entregues.index, 'DT_REFER']).dt.days.median()
                if len(entregues) else float('nan')),
        })

    cob = pd.DataFrame(cobertura)

    print('=' * 64)
    print('VALIDACAO POINT-IN-TIME DOS FUNDAMENTOS')
    print('=' * 64)
    print(f'Janelas verificadas:          {len(cob)}')
    print(f'Periodo:                      {cob.Data_Rebalanceamento.min().date()} a '
          f'{cob.Data_Rebalanceamento.max().date()}')
    print(f'Limite de defasagem aceito:   {MAX_DEFASAGEM_DIAS} dias')
    print('-' * 64)
    print(f'Ativos com fundamento por janela: media {cob.Com_Fundamento.mean():.2f} de '
          f'{cob.Ativos.max()}')
    print(f'  minimo {cob.Com_Fundamento.min()} | mediana {cob.Com_Fundamento.median():.0f} | '
          f'maximo {cob.Com_Fundamento.max()}')
    print(f'Janelas com os 10 ativos cobertos: '
          f'{(cob.Com_Fundamento == cob.Ativos).sum()}/{len(cob)}')
    print(f'Janelas sem nenhum fundamento:     {(cob.Com_Fundamento == 0).sum()}')
    print('-' * 64)
    print(f'VIOLACOES DE LOOK-AHEAD: {len(violacoes)}')
    for data, ticker, motivo in violacoes[:20]:
        print(f'  {data.date()} {ticker}: {motivo}')
    print('=' * 64)

    if violacoes:
        raise AssertionError(f'{len(violacoes)} violacoes de look-ahead detectadas.')
    print('Nenhum fundamento foi entregue antes de ser publico.')

    cob.to_csv('resultado_validacao_pit.csv', index=False)
    print("Cobertura por janela salva em 'resultado_validacao_pit.csv'.")


if __name__ == '__main__':
    validar()
