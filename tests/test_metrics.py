from __future__ import annotations

import math

import pandas as pd
import pytest

from pesquisas_eleitorais.metrics import (
    classificar,
    eixo_intencao,
    eixo_simples,
    media_meio_para_cima,
    medias_mensais,
    placar,
    placar_mensal,
    tendencia_linear,
)


# ---------------------------------------------------------------------------
# Arredondamento "meio para cima"
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("valores", "esperado"),
    [
        ([46.95], 47.0),  # o caso citado no enunciado do projeto
        ([46.94], 46.9),
        ([44.95], 45.0),  # round() nativo do Python arredondaria para 44.9 (par mais próximo)
        ([2.675], 2.7),  # 2.675 não é exatamente representável em float binário
        ([10, 20], 15.0),
        ([], math.nan),
        ([10, None, float("nan"), 20], 15.0),  # ignora ausentes
    ],
)
def test_media_meio_para_cima(valores: list[float], esperado: float) -> None:
    resultado = media_meio_para_cima(valores)
    if math.isnan(esperado):
        assert math.isnan(resultado)
    else:
        assert resultado == esperado


def test_medias_mensais_do_exemplo(df_exemplo: pd.DataFrame) -> None:
    med = medias_mensais(df_exemplo).set_index("mes")
    # Janeiro: Genial/Quaest aparece duas vezes (11/01 e 20/01) -> a média usa só a
    # mais recente (20/01: 46), não a média das duas
    assert med.loc["Jan", "lula"] == 46.0
    assert med.loc["Jan", "n_intencao"] == 1
    # n (total bruto de pesquisas do mês, sem deduplicar) continua contando as duas
    assert med.loc["Jan", "n"] == 2
    # Fevereiro: Datafolha não traz rejeição -> média usa só Atlas/Intel
    assert med.loc["Fev", "n_rejeicao"] == 1
    assert med.loc["Fev", "rej_lula"] == 48.0


def test_medias_mensais_usa_so_a_ultima_pesquisa_de_cada_instituto_no_mes() -> None:
    # Mesmo instituto, três pesquisas no mesmo mês, com uma de outro instituto no meio
    df = pd.DataFrame(
        {
            "data": pd.to_datetime(["2026-01-05", "2026-01-10", "2026-01-15", "2026-01-20"]),
            "ord": [1, 2, 3, 4],
            "mes": ["Jan"] * 4,
            "instituto": ["Genial/Quaest", "Datafolha", "Genial/Quaest", "Genial/Quaest"],
            "lula": [40.0, 50.0, 44.0, 48.0],
            "flavio": [40.0, 50.0, 44.0, 48.0],
            "nulo": [20.0, 0.0, 12.0, 4.0],
            "rej_lula": [float("nan")] * 4,
            "rej_flavio": [float("nan")] * 4,
            "margem_erro": [2.0] * 4,
        }
    )
    med = medias_mensais(df).set_index("mes")
    # média de (48 do Quaest, última pesquisa) e (50 do Datafolha) = 49.0 — não a média das 4 linhas
    assert med.loc["Jan", "lula"] == 49.0
    assert med.loc["Jan", "n_intencao"] == 2  # 2 institutos, não 4 pesquisas
    assert med.loc["Jan", "n"] == 4  # total bruto de pesquisas continua 4


# ---------------------------------------------------------------------------
# Vantagem / placar
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("a", "b", "margem", "esperado"),
    [
        (46, 44, 2, "empate"),  # diferença == margem -> ainda é empate técnico
        (46.1, 44, 2, "lula"),  # diferença > margem
        (44, 46.1, 2, "flavio"),
        (45, 45, 2, "empate"),
    ],
)
def test_classificar_vantagem(a: float, b: float, margem: float, esperado: str) -> None:
    assert classificar(a, b, margem) == esperado


def test_placar_do_exemplo(df_exemplo: pd.DataFrame) -> None:
    # 11/01: 45 vs 38 (±2) -> lula | 20/01: 46 vs 39 (±2) -> lula
    # 05/02: Datafolha 47 vs 43 (±2) -> lula | 18/02: 46.95 vs 45.05 (±1) -> lula (dif 1.9 > 1)
    resultado = placar(df_exemplo, "intencao")
    assert resultado == {"lula": 4, "empate": 0, "flavio": 0, "total": 4}


def test_placar_mensal_conta_so_pesquisas_com_o_indicador(df_exemplo: pd.DataFrame) -> None:
    tabela_intencao = placar_mensal(df_exemplo, "intencao").set_index("mes")
    assert tabela_intencao.loc["Jan", "total"] == 2
    assert tabela_intencao.loc["Fev", "total"] == 2  # Datafolha e Atlas/Intel trazem intenção

    tabela_rejeicao = placar_mensal(df_exemplo, "rejeicao").set_index("mes")
    assert tabela_rejeicao.loc["Fev", "total"] == 1  # só Atlas/Intel traz rejeição em Fevereiro


# ---------------------------------------------------------------------------
# Tendência linear
# ---------------------------------------------------------------------------
def test_tendencia_linear_reta_perfeita() -> None:
    df = pd.DataFrame({"dia_do_ano": [1, 2, 3, 4], "lula": [40.0, 42.0, 44.0, 46.0]})
    angular, intercepto = tendencia_linear(df, "lula")
    assert angular == pytest.approx(2.0)
    assert intercepto == pytest.approx(38.0)


# ---------------------------------------------------------------------------
# Eixos dos gráficos
# ---------------------------------------------------------------------------
def test_eixo_simples_cobre_os_valores_com_folga() -> None:
    eixo = eixo_simples([44.0, 48.0])
    assert eixo.y_min <= 44.0 - 1.5
    assert eixo.y_max >= 48.0 + 1.5
    assert eixo.y_max - eixo.y_min >= 8  # amplitude mínima


def test_eixo_intencao_mantem_nulo_abaixo_das_linhas() -> None:
    eixo = eixo_intencao([40, 50], [8, 12])
    # o maior valor de nulo, na escala do eixo direito, fica visivelmente abaixo do menor de lula/flávio
    posicao_nulo = 12 / eixo.y2_max
    posicao_menor_lf = (40 - eixo.y_min) / (eixo.y_max - eixo.y_min)
    assert posicao_nulo < posicao_menor_lf


def test_media_de_rejeicao_usa_a_ultima_pesquisa_do_instituto_que_tenha_rejeicao() -> None:
    # A pesquisa mais recente do Datafolha (20/01) não traz rejeição: para a rejeição vale a
    # anterior dele no mesmo mês (10/01); para a intenção vale a mais recente (20/01).
    nan = float("nan")
    df = pd.DataFrame(
        {
            "data": pd.to_datetime(["2026-01-10", "2026-01-15", "2026-01-20"]),
            "ord": [1, 2, 3],
            "mes": ["Jan"] * 3,
            "instituto": ["Datafolha", "Genial/Quaest", "Datafolha"],
            "lula": [40.0, 44.0, 48.0],
            "flavio": [40.0, 44.0, 42.0],
            "nulo": [20.0, 12.0, 10.0],
            "rej_lula": [50.0, 46.0, nan],
            "rej_flavio": [40.0, 52.0, nan],
            "margem_erro": [2.0] * 3,
        }
    )
    jan = medias_mensais(df).set_index("mes").loc["Jan"]
    assert jan["n_intencao"] == 2
    assert jan["lula"] == 46.0  # (48 + 44) / 2, usando a de 20/01 do Datafolha
    assert jan["n_rejeicao"] == 2  # Datafolha (10/01) e Quaest (15/01)
    assert jan["rej_lula"] == 48.0  # (50 + 46) / 2
    assert jan["rej_flavio"] == 46.0  # (40 + 52) / 2
