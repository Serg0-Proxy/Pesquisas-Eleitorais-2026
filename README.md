# Pesquisas Eleitorais 2026 - 2º Turno

Projeto de análise de dados que acompanha as pesquisas de intenção de voto e de rejeição do 2º turno da eleição presidencial de 2026 (Lula x Flávio Bolsonaro). Os dados ficam em um CSV, as médias e os gráficos são calculados em Python (pandas e Plotly) e o resultado é um dashboard em HTML.

Dashboard online: https://serg0-proxy.github.io/Pesquisas-Eleitorais-2026/

## Dados

Um único arquivo, `data/pesquisas.csv`, com uma pesquisa por linha: 193 pesquisas de 20 institutos, de janeiro a outubro de 2026.

| Coluna | Descrição |
|--------|-----------|
| `data` | último dia de campo da pesquisa (não a data de publicação) |
| `instituto` | nome do instituto, sempre na forma canônica definida em `config.py` |
| `lula`, `flavio`, `nulo` | intenção de voto em %; os três somam 100% |
| `rej_lula`, `rej_flavio` | rejeição em %; sempre os dois preenchidos ou os dois vazios |
| `margem_erro` | margem de erro, em pontos percentuais |

Entram só pesquisas nacionais de institutos registrados no TSE. Os dados pertencem aos institutos, e o projeto não tem vínculo com campanhas.

## Estrutura do projeto

```
Pesquisas-Eleitorais-2026/
├── data/
│   └── pesquisas.csv          # uma pesquisa por linha
├── src/pesquisas_eleitorais/
│   ├── config.py              # institutos, períodos e cores
│   ├── data.py                # leitura e validação do CSV
│   ├── metrics.py             # médias, placar e eixos
│   ├── charts.py              # gráficos Plotly
│   ├── build.py               # gera o HTML
│   ├── cli.py                 # comandos do terminal
│   └── templates/             # HTML (Jinja2) e CSS
├── tests/                     # testes com pytest
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Tecnologias

- Python 3.10+
- pandas e NumPy
- Plotly
- Jinja2
- pytest e ruff

## Como executar

1. Clone o repositório:

   ```
   git clone https://github.com/Serg0-Proxy/Pesquisas-Eleitorais-2026.git
   cd Pesquisas-Eleitorais-2026
   ```
2. Crie e ative um ambiente virtual:

   ```
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Instale as dependências:

   ```
   pip install -r requirements.txt
   ```
4. Gere o dashboard:

   ```
   pesquisas build --offline
   ```

O arquivo `site/index.html` é criado e pode ser aberto direto no navegador.

Outros comandos:

- `pesquisas validar`: confere o CSV (nomes, datas, somas e duplicatas)
- `pesquisas medias`: mostra as médias por período no terminal
- `pesquisas ordenar`: ordena o CSV por data
- `pesquisas adicionar`: inclui uma pesquisa, por exemplo:

  ```
  pesquisas adicionar --data 2026-10-20 --instituto "Genial/Quaest" --lula 44 --flavio 45 --nulo 11 --margem-erro 2 --rej-lula 47 --rej-flavio 52
  ```

Para rodar os testes:

```
pip install pytest ruff
pytest
ruff check .
```

## Como funciona

- Médias: de cada instituto entra só a pesquisa mais recente do período, para quem publica muito não pesar mais que os outros. Na rejeição, vale a mais recente que tenha rejeição.
- Períodos: os meses seguem o calendário. Outubro é dividido em quatro semanas que terminam no domingo (Out 1: até 04/10, Out 2: 05 a 11/10, Out 3: 12 a 18/10 e Out 4: 19 a 25/10), usadas nos gráficos de média e no placar. KPIs, tabelas e zoom da evolução dividem outubro em antes (até 05/10) e depois do 1º turno (a partir de 06/10).
- Arredondamento: meio para cima (46,95 vira 47,0), feito com `Decimal`.
- Placar: conta todas as pesquisas do mês, sem a regra de uma por instituto.
- Vantagem: só conta como "à frente" quando a diferença passa da margem de erro da pesquisa; senão é empate técnico.
- Votos válidos: cada candidato sobre a soma dos dois, sem nulo, branco e indecisos.
- O HTML só exibe: todos os valores e configurações dos gráficos vêm calculados do Python.
