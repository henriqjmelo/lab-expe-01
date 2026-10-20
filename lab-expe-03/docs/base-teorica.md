# Base teórica do Lab03 — medição, modelos probabilísticos e validação

Documento de apoio ao artigo. Organiza o que fundamenta as escolhas metodológicas do laboratório
e propõe o que pode ser acrescentado além das quatro métricas DORA. Os números empíricos citados
foram calculados sobre `data/dataset_dora.csv` (A1, n = 300).

---

## 1. O problema central: medimos proxies, não o atributo

A distinção de Fenton & Pfleeger entre **atributo interno** e **atributo externo** é o eixo de todo
o laboratório. Um atributo interno pode ser medido examinando apenas a própria entidade — contar
releases, contar runs de workflow. Um atributo externo só existe na relação com o ambiente —
"entregar em produção", "falhar em produção".

A tensão prática: **quem decide se importa com os atributos externos, mas só os internos são baratos
e imediatos de medir.** Toda métrica interna usada como proxy de um atributo externo é uma hipótese
que precisa ser validada.

É exatamente a posição do Lab03. O GitHub não registra "deploy" nem "falha em produção":

| Atributo externo (o que interessa) | Atributo interno (o que medimos) |
| :--- | :--- |
| Frequência de entrega em produção | Releases publicadas por semana |
| Tempo até a mudança chegar ao usuário | Intervalo commit → release |
| Mudanças que quebraram produção | Falhas de CI, ou releases seguidas de corretiva |
| Tempo até restabelecer o serviço | Episódio de falha → próximo sucesso no mesmo workflow |

A coluna da direita **não é** a da esquerda. O artigo precisa dizer isso explicitamente, e a RQ07
(sensibilidade à definição operacional) é a medida direta de quanto essa substituição custa.

### 1.1 Medição direta e derivada

Medição direta não depende de nenhuma outra: contagem de releases, duração em horas. Medição
derivada combina duas ou mais: `df = releases ÷ semanas`, `CFR = falhas ÷ total`,
`disponibilidade = MTBF ÷ (MTBF + MTTR)`.

A medição derivada **herda os problemas de escala das medidas que a compõem**. Dividir uma
quantidade por outra só é significativo se ambas admitirem a operação, e comparar valores entre
repositórios exige que numerador e denominador tenham sido definidos do mesmo modo em todos eles.

---

## 2. Escalas e significância: o que é lícito calcular

A teoria representacional define medir como um **homomorfismo** do sistema relacional empírico para
o numérico: se A é empiricamente mais complexo que B, então `m(A) > m(B)`. Se a métrica inverte ou
embaralha ordens reconhecidas, ela é inválida — e nenhum volume de dados conserta isso.

Uma afirmação sobre valores medidos é **significativa** se seu valor-verdade permanece o mesmo sob
qualquer transformação admissível da escala.

| Escala | Transformação admissível | Estatísticas válidas |
| :--- | :--- | :--- |
| Nominal | renomeação bijetiva | moda, frequências, qui-quadrado |
| Ordinal | monotônica crescente | mediana, percentis, Spearman, não paramétricos |
| Intervalar | `aM + b`, `a > 0` | média, desvio-padrão, Pearson, regressão |
| Razão | `aM`, `a > 0` | média geométrica, coeficiente de variação, razões |
| Absoluta | identidade | tudo |

**Onde isso morde no Lab03.** A classificação DORA (Elite / High / Medium / Low) é **ordinal**. Não
se tira média de categoria DORA, não se soma, não se calcula "variação percentual de nível". Na
RQ07, a comparação entre classificações tem de ser feita com medida de concordância para escala
ordinal — Kappa ponderado ou Kendall — e não com diferença aritmética de níveis.

Já as métricas de RQ01 a RQ04 são de **razão** (têm zero absoluto): releases/semana, dias, horas,
proporção. Média seria lícita pela escala. Mas, como a próxima seção mostra, a escala é apenas o
primeiro filtro — a forma da distribuição é o segundo.

---

## 3. Por que mediana e IQR: a demonstração com os dados do grupo

O enunciado manda reportar mediana e IQR. Isso costuma ser aceito como convenção; os dados da A1
permitem **demonstrar** que é obrigatório.

### 3.1 As métricas não são normais

Shapiro-Wilk sobre as métricas brutas (n = 300):

| Métrica | Assimetria | W | p | Normal? |
| :--- | ---: | ---: | ---: | :--- |
| `df_release_semana` | 8,26 | 0,269 | 1,1 × 10⁻³² | não |
| `lt_a_release_dias` | 9,96 | 0,211 | 2,6 × 10⁻³³ | não |
| `lt_b_release_dias` | 5,38 | 0,342 | 4,1 × 10⁻³¹ | não |
| `cfr_b_release` | 0,73 | 0,886 | 3,7 × 10⁻¹⁴ | não |

Rejeição em todas, com margem enorme. A assimetria à direita é a esperada: há piso natural em zero,
não há teto, e sempre existem alguns repositórios monstruosos.

### 3.2 O quanto a cauda arrasta a média

| Métrica | Média | Mediana | IQR | Máximo | Média ÷ mediana |
| :--- | ---: | ---: | :--- | ---: | ---: |
| `df_release_semana` | 1,10 | 0,35 | [0,19; 0,81] | 36,9 | **3,19×** |
| `lt_a_release_dias` | 75,25 | 13,17 | [3,08; 37,27] | 4.386,8 | **5,71×** |
| `lt_b_release_dias` | 50,41 | 8,85 | [2,82; 29,40] | 1.295,4 | **5,70×** |

A média do lead time é quase **seis vezes** a mediana. Um relatório que dissesse "o lead time típico
é de 75 dias" estaria descrevendo um repositório que não existe: três quartos da amostra está abaixo
de 37 dias.

### 3.3 E não é lognormal

A literatura trata a lognormal como o padrão das métricas de software. Testando o log:

| Métrica no log | Assimetria | W | p |
| :--- | ---: | ---: | ---: |
| `log(df_release_semana)` | 1,01 | 0,927 | 6,6 × 10⁻¹¹ |
| `log(lt_a_release_dias)` | −0,66 | 0,966 | 2,5 × 10⁻⁶ |
| `log(lt_b_release_dias)` | −0,72 | 0,965 | 1,6 × 10⁻⁶ |

O log **melhora muito** — a assimetria do `df` cai de 8,26 para 1,01, o W sobe de 0,269 para 0,927 —
mas a normalidade continua rejeitada. Achado para o artigo: as métricas DORA desta amostra são
assimétricas à direita e **aproximadamente**, não exatamente, lognormais. Isso reforça a escolha por
estatística não paramétrica em vez de "transformar e usar teste paramétrico".

---

## 4. Modelos probabilísticos: o que cabe e o que não cabe

### 4.1 Poisson e a contagem de releases

A Poisson modela contagem de eventos em intervalo fixo, sob três condições: **eventos
independentes**, **taxa média λ constante** no intervalo, e probabilidade desprezível de dois
eventos no mesmo instante. Sua marca registrada é **E[X] = Var[X] = λ**.

É o modelo natural a testar para `n_release` — número de releases publicadas na janela de um ano.

Resultado na A1:

```
n = 300     média = 57,39     variância = 28.302,10
índice de dispersão Var/E = 493,2        (Poisson exige ≈ 1)
qui-quadrado de dispersão = 147.453, gl = 299, p < 10⁻³⁰⁰
```

**A Poisson é rejeitada com folga.** A variância é 493 vezes a média — superdispersão massiva.

Isso não é um fracasso: é um resultado com interpretação de engenharia. A Poisson pressupõe taxa
constante e eventos independentes, e **nenhuma das duas hipóteses vale** em repositórios reais:

- a taxa não é constante entre repositórios — alguns lançam nightly, outros duas vezes por ano;
- as releases não são independentes dentro de um repositório — elas vêm em rajadas em torno de
  ciclos de versão, e uma corretiva é causada pela anterior.

O modelo adequado para contagem superdispersa é a **binomial negativa**, que acrescenta um parâmetro
de dispersão exatamente para acomodar heterogeneidade entre unidades.

**Como isso entra no relatório.** Como demonstração honesta do método: formula-se o modelo
candidato, testa-se a condição que ele exige, rejeita-se, e troca-se por um modelo compatível. A
superdispersão de 493× é, por si, uma caracterização da amostra — ela diz que a população de
repositórios é profundamente heterogênea em ritmo de entrega, o que também explica por que a
classificação DORA em quatro faixas tem poder discriminante limitado.

### 4.2 Exponencial, Weibull e o tempo de recuperação

A exponencial modela tempo até o próximo evento com taxa constante, com `MTTF = 1/λ`. É a única
distribuição contínua **sem memória**: `P(X > s+t | X > s) = P(X > t)` — um sistema que já funcionou
100 h tem a mesma probabilidade de durar mais 10 h que um sistema novo. A hipótese é razoável para
falhas de software disparadas por entradas aleatórias, e falsa para desgaste.

A **Weibull** generaliza, e seu parâmetro de forma β é o que interessa ao Lab03:

| β | Taxa de falha | Leitura em engenharia |
| :--- | :--- | :--- |
| β < 1 | decrescente | "mortalidade infantil": defeitos sendo corrigidos após lançamento |
| β = 1 | constante | volta a ser exponencial |
| β > 1 | crescente | desgaste — ou deterioração de arquitetura por dívida técnica |

### 4.2.1 Resultado: a recuperação tem taxa decrescente

Ajustando uma Weibull por repositório aos episódios de falha extraídos de
`data/eventos/runs.csv.gz` (238 repositórios da A1 com episódios suficientes):

```
β mediano = 0,557     IQR = [0,459; 0,724]
β < 1 em 90,3% dos repositórios
```

**A taxa de recuperação é decrescente na grande maioria dos repositórios.** A leitura em
engenharia: quanto mais tempo um episódio de falha já dura, **menor** a probabilidade instantânea de
ele ser resolvido no instante seguinte. Falhas curtas são corrigidas rápido; uma vez que o episódio
se arrasta, ele tende a se arrastar muito mais.

Isso é invisível na mediana do MTTR, que é o que a RQ04 reporta hoje — duas populações com a mesma
mediana podem ter dinâmicas opostas. E tem consequência prática: a métrica de recuperação do DORA
trata todos os episódios como equivalentes, quando os dados dizem que um episódio longo é
qualitativamente diferente de um curto, e não apenas "mais demorado".

Também explica, em parte, a assimetria de 12,9 da coluna `recuperacao_mediana_horas` — a mais
assimétrica das cinco métricas analisadas.

Resultados em `analise/saida/tabelas/distribuicoes_weibull.csv` (por repositório) e
`distribuicoes_weibull_resumo.csv` (agregado). Figura em
`analise/saida/figuras/distribuicoes-weibull.png`.

### 4.3 Normal, escore z e onde ela legitimamente aparece

A normal **não descreve** as métricas brutas, como a seção 3 mostrou. Mas ela tem dois papéis
legítimos no relatório, e confundi-los é erro comum:

**Papel 1 — padronização para comparar métricas de unidades diferentes.** O escore
`z = (x − μ) ÷ σ` diz a quantos desvios-padrão da média um valor está. Útil para construir um índice
composto, mas **inadequado aqui**, porque μ e σ não representam uma distribuição assimétrica. A
alternativa correta é padronizar por **posto percentílico**, que é invariante a transformação
monotônica e portanto lícito em escala ordinal.

**Papel 2 — distribuição amostral, via Teorema Central do Limite.** Aqui a normal entra de verdade.
Mesmo com a população assimétrica, a distribuição da *estatística* (média, ou diferença de medianas
entre grupos) tende à normal conforme n cresce, com erro padrão `σ ÷ √n`. É isso que sustenta os
intervalos de confiança e o p-valor dos testes da RQ05 e RQ06, mesmo com dados não normais.

### 4.3.1 Resultado: a convergência existe, mas é lenta

A demonstração foi construída e trouxe um achado que corrige a intuição comum. Reamostrando a
própria população da A1 (10.000 reamostragens por tamanho):

| Distribuição | Assimetria |
| :--- | ---: |
| População (`df_release_semana`) | **8,26** |
| Média de amostras de n = 30 | 1,53 |
| Média de amostras de n = 100 | 0,80 |
| Média de amostras de n = 300 | 0,49 |

A regra de bolso "n ≥ 30 basta para o TLC" **falha aqui**: com n = 30 a distribuição amostral ainda
tem assimetria 1,53 e a curva normal ajustada não acompanha o histograma. A convergência só fica
convincente perto de n = 300 — que é, não por acaso, o tamanho da amostra inteira.

Consequência direta para o artigo: os testes da RQ05 e RQ06 que usam **toda** a amostra estão em
terreno firme, mas os de **subgrupo** da RQ06 (quartis de estrelas, linguagens com poucos
repositórios) operam com n muito menor, onde a aproximação normal não vale. Isso reforça a escolha
por testes não paramétricos, que não dependem dela, e é mais um argumento para reportar tamanho de
efeito em vez de confiar no p-valor.

Figura em `analise/saida/figuras/distribuicoes-tlc.png`: os quatro painéis saem da mesma população.

---

## 5. A lógica do teste de hipótese

Teste de hipótese é prova por contradição probabilística: supõe-se ausência de efeito e verifica-se
se os dados seriam implausíveis sob essa suposição.

Quatro regras de formulação:

1. **A hipótese é sobre o parâmetro, nunca sobre a estatística.** `H₀: x̄ = 200` é incorreto — a
   média amostral já é conhecida. O objeto é o parâmetro populacional: `H₀: μ = 200`.
2. **A igualdade fica em H₀** (=, ≤, ≥) e a desigualdade estrita em H₁. Razão operacional: o teste
   precisa de um valor pontual para construir a distribuição da estatística sob H₀.
3. **A direção vem da pergunta de pesquisa**, fixada antes da coleta. Escolher a cauda depois de ver
   os dados dobra a taxa real de erro tipo I — é p-hacking.
4. **Em teste de equivalência a lógica se inverte** (TOST): define-se margem Δ e testa-se
   `H₀: |μ₁ − μ₂| ≥ Δ` contra `H₁: |μ₁ − μ₂| < Δ`, porque não rejeitar H₀ nunca é prova de
   igualdade.

A ponte com o GQM é direta: **a Question do GQM vira H₀ e H₁**, e a Metric é o que precisa ser
validado para que o teste signifique alguma coisa.

Passo que mais se esquece: **reportar tamanho de efeito**. O p-valor diz se o efeito existe; o
tamanho de efeito diz se ele importa. Com n = 600 ou 900, diferenças irrelevantes ficam
significativas — por isso ε² (Kruskal-Wallis) e delta de Cliff (Mann-Whitney) são obrigatórios, e
por isso múltiplos testes exigem correção de Holm.

---

## 6. Validação: a diferença entre engenharia e numerologia

Fenton & Pfleeger separam duas coisas que exigem validações diferentes:

| | **Medida** | **Sistema de predição** |
| :--- | :--- | :--- |
| O que é | atribui número a atributo **já existente** | estima valor **futuro ou não observado** |
| Exemplo | releases/semana mede ritmo de publicação | classificação DORA prevê desempenho de entrega |
| Validar significa | satisfazer a **condição de representação** | demonstrar **acurácia empírica** contra o observado |
| Nome | validação **interna**, teórica | validação **externa**, empírica |

**Uma medida pode ser internamente válida e inútil para predição**, e um modelo pode prever bem sem
que suas medidas sejam válidas — o que é pior, porque funciona por correlação acidental e desaba
quando o contexto muda. As duas validações são necessárias e nenhuma substitui a outra.

### 6.1 Os seis critérios da IEEE 1061

Uma métrica é considerada validada em relação a um fator de qualidade se satisfaz:

1. **Correlação** — associação estatística com o fator.
2. **Rastreamento** — quando o fator muda no tempo, a métrica muda no mesmo sentido. Correlação é
   estática; rastreamento é dinâmico.
3. **Consistência** — preserva a ordenação dos componentes.
4. **Previsibilidade** — prevê o valor do fator com erro dentro de margem declarada.
5. **Poder discriminante** — separa alta e baixa qualidade a partir de um corte.
6. **Confiabilidade** — satisfaz os anteriores de forma repetida, não num único conjunto de dados.

**Esta lista é um roteiro pronto para o artigo.** Cada proxy do Lab03 pode ser avaliado contra os
seis critérios, e vocês já têm dados para vários deles:

| Critério | Como o Lab03 já responde (ou poderia) |
| :--- | :--- |
| Correlação | RQ05: Spearman entre `df` e CFR |
| Rastreamento | RQ08 temporal: Mann-Kendall por trimestre |
| Consistência | RQ07: a ordenação muda com a definição operacional? |
| Previsibilidade | lacuna — exigiria um desfecho externo para prever |
| Poder discriminante | medido (§6.1.1): forte só no que define a faixa |
| Confiabilidade | comparação A1 × A2 × A3 — é literalmente este critério |

Vale explicitar isso: **o desenho de três amostras independentes é o critério 6 da IEEE 1061
operacionalizado.** Isso dá ao desenho amostral uma justificativa normativa, não apenas estatística.

### 6.1.1 Resultado: a classificação DORA é quase toda autorreferente

Critério 5 medido na A1 com a combinação C1 (release · LT (a) · CFR (a)). A faixa geral distribui-se
em 150 Medium, 104 High, 24 Elite e 22 Low. Kruskal-Wallis entre as faixas, p corrigido por Holm,
com os controles fora da correção:

| Atributo | Tipo | ε² | p (Holm) | Separa? |
| :--- | :--- | ---: | ---: | :--- |
| Lead time (a) | controle tautológico | 0,527 | — | — |
| Frequência de deploy | controle tautológico | 0,403 | — | — |
| CFR (b) | outra operacionalização | 0,379 | 1,0 × 10⁻²³ | sim |
| Lead time (b) | outra operacionalização | 0,296 | 4,9 × 10⁻¹⁸ | sim |
| Idade em anos | independente | 0,109 | 1,2 × 10⁻⁶ | sim |
| Contribuidores | independente | **0,022** | 0,179 | **não** |
| Estrelas | independente | **0,008** | 0,512 | **não** |

A leitura importa mais que os números. As faixas separam fortemente nas **variantes alternativas das
próprias métricas** — CFR (b) chega a ε² = 0,379, perto do controle tautológico de 0,403. Isso é
**validade convergente** entre operacionalizações, e serve à RQ07 como evidência de robustez à
definição. Não é poder discriminante no sentido da norma.

Contra atributos genuinamente independentes o resultado é magro: popularidade e tamanho de equipe
**não separam nada** (ε² de 0,008 e 0,022, não significativos depois de Holm). Só a idade separa, com
efeito pequeno.

**Isto corrige a preocupação levantada na §6.2.** O risco de a RQ05 estar medindo popularidade
disfarçada de desempenho é menor do que parecia: estrelas e contribuidores são estatisticamente
independentes da faixa DORA. A ressalva é que este é um teste sobre a faixa composta e categórica,
não sobre a correlação contínua da RQ05 — o controle por quartis continua valendo, mas como
verificação, não como suspeita forte.

**A limitação que precisa constar no artigo:** o critério 5 fala em separar alta e baixa
*qualidade*, e o estudo não tem desfecho externo de qualidade — nenhuma medida de incidente em
produção ou de satisfação que seja independente do pipeline. É a mesma lacuna do critério 4, com a
mesma causa: todo o processo de entrega é medido por proxies do próprio GitHub. As medidas CHAOSS da
#155 (tempo de resolução de bug, tempo até a primeira resposta) vêm de uma família de medição
diferente e são a melhor chance de fechar essa lacuna.

Tabela em `analise/saida/tabelas/distribuicoes_discriminancia.csv`; figura em
`analise/saida/figuras/distribuicoes-discriminancia.png`.

### 6.2 Ameaças à validade (Cook & Campbell / Wohlin)

| Tipo | Pergunta | Ameaça concreta neste laboratório |
| :--- | :--- | :--- |
| **Conclusão** | a relação estatística é real? | múltiplos testes sem correção; n pequeno em subgrupos da RQ06 |
| **Interna** | a relação é causal? | variável de confusão — **o tamanho/popularidade do repositório** |
| **Constructo** | medimos o conceito pretendido? | release ≠ deploy; falha de CI ≠ falha em produção |
| **Externa** | generaliza? | só repositórios populares, com ≥ 5 releases e ≥ 50 runs |

O exemplo canônico de confusão é instrutivo: estudos associaram métricas CK a propensão a falhas;
El Emam et al. (2001) mostraram que, **ao controlar pelo tamanho da classe**, boa parte da
associação desaparece. Classes maiores têm mais métodos, mais acoplamento e mais defeitos ao mesmo
tempo.

O análogo direto aqui: repositórios grandes e populares têm mais releases, mais runs, mais
contribuidores e mais issues de bug simultaneamente. **Qualquer correlação da RQ05 precisa ser
reexaminada controlando por tamanho** — por regressão parcial ou por estratificação em quartis de
estrelas e de contribuidores. Sem isso, a RQ05 mede popularidade disfarçada de desempenho DORA.

---

## 7. Além do DORA: o que acrescentar

O DORA é uma resposta deliberada à Lei de Goodhart — quatro métricas que se equilibram, porque
otimizar só velocidade faz a taxa de falha subir e otimizar só estabilidade trava a entrega. Mas
quatro métricas de **fluxo de entrega** não esgotam desempenho de engenharia.

### 7.1 O que a coleta GraphQL (#155) já habilita

Já coletado para a A1, com cobertura medida:

| Família | Medida | Cobertura A1 |
| :--- | :--- | ---: |
| CHAOSS / SPACE | lead time por PR | 99,3% |
| CHAOSS | tempo até a primeira resposta | 98,7% |
| CHAOSS | taxa de aceitação de PR | 99,3% |
| Flow | tempo de resolução de issue de bug | 81,0% |
| DORA "puro" | deployments e CFR reais pela API | **31,3%** |

A cobertura baixa da API de Deployments é, ela mesma, um resultado: **a API de Deployments não serve
como proxy universal**, o que justifica a escolha de releases como unidade de entrega. As medidas de
PR, com ~99%, podem ser medidas principais.

#### 7.1.1 A cobertura de Deployments não é estável entre as amostras

Com as três amostras coletadas, a cobertura da API de Deployments aparece assim:

| | A1 | A2 | A3 | 900 |
| :--- | ---: | ---: | ---: | ---: |
| Usa Deployments API | 31,3% | 41,7% | 43,3% | 38,8% |

Três amostras independentes, mesma janela, mesmos filtros, sementes diferentes. Sob permutabilidade,
a cobertura deveria oscilar ao acaso. Ela **sobe monotonicamente**, e o padrão não é ruído:

```
qui-quadrado 3x2              χ² = 10,68, gl = 2, p = 0,0048
tendência (Cochran-Armitage)  z  =  3,02,          p = 0,0026
```

**Duas explicações foram testadas e nenhuma se sustentou.**

A primeira era que a A3 teria ido mais fundo na lista de candidatos — a taxa de aceitação caiu de
~27% para 20,7% — e portanto recrutaria projetos sistematicamente diferentes. Não se confirma:
estrelas, contribuidores, idade e número de releases **não diferem entre as amostras** (Kruskal-Wallis
com p entre 0,35 e 0,92 nos quatro atributos).

A segunda era a linguagem, já que a proporção de TypeScript sobe de 26,7% para 33,7% entre A1 e A3, e
projetos web costumam ter integrações (Vercel, Netlify) que criam deployments automaticamente. A
associação entre linguagem e uso de Deployments existe, mas é fraca e vai na direção contrária ao
esperado — **Rust lidera com 51,2% e JavaScript fica em 29,8%**. E a diferença entre amostras
**sobrevive ao controle**: no grupo que não é TypeScript nem JavaScript, ela continua significativa
(p = 0,0395).

**O que fica, então, é um resultado honesto e incômodo:** a cobertura desta medida varia entre
amostras independentes do mesmo desenho, de forma estatisticamente detectável, e a causa não foi
identificada com os atributos disponíveis.

Isso importa de duas formas para o artigo:

1. **Reforça manter Deployments como subamostra de validação**, e não como medida principal. Uma
   medida cuja própria cobertura é instável entre sorteios não suporta conclusão agregada.
2. **É evidência sobre o critério 6 da IEEE 1061**, a confiabilidade — e evidência negativa, que vale
   tanto quanto a positiva. As medidas de PR passam no critério com folga (medianas praticamente
   idênticas nas três amostras); esta não passa.

Hipóteses que restam e não dá para separar com os dados atuais: a API de Deployments devolve o estado
*corrente* e as três coletas ocorreram em dias diferentes; ou o truncamento da paginação age de forma
desigual; ou é variação amostral que o teste detecta mas que não tem causa estrutural. A análise
completa de estabilidade 300 × 600 × 900 é escopo da #156.

Implementado em `cobertura_entre_amostras()`, em `analise/distribuicoes.py`.

### 7.2 Análises propostas e seu estado

Implementadas em `analise/distribuicoes.py`, com testes em `tests/test_distribuicoes.py` e saídas em
`analise/saida/`. Nenhuma delas exigiu coleta nova.

| # | Análise | Estado |
| :-- | :--- | :--- |
| 1 | Dispersão e rejeição da Poisson (§4.1) | **feita** — índice 493,2 |
| 2 | Binomial negativa como substituta (§4.1) | **feita** — ajuste por momentos |
| 3 | Weibull nos tempos de recuperação (§4.2.1) | **feita** — β mediano 0,557 |
| 4 | Normalidade, lognormalidade e centro (§3) | **feita** — 0 de 5 métricas normais |
| 5 | Demonstração do TLC por reamostragem (§4.3.1) | **feita** — figura dos quatro painéis |
| 6 | Poder discriminante das faixas DORA (§6.1.1) | **feita** — ε² de 0,008 em estrelas |
| 7 | Controle de confusão por tamanho na RQ05 (§7.4) | **feita** — não há confusão |
| 8 | Convergência entre paradigmas (§7.3) | **feita** — nenhum par chega a ρ = 0,7 |

### 7.3 Resultado: DORA e fluxo por PR são constructos distintos

Spearman por repositório nos 600 (A1 + A2), p corrigido por Holm:

| Par | n | ρ | ρ² | p (Holm) |
| :--- | ---: | ---: | ---: | ---: |
| Ritmo: releases × PRs por semana | 600 | 0,460 | 0,211 | 5,2 × 10⁻³² |
| Lead time (a): por release × por PR | 574 | 0,343 | 0,117 | 1,2 × 10⁻¹⁶ |
| Lead time (b): por release × por PR | 574 | 0,319 | 0,102 | 1,3 × 10⁻¹⁴ |
| Recuperação: CI × issue de bug | 461 | 0,216 | 0,047 | 5,7 × 10⁻⁶ |
| Falha: CFR (b) × taxa de aceitação de PR | 597 | 0,044 | 0,002 | 0,288 (n.s.) |

**Nenhum par chega perto de ρ = 0,7**, o limiar convencional para tratar duas medidas como do mesmo
constructo. O par mais direto — "quanto tempo uma mudança leva para chegar ao usuário", medido por
release e medido por PR — compartilha **10% da variância**. Os outros 90% são coisa diferente.

A leitura mais forte está no último par: o CFR por release e a taxa de aceitação de PR têm
associação **estatisticamente nula** (ρ = 0,044, p = 0,29 após Holm), mesmo com n = 597. Qualidade
medida na entrega e qualidade medida na revisão não são a mesma dimensão.

**Consequência para o artigo.** Isto é a evidência mais direta contra tratar o DORA como *a* medida
de desempenho de engenharia. Ele é *uma* lente — a da entrega por release — e outra lente legítima,
a do fluxo de trabalho por PR, ordena os mesmos 600 repositórios de maneira substancialmente
diferente. Um repositório "Elite" pela frequência de release pode ser lento na revisão, e o
contrário também.

Isso conversa diretamente com o §6.1.1: as faixas DORA separam bem o que as define, pouco além
disso, e agora se sabe que "além disso" inclui uma família inteira de medidas de fluxo que o
enunciado não cobre.

Tabela em `analise/saida/tabelas/distribuicoes_convergencia.csv`; figura em
`analise/saida/figuras/distribuicoes-convergencia.png`.

### 7.4 Resultado: a relação da RQ05 não é confusão por tamanho

A §6.2 levantou o tamanho do repositório como variável de confusão candidata, pelo paralelo com
El Emam et al. (2001). A suspeita foi testada de duas formas independentes nos 600: **estratificação**
por quartis e **correlação parcial de Spearman**.

Para `df_release_semana × cfr_b_release`, onde a associação é forte:

| Controle | Q1 | Q2 | Q3 | Q4 | ρ parcial |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Estrelas | 0,547 | 0,577 | 0,454 | 0,674 | 0,568 |
| Contribuidores | 0,612 | 0,645 | 0,529 | 0,517 | 0,593 |
| Idade em anos | 0,698 | 0,550 | 0,387 | 0,381 | 0,503 |

ρ agregado = **0,562**. A maior queda na parcial é de 0,059, e **os doze estratos mantêm o mesmo
sinal**, variando entre 0,381 e 0,698. Se a associação fosse tamanho disfarçado, ela desapareceria
dentro dos quartis. Não desaparece.

O par fraco (`cfr_a`) se comporta igual: ρ agregado 0,117, parciais entre 0,083 e 0,118, estratos
todos no mesmo sinal. Fraco, mas estável.

**A ameaça de validade interna levantada na §6.2 fica fechada**, e pode ser reportada como tal no
artigo — não como preocupação em aberto, mas como verificação feita com resultado negativo.

#### Uma observação que não é desta issue, mas vale registrar

O ρ de 0,562 entre frequência de deploy e CFR (b) é **positivo e forte**: quem publica mais releases
tem maior taxa de falha por esse proxy. Antes de interpretar isso como achado substantivo, vale
checar um acoplamento mecânico possível: o CFR (b) conta releases seguidas de uma corretiva em até
7 dias, e quem publica com mais frequência tem naturalmente mais chance de ter *alguma* release nos
7 dias seguintes a outra. A associação pode estar parcialmente embutida na definição da métrica.

Isso é exatamente o tipo de problema de validade de constructo que a §1 descreve, e é verificável:
bastaria comparar o CFR (b) observado com o esperado sob publicação aleatória na mesma cadência.
Fica como sugestão para quem cuida da RQ05 e da RQ03 (b).

Tabela em `analise/saida/tabelas/distribuicoes_confusao.csv`; figura em
`analise/saida/figuras/distribuicoes-confusao.png`.

---

## 8. Referências do material da disciplina

- Medição e teoria representacional, entidades e escalas — Fenton & Pfleeger; Aula 4.
- Validação interna e externa, seis critérios — Kitchenham, Pfleeger & Fenton (1995); IEEE 1061;
  Aula 6.
- Confusão por tamanho em métricas CK — El Emam, Benlarbi, Goel & Rai (2001).
- Distribuições, teste de hipótese, erro tipo I/II e poder — Aula 7.
- Ameaças à validade — Cook & Campbell; Wohlin et al.
- Goodhart, Campbell, McNamara e o desenho multidimensional do DORA — Aulas 1 e 2.
- DORA e SPACE — Forsgren, Humble & Kim (2018); Forsgren, Storey, Nagappan et al. (2021).
