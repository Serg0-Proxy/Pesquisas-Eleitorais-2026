"""Gera o site estático (HTML + CSV) a partir de data/pesquisas.csv."""

from __future__ import annotations

import base64
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import plotly
import plotly.graph_objects as go
from jinja2 import Environment, PackageLoader, select_autoescape

from .charts import (
    grafico_evolucao,
    grafico_instituto,
    grafico_intencao_mensal,
    grafico_placar,
    grafico_rejeicao_mensal,
    lista_institutos,
)
from .config import (
    COR_GUIA_CLARO,
    COR_GUIA_ESCURO,
    CSV_PADRAO,
    PERIODO_EXIBIDO,
    REPO_URL_PADRAO,
    SAIDA_PADRAO,
)
from .data import carregar
from .metrics import classificar, medias_mensais, medias_periodos, placar_periodos

CONFIG_ESTATICO = {"displayModeBar": False, "responsive": True}
CONFIG_EVOLUCAO = {
    "displaylogo": False,
    "responsive": True,
    "scrollZoom": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
}
BADGES = {
    "lula": {"classe": "badge-lula", "texto": "Lula"},
    "flavio": {"classe": "badge-flavio", "texto": "Flávio"},
    "empate": {"classe": "badge-tie", "texto": "Empate técnico"},
}


# ---------------------------------------------------------------------------
# Formatação
# ---------------------------------------------------------------------------
def _num(v: float | None) -> str | None:
    """Mostra 46.0 como '46.0' e valores ausentes como None."""
    return None if v is None or pd.isna(v) else f"{v:.1f}"


def _pct(v: float) -> str:
    return "—" if pd.isna(v) else f"{v:.1f}%"


def _variacao(atual: float, anterior: float | None) -> str:
    if anterior is None or pd.isna(anterior):
        return ""
    d = atual - anterior
    if abs(d) < 0.05:
        return "= vs. mês anterior"
    return f"{'▲' if d > 0 else '▼'} {abs(d):.1f} pp vs. mês anterior"


def _figura_html(fig: go.Figure, div_id: str, config: dict[str, Any]) -> str:
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=div_id, config=config)


def _tag_plotly(offline: bool) -> str:
    if offline:  # arquivo autossuficiente (~4,5 MB)
        return f"<script>{plotly.offline.get_plotlyjs()}</script>"
    versao = plotly.offline.get_plotlyjs_version()
    return f'<script src="https://cdn.plot.ly/plotly-{versao}.min.js" charset="utf-8"></script>'


# ---------------------------------------------------------------------------
# Blocos de contexto para o template
# ---------------------------------------------------------------------------
def _ultimo_mes_com_dado(med: pd.DataFrame, coluna: str) -> tuple[pd.Series | None, pd.Series | None]:
    """O mês mais recente em que `coluna` foi preenchida, e o mês imediatamente anterior a ele.

    Usado para os cards: um mês novo pode começar só com pesquisas sem rejeição (ou, em
    tese, sem intenção), e nesse caso o card deve mostrar a última média que existe, não
    "—" — a comparação ("vs. mês anterior") também usa o mês anterior a esse, não o último
    mês do calendário.
    """
    disponiveis = med.index[med[coluna].notna()]
    if disponiveis.empty:
        return None, None
    pos = med.index.get_loc(disponiveis[-1])
    anterior = med.iloc[pos - 1] if pos > 0 else None
    return med.iloc[pos], anterior


def _kpis(med: pd.DataFrame, tipo: str) -> list[dict[str, str]]:
    col_l, col_f = ("lula", "flavio") if tipo == "intencao" else ("rej_lula", "rej_flavio")
    prefixo = "" if tipo == "intencao" else "Rej. "
    ult, ant = _ultimo_mes_com_dado(med, col_l)
    if ult is None:
        rotulo = "Nenhuma pesquisa" if tipo == "intencao" else "Nenhuma pesquisa com rejeição"
        vazio = {"dot": "bg-nulo", "rotulo": rotulo, "valor": "—", "classe": "", "sub": ""}
        return [vazio, vazio, vazio]
    dif = abs(ult[col_l] - ult[col_f])
    if dif < 1e-9:
        quem = "Empatados"
    elif ult[col_l] > ult[col_f]:
        quem = "Lula à frente" if tipo == "intencao" else "Lula mais rejeitado"
    else:
        quem = "Flávio à frente" if tipo == "intencao" else "Flávio mais rejeitado"
    return [
        {
            "dot": "bg-lula",
            "rotulo": f"{prefixo}Lula — média {ult['mes_nome']}",
            "valor": _pct(ult[col_l]),
            "classe": "lula-c",
            "sub": _variacao(ult[col_l], None if ant is None else ant[col_l]),
        },
        {
            "dot": "bg-flavio",
            "rotulo": f"{prefixo}Flávio — média {ult['mes_nome']}",
            "valor": _pct(ult[col_f]),
            "classe": "flavio-c",
            "sub": _variacao(ult[col_f], None if ant is None else ant[col_f]),
        },
        {
            "dot": "bg-nulo",
            "rotulo": f"Diferença ({ult['mes_nome']})",
            "valor": f"{dif:.1f} pp",
            "classe": "",
            "sub": quem,
        },
    ]


def _tabelas(df: pd.DataFrame, med: pd.DataFrame) -> list[dict[str, Any]]:
    tabelas = []
    for m in med.itertuples():
        linhas = []
        for r in df[df["periodo"] == m.mes].itertuples():
            tem_voto = pd.notna(r.lula) and pd.notna(r.flavio)
            linhas.append(
                {
                    "data": f"{r.data:%d/%m}",
                    "instituto": r.instituto,
                    "lula": _num(r.lula),
                    "lula_w": 0 if pd.isna(r.lula) else round(r.lula / 60 * 70),
                    "flavio": _num(r.flavio),
                    "flavio_w": 0 if pd.isna(r.flavio) else round(r.flavio / 60 * 70),
                    "nulo": _num(r.nulo),
                    "rej_lula": _num(r.rej_lula),
                    "rej_flavio": _num(r.rej_flavio),
                    "erro": f"{r.margem_erro:g}",
                    "badge": BADGES[classificar(r.lula, r.flavio, r.margem_erro)] if tem_voto else None,
                }
            )
        tabelas.append(
            {
                "mes_nome": m.mes_nome,
                "n": m.n,
                "linhas": linhas,
                "media": {c: _num(getattr(m, c)) for c in ("lula", "flavio", "nulo", "rej_lula", "rej_flavio")},
            }
        )
    return tabelas


def _institutos(df: pd.DataFrame) -> list[dict[str, Any]]:
    saida = []
    for nome in lista_institutos(df):
        g = df[df["instituto"] == nome]
        kpis: list[dict[str, str]] = []
        for _tipo, col_l, col_f, pref in (("voto", "lula", "flavio", ""), ("rej", "rej_lula", "rej_flavio", "Rej. ")):
            v = g[g[col_l].notna()]
            if v.empty:
                continue
            u = v.iloc[-1]
            d = f"{u['data']:%d/%m}"
            kpis += [
                {"dot": "bg-lula", "rotulo": f"{pref}Lula ({d})", "valor": _pct(u[col_l]), "classe": "lula-c"},
                {"dot": "bg-flavio", "rotulo": f"{pref}Flávio ({d})", "valor": _pct(u[col_f]), "classe": "flavio-c"},
                {"dot": "bg-nulo", "rotulo": "Diferença", "valor": f"{abs(u[col_l] - u[col_f]):.1f} pp", "classe": ""},
            ]
        saida.append({"nome": nome, "kpis": kpis})
    return saida


def _data_uri_csv(texto: str) -> str:
    """CSV embutido no próprio HTML (data URI): o botão baixa o arquivo direto, mesmo com o
    HTML aberto sozinho do computador, sem depender da pasta data/ ao lado dele."""
    return "data:text/csv;charset=utf-8;base64," + base64.b64encode(texto.encode("utf-8")).decode("ascii")


# ---------------------------------------------------------------------------
# Construção
# ---------------------------------------------------------------------------
def construir_site(
    csv: str | Path = CSV_PADRAO,
    saida: str | Path = SAIDA_PADRAO,
    *,
    offline: bool = False,
    repo_url: str = REPO_URL_PADRAO,
) -> Path:
    """Lê e valida o CSV, calcula tudo em Python e grava `<saida>/index.html`."""
    csv, saida = Path(csv), Path(saida)
    df = carregar(csv)  # lança DadosInvalidos se houver problema
    med = medias_mensais(df)  # KPIs, tabelas e zoom: outubro em Out1/Out2
    med_geral = medias_periodos(df)  # médias e placar: outubro em quatro semanas (Out 1 a Out 4)

    fig_evolucao, evo_cfg = grafico_evolucao(df)
    fig_instituto, inst_cfg = grafico_instituto(df)
    ultima = df.iloc[-1]

    contexto = {
        "plotly_js": _tag_plotly(offline),
        "repo_url": repo_url,
        "periodo": PERIODO_EXIBIDO,
        "n_pesquisas": len(df),
        "n_institutos": df["instituto"].nunique(),
        "ultima": {"data": f"{ultima['data']:%d/%m}", "instituto": ultima["instituto"]},
        "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "kpis_intencao": _kpis(med, "intencao"),
        "kpis_rejeicao": _kpis(med, "rejeicao"),
        "placar_intencao": placar_periodos(df, "intencao").to_dict("records"),
        "placar_rejeicao": placar_periodos(df, "rejeicao").to_dict("records"),
        "fig_intencao": _figura_html(grafico_intencao_mensal(med_geral), "graf-intencao", CONFIG_ESTATICO),
        "fig_rejeicao": _figura_html(grafico_rejeicao_mensal(med_geral), "graf-rejeicao", CONFIG_ESTATICO),
        "fig_placar_intencao": _figura_html(grafico_placar(df, "intencao"), "graf-placar-intencao", CONFIG_ESTATICO),
        "fig_placar_rejeicao": _figura_html(grafico_placar(df, "rejeicao"), "graf-placar-rejeicao", CONFIG_ESTATICO),
        "fig_evolucao": _figura_html(fig_evolucao, "graf-evolucao", CONFIG_EVOLUCAO),
        "fig_instituto": _figura_html(fig_instituto, "graf-instituto", CONFIG_ESTATICO),
        "evo_cfg": evo_cfg,
        "inst_cfg": inst_cfg,
        "cores_guia": {"escuro": COR_GUIA_ESCURO, "claro": COR_GUIA_CLARO},
        "zoom_nomes": list(evo_cfg["zoom"]),
        "institutos": _institutos(df),
        "tabelas": _tabelas(df, med_geral),
    }

    env = Environment(
        loader=PackageLoader("pesquisas_eleitorais", "templates"),
        autoescape=select_autoescape(enabled_extensions=("j2",), default_for_string=True),
    )
    medias_csv = med.drop(columns=["mes_nome"]).to_csv(index=False, float_format="%g", lineterminator="\n")
    contexto["csv_uri"] = _data_uri_csv(csv.read_text(encoding="utf-8"))
    contexto["medias_uri"] = _data_uri_csv(medias_csv)
    html = env.get_template("index.html.j2").render(**contexto)

    (saida / "data").mkdir(parents=True, exist_ok=True)
    (saida / "index.html").write_text(html, encoding="utf-8")
    shutil.copyfile(csv, saida / "data" / "pesquisas.csv")
    (saida / "data" / "medias_mensais.csv").write_text(medias_csv, encoding="utf-8")
    return saida / "index.html"
