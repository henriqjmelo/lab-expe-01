# Laboratório 05 — OpenJDK 25: G1 × ZGC

> **Disciplina:** Laboratório de Experimentação de Software
> **Curso:** Engenharia de Software (6º Período — Noite)
> **Professor:** Danilo Maia
> **Pontuação:** 20 pontos (S01 5 + S02 5 + S03 5 + Documento final e apresentação 5)

---

## Integrantes e papéis

| Papel | Integrante | Responsável por |
| :--- | :--- | :--- |
| A — Planejamento e Método | Gabriel Afonso | Critérios do software, GQM, categorias, validade, conclusões, dashboard, replicação |
| B — Instrumentação e Operação | Henrique Jardim Melo | Ambiente Docker, benchmarks, script de coleta, coleta, validação dos dados, reprodutibilidade |
| C — Análise e Impacto | Guilherme Costa | Plano de análise, pipeline, testes, efeito, impacto |

Revisão cruzada: **A é revisado por B, B por C, C por A.**

---

## Links Importantes

* Repositório: `https://github.com/henriqjmelo/lab-expe-01`
* GitHub Projects (v2): `https://github.com/users/henriqjmelo/projects/1`
* Contrato entre os papéis: [docs/00-contrato.md](docs/00-contrato.md)

---

## O estudo

**Pergunta.** O coletor de lixo ZGC reduz pausas e latência de cauda em troca de quanto de vazão, CPU e memória, comparado ao G1, e isso muda com o tamanho do heap?

| Item | Escolha |
| :--- | :--- |
| Software | OpenJDK 25 LTS (Eclipse Temurin, em Docker) |
| Tipo | Experimento controlado em laboratório |
| Carga | Suíte DaCapo Chopin |
| Design | coletor (2) × heap (2) × benchmark (4) = 16 células, N invocações de JVM por célula |
| Confirmatórias | tempo da iteração e latência p99 (12 testes, Holm) |
| Exploratórias | pausa máxima de GC, CPU e pico de RSS |

O objeto de pesquisa é a **JVM em execução**, não o repositório do OpenJDK no GitHub.

---

## Como ninguém trava ninguém

As interfaces entre os papéis estão escritas em [docs/00-contrato.md](docs/00-contrato.md): esquema do CSV, caminhos, marcos e coleta em blocos. Resumo:

- C constrói e testa a análise com **dados sintéticos** e troca a entrada quando o dado real chega.
- B coleta em **blocos** com N = 30 provisório, sem esperar a decisão de C.
- C analisa os blocos já validados; só a versão final espera a tag `data-v1`.
- A revisão **não bloqueia**: o dependente trabalha a partir da branch do PR.

---

## Estrutura

```text
lab-expe-05/
  docs/        contrato, critérios, GQM, categorias, plano de análise, ameaças, relatório
  env/         Dockerfile, compose.yaml, flags.diff
  scripts/     coleta, validação, dados sintéticos, impacto
  analysis/    pipeline de análise
  data/        raw/, processed/, pilot.csv, full.csv, sintetico.csv
  results/     tabelas/ e figures/
```

## Como executar

A definir nas issues S01-B1 (ambiente), S01-C2 (análise) e S03-B1 (`make all`).

Validar um CSV de dados contra o contrato (S01-A4):

```bash
python lab-expe-05/scripts/validate_schema.py data/pilot.csv            # esquema
python lab-expe-05/scripts/validate_schema.py data/full.csv --n 30      # N linhas por célula
python -m pytest lab-expe-05/tests -q                                   # testes do validador
```

---

## Issues por sprint

### Lab05S01: proposta e piloto (5 pts)

| Código | Issue | Título | Responsável |
| :--- | :--- | :--- | :--- |
| S01-A0 | [#218](https://github.com/henriqjmelo/lab-expe-01/issues/218) | Contrato de dados e estrutura do repositório | Gabriel |
| S01-A1 | [#219](https://github.com/henriqjmelo/lab-expe-01/issues/219) | Comprovar os 3 critérios do software (OpenJDK 25) com evidências | Gabriel |
| S01-A2 | [#220](https://github.com/henriqjmelo/lab-expe-01/issues/220) | GQM, perguntas de pesquisa, hipóteses e variáveis | Gabriel |
| S01-A3 | [#221](https://github.com/henriqjmelo/lab-expe-01/issues/221) | 7 categorias da pesquisa (versão 1) e design do experimento | Gabriel |
| S01-A4 | [#222](https://github.com/henriqjmelo/lab-expe-01/issues/222) | Validador de esquema dos dados (código + testes) | Gabriel |
| S01-B1 | [#223](https://github.com/henriqjmelo/lab-expe-01/issues/223) | Ambiente Docker: JDK 25 com G1 e ZGC sob recursos idênticos + ética | Henrique |
| S01-B2 | [#224](https://github.com/henriqjmelo/lab-expe-01/issues/224) | Seleção dos 4 benchmarks e do heap mínimo de cada um | Henrique |
| S01-B3 | [#225](https://github.com/henriqjmelo/lab-expe-01/issues/225) | Script de coleta em blocos (DaCapo → CSV) e coleta piloto | Henrique |
| S01-C1 | [#226](https://github.com/henriqjmelo/lab-expe-01/issues/226) | Plano de análise pré-registrado | Guilherme |
| S01-C2 | [#227](https://github.com/henriqjmelo/lab-expe-01/issues/227) | Pipeline de análise rodando em dados sintéticos | Guilherme |
| S01-C3 | [#228](https://github.com/henriqjmelo/lab-expe-01/issues/228) | Análise do piloto: nº de repetições, iterações e plano B | Guilherme |

### Lab05S02: coleta, análise e validade (5 pts)

| Código | Issue | Título | Responsável |
| :--- | :--- | :--- | :--- |
| S02-B1 | [#229](https://github.com/henriqjmelo/lab-expe-01/issues/229) | Coleta completa em blocos (16 células × N) | Henrique |
| S02-B2 | [#230](https://github.com/henriqjmelo/lab-expe-01/issues/230) | Validar e versionar os dados (tag data-v1) | Henrique |
| S02-A1 | [#231](https://github.com/henriqjmelo/lab-expe-01/issues/231) | Ameaças à validade (4 tipos) e matriz de rastreabilidade | Gabriel |
| S02-A2 | [#232](https://github.com/henriqjmelo/lab-expe-01/issues/232) | Replicação independente de um subconjunto (outra máquina) | Gabriel |
| S02-C1 | [#233](https://github.com/henriqjmelo/lab-expe-01/issues/233) | Descritiva e gráficos nos dados reais | Guilherme |
| S02-C2 | [#234](https://github.com/henriqjmelo/lab-expe-01/issues/234) | Testes confirmatórios (RQ1): 12 testes, efeito e IC | Guilherme |
| S02-C3 | [#235](https://github.com/henriqjmelo/lab-expe-01/issues/235) | Interação GC × heap (RQ2), exploratórias e poder planejado × observado | Guilherme |

### Lab05S03: impacto e conclusões (5 pts)

| Código | Issue | Título | Responsável |
| :--- | :--- | :--- | :--- |
| S03-A1 | [#236](https://github.com/henriqjmelo/lab-expe-01/issues/236) | Dashboard interativo (reuso do Lab04) | Gabriel |
| S03-A2 | [#237](https://github.com/henriqjmelo/lab-expe-01/issues/237) | Conclusões, limitações e o que não dá para afirmar | Gabriel |
| S03-A3 | [#238](https://github.com/henriqjmelo/lab-expe-01/issues/238) | 7 categorias revisadas e justificadas | Gabriel |
| S03-B1 | [#239](https://github.com/henriqjmelo/lab-expe-01/issues/239) | Mapa "reaproveitado × novo" dos Labs e pacote reproduzível (make all) | Henrique |
| S03-B2 | [#240](https://github.com/henriqjmelo/lab-expe-01/issues/240) | Rascunho do documento: método, ambiente e coleta | Henrique |
| S03-C1 | [#241](https://github.com/henriqjmelo/lab-expe-01/issues/241) | Números públicos de impacto (com fonte, data e publicador) | Guilherme |
| S03-C2 | [#242](https://github.com/henriqjmelo/lab-expe-01/issues/242) | Cálculo de impacto com cenários | Guilherme |
| S03-C3 | [#243](https://github.com/henriqjmelo/lab-expe-01/issues/243) | Rascunho de resultados, impacto e figuras finais | Guilherme |

### Documento final e apresentação (5 pts)

| Código | Issue | Título | Responsável |
| :--- | :--- | :--- | :--- |
| F-A1 | [#244](https://github.com/henriqjmelo/lab-expe-01/issues/244) | Documento: coerência lógica de ponta a ponta | Gabriel |
| F-B1 | [#245](https://github.com/henriqjmelo/lab-expe-01/issues/245) | Reprodutibilidade e release final do repositório | Henrique |
| F-C1 | [#246](https://github.com/henriqjmelo/lab-expe-01/issues/246) | Conferência de todos os números do documento e dos slides | Guilherme |
| F-A2 | [#247](https://github.com/henriqjmelo/lab-expe-01/issues/247) | Roteiro e slides: bloco A (software, categorias e GQM, ~3,5 min) | Gabriel |
| F-B2 | [#248](https://github.com/henriqjmelo/lab-expe-01/issues/248) | Roteiro e slides: bloco B (ambiente, coleta, reuso dos Labs e ameaças, ~3 min) | Henrique |
| F-C2 | [#249](https://github.com/henriqjmelo/lab-expe-01/issues/249) | Roteiro e slides: bloco C (resultados e impacto, ~3,5 min) | Guilherme |
| F-ENS | [#250](https://github.com/henriqjmelo/lab-expe-01/issues/250) | Ensaio cronometrado e rodada de perguntas cruzadas | Gabriel + Henrique + Guilherme |
| F-REV | [#251](https://github.com/henriqjmelo/lab-expe-01/issues/251) | Revisão final cruzada do documento e dos slides | Gabriel + Henrique + Guilherme |

---

## Regras do board

1. Todo commit cita o número da Issue (ex.: `#223 fixa o coletor no compose`); commit sem referência não conta.
2. Cada integrante é assignee de ao menos uma Issue com código em cada sprint.
3. Cada entrega vai numa branch própria, mergeada via Pull Request referenciando a Issue.
4. O revisor responde em até 48 h; a revisão não bloqueia quem depende do trabalho.
