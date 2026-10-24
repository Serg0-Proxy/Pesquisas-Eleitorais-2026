"""Constantes do projeto: colunas do CSV, institutos canônicos, meses, cores e caminhos."""

from __future__ import annotations

from datetime import date, timedelta
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
#   - MDA/CNT, 21-23/10/2026 (BR-02136/2026): rejeição não achada nas matérias; nulo=8,7 (5,8 + 2,9)
#   - Instituto França, 21-23/10/2026 (BR-04863/2026): sem rejeição; nulo=11,3 (100 - 45,6 - 43,1)
#   - Veritá, 18-22/10/2026 (BR-06070/2026): sem rejeição; nulo=2,3 (1,4 + 0,9); instituto novo. As rodadas
#     de 12-16/10 e 15-19/10 (BR-06396/2026) só divulgaram votos válidos (51,1/48,9 e 50,7/49,3), sem
#     totais, e NÃO foram adicionadas
# Observações de dados (sem rejeição pendente):
#   - Real Time Big Data, 19-22/10/2026 (BR-09670/2026): totais 49/45 (nulo=6) conferidos na Transmissão
#     Política; válidos 52/48 (Poder360). Rejeição 36/33 ("não votaria") do Poder360 — nível bem abaixo
#     das outras pesquisas, reconferir a pergunta/metodologia
#   - VOX, 20-22/10/2026 (BR-03259/2026): nulo=10,3 (6,0 nenhum/branco/nulo + 4,3 NS/NR); válidos 50,6/49,4
#     batem; rejeição Lula 44,8 / Flávio 47,1 (Poder360, Bahia Notícias)
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
REPO_URL_PADRAO = "https://github.com/Serg0-Proxy/Pesquisas-Eleitorais-2026"

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
# Períodos dos gráficos de MÉDIA GERAL (intenção e rejeição)
# ---------------------------------------------------------------------------
# Nesses dois gráficos, outubro não usa "Out1/Out2": vira uma barra por SEMANA, e cada semana
# é identificada pelo domingo que a encerra (1º domingo = 04/10, dia do 1º turno; 2º = 11/10;
# 3º = 18/10; 4º = 25/10, dia do 2º turno). Ex.: o "2º domingo" reúne as pesquisas de 05 a 11/10.
# Os demais meses seguem como mês civil. O placar, a tabela e o zoom continuam com Out1/Out2.
MES_OUTUBRO = 10
MAX_DOMINGOS = 5  # outubro de 2026 tem quatro; o quinto só existiria com dias 26–31 (nunca usado)


def domingos_de_outubro(ano: int = ANO) -> tuple[date, ...]:
    """Os domingos de outubro do ano, em ordem (2026: 04, 11, 18 e 25)."""
    d = date(ano, MES_OUTUBRO, 1)
    d += timedelta(days=(6 - d.weekday()) % 7)
    domingos = []
    while d.month == MES_OUTUBRO:
        domingos.append(d)
        d += timedelta(days=7)
    return tuple(domingos)


def periodo_geral(dia: date) -> str:
    """Código do período das médias gerais: mês civil, ou "Dom1".."Dom5" em outubro."""
    if dia.month != MES_OUTUBRO:
        return MESES_CALENDARIO[dia.month - 1]
    domingo = dia + timedelta(days=(6 - dia.weekday()) % 7)  # domingo que encerra a semana
    primeiro = domingos_de_outubro(dia.year)[0]
    return f"Dom{(domingo - primeiro).days // 7 + 1}"


PERIODOS_GERAIS = (
    *MESES_CALENDARIO[:9],
    *(f"Dom{i}" for i in range(1, MAX_DOMINGOS + 1)),
    *MESES_CALENDARIO[10:],
)
_NOMES_DOMINGO = {
    f"Dom{i + 1}": f"{i + 1}º domingo ({d:%d/%m})" for i, d in enumerate(domingos_de_outubro())
}  # o 5º domingo (01/11) cai em novembro e não é usado em 2026
PERIODOS_GERAIS_NOME = {c: MESES_NOME[c] for c in MESES_CALENDARIO if c in MESES_NOME} | _NOMES_DOMINGO

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
    "Alfa Inteligência",
    "Veritá",
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
    "alfa": "Alfa Inteligência",
    "alfa inteligencia": "Alfa Inteligência",
    "verita": "Veritá",
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
# Caixinha de informações ao passar o mouse (e caixinhas dos gráficos): fundo OPACO, em um cinza-azulado
# suave que se destaca do fundo do card nos dois temas, com texto claro.
HOVER_FUNDO = "#2b3a52"
HOVER_BORDA = "rgba(255, 255, 255, 0.22)"
HOVER_TEXTO = "#f1f5f9"
HOVER_LULA = "#fca5a5"  # tons claros de Lula/Flávio para ler bem sobre o fundo da caixinha
HOVER_FLAVIO = "#93c5fd"
# Linha-guia vertical do hover: fina, sutil e branca no tema escuro (cinza-azulada no claro,
# onde o branco sumiria). O HTML só troca entre as duas conforme o tema do navegador.
COR_GUIA_ESCURO = "rgba(255, 255, 255, 0.45)"
COR_GUIA_CLARO = "rgba(71, 85, 105, 0.45)"
FONTE = "Inter, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif"
