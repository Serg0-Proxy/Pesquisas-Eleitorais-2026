"""Cálculos estatísticos e de apresentação (nenhum gráfico é desenhado aqui)."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

import numpy as np
import pandas as pd

from .config import MESES, MESES_NOME, PERIODOS_GERAIS, PERIODOS_GERAIS_ABREV, PERIODOS_GERAIS_NOME

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
# LEMBRETE IMPORTANTE: regra da média
#
# Se um instituto publicar mais de uma pesquisa no mesmo período (mês, Out1/Out2 ou semana de
# outubro nos gráficos gerais), só a mais recente dele entra na média. As outras continuam
# valendo no placar e na tabela completa, que contam pesquisa por pesquisa.
#
# A escolha é por métrica: na intenção e no nulo vale a mais recente do instituto; na rejeição
# vale a mais recente que tenha rejeição preenchida, mesmo que não seja a mesma da intenção.
# ---------------------------------------------------------------------------
def _ultima_pesquisa_por_instituto(g: pd.DataFrame) -> pd.DataFrame:
    """Mantém só a pesquisa mais recente de cada instituto (ver o LEMBRETE acima)."""
    return g.sort_values(["data", "ord"]).groupby("instituto").tail(1)


def _ultima_com_rejeicao_por_instituto(g: pd.DataFrame) -> pd.DataFrame:
    """Igual a `_ultima_pesquisa_por_instituto`, mas só entre as pesquisas com rejeição.

    Para a média de rejeição: de cada instituto, a pesquisa mais recente do período que tenha
    rej_lula e rej_flavio (que são sempre preenchidos juntos). Institutos sem nenhuma
    pesquisa com rejeição no período ficam de fora.
    """
    return _ultima_pesquisa_por_instituto(g[g["rej_lula"].notna() & g["rej_flavio"].notna()])


def _medias(df: pd.DataFrame, coluna: str, ordem: tuple[str, ...], nomes: dict[str, str]) -> pd.DataFrame:
    """Médias por grupo de `coluna` (mês ou período), na ordem de `ordem`.

    Aplica a regra do LEMBRETE acima dentro de cada grupo. A coluna de saída continua se
    chamando `mes`/`mes_nome` para servir aos mesmos gráficos, seja o grupo um mês ou uma semana.
    """
    linhas = []
    for mes in sorted(df[coluna].unique(), key=ordem.index):
        g_mes = df[df[coluna] == mes]
        g = _ultima_pesquisa_por_instituto(g_mes)
        g_rej = _ultima_com_rejeicao_por_instituto(g_mes)
        linhas.append(
            {
                "mes": mes,
                "mes_nome": nomes[mes],
                "mes_abrev": PERIODOS_GERAIS_ABREV.get(mes, mes),
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


def medias_mensais(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por mês (outubro dividido em Out1/Out2), com as médias de intenção, nulo e rejeição.

    A média entra com, no máximo, uma pesquisa por instituto no mês — sempre a mais
    recente dele —, para que um instituto que publique várias pesquisas no mesmo mês
    não pese mais que os outros. `n` é o total de pesquisas do mês (todas, sem
    deduplicar); `n_intencao`/`n_rejeicao` contam só os institutos que entraram na média. Na
    rejeição, de cada instituto vale a pesquisa mais recente do período que tenha rejeição.
    """
    return _medias(df, "mes", MESES, MESES_NOME)


def medias_periodos(df: pd.DataFrame) -> pd.DataFrame:
    """Igual a `medias_mensais`, mas com outubro em semanas (1º a 4º domingo) — gráficos gerais.

    Vale a mesma regra: dentro de cada semana, um instituto entra uma vez só (a pesquisa mais
    recente dele; na rejeição, a mais recente que traga rejeição).
    """
    return _medias(df, "periodo", PERIODOS_GERAIS, PERIODOS_GERAIS_NOME)


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


def _placar_por(
    df: pd.DataFrame, tipo: Tipo, coluna: str, ordem: tuple[str, ...], nomes: dict[str, str]
) -> pd.DataFrame:
    linhas = []
    for grupo in sorted(df[coluna].unique(), key=ordem.index):
        linhas.append({"mes": grupo, "mes_nome": nomes[grupo], **placar(df[df[coluna] == grupo], tipo)})
    return pd.DataFrame(linhas)


def placar_mensal(df: pd.DataFrame, tipo: Tipo) -> pd.DataFrame:
    """Placar de cada mês, com outubro em Out1/Out2 (colunas: mes, mes_nome, lula, empate, flavio, total)."""
    return _placar_por(df, tipo, "mes", MESES, MESES_NOME)


def placar_periodos(df: pd.DataFrame, tipo: Tipo) -> pd.DataFrame:
    """Igual a `placar_mensal`, mas com outubro em quatro semanas (Out 1 a Out 4)."""
    return _placar_por(df, tipo, "periodo", PERIODOS_GERAIS, PERIODOS_GERAIS_NOME)


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
