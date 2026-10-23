"""Linha de comando: `pesquisas <comando>` ou `python -m pesquisas_eleitorais <comando>`."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from . import __version__
from .build import construir_site
from .config import CSV_PADRAO, REPO_URL_PADRAO, SAIDA_PADRAO
from .data import DadosInvalidos, adicionar_pesquisa, ler_csv, preparar, salvar_csv, validar
from .metrics import medias_mensais


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pesquisas",
        description="Dashboard de pesquisas eleitorais 2026 (2º turno) gerado em Python.",
    )
    p.add_argument("--versao", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("--csv", type=Path, default=CSV_PADRAO, help=f"arquivo de dados (padrão: {CSV_PADRAO})")
    sub = p.add_subparsers(dest="comando", required=True)

    b = sub.add_parser("build", help="gera o site em HTML")
    b.add_argument("--saida", type=Path, default=SAIDA_PADRAO, help=f"pasta de saída (padrão: {SAIDA_PADRAO})")
    b.add_argument("--offline", action="store_true", help="embute o Plotly.js no HTML (arquivo autossuficiente)")
    b.add_argument("--repo-url", default=REPO_URL_PADRAO, help="link do repositório exibido no site")

    sub.add_parser("validar", help="valida o CSV (nomes, datas, somas, duplicatas…)")
    sub.add_parser("medias", help="mostra as médias mensais no terminal")
    sub.add_parser("ordenar", help="ordena o CSV por data")

    a = sub.add_parser("adicionar", help="adiciona uma pesquisa ao CSV (validando tudo)")
    a.add_argument("--data", required=True, help="AAAA-MM-DD do último dia de campo")
    a.add_argument("--instituto", required=True)
    a.add_argument("--lula", type=float, required=True)
    a.add_argument("--flavio", type=float, required=True)
    a.add_argument("--nulo", type=float, required=True, help="brancos, nulos, indecisos e não sabe")
    a.add_argument("--margem-erro", type=float, required=True, help="em pontos percentuais")
    a.add_argument("--rej-lula", type=float)
    a.add_argument("--rej-flavio", type=float)
    return p


def _falha(erro: DadosInvalidos) -> int:
    print(f"✗ {len(erro.erros)} problema(s):", file=sys.stderr)
    for msg in erro.erros:
        print(f"  - {msg}", file=sys.stderr)
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.comando == "build":
            destino = construir_site(args.csv, args.saida, offline=args.offline, repo_url=args.repo_url)
            print(f"✓ site gerado em {destino}")
        elif args.comando == "validar":
            df = ler_csv(args.csv)
            erros = validar(df)
            if erros:
                return _falha(DadosInvalidos(erros))
            print(f"✓ {len(df)} pesquisas válidas em {args.csv}")
        elif args.comando == "medias":
            df = preparar(ler_csv(args.csv))
            tabela = medias_mensais(df).drop(columns=["mes_nome"])
            print(tabela.to_string(index=False, float_format=lambda v: f"{v:.1f}"))
        elif args.comando == "ordenar":
            df = ler_csv(args.csv)
            salvar_csv(df, args.csv)
            print(f"✓ {args.csv} ordenado por data")
        elif args.comando == "adicionar":
            df = adicionar_pesquisa(
                args.csv,
                data=args.data,
                instituto=args.instituto,
                lula=args.lula,
                flavio=args.flavio,
                nulo=args.nulo,
                margem_erro=args.margem_erro,
                rej_lula=args.rej_lula,
                rej_flavio=args.rej_flavio,
            )
            print(f"✓ pesquisa adicionada — agora são {len(df)} no total")
    except DadosInvalidos as erro:
        return _falha(erro)
    except (FileNotFoundError, pd.errors.EmptyDataError) as erro:
        print(f"✗ {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
