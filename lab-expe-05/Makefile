PYTHON ?= python3
N ?= 30
CSV ?= data/full.csv

.PHONY: help all test config-check plan-pilot plan-full pilot full validate validate-full clean-data analysis

help:
	@printf '%s\n' \
	  'make test          — testes unitários e sintaxe Python' \
	  'make config-check  — valida Compose sem build nem execução' \
	  'make plan-pilot    — lista um plano piloto sem executar benchmarks' \
	  'make pilot         — executa o piloto (requer preflight, JAR, heaps e --execute)' \
	  'make full          — executa a coleta completa (requer preflight, JAR, heaps e --execute)' \
	  'make validate CSV=data/pilot.csv N=5 — valida esquema e arquivos brutos' \
	  'make all           — testes, Compose, validação/limpeza de full.csv e análise C'

# Fluxo completo: nunca coleta automaticamente. Falha claramente se faltarem dados ou pipeline.
all: test config-check validate-full clean-data analysis

test:
	$(PYTHON) -m py_compile scripts/validate_schema.py scripts/run_dacapo.py scripts/clean_data.py
	$(PYTHON) -m pytest tests -q

config-check:
	docker compose -f env/compose.yaml config --quiet

plan-pilot:
	$(PYTHON) scripts/run_dacapo.py --mode pilot --blocks 5

plan-full:
	$(PYTHON) scripts/run_dacapo.py --mode full --blocks 30

pilot:
	$(PYTHON) scripts/run_dacapo.py --mode pilot --execute

full:
	$(PYTHON) scripts/run_dacapo.py --mode full --execute

validate:
	$(PYTHON) scripts/validate_schema.py "$(CSV)" --n "$(N)" --base-dir data/raw

validate-full:
	@test -f data/full.csv || { echo 'Bloqueado: data/full.csv ainda não foi coletado.' >&2; exit 2; }
	$(PYTHON) scripts/validate_schema.py data/full.csv --n "$(N)" --base-dir data/raw

clean-data: validate-full
	$(PYTHON) scripts/clean_data.py data/full.csv --n "$(N)" --base-dir data/raw --force

analysis:
	@test -f analysis/run.py || { echo 'Bloqueado: analysis/run.py (pipeline da issue C) ainda não foi integrado.' >&2; exit 2; }
	@test -f data/processed/clean.csv || { echo 'Bloqueado: clean.csv não foi produzido.' >&2; exit 2; }
	$(PYTHON) analysis/run.py
