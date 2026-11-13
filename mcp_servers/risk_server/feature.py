import os
import pandas as pd
import numpy as np
from scipy.stats import skew, kurtosis
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings

# Suprime avisos do scikit-learn sobre vazamento de memória em Windows com KMeans
warnings.filterwarnings("ignore", category=UserWarning)

_RAIZ = os.path.dirname(os.path.abspath(__file__))
CAMINHO_FUNDAMENTOS = os.path.join(_RAIZ, '..', 'data_server', 'fundamentos_cvm.csv')
CAMINHO_COTACOES = os.path.join(_RAIZ, '..', 'data_server', 'cotacoes_b3_fechamentos.csv')
COLUNAS_FUNDAMENTO = ['ROE', 'Margem_Liquida', 'Crescimento_Receita',
                      'Crescimento_Lucro', 'Alavancagem']

# Demonstração mais velha que isso deixa de ser informação e vira ruído. O limite também
# protege o desenho: quando a CVM só publica uma reapresentação anos depois, o original
# some da base e a empresa fica sem fundamento no período — que é o correto, já que
# repetir o balanço antigo indefinidamente mascararia a ausência de informação.
MAX_DEFASAGEM_DIAS = 400

# Mínimo de observações para que a classificação de regime signifique algo. Abaixo disso
# os dois clusters apenas partem o ruído de um período curto ao meio.
#
# O valor é 200 e não 252 por uma restrição da base: o histórico de preços começa em
# 03/01/2011 e o primeiro rebalanceamento é em 06/01/2012, o que deixa 232 observações de
# feature (a diferenciação e a janela móvel de 21 dias consomem 22 pregões). Exigir 252
# descartaria a primeira janela do backtest sem ganho de comparabilidade — 232 contra 252
# observações não muda a posição dos centróides de forma relevante. Em contrapartida, vale
# registrar no texto que os primeiros rebalanceamentos têm os clusters ajustados sobre
# menos de um ano, e por isso são os menos comparáveis da série.
MIN_OBS_REGIME = 200

_CACHE_FUNDAMENTOS = None
_CACHE_COTACOES = None


def carregar_fundamentos() -> pd.DataFrame:
    """Lê a base point-in-time da CVM uma vez por processo."""
    global _CACHE_FUNDAMENTOS
    if _CACHE_FUNDAMENTOS is None:
        if not os.path.exists(CAMINHO_FUNDAMENTOS):
            _CACHE_FUNDAMENTOS = pd.DataFrame()
        else:
            _CACHE_FUNDAMENTOS = pd.read_csv(CAMINHO_FUNDAMENTOS,
                                             parse_dates=['DT_REFER', 'DT_RECEB'])
    return _CACHE_FUNDAMENTOS


def carregar_cotacoes() -> pd.DataFrame:
    """Histórico completo de preços, usado para ajustar o K-Means em janela expansiva."""
    global _CACHE_COTACOES
    if _CACHE_COTACOES is None:
        if not os.path.exists(CAMINHO_COTACOES):
            _CACHE_COTACOES = pd.DataFrame()
        else:
            _CACHE_COTACOES = (pd.read_csv(CAMINHO_COTACOES, parse_dates=['Date'])
                               .set_index('Date').sort_index())
    return _CACHE_COTACOES


def ajustar_clusters_regime(df_ml: pd.DataFrame) -> tuple:
    """
    Ajusta os dois clusters de regime e identifica qual deles é o turbulento.

    As features são padronizadas antes do ajuste. O K-Means minimiza distância
    euclidiana, e aqui as duas dimensões têm escalas muito diferentes: a volatilidade
    anualizada do Ibovespa fica entre 10% e 70%, enquanto a tendência anualizada do
    dólar varia em dezenas de pontos percentuais para os dois lados. Sem padronizar, a
    distância é dominada pelo dólar e o rótulo deixa de refletir a volatilidade que ele
    nomeia — chegava a classificar como Calmaria janelas com volatilidade acima do
    próprio centróide turbulento.

    Devolve (kmeans, scaler, indice_do_cluster_turbulento).
    """
    escala = StandardScaler().fit(df_ml)
    kmeans = KMeans(n_clusters=2, random_state=42, n_init=10).fit(escala.transform(df_ml))
    centroides = escala.inverse_transform(kmeans.cluster_centers_)
    return kmeans, escala, int(np.argmax(centroides[:, 0]))


class EngenhariaDeFeatures:
    def __init__(self, df_janela: pd.DataFrame):
        self.df = df_janela
        
        colunas_macro = ['^BVSP', 'USDBRL=X', 'IFIX.SA']
        self.colunas_presentes_macro = [col for col in colunas_macro if col in self.df.columns]
        
        self.df_acoes = self.df.drop(columns=self.colunas_presentes_macro, errors='ignore')
        self.df_macro = self.df[self.colunas_presentes_macro]

    def extrair_features_acoes(self) -> pd.DataFrame:
        features = []
        retornos_diarios = self.df_acoes.pct_change().dropna()
        
        for ativo in self.df_acoes.columns:
            preco_inicial = self.df_acoes[ativo].iloc[0]
            preco_final = self.df_acoes[ativo].iloc[-1]
            momentum = (preco_final / preco_inicial) - 1
            
            volatilidade = retornos_diarios[ativo].std() * np.sqrt(252)
            assimetria = skew(retornos_diarios[ativo].dropna())
            curtose = kurtosis(retornos_diarios[ativo].dropna())
            
            features.append({
                'Ativo': ativo,
                'Momentum_12M': float(round(momentum, 4)),
                'Volatilidade_Anual': float(round(volatilidade, 4)),
                'Skewness': float(round(assimetria, 4)),
                'Kurtosis': float(round(curtose, 4))
            })

        df_features = pd.DataFrame(features).set_index('Ativo')
        return df_features.join(self.extrair_fundamentos())

    def extrair_fundamentos(self) -> pd.DataFrame:
        """
        Último balanço de cada ativo que já era público no fim da janela.

        O corte é por DT_RECEB (data em que a CVM recebeu o documento), e não por
        DT_REFER: um trimestre encerrado em 31/03 só vira informação quando é entregue,
        em média 39 dias depois. Filtrar pelo fim do trimestre adiantaria ao agente um
        resultado que ninguém tinha, que é exatamente o look-ahead que este desenho evita.
        """
        base = carregar_fundamentos()
        if base.empty:
            return pd.DataFrame(index=self.df_acoes.columns)

        data_limite = self.df.index[-1]
        publicos = base[base.DT_RECEB <= data_limite]
        if publicos.empty:
            return pd.DataFrame(index=self.df_acoes.columns)

        ultimo = publicos.sort_values('DT_RECEB').groupby('Ticker').last()
        ultimo = ultimo[(data_limite - ultimo.DT_REFER).dt.days <= MAX_DEFASAGEM_DIAS]

        ultimo = ultimo.assign(Trimestre_Referencia=ultimo.DT_REFER.dt.strftime('%Y-%m'))
        colunas = COLUNAS_FUNDAMENTO + ['Trimestre_Referencia']
        return ultimo.reindex(self.df_acoes.columns)[colunas].round(4)

    @staticmethod
    def _features_regime(df_macro: pd.DataFrame) -> pd.DataFrame:
        retornos = df_macro.pct_change().dropna()
        return pd.DataFrame({
            'Volatilidade_BVSP': retornos['^BVSP'].rolling(window=21).std() * np.sqrt(252),
            'Tendencia_Dolar': retornos['USDBRL=X'].rolling(window=21).mean() * 252
        }).dropna()

    def detectar_regime_kmeans(self) -> dict:
        """
        Classifica o regime macro com os clusters ajustados em janela EXPANSIVA.

        O ajuste antes era feito só dentro da janela de 252 pregões. Isso quebrava a
        comparabilidade: os centróides eram recalculados a cada rebalanceamento sobre um
        único ano, então "Turbulência" significava apenas "volatilidade alta para os
        últimos 12 meses". Em 2017, um ano calmo, o cluster turbulento era um nível de
        volatilidade que em 2020 seria classificado como calmaria — e os agentes recebiam
        dois rótulos iguais para estados de mercado completamente diferentes.

        Agora os clusters são ajustados sobre todo o histórico ATÉ a data da janela. O
        rótulo passa a ser relativo a tudo o que já se observou, e não ao ano corrente, o
        que o torna comparável entre janelas. A janela segue expansiva e não centrada, de
        modo que nenhuma observação posterior à data de referência entra no ajuste: o
        desenho point-in-time é preservado.
        """
        if '^BVSP' not in self.df_macro.columns or 'USDBRL=X' not in self.df_macro.columns:
            return {"status": "erro", "mensagem": "Indicadores macro insuficientes para K-Means."}

        data_limite = self.df.index[-1]
        historico = carregar_cotacoes()
        colunas_ok = (not historico.empty
                      and {'^BVSP', 'USDBRL=X'}.issubset(historico.columns))
        if colunas_ok:
            base = historico.loc[:data_limite, ['^BVSP', 'USDBRL=X']]
        else:
            base = self.df_macro
        df_ml = self._features_regime(base)

        # Sem histórico suficiente para a expansiva, o rótulo seria pior que inútil:
        # seria incomparável e aparentaria ser comparável.
        if len(df_ml) < MIN_OBS_REGIME:
            return {"status": "erro",
                    "mensagem": f"Histórico insuficiente para regime comparável "
                                f"({len(df_ml)} obs., mínimo {MIN_OBS_REGIME})."}

        kmeans, escala, idx_turbulencia = ajustar_clusters_regime(df_ml)
        limiar = escala.inverse_transform(kmeans.cluster_centers_)[idx_turbulencia, 0]

        estado_hoje = df_ml.iloc[-1:]
        cluster_atual = kmeans.predict(escala.transform(estado_hoje))[0]

        nome_regime = "Turbulência (Alta Volatilidade/Risco Acumulado)" if cluster_atual == idx_turbulencia else "Calmaria (Baixa Volatilidade/Tendência de Alta)"

        return {
            "status": "sucesso",
            "regime_atual": nome_regime,
            "metricas_hoje": {
                "volatilidade_ibov_21d": float(round(estado_hoje['Volatilidade_BVSP'].iloc[0], 4)),
                "tendencia_dolar_anualizada": float(round(estado_hoje['Tendencia_Dolar'].iloc[0], 4))
            },
            # Auditoria do desenho point-in-time: quantas observações entraram no ajuste e
            # qual foi a última. A última nunca pode ser posterior à data da janela.
            "ajuste_clusters": {
                "observacoes": int(len(df_ml)),
                "primeira": str(df_ml.index[0].date()),
                "ultima": str(df_ml.index[-1].date()),
                "limiar_turbulencia_vol": float(round(limiar, 4))
            }
        }

    def gerar_contexto_llm(self) -> dict:
        features_acoes = self.extrair_features_acoes()
        regime = self.detectar_regime_kmeans()
        
        # Início da Lógica de Mascaramento (Anonimização)
        dicionario_features = features_acoes.to_dict(orient='index')
        features_anonimas = {}
        gabarito = {}
        
        for i, (ativo_real, stats) in enumerate(dicionario_features.items(), start=1):
            nome_anonimo = f"Ativo_{i}"
            gabarito[nome_anonimo] = ativo_real
            
            # Remove o nome real de dentro das métricas, se existir
            stats_copia = stats.copy()
            if 'Ativo' in stats_copia:
                stats_copia['Ativo'] = nome_anonimo

            # NaN não é JSON válido e chega ao agente como literal NaN, que o modelo lê como
            # texto. None vira null e deixa explícito que o balanço ainda não era público.
            stats_copia = {chave: (None if isinstance(valor, float) and np.isnan(valor) else valor)
                           for chave, valor in stats_copia.items()}

            features_anonimas[nome_anonimo] = stats_copia
            
        return {
            "cenario_macro": regime,
            "features_micro": features_anonimas,
            "gabarito_ativos": gabarito # Será capturado e ocultado pelo server.py
        }