"""Leitura, validação e gravação do CSV de pesquisas."""

from __future__ import annotations

import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

from .config import (
    ALIASES,
    ANO,
    COLUNAS,
    COLUNAS_NUMERICAS,
    INSTITUTOS,
    TOLERANCIA_SOMA,
    mes_da_data,
    periodo_geral,
)


class DadosInvalidos(ValueError):
    """Erro de leitura ou validação; `erros` traz uma mensagem por problema."""

    def __init__(self, erros: list[str]) -> None:
        super().__init__("\n".join(erros))
        self.erros = erros


# ---------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------
def ler_csv(caminho: str | Path) -> pd.DataFrame:
    """Lê o CSV e converte os tipos. Lança `DadosInvalidos` se algo não puder ser lido."""
    bruto = pd.read_csv(caminho, dtype=str, keep_default_na=False)
    bruto = bruto.apply(lambda coluna: coluna.str.strip())

    faltando = [c for c in COLUNAS if c not in bruto.columns]
    if faltando:
        raise DadosInvalidos([f"colunas ausentes no CSV: {', '.join(faltando)}"])

    erros: list[str] = []
    df = pd.DataFrame(index=bruto.index)
    df["data"] = pd.to_datetime(bruto["data"], format="%Y-%m-%d", errors="coerce")
    for i in df.index[df["data"].isna()]:
        erros.append(f"linha {i + 2}: data inválida {bruto.at[i, 'data']!r} (use AAAA-MM-DD)")

    df["instituto"] = bruto["instituto"]
    for coluna in COLUNAS_NUMERICAS:
        convertida = pd.to_numeric(bruto[coluna].replace("", np.nan), errors="coerce")
        ruins = bruto[coluna].ne("") & convertida.isna()
        for i in bruto.index[ruins]:
            erros.append(f"linha {i + 2}: valor não numérico em {coluna!r}: {bruto.at[i, coluna]!r}")
        df[coluna] = convertida.astype("float64")

    if erros:
        raise DadosInvalidos(erros)
    return df[list(COLUNAS)]


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------
def validar(df: pd.DataFrame) -> list[str]:
    """Devolve a lista de problemas encontrados (vazia se estiver tudo certo)."""
    erros: list[str] = []

    def onde(i: int) -> str:
        return f"linha {i + 2} ({df.at[i, 'data']:%d/%m} {df.at[i, 'instituto']})"

    if not df["data"].is_monotonic_increasing:
        erros.append("CSV fora de ordem cronológica — rode `pesquisas ordenar`")

    for i in df.index:
        r = df.loc[i]
        if r["data"].year != ANO:
            erros.append(f"{onde(i)}: ano diferente de {ANO}")
        if r["instituto"] not in INSTITUTOS:
            erros.append(f"{onde(i)}: instituto fora da forma canônica: {r['instituto']!r}")

        voto = r[["lula", "flavio", "nulo"]]
        if voto.isna().any() and not voto.isna().all():
            erros.append(f"{onde(i)}: lula, flavio e nulo devem estar todos preenchidos ou todos vazios")
        elif voto.notna().all():
            if not voto.between(0, 100).all():
                erros.append(f"{onde(i)}: intenção de voto fora do intervalo 0–100")
            soma = float(voto.sum())
            if abs(soma - 100) > TOLERANCIA_SOMA:
                erros.append(f"{onde(i)}: lula + flavio + nulo = {soma:.1f} (deveria fechar 100)")

        rej = r[["rej_lula", "rej_flavio"]]
        if rej.isna().any() and not rej.isna().all():
            erros.append(f"{onde(i)}: rej_lula e rej_flavio devem estar ambos preenchidos ou ambos vazios")
        elif rej.notna().all() and not rej.between(0, 100).all():
            erros.append(f"{onde(i)}: rejeição fora do intervalo 0–100")

        margem = r["margem_erro"]
        if pd.isna(margem) or not 0 < margem <= 10:
            erros.append(f"{onde(i)}: margem_erro inválida ({margem})")

    duplicadas = df.duplicated(subset=["data", "instituto"], keep="first")
    for i in df.index[duplicadas]:
        erros.append(f"{onde(i)}: pesquisa duplicada (mesma data e instituto)")
    return erros


# ---------------------------------------------------------------------------
# Preparação (colunas derivadas)
# ---------------------------------------------------------------------------
def preparar(df: pd.DataFrame) -> pd.DataFrame:
    """Ordena (de forma estável) e cria as colunas derivadas: ord, mes, periodo, mes_num, dia_do_ano.

    `mes` (Out1/Out2) alimenta placar, tabela e zoom; `periodo` (outubro por domingos) alimenta
    as médias gerais de intenção e de rejeição.
    """
    df = df.sort_values("data", kind="stable").reset_index(drop=True)
    df["ord"] = df.index + 1
    df["mes_num"] = df["data"].dt.month
    df["mes"] = [mes_da_data(d.day, d.month) for d in df["data"]]
    df["periodo"] = [periodo_geral(d.date()) for d in df["data"]]
    df["dia_do_ano"] = df["data"].dt.dayofyear
    return df


def carregar(caminho: str | Path) -> pd.DataFrame:
    """Atalho: lê, valida (lança `DadosInvalidos`) e prepara."""
    df = ler_csv(caminho)
    erros = validar(df)
    if erros:
        raise DadosInvalidos(erros)
    return preparar(df)


# ---------------------------------------------------------------------------
# Gravação e inclusão de pesquisas
# ---------------------------------------------------------------------------
def salvar_csv(df: pd.DataFrame, caminho: str | Path) -> None:
    """Grava só as colunas do esquema, em ordem cronológica, sem zeros à direita."""
    saida = df[list(COLUNAS)].sort_values("data", kind="stable").copy()
    saida["data"] = saida["data"].dt.strftime("%Y-%m-%d")
    saida.to_csv(caminho, index=False, float_format="%g", lineterminator="\n")


def normalizar_instituto(nome: str) -> str:
    """Converte variações ('BTG/NEXUS', 'Quaest') para a forma canônica."""

    def chave(texto: str) -> str:
        sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
        return " ".join(sem_acento.casefold().split())

    canonicos = {chave(n): n for n in INSTITUTOS}
    procurado = chave(nome)
    if procurado in canonicos:
        return canonicos[procurado]
    if procurado in ALIASES:
        return ALIASES[procurado]
    raise DadosInvalidos([f"instituto desconhecido: {nome!r}. Opções: {', '.join(INSTITUTOS)}"])


def adicionar_pesquisa(
    caminho: str | Path,
    *,
    data: str,
    instituto: str,
    lula: float,
    flavio: float,
    nulo: float,
    margem_erro: float,
    rej_lula: float | None = None,
    rej_flavio: float | None = None,
) -> pd.DataFrame:
    """Insere uma pesquisa na posição cronológica correta, validando o CSV inteiro."""
    nova = pd.DataFrame(
        [
            {
                "data": pd.to_datetime(data, format="%Y-%m-%d"),
                "instituto": normalizar_instituto(instituto),
                "lula": lula,
                "flavio": flavio,
                "nulo": nulo,
                "rej_lula": np.nan if rej_lula is None else rej_lula,
                "rej_flavio": np.nan if rej_flavio is None else rej_flavio,
                "margem_erro": margem_erro,
            }
        ]
    ).astype({c: "float64" for c in COLUNAS_NUMERICAS})

    df = pd.concat([ler_csv(caminho), nova], ignore_index=True)
    df = df.sort_values("data", kind="stable").reset_index(drop=True)  # empates: nova fica depois
    erros = validar(df)
    if erros:
        raise DadosInvalidos(erros)
    salvar_csv(df, caminho)
    return preparar(df)
