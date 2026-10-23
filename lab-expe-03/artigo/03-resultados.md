# 3. Resultados (esboço v2)

> Esboço da issue #151 para discutirmos em grupo. As análises finais de cada RQ ficam nas issues #140, #141, #142 e #158.
>
> - **Dados:** amostra 1 (A1, 300 repositórios, `data/dataset_dora.csv`) e amostra 2 (A2, 300 repositórios novos, `data/amostra2/dataset_dora.csv`). A A2 usa a mesma janela e os mesmos filtros, outra semente, e exclui os repositórios da A1.
> - **Todo resultado aparece em paralelo: 300 (A1) × 600 (A1 + A2).** A comparação formal entre as duas amostras está na seção 3.10.1.
> - **Como regenerar:** `python -m analise`, de dentro de `lab-expe-03`. As figuras de 300 ficam em `analise/saida/figuras/`, as de 600 em `analise/saida/600/figuras/` e as de comparação em `analise/saida/comparacao/figuras/`.
> - O CFR (b) usa a heurística v0 de release corretiva. Ela foi validada contra o gabarito humano (seção 2.7) e **reprovada**: F1 = 0,478, precisão de 36,5%. Foi mantida por ser a melhor disponível sem recoletar, e todo resultado marcado **[NÃO VALIDADO]** deve ser lido com essa ressalva.

Seguindo o enunciado, todas as métricas são resumidas por **mediana e IQR** (1º–3º quartil).

**Tabela 3 — Resumo das métricas, 300 × 600** (`analise/saida/comparacao/tabelas/estimativas_300_600.csv`).

| Métrica | n (300 / 600) | Mediana 300 [IQR] | Mediana 600 [IQR] |
| :--- | :--- | :--- | :--- |
| Frequência de deploy (releases/semana) | 300 / 600 | 0,35 [0,19 – 0,81] | 0,34 [0,19 – 0,84] |
| Lead time (a), por release (dias) | 293 / 582 | 13,2 [3,1 – 37,3] | 12,9 [3,5 – 37,8] |
| Lead time (b), por commit (dias) | 293 / 582 | 8,8 [2,8 – 29,4] | 9,4 [2,8 – 27,3] |
| CFR (a), proxy de CI | 300 / 600 | 5,6% [2,2% – 11,2%] | 5,0% [2,1% – 10,8%] |
| CFR (b), proxy de entrega [NÃO VALIDADO] | 300 / 600 | 25,0% [5,2% – 56,5%] | 23,8% [5,2% – 50,0%] |
| Tempo de recuperação (horas) | 278 / 554 | 2,8 [0,9 – 11,9] | 3,0 [1,0 – 14,9] |

Ficam sem lead time os repositórios com mais de 300 releases na janela, porque o cálculo foi omitido para preservar a cota da API (coluna `lt_release_omitido`): 7 na A1 e 18 no total. Ficam sem tempo de recuperação os que não tiveram nenhum episódio de falha fechado na janela: 22 na A1 e 46 no total.

**Leitura geral:** com o dobro de repositórios, **todas as medianas ficam praticamente no mesmo lugar** e dentro do intervalo de confiança da amostra 1. O detalhe está na seção 3.10.1.

---

## 3.1 RQ 01 — Frequência de deploy

| Amostra 1 (300) | A1 + A2 (600) |
| :---: | :---: |
| ![Frequência, 300](../analise/saida/figuras/fig02_rq01_frequencia.png) | ![Frequência, 600](../analise/saida/600/figuras/fig02_rq01_frequencia.png) |

**Como ler.**
- Cada ponto é um repositório, posicionado pela quantidade de releases por semana. A altura não tem significado: os pontos só se empilham para não se sobrepor.
- O eixo está em escala log: cada marca multiplica o valor, e não soma.
- As faixas ao fundo são as categorias da tabela de referência DORA, com a contagem de cada uma no topo.

**Resultado.**
- A mediana é de **0,35 release por semana** (0,34 com 600), cerca de uma release a cada 20 dias.
- Quase metade é **Medium**, entre 1 por mês e 1 por semana (46% com 300; 47% com 600). Um terço é **Low**, menos de 1 por mês (33%; 32%).
- Só 2% chegam a Elite, ≥ 7 por semana: 6 repositórios com 300 e 13 com 600.

Para a discussão: release publicada é um proxy conservador de deploy. Projetos que entregam continuamente sem publicar releases ficam subestimados. Os que nem chegam a 5 releases já foram descartados no funil, onde caíram 57% (A1) e 60% (A2) dos que usam Actions.

## 3.2 RQ 02 — Lead time for changes

| Amostra 1 (300) | A1 + A2 (600) |
| :---: | :---: |
| ![Lead time, 300](../analise/saida/figuras/fig03_rq02_lead_time.png) | ![Lead time, 600](../analise/saida/600/figuras/fig03_rq02_lead_time.png) |

**Como ler.**
- Cada ponto é um repositório: a posição horizontal é o lead time pela variante (a) e a vertical, pela variante (b), ambos em escala log.
- Na diagonal cinza as duas variantes coincidem.
- As linhas de grade marcam as fronteiras DORA: 1 dia, 1 semana e 30 dias.

**Resultado.**
- As medianas são **13,2 dias pela variante (a)** e **8,8 dias pela (b)** com 300, e 12,9 e 9,4 com 600.
- Em **65% dos repositórios a variante (b) dá um valor menor**, com o ponto abaixo da diagonal (67% com 600).

**Por que as variantes divergem** (o enunciado pede essa explicação):
- A variante (a) mede o tempo desde o commit **mais antigo** de cada release. Um único commit que esperou muito puxa o valor da release inteira para cima.
- A variante (b) usa a mediana de **todos** os commits. Releases grandes pesam mais, e a maioria dos commits entra perto da data de publicação.
- Quando cada release tem poucos commits, as duas variantes convergem. Os pontos acima da diagonal merecem uma inspeção caso a caso: uma hipótese é que poucas releases concentrem muitos commits antigos.

## 3.3 RQ 03 — Change failure rate

| Amostra 1 (300) | A1 + A2 (600) |
| :---: | :---: |
| ![CFR, 300](../analise/saida/figuras/fig04_rq03_cfr.png) | ![CFR, 600](../analise/saida/600/figuras/fig04_rq03_cfr.png) |

**Como ler.**
- É uma curva acumulada. Para cada valor de CFR no eixo horizontal, a altura da curva é a % de repositórios com CFR até aquele valor.
- Quanto mais cedo a curva sobe, mais repositórios têm taxa de falha baixa.
- As linhas verticais são as fronteiras DORA (15%, 30% e 45%). O ponto marca quantos repositórios são Elite (≤ 15%).

**Resultado.** Os dois proxies contam histórias opostas, e isso se repete nas duas amostras:
- Pela **falha de CI**, CFR (a), **84% dos repositórios são Elite** com 300 (83% com 600), com mediana de 5,6% (5,0%).
- Pela **release corrigida em até 7 dias**, CFR (b), só **37%** são Elite (38%), com mediana de 25% (24%). Cerca de 23% dos repositórios têm CFR (b) igual a zero, o degrau vertical no início da curva laranja.

Para a discussão: o CFR (a) mede a falha do *pipeline*, não a falha em produção. Testes instáveis e falhas corrigidas antes do merge entram como falha. O CFR (b) depende da heurística de corretiva, e a v0 provavelmente o infla.

## 3.4 RQ 04 — Tempo de recuperação

| Amostra 1 (300) | A1 + A2 (600) |
| :---: | :---: |
| ![Recuperação, 300](../analise/saida/figuras/fig05_rq04_recuperacao.png) | ![Recuperação, 600](../analise/saida/600/figuras/fig05_rq04_recuperacao.png) |

**Como ler.**
- É a mesma lógica de curva acumulada, com a mediana do tempo de recuperação de cada repositório no eixo horizontal, em escala log.
- Os pontos marcados respondem diretamente "que % dos repositórios se recupera em menos de X".

**Resultado.**
- A mediana é de **2,8 horas** (3,0 com 600).
- Em menos de 1 hora (Elite) recuperam-se **27%** (26% com 600). Em menos de 1 dia, **83%** (82%). Em menos de 1 semana, **97%** (95%).
- Os episódios **censurados** (sem recuperação até o fim da janela) são **0,7%** dos 20.077 episódios da A1 e 0,6% dos 41.546 das duas amostras.

## 3.5 Classificação DORA (combinação de referência C1)

| Amostra 1 (300) | A1 + A2 (600) |
| :---: | :---: |
| ![Perfil DORA, 300](../analise/saida/figuras/fig06_perfil_dora.png) | ![Perfil DORA, 600](../analise/saida/600/figuras/fig06_perfil_dora.png) |

**Como ler.**
- Cada barra soma 100% dos repositórios, divididos pela categoria DORA de cada métrica.
- O azul mais escuro é Elite e o mais claro é Low.
- **Geral** é a classificação final do enunciado: a mediana dos pontos das quatro métricas (Elite = 4 … Low = 1), arredondada para baixo.

**Resultado.**

| Classificação geral | Elite | High | Medium | Low |
| :--- | ---: | ---: | ---: | ---: |
| 300 | 8% | 35% | 50% | 7% |
| 600 | 7% | 36% | 48% | 9% |

- **Cerca de metade é Medium e um terço é High**, nas duas versões.
- Cada métrica puxa para um lado diferente:
  - o **CFR (a)** quase todo em Elite puxa para cima;
  - a **frequência**, com ~80% entre Medium e Low, puxa para baixo;
  - o **lead time** está espalhado pelas quatro categorias.

## 3.6 RQ 05 — Velocidade × estabilidade

| Amostra 1 (300) | A1 + A2 (600) |
| :---: | :---: |
| ![RQ05, 300](../analise/saida/figuras/fig07_rq05_velocidade_estabilidade.png) | ![RQ05, 600](../analise/saida/600/figuras/fig07_rq05_velocidade_estabilidade.png) |

**Como ler.**
- Cada ponto é um repositório, com a frequência de deploy no eixo horizontal (escala log) e o CFR no vertical.
- O ρ de Spearman vai de −1 a 1: perto de 0 indica ausência de relação monotônica, e valores positivos indicam que o CFR sobe junto com a frequência.

**Resultado.**

| Correlação de Spearman com a frequência | 300 | 600 |
| :--- | :--- | :--- |
| CFR (a), proxy de CI | ρ = 0,18 (p = 0,002) | ρ = 0,12 (p = 0,004) |
| CFR (b), proxy de entrega [NÃO VALIDADO] | ρ = 0,60 (p < 0,001) | ρ = 0,56 (p < 0,001) |

- **Pelo CI**, a correlação é significativa mas **fraca**, e fica ainda menor com 600. Na prática, publicar mais não se associa a quebrar mais o CI.
- **Pela entrega**, a correlação é **forte** nas duas, mas em boa parte é um artefato da definição: quem publica muitas releases tem, por construção, mais chance de que uma delas seja uma "corretiva" publicada em até 7 dias.

Para a discussão: o resultado com o proxy de CI é coerente com a afirmação do DORA de que velocidade e estabilidade não são *trade-off*. O resultado com o proxy de entrega não deve ser lido como evidência do contrário antes da heurística validada (#138). Em nenhum dos dois casos a correlação implica causalidade.

## 3.7 RQ 06 — Características associadas ao desempenho

| Amostra 1 (300) | A1 + A2 (600) |
| :---: | :---: |
| ![RQ06, 300](../analise/saida/figuras/fig08_rq06_fatores.png) | ![RQ06, 600](../analise/saida/600/figuras/fig08_rq06_fatores.png) |

**Como ler.**
- Cada célula cruza uma característica do repositório (linha) com uma métrica (coluna).
- O valor é o tamanho de efeito **ε² = H/(n−1)** do teste de Kruskal-Wallis: quanto da variação da métrica a característica explica. A referência é < 0,01 desprezível, < 0,06 pequeno, < 0,14 médio e ≥ 0,14 grande.
- Os valores em **negrito com \*** continuam significativos depois da correção de Holm para os 24 testes.
- Linguagem considera as linguagens com pelo menos 15 repositórios: 6 com 300 e 10 com 600. Os demais fatores estão divididos em quartis.

**Resultado, com 300.**

| Fator | Q1 → Q4 | Lead time (a) Q1 → Q4 | Frequência Q1 → Q4 | CFR (b) Q1 → Q4 |
| :--- | :--- | :--- | :--- | :--- |
| Idade | ≤ 2 anos → > 10,9 anos | 2,0 → 28,5 dias | 0,67 → 0,23 por semana | 57% → 10% |
| Contribuidores | ≤ 48 → > 338 | 4,7 → 18,5 dias | sem efeito | 37% → 18% |
| Estrelas | quartis | 6,1 → 18,4 dias | sem efeito | sem efeito |

- **A idade é o fator com maior efeito**, e isso se mantém com 600: ε² de 0,25 → 0,21 no lead time (a), efeito grande. Repositórios com até 2 anos publicam com mais frequência e mais rápido, com lead time mediano de 2 dias contra 28,5 nos mais antigos. Também têm mais releases corretivas.
- **Equipes maiores têm lead time maior**, também nas duas: ε² de 0,11–0,14 com 300 e 0,08–0,11 com 600, efeito médio.
- **O que muda com 600: a linguagem passa a ser significativa.**
  - Com 300 ela não tinha efeito após Holm. Com 600 aparece no lead time (ε² = 0,10, efeito médio), na frequência e no CFR (b).
  - Lead time (a) mediano por linguagem: TypeScript 7,1 dias, JavaScript 8,9, Python 11,5, Rust 14,1, Go 16,7, Java 22,9, C 35,3, C++ 60,6.
  - É o exemplo clássico de **poder estatístico**: o efeito existia, mas 300 repositórios divididos em 6 grupos não bastavam para detectá-lo depois da correção.
- **O CFR (a) não se associa a nenhum fator** nas duas versões. Com 600, a idade passa a ter um efeito pequeno no tempo de recuperação (ε² = 0,03).

Para a discussão: idade, contribuidores, estrelas e linguagem são correlacionados entre si. Projetos em C/C++ tendem a ser mais antigos, e projetos antigos tendem a ser maiores e mais populares. O Kruskal-Wallis univariado não separa esses efeitos: **a #141 testa cada fator controlando os demais**. Uma hipótese é que projetos jovens estejam em fase de iteração rápida, com muitas releases de *patch*.

### Robustez (issue #141): o efeito se mantém controlando os demais fatores?

![RQ06, robustez](../analise/saida/figuras/fig16_rq06_robustez.png)

A correlação entre os três fatores contínuos é moderada: estrelas × contribuidores ρ = 0,59, contribuidores × idade ρ = 0,44, estrelas × idade ρ = 0,07 (com 600). O VIF de cada preditor na regressão fica entre 1,2 e 1,9, abaixo do corte de 5 — a multicolinearidade não impede separar os efeitos.

A correlação parcial de Spearman, controlando os outros dois fatores contínuos, confirma a leitura da idade e reduz a dos contribuidores:

- **Idade** continua associada a quase todas as métricas depois de controlar contribuidores e estrelas, com 600: ρ parcial = 0,34 no lead time (a), −0,39 na frequência, −0,34 no CFR (b), todas com p ajustado < 0,001. Na regressão log-log, o coeficiente padronizado da idade no lead time (a) é 0,52 (IC 95% [0,38; 0,65]), o maior dos três fatores.
- **Contribuidores** perde a associação com o lead time (a) depois de controlar idade e estrelas: a correlação parcial cai para ρ = 0,10 (p ajustado = 0,17, não significativo), e o coeficiente padronizado da regressão (0,21, IC [0,05; 0,37]) é menos da metade do da idade. A associação com a frequência se mantém (ρ parcial = 0,21, p ajustado < 0,001).
- **Estrelas** não tem associação parcial significativa com nenhuma métrica, em nenhuma das duas amostras.

A leitura muda em relação à seção 3.7: parte do efeito de "equipes maiores" que o Kruskal-Wallis univariado atribuía aos contribuidores parece, na verdade, efeito da idade. Repositórios mais antigos acumulam contribuidores e, ao mesmo tempo, têm lead time maior, por uma razão que não é só o tamanho da equipe. É uma associação, não uma relação causal — outras variáveis não medidas (maturidade do processo de release, dívida técnica acumulada) podem explicar a idade.

## 3.8 RQ 07 — Sensibilidade à definição operacional

| Amostra 1 (300) | A1 + A2 (600) |
| :---: | :---: |
| ![RQ07, 300](../analise/saida/figuras/fig09_rq07_sensibilidade.png) | ![RQ07, 600](../analise/saida/600/figuras/fig09_rq07_sensibilidade.png) |

**Como ler.**
- **À esquerda:** a distribuição das categorias DORA gerais em cada combinação de definições.
- **À direita:** para cada par de combinações, a % de repositórios que **ficou na mesma categoria**, **subiu** ou **desceu**, e o κ de Cohen ponderado linear, em que 1 é concordância perfeita.

| Combinação | Unidade de deploy | Lead time | CFR |
| :--- | :--- | :--- | :--- |
| C1 (referência) | release | (a) | (a) |
| C2 | release + pré-release | (b) | (b) [NÃO VALIDADO] |
| C3 | tag | (b) | (a) |

**Resultado.**

| Par | Mudam de categoria (300 → 600) | κ ponderado (300 → 600) |
| :--- | :--- | :--- |
| C1 × C2 | 36% → 35% | 0,42 → 0,46 |
| C1 × C3 | 28% → 28% | 0,63 → 0,64 |
| C2 × C3 | 33% → 34% | 0,54 → 0,53 |

- **Entre 28% e 36% dos repositórios mudam de categoria** só por trocar a definição. A proporção praticamente não muda de 300 para 600, então o efeito não é ruído amostral.
- A concordância é **moderada**, com κ entre 0,42 e 0,64.
- A direção das mudanças segue o componente trocado:
  - em **C2**, ~23% descem e ~13% sobem, porque o CFR (b) é mais severo que o (a);
  - em **C3**, ~23% sobem e só ~5% descem, porque tags são mais frequentes que releases e o lead time (b) é menor.

Para a discussão: a classificação DORA de um repositório **não é robusta à definição operacional**, e isso se mantém com o dobro da amostra. As comparações entre estudos que usam proxies diferentes precisam ser feitas com cautela. A RQ07 final (#142) deve recalcular C2 com a heurística validada.

## 3.9 RQ 08 (bônus) — Evolução temporal

> A outra opção do bônus, a rework rate, fica para a #142. Esta seção responde à RQ08 pela opção de evolução temporal (issue #158): os repositórios melhoram ou pioram nas métricas DORA ao longo dos 12 meses da janela?

**Armadilha estatística, decidida antes de olhar o resultado.** O enunciado sugere métricas por trimestre com o teste de Mann-Kendall. Com só 4 pontos por série, esse teste nunca alcança p < 0,05, mesmo com a série perfeitamente monótona (o menor p bilateral possível com n = 4 é ≈ 0,089). Por isso a análise principal usa a **série mensal** (12 pontos), em que o teste tem poder de verdade; o recorte trimestral fica só como leitura visual na Figura 18 (linhas verticais), sem teste de hipótese.

![RQ08, tendência](../analise/saida/figuras/fig17_rq08_tendencia_600.png)

![RQ08, trajetória](../analise/saida/figuras/fig18_rq08_trajetoria_600.png)

**Como ler.**
- Mann-Kendall por repositório e por métrica, mês a mês, mínimo de 8 dos 12 meses com dado (senão "dados insuficientes"). "Melhora" e "piora" dependem da métrica: frequência melhora subindo; lead time, CFR e recuperação melhoram descendo.
- São ~250 a 600 testes por métrica (repositórios com menos de 8 meses de dado ficam fora): correção de **Benjamini-Hochberg (FDR)**, reportada ao lado do Holm nas tabelas. Com tantos testes simultâneos, o Holm fica conservador demais; o FDR é o resultado principal.
- A Figura 18 mostra a mediana entre repositórios a cada mês, com a faixa entre Q1 e Q3 sombreada.

**Resultado, com 600 (A1 + A2).**

| Métrica | % com p bruto < 0,05 | % significativo após FDR | % "dados insuficientes" |
| :--- | :---: | :---: | :---: |
| Frequência | 16,8% | 0% | 0% |
| Lead time (a) | 16,7% | 0% | 50,2% |
| CFR (a) | 13,2% | 0,17% (1 repositório, piora) | 19,2% |
| Recuperação | 16,5% | 0% | 59,7% |

- **O teste bruto, sem correção, "encontra" tendência em 13% a 17% dos repositórios em todas as métricas** — bem mais que os 5% esperados por acaso num teste isolado, o que sugere que há, sim, alguma oscilação mensal real nas séries.
- **Depois da correção por FDR, quase nada sobrevive**: só 1 dos 600 repositórios mantém uma tendência significativa (CFR a, piora). Com 250 a 600 testes simultâneos por métrica, o FDR exige um p bruto bem menor que 0,05 pra sobreviver (o menor p-valor FDR observado foi 0,033, só na CFR). É o retrato didático de por que a correção de múltiplos testes importa: a aparência de 1 em cada 6 repositórios "mudando" vira ruído estatístico quase por completo quando se testa centenas deles ao mesmo tempo.
- **"Dados insuficientes" é alto em lead time e recuperação** (50% e 60%) porque nem todo repositório publica release ou tem episódio de falha em pelo menos 8 dos 12 meses — frequência nunca é "insuficiente" porque zero releases no mês é um valor válido (zero), não um dado faltante.
- **A Figura 18 mostra um salto na mediana de frequência no último mês da janela** (de ≈ 0,23 para ≈ 0,47 release/semana). Não há teste de hipótese que sustente isso como tendência (o Mann-Kendall olha a série inteira, não só a ponta), e o padrão é compatível com um viés de seleção: o critério de inclusão (seção 3.2) exige atividade mínima dentro da janela, o que tende a favorecer repositórios com releases recentes bem próximas do fim da coleta. Fica registrado como limitação, não como achado de tendência.

Para a discussão: o resultado da RQ08 não aponta melhora nem piora sistemática nas métricas DORA ao longo do ano, na amostra estudada. A conclusão mais defensável é metodológica, não substantiva: com 12 meses e centenas de repositórios testados ao mesmo tempo, a correção de múltiplos testes consome quase todo o poder estatístico disponível para detectar tendência individual por repositório. Uma análise de tendência agregada (por exemplo, a mediana por mês ao longo da amostra inteira, sem testar repositório por repositório) teria mais poder, mas também mistura tendência real com mudança de composição da amostra ao longo do tempo — e não foi o que esta issue pediu.

---
---

## 3.10 Análises complementares (além do escopo pedido)

O escopo do enunciado são 300 repositórios e as RQ01–RQ08, respondidas acima. O grupo estendeu o estudo para **900 repositórios em três amostras independentes** e acrescentou análises de validade das medidas que o enunciado não pede. Esta seção traz **apenas as conclusões**; o material completo — tabelas, figuras, testes e derivações — está em `analise/saida/`, em `docs/base-teorica.md` e no histórico das issues #154, #156, #158 e #166.

### 3.10.1 As conclusões não dependem dos 300 sorteados

Três amostras de 300, com sementes 42, 2026 e 2027, sem nenhum repositório em comum. **A1 e A2 são estatisticamente indistinguíveis** em todas as seis métricas: nenhum p significativo após Holm, e todos os |δ| de Cliff abaixo de 0,07 — bem dentro do desprezível.

Ao empilhar 300 → 600 → 900, **todas as medianas dos níveis maiores caem dentro do intervalo de confiança de 300**, e os intervalos encolhem de 21% a 51%.

| Métrica | 300 | 600 | 900 |
| :--- | ---: | ---: | ---: |
| Frequência (releases/semana) | 0,35 | 0,34 | 0,35 |
| Lead time (a) (dias) | 13,17 | 12,88 | 12,04 |
| Lead time (b) (dias) | 8,85 | 9,44 | 9,01 |
| CFR (a) | 5,6% | 5,0% | 5,3% |
| CFR (b) | 25,0% | 23,8% | 25,0% |
| Recuperação (horas) | 2,79 | 2,96 | 3,14 |

A única conclusão que muda é a da RQ06: com 600, a linguagem passa a ter efeito significativo que em 300 estava escondido por falta de poder. Não é a métrica mudando, é o teste ganhando poder — razão para sempre reportar `n` e tamanho de efeito ao lado do p.

### 3.10.2 A heurística de falha não passa na validação humana

Esta é a conclusão mais consequente do trabalho, e está detalhada na seção 2.7. Contra o gabarito de 300 releases rotuladas por três pessoas, **nenhuma das quatro versões da heurística atinge o F1 mínimo de 0,70**. A versão que gerou o `cfr_b_release` de todo o dataset tem **precisão de 36,5%**: de cada três releases que ela marca como corretivas, duas não são.

O κ de Fleiss entre os três avaliadores em `corretiva` é 0,504 — apenas moderado. A prevalência de "sim" variou de 16,7% a 37,3% entre eles. Nem três humanos lendo as mesmas notas concordam sobre o que é uma release corretiva.

**Consequência:** todo resultado que depende do CFR (b) — a RQ03 (b), a RQ05 (b) e a combinação C2 da RQ07 — deve ser lido como medida de um proxy mal validado, não como taxa de falha.

### 3.10.3 O CFR (b) mede cadência de publicação, não falha

A correlação positiva entre frequência de deploy e CFR (b) (ρ = 0,604) parecia contradizer a tese do DORA. Não contradiz: é artefato da definição.

Quem publica mais releases tem mais oportunidade de ter uma release seguida por outra em até 7 dias. Ao condicionar pela oportunidade de observação, **a correlação desaparece: ρ = −0,039 (p = 0,52)**, contra ρ = 0,784 entre frequência e a própria oportunidade.

Ou seja, o CFR (b) está medindo, em boa medida, o ritmo de publicação do repositório. Isso é coerente com a precisão de 36,5% da seção anterior: as duas evidências, uma estatística e uma humana, apontam para o mesmo defeito.

**A relação não é tamanho disfarçado.** Antes de concluir pelo artefato de cadência, a hipótese alternativa — de que repositórios maiores simplesmente publicam e falham mais — foi testada por dois caminhos independentes: estratificação em quartis de estrelas, contribuidores e idade, e correlação parcial de Spearman controlando esses fatores. O ρ agregado de 0,562 cai no máximo 0,059 na parcial, e os doze estratos mantêm o mesmo sinal, variando entre 0,381 e 0,698. **Verificação feita, confusão por tamanho não encontrada** — o que reforça que o mecanismo é a oportunidade de observação, não o porte do projeto.

### 3.10.4 As faixas DORA quase não discriminam

A classificação Elite/High/Medium/Low **não separa** repositórios por popularidade (ε² = 0,008) nem por número de contribuidores (ε² = 0,022), e nenhuma das duas sobrevive à correção de Holm. Só a idade mostra algum efeito (ε² = 0,109).

O que as faixas separam bem são **as próprias variáveis que as definem**: CFR (b) alcança ε² = 0,379, perto do controle tautológico da frequência de deploy (0,403). Isso é validade convergente, não poder discriminante. Nesta população, a classificação DORA é em grande parte uma relabelagem de variáveis contínuas.

### 3.10.5 Por que mediana e IQR, demonstrado

A exigência do enunciado deixa de ser convenção e vira resultado:

- **Nenhuma das cinco métricas passa em teste de normalidade** (Shapiro-Wilk), e a média chega a 5,7× a mediana.
- **A contagem de releases não é Poisson:** o índice de dispersão é 493× o esperado. A binomial negativa (r = 0,148) reduz o qui-quadrado em dez ordens de grandeza, mas ainda assim é formalmente rejeitada.
- **A recuperação tem taxa decrescente:** o ajuste de Weibull dá forma mediana β = 0,557, com β < 1 em **87,8% dos repositórios** (n = 238). Quanto mais tempo um pipeline passa quebrado, menor a chance de ser consertado na hora seguinte. Isso invalida o modelo exponencial, que assume taxa constante.
- **O Teorema do Limite Central precisa de n ≈ 300 aqui, não de 30.** Com a assimetria observada, a distribuição das médias amostrais só fica aproximadamente normal perto de n = 300.

### 3.10.6 O DORA não é a única lente, e as lentes discordam

Comparando as métricas DORA com medidas de fluxo por pull request (padrões CHAOSS e SPACE) nos mesmos repositórios, **nenhum par chega a ρ = 0,7**:

| Par | ρ | Variância compartilhada |
| :--- | ---: | ---: |
| Lead time por release × por PR | 0,319 | 10% |
| Ritmo: releases × PRs por semana | 0,460 | 21% |
| Recuperação de CI × resolução de bug | 0,216 | 5% |
| **CFR (b) × taxa de aceitação de PR** | **0,044** | **0,2%** (não significativo) |

O par que deveria falar sobre qualidade pelos dois lados — CFR (b) e aceitação de PR — não tem associação alguma. A conclusão é que **o DORA é *uma* medida de desempenho de engenharia, não *a* medida**: uma lente igualmente legítima ordena os mesmos repositórios de forma substancialmente diferente.

No mesmo sentido, trocar o proxy de falha reclassifica quase tudo: o mesmo conjunto aparece como 99% Elite (releases revertidas), 84% Elite (falha de CI) ou 38% Elite (release corretiva).

### 3.10.7 Um índice contínuo no lugar das quatro faixas

Como as faixas descartam informação, o grupo propôs um índice contínuo por posto percentílico sobre as quatro métricas. O resultado quantifica a perda: **as faixas retêm 63,2% da variância do índice**, e 8,2% dos pares de repositórios em faixas diferentes aparecem invertidos — o repositório da faixa pior tem índice melhor que o da faixa melhor. A inversão chega a 15,7% entre Elite e High e 17,8% entre Medium e Low, e é zero entre Elite e Low.

A leitura é que as faixas funcionam para separar extremos e falham entre vizinhas, que é justamente onde a maioria dos repositórios está.

### 3.10.8 Uma medida auxiliar que não se reproduz

Nem toda evidência de confiabilidade é positiva. A cobertura da API de Deployments varia entre as três amostras do mesmo desenho — 31,3%, 41,7% e 43,3% — e a diferença é estatisticamente detectável (p = 0,0048). Nem o perfil dos repositórios nem a linguagem explicam a variação.

Registrado como evidência **negativa** de confiabilidade, e motivo para manter essa medida como subamostra de validação e não como medida principal. O contraste é informativo: o mesmo desenho que confirma a robustez das métricas DORA detecta a fragilidade de uma medida auxiliar.
