"""Gráficos do dashboard, todos desenhados em Python com Plotly.

As funções que precisam de interação (zoom por mês, camadas, troca de instituto)
devolvem, junto com a figura, um dicionário de configuração calculado aqui em
Python. O HTML só aplica essas configurações via `Plotly.relayout/restyle/update`.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .config import (
    ANO,
    COR_FLAVIO,
    COR_GRADE,
    COR_GUIA_ESCURO,
    COR_LULA,
    COR_NULO,
    COR_TEXTO,
    FONTE,
    HOVER_BORDA,
    HOVER_FLAVIO,
    HOVER_FUNDO,
    HOVER_LULA,
    HOVER_TEXTO,
    MESES,
    MESES_CALENDARIO,
    MESES_NOME,
)
from .metrics import (
    ajustar_y,
    classificar,
    eixo_intencao,
    eixo_simples,
    faixa_agradavel,
    faixa_mensal,
    media_movel,
    passo_para,
    placar_mensal,
    tendencia_linear,
)

FORMATO_DATA = "%Y-%m-%d %H:%M"
MAX_ROTULOS = 14  # acima disso, o gráfico por instituto não escreve os valores nos pontos


def _rgba(cor_hex: str, alfa: float) -> str:
    h = cor_hex.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alfa})"


def _layout(altura: int, **extra: Any) -> dict[str, Any]:
    """Layout comum: fundo transparente e tons neutros (funcionam em tema claro e escuro)."""
    base: dict[str, Any] = {
        "height": altura,
        "font": {"family": FONTE, "size": 12, "color": COR_TEXTO},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "margin": {"l": 52, "r": 52, "t": 28, "b": 48},
        "showlegend": False,
        "hoverlabel": {
            "bgcolor": HOVER_FUNDO,
            "bordercolor": HOVER_BORDA,
            "font": {"family": FONTE, "color": HOVER_TEXTO, "size": 12},
        },
    }
    return base | extra


def _guia_x() -> dict[str, Any]:
    """Linha-guia vertical do hover unificado: bem fina, sólida e sutil (no lugar da pontilhada)."""
    return {
        "showspikes": True,
        "spikemode": "across",
        "spikesnap": "cursor",
        "spikedash": "solid",
        "spikethickness": 1,
        "spikecolor": COR_GUIA_ESCURO,
    }


def _validos(lula: pd.Series | list[float], flavio: pd.Series | list[float]) -> tuple[list[float], list[float]]:
    """Votos válidos (%) de Lula e de Flávio: cada um sobre a soma dos dois (Nulo/Branco/NS fora)."""
    v_l, v_f = [], []
    for a, b in zip(lula, flavio, strict=True):
        if pd.isna(a) or pd.isna(b) or (a + b) == 0:
            v_l.append(float("nan"))
            v_f.append(float("nan"))
        else:
            v_l.append(float(a) / float(a + b) * 100)
            v_f.append(float(b) / float(a + b) * 100)
    return v_l, v_f


def _caixa_validos(titulo: str, lula: float, flavio: float, *, y: float) -> dict[str, Any]:
    """Caixinha (annotation opaca) com os votos válidos, acima do gráfico e alinhada à direita."""
    return {
        "text": (
            f"<b>Votos válidos</b> · {titulo}<br>"
            f'<span style="color:{HOVER_LULA}"><b>Lula {lula:.1f}%</b></span>'
            "  ×  "
            f'<span style="color:{HOVER_FLAVIO}"><b>Flávio {flavio:.1f}%</b></span>'
        ),
        "xref": "paper",
        "yref": "paper",
        "x": 1,
        "y": y,
        "xanchor": "right",
        "yanchor": "bottom",
        "showarrow": False,
        "align": "right",
        "bgcolor": HOVER_FUNDO,
        "bordercolor": HOVER_BORDA,
        "borderwidth": 1,
        "borderpad": 6,
        "font": {"family": FONTE, "size": 11, "color": HOVER_TEXTO},
    }


def _serie(
    nome: str,
    x: list[str],
    y: pd.Series | list[float],
    cor: str,
    posicoes: list[str] | str,
    *,
    tracejado: bool = False,
    com_texto: bool = True,
    validos: list[float] | None = None,
) -> go.Scatter:
    valores = [None if pd.isna(v) else float(v) for v in y]
    if validos is None:
        extra: dict[str, Any] = {"hovertemplate": f"{nome}: %{{y:.1f}}%<extra></extra>"}
    else:  # mostra, junto da intenção, a taxa de votos válidos daquele ponto
        extra = {
            "customdata": [None if pd.isna(v) else float(v) for v in validos],
            "hovertemplate": f"{nome}: %{{y:.1f}}% · válidos %{{customdata:.1f}}%<extra></extra>",
        }
    return go.Scatter(
        x=x,
        y=valores,
        name=nome,
        mode="lines+markers+text" if com_texto else "lines+markers",
        text=[f"{v:.1f}" if v is not None else "" for v in valores],
        textposition=posicoes,
        textfont={"color": cor, "size": 11},
        line={"color": cor, "width": 2 if tracejado else 2.5, "dash": "dash" if tracejado else "solid"},
        marker={"size": 7 if tracejado else 9, "color": "white", "line": {"color": cor, "width": 2.5}},
        connectgaps=True,
        **extra,
    )


def _posicoes(lula: pd.Series, flavio: pd.Series) -> tuple[list[str], list[str]]:
    """Rótulo do maior valor acima do ponto e o do menor abaixo, para não se sobreporem."""
    acima = (lula >= flavio).tolist()
    return (
        ["top center" if a else "bottom center" for a in acima],
        ["bottom center" if a else "top center" for a in acima],
    )


# ---------------------------------------------------------------------------
# Médias mensais
# ---------------------------------------------------------------------------
def grafico_intencao_mensal(med: pd.DataFrame) -> go.Figure:
    """Lula e Flávio no eixo esquerdo (ampliado); Nulo/Branco/NS no eixo direito, mais embaixo."""
    eixo = eixo_intencao(pd.concat([med["lula"], med["flavio"]]), med["nulo"])
    rotulos = [f"{r.mes_nome}<br>{r.n_intencao} institutos" for r in med.itertuples()]
    pos_l, pos_f = _posicoes(med["lula"], med["flavio"])
    val_l, val_f = _validos(med["lula"], med["flavio"])

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(_serie("Lula", rotulos, med["lula"], COR_LULA, pos_l, validos=val_l), secondary_y=False)
    fig.add_trace(_serie("Flávio", rotulos, med["flavio"], COR_FLAVIO, pos_f, validos=val_f), secondary_y=False)
    fig.add_trace(
        _serie("Nulo/Branco/NS", rotulos, med["nulo"], COR_NULO, "bottom center", tracejado=True),
        secondary_y=True,
    )
    ultimo = med.iloc[-1]  # período mais recente: é o que a caixinha de votos válidos mostra
    caixa = _caixa_validos(str(ultimo["mes_nome"]), val_l[-1], val_f[-1], y=1.02)
    fig.update_layout(
        **_layout(380, hovermode="x unified", margin={"l": 52, "r": 52, "t": 64, "b": 48}, annotations=[caixa])
    )
    fig.update_xaxes(type="category", showgrid=False, tickangle=0, **_guia_x())
    fig.update_yaxes(
        range=[eixo.y_min, eixo.y_max],
        dtick=eixo.passo,
        ticksuffix="%",
        gridcolor=COR_GRADE,
        zeroline=False,
        secondary_y=False,
    )
    fig.update_yaxes(
        range=[0, eixo.y2_max],
        tickvals=list(eixo.y2_ticks),
        ticksuffix="%",
        showgrid=False,
        zeroline=False,
        secondary_y=True,
    )
    return fig


def grafico_rejeicao_mensal(med: pd.DataFrame) -> go.Figure:
    eixo = eixo_simples(pd.concat([med["rej_lula"], med["rej_flavio"]]))
    rotulos = [f"{r.mes_nome}<br>{r.n_rejeicao} institutos" for r in med.itertuples()]
    pos_l, pos_f = _posicoes(med["rej_lula"], med["rej_flavio"])

    fig = go.Figure()
    fig.add_trace(_serie("Rejeição Lula", rotulos, med["rej_lula"], COR_LULA, pos_l))
    fig.add_trace(_serie("Rejeição Flávio", rotulos, med["rej_flavio"], COR_FLAVIO, pos_f))
    fig.update_layout(**_layout(380, hovermode="x unified"))
    fig.update_xaxes(type="category", showgrid=False, tickangle=0, **_guia_x())
    fig.update_yaxes(
        range=[eixo.y_min, eixo.y_max],
        dtick=eixo.passo,
        ticksuffix="%",
        gridcolor=COR_GRADE,
        zeroline=False,
    )
    return fig


# ---------------------------------------------------------------------------
# Placar (visão "todos os meses")
# ---------------------------------------------------------------------------
def grafico_placar(df: pd.DataFrame, tipo: str) -> go.Figure:
    tabela = placar_mensal(df, tipo)  # type: ignore[arg-type]
    nomes = {
        "intencao": ("Lula à frente", "Flávio à frente"),
        "rejeicao": ("Lula mais rejeitado", "Flávio mais rejeitado"),
    }[tipo]
    fig = go.Figure()
    for coluna, nome, cor in (
        ("lula", nomes[0], COR_LULA),
        ("empate", "Empate técnico", COR_NULO),
        ("flavio", nomes[1], COR_FLAVIO),
    ):
        fig.add_trace(
            go.Bar(
                y=tabela["mes_nome"],
                x=tabela[coluna],
                name=nome,
                orientation="h",
                marker={"color": cor},
                text=[str(v) if v else "" for v in tabela[coluna]],
                textposition="inside",
                insidetextanchor="middle",
                textfont={"color": "white", "size": 12},
                hovertemplate=f"{nome}: %{{x}}<extra></extra>",
            )
        )
    fig.update_layout(
        **_layout(
            80 + 34 * len(tabela),
            barmode="stack",
            showlegend=True,
            legend={"orientation": "h", "y": 1.0, "yanchor": "bottom", "x": 0},
            margin={"l": 90, "r": 20, "t": 40, "b": 30},
        )
    )
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(showgrid=True, gridcolor=COR_GRADE, zeroline=False, dtick=5)
    return fig


# ---------------------------------------------------------------------------
# Evolução das pesquisas (dispersão + camadas + zoom)
# ---------------------------------------------------------------------------
def _segmentos(pesquisas: pd.DataFrame) -> tuple[list[Any], list[Any]]:
    """Segmentos verticais (Lula ↔ Flávio) separados por None, para desenhar em um único traço."""
    x: list[Any] = []
    y: list[Any] = []
    for r in pesquisas.itertuples():
        x += [r.data, r.data, None]
        y += [r.lula, r.flavio, None]
    return x, y


def _fmt(ts: pd.Timestamp) -> str:
    return ts.strftime(FORMATO_DATA)


def grafico_evolucao(df: pd.DataFrame) -> tuple[go.Figure, dict[str, Any]]:
    """Devolve a figura e a configuração (camadas e zoom por mês) usada pelo HTML."""
    fig = go.Figure()
    grupos: dict[str, list[int]] = {
        "faixaMensal": [],
        "conectores": [],
        "vantagem": [],
        "mediaMovel": [],
        "tendencia": [],
    }

    def adicionar(traco: go.Scatter, grupo: str | None = None) -> None:
        fig.add_trace(traco)
        if grupo:
            grupos[grupo].append(len(fig.data) - 1)

    pares = df[df["lula"].notna() & df["flavio"].notna()]
    series = (("lula", COR_LULA, "Lula"), ("flavio", COR_FLAVIO, "Flávio"))

    # 1) faixas mensais (mín–máx) — ficam atrás de tudo
    for coluna, cor, _ in series:
        for f in faixa_mensal(df, coluna).itertuples():
            adicionar(
                go.Scatter(
                    x=[f.inicio, f.fim, f.fim, f.inicio, f.inicio],
                    y=[f.minimo, f.minimo, f.maximo, f.maximo, f.minimo],
                    mode="lines",
                    fill="toself",
                    fillcolor=_rgba(cor, 0.10),
                    line={"color": _rgba(cor, 0.28), "width": 1},
                    hoverinfo="skip",
                    visible=False,
                ),
                "faixaMensal",
            )

    # 2) conectores Lula ↔ Flávio: cinza (padrão) ou coloridos pela vantagem
    x, y = _segmentos(pares)
    adicionar(
        go.Scatter(
            x=x,
            y=y,
            mode="lines",
            line={"color": "rgba(140,150,165,0.55)", "width": 1, "dash": "dot"},
            hoverinfo="skip",
        ),
        "conectores",
    )
    classes = pares.apply(lambda r: classificar(r["lula"], r["flavio"], r["margem_erro"]), axis=1)
    for chave, cor in (("lula", COR_LULA), ("flavio", COR_FLAVIO), ("empate", "rgba(140,150,165,0.55)")):
        x, y = _segmentos(pares[classes == chave])
        largura = 1.8 if chave != "empate" else 1.2
        adicionar(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                line={"color": cor, "width": largura, "dash": "dot"},
                hoverinfo="skip",
                visible=False,
            ),
            "vantagem",
        )

    # 3) média móvel de 3 pesquisas
    for coluna, cor, _ in series:
        mm = media_movel(df, coluna, 3)
        adicionar(
            go.Scatter(
                x=mm["data"],
                y=mm["valor"],
                mode="lines",
                line={"color": _rgba(cor, 0.9), "width": 2},
                hoverinfo="skip",
                visible=False,
            ),
            "mediaMovel",
        )

    # 4) tendência linear (mínimos quadrados) do 1º dia do ano ao fim do último mês
    x0 = pd.Timestamp(year=ANO, month=1, day=1)
    x1 = df["data"].max() + pd.offsets.MonthEnd(0)
    for coluna, cor, _ in series:
        a, b = tendencia_linear(df, coluna)
        adicionar(
            go.Scatter(
                x=[x0, x1],
                y=[a * x0.dayofyear + b, a * x1.dayofyear + b],
                mode="lines",
                line={"color": _rgba(cor, 0.6), "width": 2.5, "dash": "dash"},
                hoverinfo="skip",
            ),
            "tendencia",
        )

    # 5) as pesquisas (por cima de tudo)
    for coluna, cor, nome in series:
        v = df[df[coluna].notna()]
        fig.add_trace(
            go.Scatter(
                x=v["data"],
                y=v[coluna],
                mode="markers",
                name=nome,
                marker={"size": 8, "color": _rgba(cor, 0.85), "line": {"width": 1, "color": "white"}},
                customdata=list(zip(v["instituto"], v["data"].dt.strftime("%d/%m"), v["margem_erro"], strict=True)),
                hovertemplate=(
                    "<b>%{customdata[0]}</b> · %{customdata[1]}<br>"
                    f"{nome}: %{{y:.1f}}%<br>Margem de erro ±%{{customdata[2]}} pp<extra></extra>"
                ),
            )
        )

    # eixos: visão completa e zoom por mês, calculados aqui
    lf = pd.concat([df["lula"], df["flavio"]]).dropna()
    y_lo, y_hi = faixa_agradavel(lf, 1.5, 1.5)
    completo = {
        "xaxis.range": [_fmt(x0 - pd.Timedelta(days=2)), _fmt(x1 + pd.Timedelta(days=2))],
        "yaxis.range": [y_lo, y_hi],
        "yaxis.dtick": passo_para(y_hi - y_lo),
    }
    zoom: dict[str, Any] = {"Tudo": completo}
    largura_minima = pd.Timedelta(days=4)  # janela mínima, para meses com poucos dias de pesquisa (ex.: Out1)
    for mes in sorted(df["mes"].unique(), key=MESES.index):
        g = df[df["mes"] == mes]
        # O zoom de cada mês cobre as datas das próprias pesquisas do grupo, não o mês
        # civil inteiro — outubro é dividido em "Out1"/"Out2" (ver `mes_da_data`), e cada
        # metade deve ampliar só os dias que cobre.
        ini, fim = g["data"].min(), g["data"].max()
        if fim - ini < largura_minima:
            centro = ini + (fim - ini) / 2
            ini, fim = centro - largura_minima / 2, centro + largura_minima / 2
        lo, hi = ajustar_y(pd.concat([g["lula"], g["flavio"]]).dropna())
        zoom[MESES_NOME[mes]] = {
            "xaxis.range": [_fmt(ini - pd.Timedelta(days=1)), _fmt(fim + pd.Timedelta(days=1))],
            "yaxis.range": [lo, hi],
            "yaxis.dtick": 1 if hi - lo <= 8 else 2,
        }

    fig.update_layout(
        **_layout(
            520,
            hovermode="closest",
            dragmode="zoom",
            margin={"l": 52, "r": 24, "t": 16, "b": 48},
            xaxis={
                "type": "date",
                "range": completo["xaxis.range"],
                "tickformat": "%d/%m",
                "gridcolor": COR_GRADE,
                "zeroline": False,
            },
            yaxis={
                "range": completo["yaxis.range"],
                "dtick": completo["yaxis.dtick"],
                "ticksuffix": "%",
                "gridcolor": COR_GRADE,
                "zeroline": False,
            },
        )
    )
    config = {
        "camadas": {
            "tendencia": {"mostrar": grupos["tendencia"], "ocultar": []},
            "mediaMovel": {"mostrar": grupos["mediaMovel"], "ocultar": []},
            "vantagem": {"mostrar": grupos["vantagem"], "ocultar": grupos["conectores"]},
            "faixaMensal": {"mostrar": grupos["faixaMensal"], "ocultar": []},
        },
        "ativas": ["tendencia"],
        "zoom": zoom,
    }
    return fig, config


# ---------------------------------------------------------------------------
# Por instituto (um só gráfico; o HTML escolhe qual instituto mostrar)
# ---------------------------------------------------------------------------
TRACOS_POR_INSTITUTO = 5  # Lula, Flávio, Nulo (linha 1) + Rejeição Lula e Flávio (linha 2)


def lista_institutos(df: pd.DataFrame) -> list[str]:
    return sorted(df["instituto"].unique(), key=str.casefold)


def _rotulos(g: pd.DataFrame) -> list[str]:
    # Mês civil abreviado (não o código interno "mes", que em outubro vira "Out1"/"Out2").
    return [f"{d:%d/%m}<br>{MESES_CALENDARIO[d.month - 1]}" for d in g["data"]]


def grafico_instituto(df: pd.DataFrame) -> tuple[go.Figure, dict[str, Any]]:
    """Figura com os traços de todos os institutos (só o primeiro visível) e a config de cada um."""
    institutos = lista_institutos(df)
    rotulos_secao = [
        {
            "text": "INTENÇÃO DE VOTO",
            "xref": "paper",
            "yref": "paper",
            "x": 0,
            "y": 1.06,
            "showarrow": False,
            "font": {"size": 11, "color": COR_TEXTO},
            "xanchor": "left",
        },
        {
            "text": "REJEIÇÃO",
            "xref": "paper",
            "yref": "paper",
            "x": 0,
            "y": 0.40,
            "showarrow": False,
            "font": {"size": 11, "color": COR_TEXTO},
            "xanchor": "left",
        },
    ]
    fig = make_subplots(
        rows=2,
        cols=1,
        specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
        vertical_spacing=0.12,
        row_heights=[0.55, 0.45],
    )
    total = len(institutos) * TRACOS_POR_INSTITUTO
    config: dict[str, Any] = {}

    for i, nome in enumerate(institutos):
        g = df[df["instituto"] == nome]
        gi, gr = g[g["lula"].notna()], g[g["rej_lula"].notna()]
        visivel = i == 0
        texto = len(gi) <= MAX_ROTULOS
        rot_i, rot_r = _rotulos(gi), _rotulos(gr)
        pos_l, pos_f = _posicoes(gi["lula"], gi["flavio"])
        pos_rl, pos_rf = _posicoes(gr["rej_lula"], gr["rej_flavio"])
        val_l, val_f = _validos(gi["lula"], gi["flavio"])

        tracos = [
            (_serie("Lula", rot_i, gi["lula"], COR_LULA, pos_l, com_texto=texto, validos=val_l), 1, False),
            (_serie("Flávio", rot_i, gi["flavio"], COR_FLAVIO, pos_f, com_texto=texto, validos=val_f), 1, False),
            (
                _serie("Nulo/Branco/NS", rot_i, gi["nulo"], COR_NULO, "bottom center", tracejado=True, com_texto=texto),
                1,
                True,
            ),
            (_serie("Rejeição Lula", rot_r, gr["rej_lula"], COR_LULA, pos_rl, com_texto=texto), 2, False),
            (_serie("Rejeição Flávio", rot_r, gr["rej_flavio"], COR_FLAVIO, pos_rf, com_texto=texto), 2, False),
        ]
        for traco, linha, secundario in tracos:
            traco.visible = visivel
            fig.add_trace(traco, row=linha, col=1, secondary_y=secundario if linha == 1 else None)

        mascara = [False] * total
        for k in range(TRACOS_POR_INSTITUTO):
            mascara[i * TRACOS_POR_INSTITUTO + k] = True

        ei = eixo_intencao(pd.concat([gi["lula"], gi["flavio"]]), gi["nulo"])
        layout: dict[str, Any] = {
            "yaxis.range": [ei.y_min, ei.y_max],
            "yaxis.dtick": ei.passo,
            "yaxis2.range": [0, ei.y2_max],
            "yaxis2.tickvals": list(ei.y2_ticks),
        }
        ultima = gi.iloc[-1]  # pesquisa mais recente do instituto: a caixinha mostra os válidos dela
        caixa = _caixa_validos(f"última pesquisa ({ultima['data']:%d/%m})", val_l[-1], val_f[-1], y=1.0)
        rotulos_secao_i = [*rotulos_secao, caixa]
        if len(gr):
            er = eixo_simples(pd.concat([gr["rej_lula"], gr["rej_flavio"]]))
            layout |= {"yaxis3.range": [er.y_min, er.y_max], "yaxis3.dtick": er.passo, "annotations": rotulos_secao_i}
        else:
            layout |= {
                "yaxis3.range": [40, 52],
                "yaxis3.dtick": 2,
                "annotations": [
                    *rotulos_secao_i,
                    {
                        "text": "Instituto sem dados de rejeição",
                        "xref": "paper",
                        "yref": "paper",
                        "x": 0.5,
                        "y": 0.17,
                        "showarrow": False,
                        "font": {"size": 14, "color": COR_TEXTO},
                    },
                ],
            }
        config[nome] = {"visible": mascara, "layout": layout}

    inicial = config[institutos[0]]["layout"]
    fig.update_layout(**_layout(660, hovermode="x unified", margin={"l": 52, "r": 52, "t": 56, "b": 40}))
    fig.update_xaxes(type="category", showgrid=False, tickangle=0, **_guia_x())
    fig.update_yaxes(ticksuffix="%", gridcolor=COR_GRADE, zeroline=False)
    fig.update_yaxes(showgrid=False, row=1, col=1, secondary_y=True)
    fig.update_layout(
        yaxis={"range": inicial["yaxis.range"], "dtick": inicial["yaxis.dtick"]},
        yaxis2={"range": inicial["yaxis2.range"], "tickvals": inicial["yaxis2.tickvals"]},
        yaxis3={"range": inicial["yaxis3.range"], "dtick": inicial["yaxis3.dtick"]},
        annotations=inicial["annotations"],
    )
    return fig, config
