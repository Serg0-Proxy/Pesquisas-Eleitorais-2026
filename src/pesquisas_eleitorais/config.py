"""Constantes do projeto: colunas do CSV, institutos canônicos, meses, cores e caminhos."""

from __future__ import annotations

from pathlib import Path

ANO = 2026
PERIODO_EXIBIDO = "Jan–Out 2026"  # texto do subtítulo (a coleta segue até o 2º turno)

# TODO(dados): rejeição ainda não encontrada nas matérias que noticiaram estas pesquisas —
# conferir se saiu depois (ou no PDF/metodologia completa) e preencher rej_lula/rej_flavio.
# (Rejeições já preenchidas em 22/10/2026: PoderData/Aya 5-7, 10-12, 16-18 e 19-21/10; Ipespe 6-8 e
# 13-15/10; Quaest 2-3 e 10-13/10; Indexa 13-14/10; Palver 10-13 e 18-20/10; Datafolha 13-14/10;
# Futura/Apex 14-15 e 19-20/10; MDA/CNT 13-15/10; BTG/Nexus 16-18/10; Meio/Ideia 15-19/10.)
#   - Datafolha, 22-23/09/2026 (BR-00304/2026)
#   - Palver, 20-23/09/2026 (BR-09587/2026) — a rejeição 51/48 divulgada em 29/09 é da rodada 24-27/09
#   - AtlasIntel, 23-28/09/2026 (BR-04391/2026) — instituto raramente publica rejeição
#   - VOX, 26-28/09/2026 (BR-00895/2026)
#   - Futura/Apex, 25-29/09/2026 (BR-01122/2026)
#   - Datafolha, 28/09-01/10/2026 (BR-08039/2026) — data corrigida de 30/09 para 01/10
#     (campo real da pesquisa), confirmado via busca. Uma matéria cita rejeição de 45%/45% "em 1º de
#     outubro" (Datafolha), mas não confirmei se é esta ou a de 29/09-03/10 — reconferir
#   - VOX, 29/09-01/10/2026 (BR-00148/2026)
#   - GERP, 30/09-02/10/2026 (BR-00509/2026) — matéria só trouxe votos válidos (53/47);
#     nulo=7 é estimado (ver cenário de 1º turno da mesma pesquisa), reconferir se publicarem votos totais
#   - Instituto França, 28/09-02/10/2026 (BR-02928/2026)
#   - Datafolha, 29/09-03/10/2026 (BR-01708/2026) — ver nota da Datafolha de 28/09-01/10
#   - AtlasIntel, 27/09-02/10/2026 (BR-00999/2026) — nulo=5,0 estimado a partir dos votos
#     válidos (50,1/49,8); instituto raramente publica rejeição
#   - VOX, 05-07/10/2026
#   - DataTrends, 07-09/10/2026 (BR-03576/2026) — instituto novo, 1ª pesquisa dele
#   - AtlasIntel, 03-08/10/2026 e 13-18/10/2026 (BR-02418/2026) — instituto raramente publica rejeição
#   - DataTrends, 15-17/10/2026 (BR-04454/2026) — nulo=5 (49+46 = 95 nos totais; válidos 51,5/48,5)
#   - Real Time Big Data, 15-19/10/2026 (BR-02952/2026) — nulo=7 (5 + 2)
#   - Instituto França, 16-20/10/2026 (BR-07896/2026) — nulo=19,4 (10,56 branco/nulo + 8,84 NS/NR);
#     instituto reporta muitos indecisos — válidos 50,8/49,2 batem com 40,95/39,65
#   - GERP, 19-21/10/2026 (BR-03835/2026) — fonte somou 99 (50 + 45 + 2 nenhum + 2 NS/NR,
#     arredondamento); nulo ajustado para 5 para fechar 100 (lula/flavio intactos)
#   - Indexa/Broadcast, 20-21/10/2026 (BR-02348/2026) — rejeição não saiu; nulo=10,7 (100 - 44,1 - 45,2)
# Observações de dados (sem rejeição pendente):
#   - Palver, 18-20/10/2026: fonte somou 99 (branco/nulo 1); nulo ajustado para 2 (lula/flavio intactos)
#   - Futura/Apex, 16-17/10/2026 (BR-06715/2026): fonte somou 100,1 (nulo 2,4 + indecisos 1,9); nulo
#     ajustado para 4,2 (lula/flavio intactos)
#   - PoderData/Aya, 16-18/10/2026: totais 49/46 vieram de agregador secundário (Quenty), válidos 52/48
#     confirmados na CNN/Gazeta — reconferir totais no Poder360
#   - Alfa Inteligência, divulgada 20/10/2026 — citada em chamada da CNN, não consegui confirmar números
#     (totais/campo) na fonte; NÃO adicionada, reconferir
#   - Palver, 15-20/09/2026: Flávio 47 / Lula 43 / branco-nulo 9 (+ indecisos não informados); nulo=10
#     estimado para fechar 100. Margem 3 pp veio da Wikipedia (não achei nas matérias) e a rejeição
#     (53/50, CNN, BR-00860/2026) cita campo "15-17/09" — conferir se é a mesma pesquisa
#   - Palver, 24-27/09/2026 (BR-02990/2026): Gazeta cita campo até 28/09; CNN e Wikipedia, 27/09 (usado)
#   - Palver, 30/09-03/10/2026: rejeição não encontrada (pendente); nulo=7 (6 branco/nulo + 1 indeciso)
#   - Datafolha, 20-22/10/2026 (BR-09709/2026): nulo=7 (100 - 47 - 46); rejeição 48/48 (Terra/UOL)
CSV_PADRAO = Path("data/pesquisas.csv")
SAIDA_PADRAO = Path("site")
REPO_URL_PADRAO = "https://github.com/SEU-USUARIO/pesquisas-eleitorais-2026"

# ---------------------------------------------------------------------------
# Esquema do CSV (uma linha = uma pesquisa de 2º turno)
# ---------------------------------------------------------------------------
COLUNAS = (
    "data",  # AAAA-MM-DD do ÚLTIMO dia de campo (não a data de publicação)
    "instituto",  # nome canônico (ver INSTITUTOS)
    "lula",  # intenção de voto em Lula (%)
    "flavio",  # intenção de voto em Flávio Bolsonaro (%)
    "nulo",  # brancos, nulos, indecisos e "não sabe" (%)
    "rej_lula",  # rejeição a Lula (%), vazio se a pesquisa não trouxe
    "rej_flavio",  # rejeição a Flávio (%), vazio se a pesquisa não trouxe
    "margem_erro",  # margem de erro, em pontos percentuais
)
COLUNAS_NUMERICAS = COLUNAS[2:]
TOLERANCIA_SOMA = 0.05  # lula + flavio + nulo precisa fechar 100 (± tolerância)

# ---------------------------------------------------------------------------
# Meses
# ---------------------------------------------------------------------------
# Outubro de 2026 é tratado como DOIS "meses" no dashboard — antes e depois do dia da
# votação do 1º turno (04/10/2026) — para deixar essa virada bem evidente nas médias, no
# placar e na tabela completa. OUTUBRO_CORTE_1_TURNO é o primeiro dia já considerado
# "pós-1º turno" (dias 1 a 5 ficam no "Out1"; 6 em diante, no "Out2").
OUTUBRO_CORTE_1_TURNO = 6
MESES_CALENDARIO = ("Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez")


def mes_da_data(dia: int, mes_civil: int) -> str:
    """Código do 'mês' (coluna derivada `mes`) a partir do dia e do mês civil da pesquisa.

    Igual ao mês civil para todos os meses, exceto outubro, que é dividido em
    "Out1" (dias 1 a `OUTUBRO_CORTE_1_TURNO - 1`) e "Out2" (do corte em diante).
    """
    if mes_civil == 10:
        return "Out1" if dia < OUTUBRO_CORTE_1_TURNO else "Out2"
    return MESES_CALENDARIO[mes_civil - 1]


MESES = ("Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out1", "Out2", "Nov", "Dez")
MESES_NOME = dict(
    zip(
        MESES,
        (
            "Janeiro",
            "Fevereiro",
            "Março",
            "Abril",
            "Maio",
            "Junho",
            "Julho",
            "Agosto",
            "Setembro",
            "Out (até 1ºT)",
            "Out (pós 1ºT)",
            "Novembro",
            "Dezembro",
        ),
        strict=True,
    )
)

# ---------------------------------------------------------------------------
# Institutos: apenas as formas canônicas são aceitas no CSV
# ---------------------------------------------------------------------------
INSTITUTOS = (
    "Genial/Quaest",
    "Datafolha",
    "Atlas/Intel",
    "Futura/Apex",
    "GERP",
    "BTG/Nexus",
    "Big Data",
    "Meio/Ideia",
    "VOX",
    "PoderData/Aya",
    "MDA/CNT",
    "Paraná Pesquisas",
    "Indexa",
    "Palver",
    "American Analytics Times Brasil/CNBC",
    "Instituto França",
    "Ipespe",
    "DataTrends",
)

# Variações comuns (em minúsculas) aceitas apenas no comando `adicionar`,
# que as converte para a forma canônica antes de gravar no CSV.
ALIASES = {
    "quaest": "Genial/Quaest",
    "poderdata": "PoderData/Aya",
    "nexus": "BTG/Nexus",
    "nexus/btg": "BTG/Nexus",
    "cnt/mda": "MDA/CNT",
    "bigdata": "Big Data",
    "real time big data": "Big Data",
    "atlas": "Atlas/Intel",
    "aatb/cnbc": "American Analytics Times Brasil/CNBC",
    "aatb": "American Analytics Times Brasil/CNBC",
    "american analytics": "American Analytics Times Brasil/CNBC",
    "american analytics times brasil": "American Analytics Times Brasil/CNBC",
    "frança": "Instituto França",
    "franca": "Instituto França",
    "ipespe/abrapel": "Ipespe",
    "datatrends": "DataTrends",
    "atlasintel": "Atlas/Intel",
    "futura": "Futura/Apex",
    "ideia": "Meio/Ideia",
    "parana pesquisas": "Paraná Pesquisas",
}

# ---------------------------------------------------------------------------
# Aparência dos gráficos (tons neutros funcionam em tema claro e escuro)
# ---------------------------------------------------------------------------
COR_LULA = "#dc2626"
COR_FLAVIO = "#2563eb"
COR_NULO = "#94a3b8"
COR_TEXTO = "#64748b"
COR_GRADE = "rgba(148, 163, 184, 0.25)"
FONTE = "Inter, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif"
