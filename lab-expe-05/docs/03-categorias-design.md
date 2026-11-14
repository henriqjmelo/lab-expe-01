# As 7 categorias da pesquisa (versão 1) e o design do experimento

**Versão 1**, escrita na S01 antes da coleta. A versão revisada, comparada com o que foi realmente feito, é a da issue S03-A3 e termina com um changelog v1 → v2 no fim deste arquivo.

> **Terminologia.** Os nomes das categorias e das opções seguem o material da Aula 8. Esta versão usa os nomes mais comuns da literatura; se o material da aula usar outro termo para alguma opção, trocar o termo e manter a justificativa.

## 1. As 7 categorias

| Categoria | Classificação | Justificativa |
| :--- | :--- | :--- |
| **Natureza** | Aplicada | O estudo não busca uma teoria nova sobre coleta de lixo. Busca uma resposta que um operador de aplicações Java use para escolher o coletor e o tamanho do heap. |
| **Objetivos** | Explicativa | A pergunta é causal: o **coletor** (e o heap) **causa** diferença de tempo, latência de cauda e uso de recursos? Não se limita a descrever os valores de cada coletor (descritiva) nem a procurar padrões sem hipótese (exploratória). |
| **Abordagem** | Quantitativa | Todas as métricas são numéricas, de escala de razão, e a conclusão vem de teste de hipótese, tamanho do efeito e intervalo de confiança. |
| **Procedimentos** | Experimento em laboratório | O grupo manipula as variáveis independentes (coletor, heap, benchmark) num ambiente controlado: contêiner com CPU e memória fixas, mesma imagem, mesma máquina. |
| **Tempo** | Transversal | A coleta acontece numa janela curta, sem acompanhar o mesmo sistema por semanas. Cada invocação de JVM é uma medida independente no tempo. |
| **Controle** | Experimental | Os tratamentos são atribuídos pelo grupo (não observados), as demais variáveis são fixadas e a **ordem das execuções é randomizada em blocos**. |
| **Nível de evidência** | Moderado (a rever na S03) | Controle interno alto, mas a validade externa é limitada: 1 máquina, 1 JDK, 4 benchmarks, 1 número de CPUs, carga sintética. Resultados são evidência sobre **este** desenho, não sobre qualquer aplicação. |

## 2. Pontos fracos da classificação

- **"Experimento" com unidades que não são pessoas.** As unidades experimentais são invocações de JVM, que não têm heterogeneidade própria como participantes humanos. A randomização aqui **não** equilibra características das unidades: ela impede que o tratamento coincida com deriva da máquina (temperatura, processos em segundo plano). A defesa de "experimento" e não "quase-experimento" é que o grupo atribui o tratamento a cada execução e controla a ordem.
- **Transversal, mas não instantâneo.** A coleta leva horas, e mudanças na máquina ao longo desse tempo são uma ameaça interna, tratadas por blocos randomizados e pelo gráfico de repetição × tempo.
- **Nível de evidência.** "Moderado" é uma classificação a discutir: o controle é alto, mas há replicação em outra máquina só de um subconjunto (S02-A2).
- **Explicativa, mas sem mecanismo.** O estudo mostrará **que** os coletores diferem e quanto, não **por que** (isso exigiria análise do funcionamento interno de cada coletor).

## 3. Design do experimento

### 3.1 Estrutura fatorial

Fatorial completo **coletor (2) × heap (2) × benchmark (4) = 16 células**.

| Fator | Níveis | Observação |
| :--- | :--- | :--- |
| Coletor | G1, ZGC | variável independente principal |
| Heap | 2 níveis | múltiplos do heap mínimo de cada benchmark (definidos na S01-B2) |
| Benchmark | 4 | 2 sensíveis a latência e 2 de vazão (definidos na S01-B2) |

- **Repetições:** N invocações de JVM por célula, **N = 30 provisório** (a S01-C3 confirma ou pede mais blocos). Total provisório: 16 × 30 = **480 runs**. O piloto são 5 repetições por célula: **80 runs**.
- **Unidade experimental:** **uma invocação de JVM** (um processo `java` que executa o benchmark com **k iterações internas**, valor a decidir no piloto: S01-B3 e S01-C3, contrato seção 8). A medida é a **iteração final**, depois do aquecimento do JIT. A iteração do benchmark não é a unidade, porque as iterações dentro de uma mesma invocação compartilham o estado da JVM e não são independentes.
- **Comparações de interesse:** o coletor é comparado **dentro de cada par heap × benchmark**: **8 pares**, 4 deles com p99 (benchmarks com latência). Daí os **12 testes confirmatórios** do contrato.

### 3.2 Randomização

- Um **bloco** é uma repetição de cada uma das 16 células. Dentro de cada bloco a **ordem das 16 execuções é embaralhada** com semente registrada (coluna `seed`).
- Motivo: evitar que um coletor rode sempre antes ou depois do outro, o que confundiria o coletor com horário, temperatura ou cache do SO.
- O desenho é de **blocos completos randomizados**: cada bloco roda todas as 16 células uma vez, e o que se randomiza é a **ordem** dentro do bloco.
- O bloco como unidade de coleta também permite parar, retomar e estender a coleta sem refazer nada (ver o contrato, seção 6).

### 3.3 Instrumentação

- **Carga:** suíte DaCapo Chopin, versão exata e todas as opções de linha de comando registradas.
- **Tempo e latência:** saída do próprio DaCapo (iteração final; p99 nos benchmarks com métrica de latência).
- **Pausas de GC:** log de GC (`-Xlog:gc*`), de onde sai a pausa máxima e a confirmação de qual coletor rodou.
- **CPU e memória:** medição fixa dentro do contêiner (ex.: `/usr/bin/time -v`: user + sys e pico de RSS).
- **Ambiente:** imagem Eclipse Temurin JDK 25 com tag e digest fixados; contêiner com CPUs e memória fixas; coletor fixado explicitamente; `-Xms` = `-Xmx`.

### 3.4 Operação

| Quem | O quê | Onde |
| :--- | :--- | :--- |
| B (Henrique) | Roda o piloto e a coleta completa, em blocos, e valida os dados | Máquina oficial de coleta |
| A (Gabriel) | Replica um subconjunto seguindo só o README | Outra máquina ou outro dia |
| C (Guilherme) | Analisa os blocos validados; ensaia o pipeline em dados sintéticos | Qualquer máquina |

Antes da coleta: pré-voo (máquina na tomada, plano de energia em desempenho, atualizações desligadas, nada pesado aberto) e um diário de coleta com qualquer evento.

## 4. Pergunta que o professor pode fazer

**"Por que a unidade experimental é a invocação da JVM e não a iteração do benchmark?"**
Porque as iterações de uma mesma invocação compartilham a JVM (JIT, heap, estado do coletor) e portanto não são independentes. Cada invocação é um processo novo e é a menor unidade que o grupo pode atribuir a um tratamento de forma independente.

**"Por que é experimento e não quase-experimento?"**
Porque o grupo atribui o tratamento (coletor e heap) a cada execução, controla as demais variáveis e randomiza a ordem. O limite é que as unidades são invocações e não pessoas, então a randomização protege contra deriva do ambiente, não contra diferenças entre sujeitos.

## Changelog v1 → v2

*(preenchido na issue S03-A3)*
