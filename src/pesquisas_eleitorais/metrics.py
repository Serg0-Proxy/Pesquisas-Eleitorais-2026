"""Cálculos estatísticos e de apresentação (nenhum gráfico é desenhado aqui)."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

import numpy as np
import pandas as pd

from .config import MESES, MESES_NOME

Tipo = Literal["intencao", "rejeicao"]
Vantagem = Literal["lula", "flavio", "empate"]

# (coluna de Lula, coluna de Flávio) para cada tipo de indicador
COLUNAS_TIPO: dict[Tipo, tuple[str, str]] = {
    "intencao": ("lula", "flavio"),
    "rejeicao": ("rej_lula", "rej_flavio"),
}


# ---------------------------------------------------------------------------
# Médias mensais
# ---------------------------------------------------------------------------
def media_meio_para_cima(valores: Iterable[float], casas: int = 1) -> float:
    """Média ignorando NaN, com arredondamento "meio para cima" (46,95 -> 47,0).

    Usa `Decimal` porque o `round` do Python arredonda metades para o par
    (46,95 -> 46,9) e porque floats binários erram em casos como 2,675.
    """
    v = [Decimal(str(float(x))) for x in valores if pd.notna(x)]
    if not v:
        return math.nan
    media = sum(v, Decimal(0)) / len(v)
    return float(media.quantize(Decimal(1).scaleb(-casas), rounding=ROUND_HALF_UP))


# ---------------------------------------------------------------------------
# LEMBRETE IMPORTANTE — regra da média mensal (pedido explícito do usuário)
#
# Se um instituto publicar MAIS DE UMA pesquisa no mesmo mês (ou no mesmo "Out1"/"Out2",
# já que outubro é dividido em dois — ver mes_da_data em config.py), a média mensal usa
# SÓ A PESQUISA MAIS RECENTE desse instituto naquele mês/período. As pesquisas mais
# antigas do mesmo instituto no mesmo mês NÃO entram na soma nem na média — é como se
# não existissem para esse cálculo (mas continuam valendo normalmente para o placar e
# para a tabela completa, que olham pesquisa por pesquisa, não por instituto).
#
# Isso é feito por _ultima_pesquisa_por_instituto(), logo abaixo, chamada de dentro de
# medias_mensais(). Não mude essa função para incluir todas as pesquisas do mês sem
# querer — isso quebraria essa regra.
#
# A escolha da "mais recente" é feita POR MÉTRICA: para intenção e nulo vale a mais recente
# do instituto no período; para REJEIÇÃO vale a mais recente do instituto no período QUE TENHA
# rejeição preenchida (se a última pesquisa dele não trouxe rejeição, usa-se a anterior do mesmo
# período que trouxe). Sem isso, a média de rejeição ficaria com poucos institutos e distorcida.
# ---------------------------------------------------------------------------
def _ultima_pesquisa_por_instituto(g: pd.DataFrame) -> pd.DataFrame:
    """De cada instituto presente em `g`, mantém só a pesquisa mais recente.

    Ver o LEMBRETE acima: é isso que garante que a média mensal nunca conte duas
    pesquisas do mesmo instituto no mesmo mês — só a mais recente das duas (ou mais)
    é usada no cálculo.
    """
    return g.sort_values(["data", "ord"]).groupby("instituto").tail(1)


def _ultima_com_rejeicao_por_instituto(g: pd.DataFrame) -> pd.DataFrame:
    """Igual a `_ultima_pesquisa_por_instituto`, mas só entre as pesquisas com rejeição.

    Para a média de rejeição: de cada instituto, a pesquisa mais recente do período que tenha
    rej_lula e rej_flavio (que são sempre preenchidos juntos). Institutos sem nenhuma
    pesquisa com rejeição no período ficam de fora.
    """
    return _ultima_pesquisa_por_instituto(g[g["rej_lula"].notna() & g["rej_flavio"].notna()])


def medias_mensais(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por mês, com as médias de intenção, nulo e rejeição.

    A média entra com, no máximo, uma pesquisa por instituto no mês — sempre a mais
    recente dele —, para que um instituto que publique várias pesquisas no mesmo mês
    não pese mais que os outros. `n` é o total de pesquisas do mês (todas, sem
    deduplicar); `n_intencao`/`n_rejeicao` contam só os institutos que entraram na média. Na
    rejeição, de cada instituto vale a pesquisa mais recente do período que tenha rejeição.
    """
    linhas = []
    for mes in sorted(df["mes"].unique(), key=MESES.index):
        g_mes = df[df["mes"] == mes]
        g = _ultima_pesquisa_por_instituto(g_mes)
        g_rej = _ultima_com_rejeicao_por_instituto(g_mes)
        linhas.append(
            {
                "mes": mes,
                "mes_nome": MESES_NOME[mes],
                "n": len(g_mes),
                "n_intencao": int(g["lula"].notna().sum()),
                "n_rejeicao": len(g_rej),
                "lula": media_meio_para_cima(g["lula"]),
                "flavio": media_meio_para_cima(g["flavio"]),
                "nulo": media_meio_para_cima(g["nulo"]),
                "rej_lula": media_meio_para_cima(g_rej["rej_lula"]),
                "rej_flavio": media_meio_para_cima(g_rej["rej_flavio"]),
            }
        )
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# Vantagem e placar
# ---------------------------------------------------------------------------
def classificar(a: float, b: float, margem: float) -> Vantagem:
    """'lula' se a > b + margem; 'flavio' se b > a + margem; senão 'empate' (técnico)."""
    dif = round(a - b, 6)
    if abs(dif) <= margem:
        return "empate"
    return "lula" if dif > 0 else "flavio"


def classificar_pesquisas(df: pd.DataFrame, tipo: Tipo) -> pd.Series:
    """Classificação de cada pesquisa que traz o indicador; as demais ficam de fora."""
    col_l, col_f = COLUNAS_TIPO[tipo]
    validas = df[df[col_l].notna() & df[col_f].notna()]
    return pd.Series(
        [classificar(r[col_l], r[col_f], r["margem_erro"]) for _, r in validas.iterrows()],
        index=validas.index,
        dtype="object",
    )


def placar(df: pd.DataFrame, tipo: Tipo) -> dict[str, int]:
    """Contagem de pesquisas com Lula à frente, empate técnico e Flávio à frente."""
    contagem = classificar_pesquisas(df, tipo).value_counts()
    return {k: int(contagem.get(k, 0)) for k in ("lula", "empate", "flavio")} | {"total": int(contagem.sum())}


def placar_mensal(df: pd.DataFrame, tipo: Tipo) -> pd.DataFrame:
    """Placar de cada mês (colunas: mes, mes_nome, lula, empate, flavio, total)."""
    linhas = []
    for mes in sorted(df["mes"].unique(), key=MESES.index):
        linhas.append({"mes": mes, "mes_nome": MESES_NOME[mes], **placar(df[df["mes"] == mes], tipo)})
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# Séries para o gráfico de evolução
# ---------------------------------------------------------------------------
def tendencia_linear(df: pd.DataFrame, coluna: str) -> tuple[float, float]:
    """Reta de mínimos quadrados (coeficiente angular, intercepto) sobre o dia do ano."""
    v = df[df[coluna].notna()]
    angular, intercepto = np.polyfit(v["dia_do_ano"], v[coluna], 1)
    return float(angular), float(intercepto)


def media_movel(df: pd.DataFrame, coluna: str, janela: int = 3) -> pd.DataFrame:
    """Média móvel das últimas `janela` pesquisas (colunas: data, valor)."""
    v = df[df[coluna].notna()].sort_values("data", kind="stable")
    return pd.DataFrame({"data": v["data"], "valor": v[coluna].rolling(janela, min_periods=1).mean()})


def faixa_mensal(df: pd.DataFrame, coluna: str) -> pd.DataFrame:
    """Mínimo e máximo por mês (só meses com 2+ pesquisas).

    `inicio`/`fim` usam a primeira e a última data das pesquisas do próprio grupo — não o
    1º e o último dia do mês civil — porque outubro é dividido em dois grupos ("Out1" e
    "Out2"; ver `mes_da_data`) e cada um deve desenhar a faixa só sobre os dias que cobre.
    """
    linhas = []
    for mes, g in df[df[coluna].notna()].groupby("mes"):
        if len(g) < 2:
            continue
        linhas.append(
            {
                "mes": mes,
                "inicio": g["data"].min(),
                "fim": g["data"].max(),
                "minimo": float(g[coluna].min()),
                "maximo": float(g[coluna].max()),
            }
        )
    return pd.DataFrame(linhas, columns=["mes", "inicio", "fim", "minimo", "maximo"])


# ---------------------------------------------------------------------------
# Eixos "ampliados" dos gráficos
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class EixoSimples:
    y_min: int
    y_max: int
    passo: int


@dataclass(frozen=True)
class EixoIntencao(EixoSimples):
    """Eixo esquerdo (Lula/Flávio) ampliado + eixo direito (Nulo/NS) sempre abaixo das linhas."""

    y2_max: int = 100
    y2_ticks: tuple[int, ...] = (10, 20)


def passo_para(amplitude: float) -> int:
    return 2 if amplitude <= 12 else 4 if amplitude <= 24 else 5


def faixa_agradavel(valores: Iterable[float], pad_baixo: float, pad_cima: float, passo: int = 2) -> tuple[int, int]:
    v = list(valores)
    return (
        math.floor((min(v) - pad_baixo) / passo) * passo,
        math.ceil((max(v) + pad_cima) / passo) * passo,
    )


def eixo_simples(valores: Iterable[float], pad: float = 1.5, amplitude_minima: int = 8) -> EixoSimples:
    lo, hi = faixa_agradavel(valores, pad, pad)
    if hi - lo < amplitude_minima:
        centro = (lo + hi) / 2
        lo = math.floor((centro - amplitude_minima / 2) / 2) * 2
        hi = lo + amplitude_minima
    return EixoSimples(lo, hi, passo_para(hi - lo))


def eixo_intencao(lula_flavio: Iterable[float], nulos: Iterable[float]) -> EixoIntencao:
    lf, nu = list(lula_flavio), list(nulos)
    lo, hi = faixa_agradavel(lf, 3, 1.5)
    if hi - lo < 8:
        hi = lo + 8
    menor = min(lf)
    while (menor - lo) / (hi - lo) < 0.32:  # garante espaço para a linha de nulo embaixo
        lo -= 2
    posicao_menor = (menor - lo) / (hi - lo)
    max_nulo = max(nu)
    limite = min(0.2, posicao_menor - 0.17)
    y2_max = next((v for v in (40, 50, 60, 80, 100, 120, 150) if max_nulo / v <= limite), 150)
    ate = math.ceil(max_nulo / 10) * 10
    return EixoIntencao(lo, hi, passo_para(hi - lo), y2_max, tuple(range(10, ate + 1, 10)))


def ajustar_y(valores: Iterable[float]) -> tuple[int, int]:
    """Faixa Y que enquadra os valores visíveis num zoom (mínimo de 4 pontos de altura)."""
    v = list(valores)
    lo, hi = math.floor(min(v) - 1), math.ceil(max(v) + 1)
    if hi - lo < 4:
        centro = (lo + hi) / 2
        lo, hi = math.floor(centro - 2), math.ceil(centro + 2)
    return lo, hi
