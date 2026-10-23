from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from pesquisas_eleitorais.config import mes_da_data
from pesquisas_eleitorais.data import (
    DadosInvalidos,
    adicionar_pesquisa,
    carregar,
    ler_csv,
    normalizar_instituto,
    preparar,
    salvar_csv,
    validar,
)


def test_le_e_prepara_o_csv_de_exemplo(df_exemplo: pd.DataFrame) -> None:
    assert len(df_exemplo) == 4
    # ord segue a ordem cronológica, começando em 1
    assert df_exemplo["ord"].tolist() == [1, 2, 3, 4]
    # o mês é derivado da própria data
    assert df_exemplo["mes"].tolist() == ["Jan", "Jan", "Fev", "Fev"]


def test_carregar_nao_reclama_do_csv_valido(csv_exemplo: Path) -> None:
    df = carregar(csv_exemplo)  # não deve levantar DadosInvalidos
    assert validar(df) == []


@pytest.mark.parametrize(
    ("coluna", "valor", "trecho_esperado"),
    [
        ("instituto", "Quaest", "forma canônica"),  # variação não canônica
        ("lula", 200, "0–100"),  # fora do intervalo
        ("margem_erro", 0, "margem_erro inválida"),
    ],
)
def test_validar_rejeita_valores_invalidos(
    df_exemplo: pd.DataFrame, coluna: str, valor: object, trecho_esperado: str
) -> None:
    df = df_exemplo.copy()
    df.loc[0, coluna] = valor
    erros = validar(df)
    assert any(trecho_esperado in e for e in erros), erros


def test_validar_acusa_soma_fora_de_100(df_exemplo: pd.DataFrame) -> None:
    df = df_exemplo.copy()
    df.loc[0, "nulo"] = 50  # 45 + 38 + 50 = 133
    erros = validar(df)
    assert any("deveria fechar 100" in e for e in erros)


def test_validar_acusa_pesquisa_duplicada(df_exemplo: pd.DataFrame) -> None:
    df = pd.concat([df_exemplo, df_exemplo.iloc[[0]]], ignore_index=True)
    erros = validar(df)
    assert any("duplicada" in e for e in erros)


def test_validar_exige_rejeicao_completa_ou_vazia(df_exemplo: pd.DataFrame) -> None:
    df = df_exemplo.copy()
    df.loc[0, "rej_flavio"] = float("nan")  # rej_lula continua preenchido
    erros = validar(df)
    assert any("rej_lula e rej_flavio" in e for e in erros)


def test_ler_csv_relata_linha_e_coluna_do_erro(tmp_path: Path) -> None:
    ruim = tmp_path / "ruim.csv"
    ruim.write_text(
        "data,instituto,lula,flavio,nulo,rej_lula,rej_flavio,margem_erro\n31/13/2026,Datafolha,abc,43,10,,,2\n",
        encoding="utf-8",
    )
    with pytest.raises(DadosInvalidos) as exc:
        ler_csv(ruim)
    erros = "\n".join(exc.value.erros)
    assert "linha 2" in erros and "data inválida" in erros and "lula" in erros


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("Genial/Quaest", "Genial/Quaest"),
        ("quaest", "Genial/Quaest"),
        ("BTG/NEXUS", "BTG/Nexus"),
        ("nexus/btg", "BTG/Nexus"),
        ("Paraná Pesquisas", "Paraná Pesquisas"),
        ("parana pesquisas", "Paraná Pesquisas"),
    ],
)
def test_normalizar_instituto_aceita_variacoes_conhecidas(entrada: str, esperado: str) -> None:
    assert normalizar_instituto(entrada) == esperado


def test_normalizar_instituto_rejeita_desconhecido() -> None:
    with pytest.raises(DadosInvalidos):
        normalizar_instituto("Instituto Que Não Existe")


def test_salvar_csv_e_reler_preserva_os_dados(df_exemplo: pd.DataFrame, tmp_path: Path) -> None:
    destino = tmp_path / "saida.csv"
    salvar_csv(df_exemplo, destino)
    relido = preparar(ler_csv(destino))
    pd.testing.assert_frame_equal(
        df_exemplo[["data", "instituto", "lula", "flavio", "nulo"]],
        relido[["data", "instituto", "lula", "flavio", "nulo"]],
    )


def test_adicionar_pesquisa_insere_na_posicao_cronologica(csv_exemplo: Path) -> None:
    df = adicionar_pesquisa(
        csv_exemplo,
        data="2026-01-15",
        instituto="btg/nexus",
        lula=44,
        flavio=44,
        nulo=12,
        margem_erro=2,
    )
    # entre as duas pesquisas de Genial/Quaest (11/01 e 20/01)
    assert df.loc[1, "instituto"] == "BTG/Nexus"
    assert df["ord"].tolist() == [1, 2, 3, 4, 5]


def test_adicionar_pesquisa_com_dados_invalidos_nao_grava_nada(csv_exemplo: Path) -> None:
    antes = csv_exemplo.read_text(encoding="utf-8")
    with pytest.raises(DadosInvalidos):
        adicionar_pesquisa(
            csv_exemplo,
            data="2026-01-15",
            instituto="btg/nexus",
            lula=90,
            flavio=44,
            nulo=12,
            margem_erro=2,
        )
    assert csv_exemplo.read_text(encoding="utf-8") == antes


# ---------------------------------------------------------------------------
# Outubro dividido em dois "meses" (antes/depois do 1º turno)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("dia", "mes_civil", "esperado"),
    [
        (1, 10, "Out1"),
        (5, 10, "Out1"),
        (6, 10, "Out2"),
        (31, 10, "Out2"),
        (15, 9, "Set"),  # outros meses não são afetados
        (1, 1, "Jan"),
    ],
)
def test_mes_da_data_divide_outubro_no_1o_turno(dia: int, mes_civil: int, esperado: str) -> None:
    assert mes_da_data(dia, mes_civil) == esperado


def test_preparar_aplica_a_divisao_de_outubro(tmp_path: Path) -> None:
    csv = tmp_path / "pesquisas.csv"
    csv.write_text(
        "data,instituto,lula,flavio,nulo,rej_lula,rej_flavio,margem_erro\n"
        "2026-10-03,Genial/Quaest,44,42,14,,,2\n"
        "2026-10-08,Datafolha,45,49,6,46,43,2\n",
        encoding="utf-8",
    )
    df = preparar(ler_csv(csv))
    assert df.set_index("instituto")["mes"].to_dict() == {"Genial/Quaest": "Out1", "Datafolha": "Out2"}
