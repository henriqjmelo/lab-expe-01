# GQM, perguntas de pesquisa, hipóteses e variáveis

As decisões de base (software, carga, design, métricas) estão fixadas em [00-contrato.md](00-contrato.md). Este documento as **justifica**: liga cada métrica a uma pergunta e cada pergunta ao objetivo, para que nada seja medido só porque é fácil de medir (Falácia de McNamara).

## 1. Objetivo (template de Basili)

> Analisar **os coletores de lixo G1 e ZGC do OpenJDK 25**
> com o propósito de **compará-los**
> com respeito a **desempenho (tempo, latência de cauda e uso de recursos)**
> do ponto de vista de **operadores de aplicações Java**
> no contexto de **uma JVM em contêiner com CPU e memória fixas, executando benchmarks da suíte DaCapo Chopin**.

Pergunta de pesquisa: o ZGC reduz pausas e latência de cauda em troca de quanto de vazão, CPU e memória, comparado ao G1, e isso muda com o tamanho do heap?

Nota sobre o ZGC: no JDK 25 o ZGC existe **somente no modo geracional** (o modo não geracional foi removido no JDK 24 pela JEP 490, e o geracional já era o padrão desde o JDK 23). A comparação é, portanto, G1 × ZGC geracional. Isso limita a comparação com a literatura mais antiga sobre o ZGC, que mede o modo não geracional. *Conferir na documentação do JDK 25 antes de citar.*

## 2. Perguntas e métricas

| Pergunta | Métrica (coluna do CSV) | Unidade | Escala | Medida | Papel |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Q1.** O tempo de execução difere entre os coletores? | Tempo da iteração final (`exec_ms`) | ms | Razão | Direta | **Confirmatória** |
| **Q2.** A latência de cauda difere? | Latência p99 de requisição (`lat_p99_ms`), reportada pelo DaCapo | ms | Razão | Derivada (percentil da distribuição de latências) | **Confirmatória** |
| **Q3.** As pausas de GC diferem? | Pausa máxima stop-the-world (`gc_pause_max_ms`), do log de GC | ms | Razão | Derivada (máximo sobre as pausas do log) | Exploratória |
| **Q4.** O uso de CPU e de memória difere? | CPU total do processo (`cpu_s`, user + sys) e pico de RSS (`rss_peak_mb`) | s; MB | Razão | Direta | Exploratória |
| **Q5.** A diferença entre os coletores depende do tamanho do heap? | Interação GC × heap sobre log(`exec_ms`) | adimensional | Razão (variável original; o modelo usa o log) | Derivada (contraste de log = razão de razões ZGC/G1) | **Confirmatória** (RQ2) |

O p99 só existe nos benchmarks que reportam latência (Q2 usa só esses). Nos demais, `lat_p99_ms` fica vazio, o que é dado e não erro.

### Escalas e estatísticas permitidas

Todas as métricas têm **zero absoluto** (0 ms de tempo, 0 MB de memória) e razões entre valores têm sentido ("o ZGC levou 8 % mais tempo"). Por isso são de **razão**, e são permitidos média, mediana, desvio-padrão, coeficiente de variação, razão entre médias e média geométrica. A razão ZGC/G1 é a medida de efeito natural. As variáveis `gc` e `benchmark` são **nominais**: só frequências e comparação entre grupos, nunca média.

## 3. Hipóteses

**RQ1 (Q1 e Q2).** Para cada par heap × benchmark, comparando G1 e ZGC:

- **Q1:** H₀: o `exec_ms` do G1 e o do ZGC são iguais. **Q2:** H₀: o `lat_p99_ms` do G1 e o do ZGC são iguais.
- Com o teste t de Welch (dados aproximadamente normais), H₀ é de **médias iguais**; com Mann-Whitney, de **mesma distribuição** (ordenação estocástica igual). A escolha do teste está no plano de análise.
- H₁: os coletores diferem. **Bicaudal**: o grupo não assume a direção antes de medir, embora se espere menor latência de cauda no ZGC.

São **8 pares** para o tempo (2 heaps × 4 benchmarks) e **4 pares** para o p99 (2 heaps × 2 benchmarks com latência), ou seja, **12 testes confirmatórios**, com correção de Holm.

**RQ2 (Q5).**

- H₀: não há interação coletor × heap (a razão ZGC/G1 é a mesma nos dois tamanhos de heap).
- H₁: a diferença entre os coletores muda com o tamanho do heap.

**Nível de significância:** α = 0,05, definido antes de ver os dados completos. É a **separação** entre confirmatórias e exploratórias que limita o número de testes confirmatórios (12) e a inflação do erro tipo I. Q3 e Q4 são exploratórias: recebem correção própria, definida no plano de análise (`04-plano-analise.md`), e são sempre rotuladas assim. O RQ2 é um modelo à parte (α = 0,05) e fica fora do Holm dos 12 testes.

## 4. Variáveis

| Tipo | Variável | Escala | Valores |
| :--- | :--- | :--- | :--- |
| **Independente (principal)** | Coletor | Nominal | G1, ZGC |
| **Fator** | Tamanho do heap | Razão | 2 níveis, múltiplos do heap mínimo de cada benchmark (definidos na S01-B2) |
| **Fator** | Benchmark | Nominal | 4 benchmarks DaCapo (2 de latência, 2 de vazão) |
| **Controladas** | Versão do JDK e imagem (tag e digest) | Nominal | JDK 25.0.x, uma imagem |
| | Flags da JVM, exceto coletor e heap | Nominal | iguais nas duas condições; o `diff` de `PrintFlagsFinal` deve mostrar diferenças **apenas** nas flags do coletor e nas derivadas dele (ex.: nº de threads de GC) |
| | `-Xms` = `-Xmx` | Razão | sem redimensionamento do heap |
| | **Número de CPUs** e memória do contêiner | Razão | um valor só (ver validade externa) |
| | Máquina, SO, versão do Docker, plano de energia | Nominal | uma máquina oficial de coleta |
| | Versão e opções do DaCapo, iterações internas | Nominal/Razão | fixas e registradas |
| | Resfriamento entre runs | Razão | fixo |
| **Dependentes** | `exec_ms`, `lat_p99_ms`, `gc_pause_max_ms`, `cpu_s`, `rss_peak_mb` | Razão | uma linha por invocação de JVM |

Variável **não controlável** que a randomização em blocos distribui: temperatura e carga residual da máquina ao longo da coleta.

## 5. Entidade e atributo

- **Entidade:** produto (a JVM em execução com cada coletor).
- **Atributo:** **externo**, pois só aparece com o software em uso (executando uma carga).
- **Característica da ISO/IEC 25010:** eficiência de desempenho, em duas subcaracterísticas: **comportamento temporal** (Q1, Q2, Q3) e **utilização de recursos** (Q4).

## 6. Armadilha de medição (Goodhart e Campbell)

- **Lei de Goodhart:** quando uma medida vira meta, deixa de ser uma boa medida.
- **Lei de Campbell:** quanto mais um indicador é usado para decidir, maior a pressão para distorcê-lo (e para ele distorcer o que mede).

"Pausa de GC menor" é uma métrica fácil de otimizar e **não é o mesmo que latência percebida pelo usuário**. Um coletor pode ter pausas muito curtas e ainda assim piorar a latência de cauda (por exemplo, consumindo CPU que a aplicação precisaria). Por isso:

1. A **latência de requisição (p99)** é a métrica primária de cauda; a pausa máxima é só exploratória.
2. Nenhum resultado é reportado sozinho: vazão, CPU e memória aparecem junto, para não declarar vitória só pela métrica que o ZGC favorece.
3. Heaps e benchmarks são fixados **antes** da coleta completa. Isso protege contra flexibilidade analítica (ajustar o desenho ao resultado), um risco vizinho ao de Goodhart.

O risco inverso também existe: medir só tempo de execução favoreceria o coletor de maior vazão. A combinação de métricas é a defesa contra os dois lados.

## 7. Rastreabilidade (resumo)

| Pergunta | Hipótese | Teste (plano de análise) | Entrega |
| :--- | :--- | :--- | :--- |
| Q1 | RQ1 | Welch ou Mann-Whitney, 8 pares, Holm | `results/tabelas/testes.csv` |
| Q2 | RQ1 | idem, 4 pares | `results/tabelas/testes.csv` |
| Q3 | exploratória | descritiva e testes rotulados | `results/tabelas/exploratorias.csv` |
| Q4 | exploratória | idem | `results/tabelas/exploratorias.csv` |
| Q5 | RQ2 | modelo com interação sobre log(tempo) | `results/tabelas/interacao.csv` |

A matriz completa, com a escala e a estatística de cada análise, é a da issue S02-A1 (`07-rastreabilidade.md`).

## 8. Perguntas que o professor pode fazer

- **"Por que a pausa de GC não é a métrica principal de latência?"** Porque pausa curta não garante latência de cauda baixa: o coletor concorrente do ZGC consome CPU que a aplicação disputa. O que o usuário sente é a latência da requisição, então o p99 é a métrica primária e a pausa é exploratória.
- **"Por que o tempo é de razão e o que isso permite?"** Tem zero absoluto, então razões fazem sentido. Permite reportar o efeito como razão ZGC/G1 com intervalo de confiança.
- **"Por que só duas métricas são confirmatórias?"** São três perguntas confirmatórias (Q1, Q2 e Q5), mas só duas métricas (`exec_ms` e `lat_p99_ms`; o Q5 usa `exec_ms`). Isso limita o número de testes (12) e a inflação do erro tipo I. O resto é explorado, mas rotulado como tal.
