# Mapa “reaproveitado × novo” dos Labs 01–04

Este mapa responde a duas perguntas: o que veio dos laboratórios anteriores e onde isso aparece no Lab05. A regra vale para todas as linhas: o reuso é de **prática, estrutura e ferramenta**, nunca de dado ou resultado. Nenhum número dos Labs 01–04 entra como medição do Lab05.

## Tabela

| Lab | O que foi reaproveitado | Onde aparece no Lab05 | O que ficou de fora |
| :--- | :--- | :--- | :--- |
| Lab01 | Disciplina de versionar dados, manter scripts de validação e registrar fonte e data de cada número | `requirements.txt`, `scripts/validate_schema.py`, `docs/00-contrato.md` | Coletor GraphQL, credenciais e métricas de repositório |
| Lab02 | Definição prévia de tratamentos, randomização da ordem, protocolo operacional e registro de desvios | `scripts/run_dacapo.py` (ordem por bloco e semente), `docs/06-diario-coleta.md` | Crossover com participantes e o timer de kata |
| Lab03 | Separação entre coleta, análise e dataset, testes automatizados e preocupação com retomada | `tests/`, `scripts/clean_data.py`, `Makefile`, `docs/00-contrato.md` | Mineração da API do GitHub e métricas DORA |
| Lab04 | Pin de dependências, testes, organização de outputs e análise a partir de dados explícitos | `requirements.txt`, `tests/`, `results/`, `data/processed/` | Dataset KC1, simulação Pearson × Spearman, Streamlit e seus resultados |

## Por que o Lab03 não entrou como objeto

O Lab03 é o único dos quatro cujo objeto — mineração de repositórios públicos e métricas DORA — está fora do escopo do Lab05, porque o enunciado proíbe pesquisa baseada em mineração de repositório. O que sobreviveu foi o desenho de pipeline: coletar, validar, versionar e só então analisar, com testes que rodam sem depender do dado real. Essa disciplina é a razão de `make all` existir neste repositório.

## Novo no Lab05

São específicos deste estudo, sem equivalente anterior: contêiner Temurin JDK 25 com digest fixado, flags `-XX:+UseG1GC` e `-XX:+UseZGC`, suíte DaCapo Chopin, definição de heap mínimo por benchmark, captura de pausa de GC, CPU e pico de RSS, parser de `exec_ms` e de p99, desenho 2×2×4 com 16 células e o CSV do contrato.

A implementação de `make all` separa o teste sintético da análise de `clean.csv`; o primeiro nunca é apresentado como resultado empírico.

## Rastreabilidade de arquivos

- Lab01: `lab-expe-01/README.md`, `src/` e `data/`; exemplo de coleta e reprodutibilidade de dados, não de software em operação.
- Lab02: `lab-expe-02/PROTOCOLO.md` e `DESENHO.md`; exemplo de protocolo, tratamento, ordem e log de desvios.
- Lab03: `lab-expe-03/README.md`, `pipeline/`, `analysis/` e `tests/`; exemplo de pipeline retomável e testado, com objeto e métricas diferentes.
- Lab04: `lab-expe-04/README.md`, `requirements.txt`, `src/` e `tests/`; exemplo de dependências fixadas e análise reproduzível, sem reuso do dataset ou da simulação.
- Lab05: `env/`, `scripts/`, `docs/`, `data/`, `results/` e `slides/`; material novo e específico do experimento atual.

## Estado

Mapa completo em relação aos quatro laboratórios. O pacote reproduzível depende do pipeline de análise do papel C (`analysis/run.py`), que ainda não está nesta branch: hoje `make all` testa, valida a configuração e para, corretamente, na ausência de `data/full.csv`.
