# Contrato do Lab05

Este arquivo fixa as **interfaces entre os três papéis**. Cada um trabalha contra o contrato, não contra o trabalho em andamento do outro. Se algo aqui precisar mudar, quem percebe abre um PR neste arquivo e avisa o grupo; a mudança vale a partir do merge.

## 1. Decisões fixas

| Item | Decisão |
| :--- | :--- |
| Software | OpenJDK 25 LTS, build Eclipse Temurin, em Docker. Conferir no dia o último `25.0.x` e fixar tag e digest |
| Pergunta | O ZGC reduz pausas e latência de cauda em troca de quanto de vazão, CPU e memória, comparado ao G1, e isso muda com o tamanho do heap? |
| Tipo de estudo | Experimento controlado em laboratório |
| Carga | Suíte DaCapo Chopin (`.jar` baixado do site oficial; não é mineração de repositório). Registrar o nome exato da versão e **todas** as opções de linha de comando |
| Coletores | G1 e ZGC, fixados explicitamente (`-XX:+UseG1GC`, `-XX:+UseZGC`). No JDK 25 o ZGC é só o modo geracional (JEP 490, conferir) |
| Heap | `-Xms` = `-Xmx`, 2 níveis, múltiplos do heap mínimo de cada benchmark |
| Benchmarks | 4 (2 sensíveis a latência, 2 de vazão), escolhidos na issue S01-B2 |
| Unidade experimental | Uma invocação de JVM (mede-se a iteração final, depois do aquecimento do JIT) |
| Métricas confirmatórias | Tempo da iteração (`exec_ms`) e latência p99 (`lat_p99_ms`) |
| Métricas exploratórias | Pausa máxima de GC, CPU total, pico de RSS |
| α | 0,05, com Holm |

## 2. Design e contagem de testes

- 16 células = coletor (2) × heap (2) × benchmark (4).
- A comparação G1 × ZGC acontece dentro de cada par heap × benchmark: **8 pares**, não 16.
- O p99 só existe nos benchmarks com métrica de latência (2 benchmarks × 2 heaps = **4 pares**).
- **Testes confirmatórios: 8 (tempo) + 4 (p99) = 12.** Holm sobre esses 12. Reconferir depois da S01-B2.
- RQ2 (interação GC × heap) é um modelo à parte, sobre log(tempo).
- O número de CPUs do contêiner é **variável controlada**, com um valor só. Entra na validade externa. Um segundo nível é opcional e só se decide depois do piloto.

## 3. Esquema do CSV (uma linha por invocação de JVM)

Vale para `data/pilot.csv`, `data/full.csv`, `data/processed/clean.csv` e `data/sintetico.csv`.

| Coluna | Tipo | Regra |
| :--- | :--- | :--- |
| `run_id` | texto | único, ex.: `ZGC-h2-r07-<benchmark>` |
| `rep` | inteiro | 1 a N; **é o bloco** (1 bloco = 1 repetição de cada uma das 16 células) |
| `timestamp` | ISO 8601 UTC | |
| `host` | texto | identifica a máquina |
| `jdk_version` | texto | saída de `java -version` |
| `image_digest` | texto | digest da imagem Temurin |
| `gc` | `G1` ou `ZGC` | |
| `cpus` | inteiro | limite de CPUs do contêiner |
| `heap_mult` | decimal | múltiplo do heap mínimo |
| `heap_mb` | inteiro | `-Xms` = `-Xmx` |
| `benchmark` | texto | nome DaCapo |
| `iterations` | inteiro | iterações internas; a medida é a última |
| `exec_ms` | decimal | tempo da iteração final |
| `lat_p99_ms` | decimal | **vazio** nos benchmarks sem métrica de latência (isso é dado, não erro) |
| `gc_pause_max_ms` | decimal | do log de GC |
| `cpu_s` | decimal | user + sys do processo |
| `rss_peak_mb` | decimal | pico de RSS |
| `failed` | 0 ou 1 | 1 para OOM, falha de validação do benchmark ou erro de contêiner |
| `failure_reason` | texto | vazio se `failed` = 0 |
| `seed` | inteiro | semente da ordem embaralhada do bloco (repete nas 16 linhas do mesmo bloco) |
| `raw_file` | caminho | saída bruta em `data/raw/` |
| `gc_log_file` | caminho | log de GC em `data/raw/` |

Regras que o validador (`scripts/validate_schema.py`) aplica além da tabela: `timestamp` em UTC (`Z` ou `+00:00`); em runs com `failed` = 1 as métricas (`exec_ms`, `gc_pause_max_ms`, `cpu_s`, `rss_peak_mb`) podem ficar vazias, mas `failure_reason` é obrigatório; `rep` fica em 1..N; `raw_file` e `gc_log_file` são relativos à pasta passada em `--base-dir`.

## 4. Arquivos: quem produz e quem consome

| Arquivo | Produz | Consome |
| :--- | :--- | :--- |
| `docs/00-contrato.md` | A (S01-A0) | todos |
| `scripts/validate_schema.py` | A (S01-A4) | B (S01-B3 e S02-B2), C |
| `data/sintetico.csv`, `scripts/gerar_sintetico.py` | C (S01-C2) | A, B (testes) |
| `analysis/` e `analysis/run.py` | C (S01-C2) | C, A (dashboard), B (`make all`) |
| `data/pilot.csv` | B (S01-B3) | C (S01-C3) |
| `data/full.csv` (cresce por bloco) | B (S02-B1) | C |
| `data/processed/clean.csv` + tag `data-v1` | B (S02-B2) | C, A, B |
| `results/tabelas/descritiva.csv` | C (S02-C1) | A (dashboard) |
| `results/tabelas/testes.csv` | C (S02-C2) | A, C (impacto) |
| `results/tabelas/interacao.csv`, `exploratorias.csv` | C (S02-C3) | A |
| `results/tabelas/impacto.csv` | C (S03-C2) | A (S03-A2) |
| `results/figures/` | C | A, B |

## 5. Marcos

Datas: `[PREENCHER com o calendário da disciplina]`.

| Marco | Entrega | Quando |
| :--- | :--- | :--- |
| M1 | `data/pilot.csv`, `scripts/validate_schema.py` | fim da S01 |
| M2 | blocos entram em `data/full.csv` ao longo da S02; `clean.csv` + `data-v1` | até 2/3 da S02 |
| M3 | `results/tabelas/impacto.csv` | até metade da S03 |

## 6. Coleta em blocos

Um **bloco** é uma repetição de cada uma das 16 células, em ordem embaralhada (semente gravada). A coleta pode ser parada, retomada e estendida sem refazer nada.

- N provisório: **30 blocos**. A S01-C3 pode pedir mais (`+10`); B roda no fim, sem bloquear quem já analisa.
- O piloto são 5 blocos (80 runs).
- Cada bloco concluído é anexado a `data/full.csv` e validado.

## 7. Como ninguém trava ninguém

1. **Contrato antes do trabalho.** Esquema, caminhos e marcos estão aqui.
2. **Dado sintético.** C constrói e testa o pipeline com `data/sintetico.csv` e troca a entrada quando o dado real chega. A constrói o dashboard do mesmo jeito.
3. **Entrega por bloco.** C analisa o que já foi validado; só a versão final espera a tag `data-v1`.
4. **N provisório.** B começa a coleta completa com N = 30, sem esperar a decisão de C.
5. **Revisão não bloqueia.** O revisor responde em até 48 h. O dependente pode trabalhar a partir da branch do PR; o merge exige 1 aprovação.
6. **Ordem dentro da sprint.** Cada pessoa tem issues independentes para fazer primeiro; a que depende de outra pessoa fica por último e tem sempre um plano alternativo descrito na própria issue.

Revisão cruzada: **A é revisado por B, B por C, C por A.**

## 8. Parâmetros a preencher

| Parâmetro | Valor | Definido em |
| :--- | :--- | :--- |
| CPUs e memória do contêiner | `[PREENCHER]` | S01-B1 |
| Máquina oficial de coleta | `[PREENCHER]` | S01-B1 |
| 4 benchmarks e 2 níveis de heap | `[DECIDIR no piloto]` | S01-B2 |
| Iterações internas | `[DECIDIR no piloto]` | S01-B3 / S01-C3 |
| Menor efeito de interesse prático | `[PREENCHER com o grupo]` | S01-C1 |
| Limiar de CV do plano B | 5 % `[AJUSTAR]` | S01-C3 |
| Formato do documento | Relatório em Markdown (`docs/relatorio.md`) exportado para PDF, mais o dashboard e slides. Só muda se o grupo decidir antes do início da S03 | S03-B2 |
