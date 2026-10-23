from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from pesquisas_eleitorais.data import preparar

# CSV mínimo e propositalmente conhecido: fácil de conferir os cálculos "na mão".
# Genial/Quaest tem duas pesquisas em Janeiro (médias meio-para-cima previsíveis)
# e Datafolha não traz rejeição, para testar os campos vazios.
CSV_EXEMPLO = """\
data,instituto,lula,flavio,nulo,rej_lula,rej_flavio,margem_erro
2026-01-11,Genial/Quaest,45,38,17,43,55,2
2026-01-20,Genial/Quaest,46,39,15,44,54,2
2026-02-05,Datafolha,47,43,10,,,2
2026-02-18,Atlas/Intel,46.95,45.05,8,48,46,1
"""


@pytest.fixture
def csv_exemplo(tmp_path: Path) -> Path:
    caminho = tmp_path / "pesquisas.csv"
    caminho.write_text(CSV_EXEMPLO, encoding="utf-8")
    return caminho


@pytest.fixture
def df_exemplo(csv_exemplo: Path) -> pd.DataFrame:
    from pesquisas_eleitorais.data import ler_csv

    return preparar(ler_csv(csv_exemplo))
