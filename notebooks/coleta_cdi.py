"""
Serie diaria do CDI (BCB/SGS 12) para usar como taxa livre de risco real.

O trabalho usava Selic fixa de 10,5% ao ano para todo o periodo. Num estudo que cobre
2012 a 2026 isso e uma premissa forte demais: a Selic foi a 14,25% em 2016, caiu a 2,00%
em 2020 e voltou acima de 14% em 2025. Com taxa constante, o Sharpe e o alfa de Jensen
ficam errados nas duas pontas — subestimados quando o juro real era baixo e
superestimados quando era alto.

A API do SGS aceita no maximo 10 anos por consulta em serie diaria, por isso a coleta e
fatiada. A serie 12 e a taxa CDI em % ao dia util.
"""

import json
import os
import urllib.request

import pandas as pd

SERIE = 12
DESTINO = '../mcp_servers/data_server/cdi_diario.csv'
FATIAS = [('01/01/2011', '31/12/2018'), ('01/01/2019', '06/06/2026')]
CABECALHO = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}


def baixar(data_inicial: str, data_final: str) -> list:
    url = (f'https://api.bcb.gov.br/dados/serie/bcdata.sgs.{SERIE}/dados'
           f'?formato=json&dataInicial={data_inicial}&dataFinal={data_final}')
    with urllib.request.urlopen(urllib.request.Request(url, headers=CABECALHO), timeout=60) as r:
        return json.load(r)


def coletar():
    registros = []
    for inicio, fim in FATIAS:
        parte = baixar(inicio, fim)
        print(f'{inicio} a {fim}: {len(parte)} pregoes')
        registros.extend(parte)

    df = (pd.DataFrame(registros)
          .assign(Date=lambda x: pd.to_datetime(x.data, format='%d/%m/%Y'),
                  CDI_Dia=lambda x: x.valor.astype(float) / 100)
          .drop(columns=['data', 'valor'])
          .drop_duplicates(subset=['Date'])
          .sort_values('Date')
          .reset_index(drop=True))

    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    df.to_csv(DESTINO, index=False)

    anual = (1 + df.set_index('Date').CDI_Dia).resample('YE').prod() - 1
    print(f"\n{len(df)} pregoes de {df.Date.min().date()} a {df.Date.max().date()}")
    print('CDI acumulado por ano:')
    for data, valor in anual.items():
        print(f'  {data.year}: {valor*100:5.2f}%')
    print(f"\nSalvo em '{DESTINO}'.")


if __name__ == '__main__':
    coletar()
