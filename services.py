import yfinance as yf
import pandas as pd
import plotly.express as px
import time
from datetime import date, timedelta

_cache_precos = {}
_cache_historicos = {}
CACHE_SEGUNDOS = 600

URL_TESOURO = ("https://www.tesourotransparente.gov.br/ckan/dataset/"
               "df56aa42-484a-4a59-8184-7676580c81e3/resource/"
               "796d2059-14e9-44e3-80c9-2d9e30b405c1/download/precotaxatesourodireto.csv")
_cache_tesouro = {"df": None, "momento": 0.0}
_cache_cdi = {}
CACHE_TESOURO_SEGUNDOS = 60 * 60 * 12

def preco_atual(ticker):
    agora = time.time()

    if ticker in _cache_precos:
        preco, momento = _cache_precos[ticker]
        if agora - momento < CACHE_SEGUNDOS:
            return preco

    try:
        historico = yf.Ticker(ticker).history(period="1d")
        if historico.empty:
            preco = None
        else:
            preco = float(historico["Close"].iloc[-1])
    except Exception:
        preco = None

    _cache_precos[ticker] = (preco, agora)
    return preco

def historico_precos(ticker, inicio):
    agora = time.time()
    chave = (ticker, inicio)

    if chave in _cache_historicos:
        precos, momento = _cache_historicos[chave]
        if agora - momento < CACHE_SEGUNDOS:
            return precos

    precos = yf.Ticker(ticker).history(start=inicio)["Close"]
    precos.index = precos.index.date

    _cache_historicos[chave] = (precos, agora)
    return precos

def tabela_tesouro():
    agora = time.time()
    df_antigo = _cache_tesouro["df"]
    if df_antigo is not None and agora - _cache_tesouro["momento"] < CACHE_TESOURO_SEGUNDOS:
        return df_antigo

    try:
        df = pd.read_csv(URL_TESOURO, sep=";", decimal=",")
        df["Data Base"] = pd.to_datetime(df["Data Base"], format="%d/%m/%Y")
        df["Data Vencimento"] = pd.to_datetime(df["Data Vencimento"], format="%d/%m/%Y")
        df["titulo"] = df["Tipo Titulo"] + " " + df["Data Vencimento"].dt.year.astype(str)
    except Exception:
        return df_antigo  # download falhou: melhor a tabela velha do que nenhuma

    _cache_tesouro["df"] = df
    _cache_tesouro["momento"] = agora
    return df

def serie_tesouro(nome_titulo, inicio=None):
    df = tabela_tesouro()
    if df is None:
        return None
    linhas = df[(df["titulo"] == nome_titulo) & (df["PU Venda Manha"] > 0)]
    if linhas.empty:
        return None
    serie = linhas.groupby("Data Base")["PU Venda Manha"].last().sort_index()
    serie.index = serie.index.date
    if inicio is not None:
        serie = serie[serie.index >= inicio]
    return serie

def preco_tesouro(nome_titulo):
    serie = serie_tesouro(nome_titulo)
    if serie is None or serie.empty:
        return None
    return float(serie.iloc[-1])

def calcular_posicao(ativo):
    qtd_comprada = 0
    qtd_vendida = 0
    total_gasto = 0
    for t in ativo.transacoes:
        if t.tipo == "compra":
            qtd_comprada += t.quantidade
            total_gasto += t.quantidade * t.preco_unitario
        else:
            qtd_vendida += t.quantidade

    quantidade = qtd_comprada - qtd_vendida
    if quantidade <= 0:
        return None

    preco_medio = total_gasto / qtd_comprada
    custo = quantidade * preco_medio
    proventos = sum(p.valor for p in ativo.proventos)
    if ativo.tipo == "Tesouro Direto":
        cotacao = preco_tesouro(ativo.ticker)
    else:
        cotacao = preco_atual(ativo.ticker)

    posicao = {
        "ativo": ativo,
        "quantidade": quantidade,
        "preco_medio": preco_medio,
        "custo": custo,
        "proventos": proventos,
        "cotacao": cotacao,
        "valor_atual": None,
        "resultado": None,
        "rentabilidade": None,
    }
    if cotacao is not None:
        posicao["valor_atual"] = quantidade * cotacao
        posicao["resultado"] = posicao["valor_atual"] - custo + proventos
        posicao["rentabilidade"] = posicao["resultado"] / custo * 100
    return posicao

def serie_valor_ativo(ativo):
    inicio = min(t.data for t in ativo.transacoes)
    if ativo.tipo == "Tesouro Direto":
        precos = serie_tesouro(ativo.ticker, inicio)
    else:
        precos = historico_precos(ativo.ticker, inicio)
    if precos is None or precos.empty:
        return None

    quantidades = pd.Series(0.0, index=precos.index)
    for t in ativo.transacoes:
        sinal = 1 if t.tipo == "compra" else -1
        quantidades[quantidades.index >= t.data] += sinal * t.quantidade

    return precos * quantidades


def historico_carteira(ativos):
    series = {}
    for ativo in ativos:
        if not ativo.transacoes:
            continue
        serie = serie_valor_ativo(ativo)
        if serie is not None:
            series[ativo.ticker] = serie
    if not series:
        return None
    df = pd.DataFrame(series)
    return df.ffill().fillna(0).sum(axis=1)


def serie_cdi(inicio):
    agora = time.time()
    if inicio in _cache_cdi:
        fator, momento = _cache_cdi[inicio]
        if agora - momento < CACHE_TESOURO_SEGUNDOS:
            return fator

    try:
        url = ("https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados"
               "?formato=json&dataInicial=" + inicio.strftime("%d/%m/%Y"))
        df = pd.read_json(url)
        df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
        df["valor"] = pd.to_numeric(df["valor"])
        fator = (1 + df.set_index("data")["valor"] / 100).cumprod()
        fator.index = fator.index.date
    except Exception:
        return None

    _cache_cdi[inicio] = (fator, agora)
    return fator


def serie_cota(ativos):
    carteira = historico_carteira(ativos)
    if carteira is None or carteira.empty:
        return None

    # fluxos externos por dia: compras entram (+), vendas saem (-),
    # proventos saem para o bolso (-) e por isso contam como rendimento
    fluxos = {}
    for ativo in ativos:
        for t in ativo.transacoes:
            sinal = 1 if t.tipo == "compra" else -1
            fluxos[t.data] = fluxos.get(t.data, 0) + sinal * t.quantidade * t.preco_unitario
        for p in ativo.proventos:
            fluxos[p.data] = fluxos.get(p.data, 0) - p.valor

    cotas = []
    n_cotas = None
    valor_cota = 1.0
    for dia, valor in carteira.items():
        fluxo = fluxos.get(dia, 0)
        if n_cotas is None:
            n_cotas = valor  # primeiro dia: tudo é aporte, cota vale 1
        else:
            valor_sem_fluxo = valor - fluxo
            if n_cotas > 0:
                valor_cota = valor_sem_fluxo / n_cotas
            if fluxo != 0 and valor_cota > 0:
                n_cotas += fluxo / valor_cota
        cotas.append(valor_cota)

    return pd.Series(cotas, index=carteira.index)


def comparacao_completa(ativos):
    cota = serie_cota(ativos)
    if cota is None or cota.empty:
        return None

    colunas = {"Carteira": cota}
    ibov = historico_precos("^BVSP", cota.index[0])
    if ibov is not None and not ibov.empty:
        colunas["IBOV"] = ibov
    cdi = serie_cdi(cota.index[0])
    if cdi is not None and not cdi.empty:
        colunas["CDI"] = cdi

    df = pd.DataFrame(colunas).dropna()
    if df.empty:
        return None
    return df / df.iloc[0] * 100

def grafico_alocacao(posicoes):
    tickers = [p["ativo"].ticker for p in posicoes if p["valor_atual"]]
    valores = [p["valor_atual"] for p in posicoes if p["valor_atual"]]
    if not valores:
        return None
    fig = px.pie(names=tickers, values=valores, title="Alocação da carteira")
    return fig.to_html(full_html=False, include_plotlyjs="cdn")


def grafico_evolucao(comparacao):
    if comparacao is None:
        return None
    fig = px.line(comparacao, title="Carteira x Benchmarks (base 100, método de cotas)")
    return fig.to_html(full_html=False, include_plotlyjs=False)


def grafico_patrimonio(ativos):
    carteira = historico_carteira(ativos)
    if carteira is None or carteira.empty:
        return None
    fig = px.area(carteira, title="Evolução do patrimônio (R$)")
    fig.update_layout(showlegend=False)
    return fig.to_html(full_html=False, include_plotlyjs=False)


def calcular_rsi(precos, periodo=14):
    variacao = precos.diff()
    ganho = variacao.clip(lower=0).rolling(periodo).mean()
    perda = (-variacao.clip(upper=0)).rolling(periodo).mean()
    return 100 - 100 / (1 + ganho / perda)


def graficos_ativo(ativo):
    inicio = date.today() - timedelta(days=365)
    if ativo.tipo == "Tesouro Direto":
        precos = serie_tesouro(ativo.ticker, inicio)
    else:
        precos = historico_precos(ativo.ticker, inicio)
    if precos is None or precos.empty:
        return None

    df = pd.DataFrame({
        "Preço": precos,
        "Média 20 dias": precos.rolling(20).mean(),
        "Média 50 dias": precos.rolling(50).mean(),
    })
    fig_precos = px.line(df, title=f"{ativo.ticker} — preço e médias móveis (1 ano)")

    rsi = calcular_rsi(precos)
    fig_rsi = px.line(rsi, title="RSI — Índice de Força Relativa (14 dias)")
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
    fig_rsi.update_yaxes(range=[0, 100])
    fig_rsi.update_layout(showlegend=False)

    return (fig_precos.to_html(full_html=False, include_plotlyjs="cdn"),
            fig_rsi.to_html(full_html=False, include_plotlyjs=False))


def metricas_risco(serie):
    retornos = serie.pct_change().dropna()
    if len(retornos) < 2:
        return None
    topo = serie / serie.cummax()
    return {
        "retorno": float((serie.iloc[-1] / serie.iloc[0] - 1) * 100),
        "volatilidade": float(retornos.std() * (252 ** 0.5) * 100),
        "drawdown": float((1 - topo.min()) * 100),
    }


def analise_risco(ativos):
    linhas = []
    retornos = {}
    for ativo in ativos:
        if not ativo.transacoes:
            continue
        inicio = min(t.data for t in ativo.transacoes)
        if ativo.tipo == "Tesouro Direto":
            precos = serie_tesouro(ativo.ticker, inicio)
        else:
            precos = historico_precos(ativo.ticker, inicio)
        if precos is None or precos.empty:
            continue
        metricas = metricas_risco(precos)
        if metricas is None:
            continue
        metricas["ticker"] = ativo.ticker
        linhas.append(metricas)
        retornos[ativo.ticker] = precos.pct_change()

    cota = serie_cota(ativos)
    if cota is not None and not cota.empty:
        metricas = metricas_risco(cota)
        if metricas is not None:
            metricas["ticker"] = "CARTEIRA (cotas)"
            linhas.insert(0, metricas)

    correlacao = None
    if len(retornos) >= 2:
        correlacao = pd.DataFrame(retornos).corr().round(2)
    return linhas, correlacao

