import yfinance as yf
import pandas as pd
import plotly.express as px
import time

_cache_precos = {}
_cache_historicos = {}
CACHE_SEGUNDOS = 600

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
    cotacao = preco_atual(ativo.ticker)

    posicao = {
        "ativo": ativo,
        "quantidade": quantidade,
        "preco_medio": preco_medio,
        "custo": custo,
        "cotacao": cotacao,
        "valor_atual": None,
        "resultado": None,
        "rentabilidade": None,
    }
    if cotacao is not None:
        posicao["valor_atual"] = quantidade * cotacao
        posicao["resultado"] = posicao["valor_atual"] - custo
        posicao["rentabilidade"] = posicao["resultado"] / custo * 100
    return posicao

def serie_valor_ativo(ativo):
    inicio = min(t.data for t in ativo.transacoes)
    precos = historico_precos(ativo.ticker, inicio)
    if precos.empty:
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


def comparar_com_ibov(carteira):
    ibov = historico_precos("^BVSP", carteira.index[0])
    df = pd.DataFrame({"Carteira": carteira, "IBOV": ibov}).dropna()
    return df / df.iloc[0] * 100

def grafico_alocacao(posicoes):
    tickers = [p["ativo"].ticker for p in posicoes if p["valor_atual"]]
    valores = [p["valor_atual"] for p in posicoes if p["valor_atual"]]
    if not valores:
        return None
    fig = px.pie(names=tickers, values=valores, title="Alocação da carteira")
    return fig.to_html(full_html=False, include_plotlyjs="cdn")


def grafico_evolucao(ativos):
    carteira = historico_carteira(ativos)
    if carteira is None:
        return None
    comparacao = comparar_com_ibov(carteira)
    fig = px.line(comparacao, title="Carteira x IBOV (base 100)")
    return fig.to_html(full_html=False, include_plotlyjs=False)

