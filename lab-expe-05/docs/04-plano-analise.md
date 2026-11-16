# Plano de análise pré-registrado

> **Pré-registro.** Tudo neste documento é escrito **antes** de olhar os dados completos. O que estiver aqui vale para a S02; qualquer mudança depois da tag `data-v1` entra como *análise post-hoc*, rotulada como tal no relatório, nunca como confirmatória.
>
> Base: [00-contrato.md](00-contrato.md) (métricas, design e contagem de testes) e [02-gqm-hipoteses.md](02-gqm-hipoteses.md) (perguntas, hipóteses e escalas). Este documento não redecide nada daquilo: escolhe **o teste, o efeito, a correção e a regra de exclusão**.

| Parâmetro | Valor | Onde foi fixado |
| :--- | :--- | :--- |
| α | 0,05, bicaudal | contrato |
| Testes confirmatórios | **12** (8 de tempo + 4 de p99) | contrato §2 |
| Correção | **Holm** sobre os 12 | contrato |
| Família exploratória | Benjamini-Hochberg (FDR 0,05), separada | este documento, §8 |
| Menor efeito de interesse prático | razão ZGC/G1 de **1,05** no tempo e **1,10** no p99 | este documento, §9 |
| Unidade experimental | uma invocação de JVM | contrato |
| Escala de trabalho | **log** das métricas de tempo | este documento, §4 |

---

## 1. Confirmatórias × exploratórias

| Papel | Métrica | Pergunta | Correção |
| :--- | :--- | :--- | :--- |
| **Confirmatória** | `exec_ms` | Q1 (8 pares) | Holm sobre os 12 |
| **Confirmatória** | `lat_p99_ms` | Q2 (4 pares) | Holm sobre os 12 |
| **Confirmatória (RQ2)** | `log(exec_ms)` | Q5 (interação GC × heap) | modelo à parte, α = 0,05, fora do Holm |
| Exploratória | `gc_pause_max_ms` | Q3 | BH (FDR 0,05) na família exploratória |
| Exploratória | `cpu_s`, `rss_peak_mb` | Q4 | idem |

A separação é o que segura a inflação do erro tipo I: são 12 testes com conclusão, e o resto é descrição. Nenhuma métrica exploratória gera afirmação de "diferença significativa" no relatório — só "indício, a confirmar".

---

## 2. Estatística descritiva (S02-C1)

Para **cada célula** (coletor × heap × benchmark) e **cada métrica**:

| Estatística | Por quê |
| :--- | :--- |
| `n` e `n_falhas` | quantas invocações entraram e quantas foram excluídas |
| média, mediana | centro; a mediana aguenta a cauda longa |
| desvio-padrão, IQR | dispersão em duas leituras |
| mínimo, máximo | detecta run travado ou thermal throttling |
| **CV** (dp/média) | é o número que dispara o plano B (contrato §8, limiar 5 %) |
| média geométrica | coerente com efeito em razão (§6) |

Escala de razão (zero absoluto, razões fazem sentido) permite todas essas. `gc` e `benchmark` são nominais: só contagem.

Saída: `results/tabelas/descritiva.csv`.

Gráficos: violino + pontos por célula, ECDF por par (G1 × ZGC) e, para o p99, eixo em log.

---

## 3. Pressupostos

Verificados **por célula**, e reportados, não escondidos:

| Pressuposto | Como | O que se faz com o resultado |
| :--- | :--- | :--- |
| Normalidade | **Shapiro-Wilk** no log da métrica + **Q-Q plot** | entra na árvore de decisão (§5) |
| Homocedasticidade | **Levene** (centrado na mediana) | **descritivo apenas**: não escolhe o teste |
| Independência | garantida pelo desenho (uma JVM nova por linha, blocos embaralhados) | não se testa |

Duas decisões que precisam ficar explícitas:

1. **Levene não é um portão.** Escolher entre t clássico e Welch *depois* de olhar o Levene é um teste condicional, e isso infla o erro tipo I. O Welch é escolhido de saída (§5), e o Levene entra só como descrição de quanto as variâncias diferem.
2. **Shapiro com n = 30 tem pouco poder.** Ele raramente rejeita nesse tamanho, então o Q-Q plot é a evidência principal e o Shapiro é o critério objetivo de desempate. Por isso a tela de normalidade roda a **α = 0,01**, não 0,05: o padrão é ficar no teste paramétrico, e só sair dele diante de desvio forte.

---

## 4. Escala de trabalho: log

As métricas de tempo são de razão, positivas e com cauda à direita. O trabalho é feito no **log**:

- `log` transforma a razão ZGC/G1 numa **diferença de médias**, que é exatamente o que um teste t estima;
- a cauda longa da latência fica aproximadamente simétrica em log;
- a dispersão relativa (CV) de cada célula vira dispersão absoluta comparável entre células com tempos muito diferentes — sem isso, um benchmark de 4 s domina o modelo sobre um de 200 ms.

O resultado é sempre **traduzido de volta para razão** (`exp` da diferença) antes de ir para o relatório. Ninguém lê "diferença de 0,049 em log".

---

## 5. Árvore de decisão do teste (RQ1)

Para cada um dos 12 pares (um par = heap × benchmark, comparando G1 × ZGC):

```text
                      par heap × benchmark
                              │
              exclui as invocações com failed = 1 (§10)
                              │
                     n ≥ 10 em cada grupo?
                       ┌──────┴──────┐
                      não            sim
                       │              │
         célula marcada "sem           │
         poder"; entra só na      Shapiro-Wilk em log(métrica),
         descritiva, não no       nos DOIS grupos, α = 0,01
         Holm (e o k cai)              │
                            ┌──────────┴──────────┐
                     os dois passam          algum rejeita
                            │                      │
                  ┌─────────┴─────────┐            │
                  │  t de WELCH       │            │
                  │  sobre log        │   ┌────────┴────────┐
                  │  (principal)      │   │ MANN-WHITNEY U  │
                  └─────────┬─────────┘   │  (principal)    │
                            │             └────────┬────────┘
                   Mann-Whitney roda            Welch roda
                   como sensibilidade           como sensibilidade
                            │                      │
                            └──────────┬───────────┘
                                       │
                            os dois concordam?
                              ┌────────┴────────┐
                             sim               não
                              │                 │
                     reporta o principal   vale o MANN-WHITNEY,
                                           e o desacordo é
                                           reportado no texto
```

**Os dois testes rodam sempre**, nos 12 pares. Isso custa quase nada em código e tira do caminho a crítica de "vocês escolheram o teste que deu o resultado que queriam": a regra de desempate está escrita aqui, antes dos dados, e favorece o teste de pressuposto mais fraco.

**Por que Welch e não o t clássico.** O t clássico supõe variâncias iguais nos dois grupos. Aqui há motivo teórico para elas serem diferentes: o ZGC faz trabalho de coleta **concorrente**, disputando CPU com a aplicação, o que tende a gerar mais variação de run para run do que as pausas mais previsíveis do G1. E o preço de usar Welch quando as variâncias *são* iguais é desprezível — ele perde uma fração de grau de liberdade. Ou seja: o Welch nunca custa caro e às vezes salva. Não existe cenário em que o t clássico seja a escolha melhor aqui.

---

## 6. Tamanho do efeito e intervalo de confiança

Significância diz "a diferença existe"; efeito diz "a diferença importa". Os dois sempre juntos.

| Quando | Efeito padronizado | Efeito prático |
| :--- | :--- | :--- |
| Welch | **g de Hedges** sobre log | **razão ZGC/G1** das médias geométricas |
| Mann-Whitney | **delta de Cliff** | **razão ZGC/G1** das medianas |

- O **g de Hedges** é o d de Cohen com a correção para amostra pequena; com n = 30 por grupo a correção é pequena, mas é gratuita.
- O **delta de Cliff** é a probabilidade de um run do ZGC ser maior que um do G1, menos a inversa. Vai de −1 a +1 e não supõe distribuição nenhuma — casa com o Mann-Whitney.
- A **razão** é o número que vai para o relatório e para o cálculo de impacto (S03-C2): "o ZGC levou 1,08× o tempo do G1" é uma frase que um operador entende.

**IC 95 % por bootstrap**, porque a razão de duas médias não tem fórmula fechada confortável:

| Parâmetro | Valor |
| :--- | :--- |
| Método | percentil **BCa** (corrige viés e assimetria) |
| Reamostragens | 10 000 |
| Semente | 42 (gravada na saída) |
| Reamostragem | dentro de cada grupo, independentemente |

O IC da razão é reportado junto do p corrigido em `results/tabelas/testes.csv`.

---

## 7. Múltiplas comparações: Holm sobre 12

**Por que corrigir.** Com α = 0,05 e 12 testes sem efeito nenhum, a chance de pelo menos um falso positivo é 1 − 0,95¹² ≈ **46 %**. Quase meio a meio. Sem correção, "achamos uma diferença significativa em um dos 12 pares" não significa nada.

**Por que Holm e não Bonferroni.** O Bonferroni compara todos os p contra α/12 = 0,00417. O Holm ordena os p do menor para o maior e compara o k-ésimo contra α/(12 − k + 1): o primeiro contra α/12, o segundo contra α/11, e assim por diante, parando no primeiro que não passa. Controla **a mesma** taxa de erro familiar (FWER a 5 %) e nunca rejeita menos que o Bonferroni — só mais. É estritamente melhor, sem custo de pressuposto.

**A família é de 12.** Os 8 pares de tempo e os 4 de p99 entram no **mesmo** Holm. Separar em duas famílias de 8 e 4 seria mais permissivo e teria de ser justificado; não é o que se faz aqui.

**Se o k mudar.** A contagem depende de a S01-B2 confirmar 4 benchmarks, 2 com latência, e 2 níveis de heap. Se mudar, o k muda junto, e a mudança é registrada neste arquivo por PR **antes** da análise final. Um par descartado por `n < 10` (§5) também reduz o k, e isso é declarado na tabela de saída.

O RQ2 **fica de fora** do Holm: é um modelo único, com uma hipótese própria, testado a α = 0,05.

---

## 8. RQ2 e as exploratórias

**RQ2 — a diferença entre os coletores muda com o heap?**

Modelo linear sobre `log(exec_ms)`:

```text
log(exec_ms) ~ gc * heap_mult + gc * benchmark + bloco
```

- **O coeficiente de interesse é `gc:heap_mult`.** Num modelo em log, ele é um *contraste de razões*: quanto a razão ZGC/G1 no heap maior difere da razão no heap menor. H₀ é esse coeficiente ser zero.
- `benchmark` entra como fator, e `gc:benchmark` responde se a vantagem depende da carga.
- `bloco` (a coluna `rep`) entra como efeito para absorver deriva ao longo da coleta (máquina esquentando, carga residual). É a razão de a coleta ser em blocos embaralhados.
- Reportado: coeficiente, IC 95 %, p, e R² do modelo. Os resíduos vão para Q-Q e resíduo × ajustado; se o modelo não servir, o fallback pré-registrado é **ANOVA fatorial** com os mesmos termos sobre a mesma variável.

Saída: `results/tabelas/interacao.csv`.

**Exploratórias (Q3, Q4).** Mesma descritiva e mesma árvore de decisão, mas:

- correção **Benjamini-Hochberg** (FDR 0,05) dentro da própria família, não Holm — controlar FDR em vez de FWER é o certo quando o objetivo é levantar pistas, não decidir;
- toda linha da tabela sai com a coluna `papel = exploratoria`;
- no texto do relatório, a frase é "indício de que…", nunca "o ZGC é significativamente melhor em…".

Saída: `results/tabelas/exploratorias.csv`.

---

## 9. Poder e o menor efeito de interesse prático

### 9.1 O efeito mínimo

> **Proposta de C, a confirmar com o grupo neste PR** (o contrato §8 deixa este parâmetro em aberto).

| Métrica | Menor efeito de interesse | Por quê |
| :--- | :--- | :--- |
| `exec_ms` | razão **1,05** (5 %) | abaixo disso a diferença some dentro do ruído de uma máquina real e não justifica trocar de coletor em produção |
| `lat_p99_ms` | razão **1,10** (10 %) | a cauda é mais barulhenta; 10 % é o patamar em que um p99 começa a aparecer em SLO |

O 5 % não é arbitrário: é o mesmo número do **limiar de CV do plano B** (contrato §8). Se a variação de uma célula for maior que o efeito que se quer detectar, o experimento não tem como enxergá-lo — e é exatamente aí que o plano B dispara.

### 9.2 Poder simulado

Simulação de Monte Carlo no espírito do Lab04: 10 000 repetições, semente 42, `exec_ms` lognormal com o CV indicado, efeito de razão 1,05, teste bicaudal.

As duas colunas de α são os **limites** do Holm: ele nunca é mais rigoroso que α/12 (primeiro p da fila) nem mais permissivo que α. O poder real de cada par fica entre as duas.

| CV da célula | N = 20 | N = 30 | N = 40 | N = 50 |
| :--- | :--- | :--- | :--- | :--- |
| **2 %** | 100 % / 100 % | 100 % / 100 % | 100 % / 100 % | 100 % / 100 % |
| **3 %** | 99,9 % / 97,7 % | 100 % / 99,9 % | 100 % / 100 % | 100 % / 100 % |
| **5 %** | 85,6 % / 52,1 % | 96,0 % / **77,8 %** | 99,0 % / 91,5 % | 99,8 % / 97,4 % |
| **8 %** | 47,2 % / 14,5 % | 64,7 % / **27,4 %** | 76,6 % / 42,0 % | 86,1 % / 55,1 % |

*(cada célula: poder a α = 0,05 / poder a α/12. Mann-Whitney fica 2 a 4 pontos abaixo do Welch em todas as linhas — o preço de não supor distribuição.)*

**N mínimo para 80 % de poder no pior caso (α/12), efeito 1,05:**

| CV | 2 % | 3 % | 5 % | 8 % |
| :--- | :--- | :--- | :--- | :--- |
| N por célula | ~10 | ~15 | ~35 | ~80 |

**Leitura.** O N = 30 do contrato é adequado **se o CV ficar em até 5 %** — nesse ponto o poder no pior caso é 77,8 %, à beira do alvo de 80 %, e o poder típico é maior porque nem todo par está no fim da fila do Holm. Com CV de 8 % o experimento perde a capacidade de enxergar 5 %: o poder no pior caso cai para 27,4 %, ou seja, **quase três em cada quatro diferenças reais passariam batido**. Esse é o conteúdo técnico do limiar de 5 %: não é um número de gosto, é o ponto em que N = 30 deixa de bastar.

A decisão final de N sai da **S01-C3**, com o CV medido no piloto. A simulação reprodutível vai em `analysis/poder.py` (S01-C2); os números desta tabela são regenerados por ela.

### 9.3 Validação da simulação

Com efeito zero (razão = 1,00), N = 30: Welch rejeita em **4,83 %** dos casos e Mann-Whitney em **4,74 %**, contra os 5 % esperados. Os testes estão calibrados — o α é o que se pensa que é.

---

## 10. Regra de exclusão (escrita antes dos dados)

Uma invocação de JVM é excluída **se e somente se** tiver `failed = 1` no CSV, com um destes motivos em `failure_reason`:

| Motivo | Exemplo |
| :--- | :--- |
| `oom` | `OutOfMemoryError` ou o contêiner morto pelo OOM killer |
| `validacao_benchmark` | o DaCapo recusou a execução (`validation FAILED`) |
| `erro_container` | o contêiner não subiu, morreu ou perdeu limite de recurso |
| `interrupcao_so` | run interrompido por fora (reboot, perda de energia, sessão derrubada) |

**Nunca se exclui por valor extremo.** Um run lento é dado: ele é o comportamento de cauda que este experimento quer medir. Jogar fora o outlier seria apagar justamente o que distingue um coletor do outro no p99.

**O que fazer com a falha.** Toda invocação excluída é contada e aparece na descritiva (`n_falhas` por célula). Falha não é silêncio: se uma célula falhar mais que as outras, isso **é um resultado** (por exemplo, um coletor que estoura memória no heap menor) e vai para o relatório mesmo que a célula fique fora do teste.

**Falha de célula inteira.** Se um par perder tanta invocação que fique com `n < 10` em algum dos grupos, ele sai dos testes confirmatórios, o k do Holm cai e a tabela registra o motivo. Isso está na árvore de decisão (§5) por escrito, antes dos dados.

---

## 11. O que cada etapa produz

| Etapa | Issue | Arquivo |
| :--- | :--- | :--- |
| Descritiva e gráficos | S02-C1 | `results/tabelas/descritiva.csv`, `results/figures/` |
| 12 testes confirmatórios, efeito e IC | S02-C2 | `results/tabelas/testes.csv` |
| Interação GC × heap | S02-C3 | `results/tabelas/interacao.csv` |
| Exploratórias | S02-C3 | `results/tabelas/exploratorias.csv` |
| Poder planejado × observado | S02-C3 | `results/tabelas/poder.csv` |

Colunas mínimas de `testes.csv`: `metrica`, `benchmark`, `heap_mult`, `n_g1`, `n_zgc`, `teste`, `estatistica`, `p`, `p_holm`, `efeito`, `efeito_valor`, `razao`, `razao_ic_baixo`, `razao_ic_alto`, `papel`, `shapiro_g1`, `shapiro_zgc`, `levene_p`, `teste_sensibilidade`, `p_sensibilidade`, `concordam`.

---

## 12. Perguntas que o professor pode fazer

**"Por que só duas métricas são confirmatórias?"**
São três perguntas confirmatórias (Q1, Q2 e Q5), mas duas métricas: `exec_ms` e `lat_p99_ms` — o RQ2 reusa o `exec_ms`. Cada métrica confirmatória a mais multiplicaria os testes e a chance de falso positivo: já com 12 testes a chance de ao menos um falso positivo sem correção seria de 46 %. Pausa de GC, CPU e RSS continuam sendo medidas e reportadas, mas como exploratórias, com correção própria e rotuladas assim. Isso é uma escolha de desenho, não falta de dado.

**"Por que Welch e não o t clássico?"**
Porque o t clássico supõe variâncias iguais e há razão teórica para elas não serem: o ZGC coleta de forma concorrente, disputando CPU com a aplicação, o que acrescenta variabilidade que o G1 não tem. E o Welch custa praticamente nada quando as variâncias *são* iguais — perde uma fração de grau de liberdade. Como ele nunca é pior e às vezes é necessário, é a escolha de saída. Também não se usa o Levene como portão: escolher o teste depois de testar a variância é uma decisão condicional que infla o erro tipo I.

**"E se os dados não forem normais?"**
A árvore de decisão (§5) está escrita antes dos dados: Shapiro-Wilk a α = 0,01 no log, nos dois grupos; se algum rejeitar, o principal passa a ser o Mann-Whitney. Os dois testes rodam em todos os pares de qualquer forma, e a regra de desempate — se discordarem, vale o Mann-Whitney — também está escrita aqui.

**"Por que trabalhar em log?"**
Porque a métrica é de razão e o efeito de interesse é uma razão. Em log, razão vira diferença, que é o que o teste t estima; a cauda longa fica simétrica; e benchmarks de escalas muito diferentes passam a ser comparáveis dentro do mesmo modelo. O resultado volta para razão (`exp`) antes de ir para o relatório.

**"Por que não jogar fora os outliers?"**
Porque o outlier de latência é o objeto de estudo. O p99 existe justamente para medir a cauda; remover a cauda apagaria a diferença que se quer detectar. A exclusão é só por falha registrada de execução, e essas falhas são contadas e reportadas.

**"N = 30 é suficiente?"**
Depende do CV, e isso está simulado (§9.2). Com CV de até 5 %, sim: 77,8 % de poder no pior caso do Holm para um efeito de 5 %. Com CV de 8 %, não: 27,4 %. Por isso o plano B dispara em CV > 5 %, e a decisão final de N sai da S01-C3 com o CV medido no piloto.
