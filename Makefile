.PHONY: install test lint format build serve validar

install:   ## cria o ambiente virtual e instala o projeto (modo desenvolvimento)
	python3 -m venv .venv
	.venv/bin/pip install -e ".[dev]"

test:      ## roda a suíte de testes
	.venv/bin/pytest

lint:      ## confere estilo e possíveis erros (ruff)
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .

format:    ## formata o código automaticamente
	.venv/bin/ruff format .

validar:   ## valida data/pesquisas.csv
	.venv/bin/pesquisas validar

build: validar   ## gera o site em site/index.html
	.venv/bin/pesquisas build

serve: build     ## gera o site e o serve em http://localhost:8000
	python3 -m http.server 8000 --directory site
