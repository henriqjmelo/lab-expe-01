# 3. Resultados (esboço v1)

> Esboço da issue #151 para discutirmos em grupo. As análises finais de cada RQ ficam nas issues #140 (RQ01–04 e classificação C1), #141 (RQ05–06) e #142 (RQ07, RQ08 e Discussão).
>
> - **Dados:** os 300 repositórios de `data/dataset_dora.csv` (amostra 1, issue #139).
> - **Como regenerar:** `python -m analise`, de dentro de `lab-expe-03`, gera todas as figuras e tabelas. As dependências estão em `requirements-analise.txt`.
> - **Pendências:**
>   - **[PRELIMINAR]** O CFR (b) ainda usa a heurística v0 de release corretiva, até chegar a da #138.
>   - **[PENDENTE]** A comparação com a amostra 2 entra quando a coleta dela terminar.

Seguindo o enunciado, todas as métricas são resumidas por **mediana e IQR** (1º–3º quartil).

**Tabela 3 — Resumo das métricas** (`analise/saida/tabelas/resumo.csv`).

| Métrica | n | Mediana | IQR |
| :--- | ---: | ---: | :--- |
| Frequência de deploy (releases/semana) | 300 | 0,35 | 0,19 – 0,81 |
| Lead time (a), por release (dias) | 293 | 13,2 | 3,1 – 37,3 |
| Lead time (b), por commit (dias) | 293 | 8,8 | 2,8 – 29,4 |
| CFR (a), proxy de CI | 300 | 5,6% | 2,2% – 11,2% |
| CFR (b), proxy de entrega [PRELIMINAR] | 300 | 25,0% | 5,2% – 56,5% |
| Tempo de recuperação (horas) | 278 | 2,8 | 0,9 – 11,9 |

Sete repositórios ficam sem lead time porque tinham mais de 300 releases na janela, e o cálculo foi omitido para preservar a cota da API (coluna `lt_release_omitido`). Outros 22 ficam sem tempo de recuperação porque não tiveram nenhum episódio de falha fechado na janela.

---

## 3.1 RQ 01 — Frequência de deploy

![Frequência de deploy](../analise/saida/figuras/fig02_rq01_frequencia.png)

**Como ler.**
- Cada ponto é um repositório, posicionado pela quantidade de releases por semana. A altura não tem significado: os pontos só se empilham para não se sobrepor.
- O eixo está em escala log: cada marca multiplica o valor, e não soma.
- As faixas ao fundo são as categorias da tabela de referência DORA, com a contagem de cada uma no topo.

**Resultado.**
- A mediana é de **0,35 release por semana**, cerca de uma release a cada 20 dias.
- Quase metade da amostra (46%) é **Medium** (entre 1 por mês e 1 por semana), e um terço é **Low** (menos de 1 por mês).
- Só 6 repositórios (2%) chegam a Elite (≥ 7 por semana).

Para a discussão: release publicada é um proxy conservador de deploy. Projetos que entregam continuamente sem publicar releases ficam subestimados. Os que nem chegam a 5 releases já foram descartados no funil, onde 57% caíram nesse filtro.

## 3.2 RQ 02 — Lead time for changes

![Lead time (a) × (b)](../analise/saida/figuras/fig03_rq02_lead_time.png)

**Como ler.**
- Cada ponto é um repositório: a posição horizontal é o lead time pela variante (a) e a vertical, pela variante (b), ambos em escala log.
- Na diagonal cinza as duas variantes coincidem.
- As linhas de grade marcam as fronteiras DORA: 1 dia, 1 semana e 30 dias.

**Resultado.**
- As medianas são **13,2 dias pela variante (a)** e **8,8 dias pela (b)**.
- Em **65% dos repositórios a variante (b) dá um valor menor**, com o ponto abaixo da diagonal.

**Por que as variantes divergem** (o enunciado pede essa explicação):
- A variante (a) mede o tempo desde o commit **mais antigo** de cada release. Um único commit que esperou muito puxa o valor da release inteira para cima.
- A variante (b) usa a mediana de **todos** os commits. Releases grandes pesam mais, e a maioria dos commits entra perto da data de publicação.
- Quando cada release tem poucos commits, as duas variantes convergem. Os pontos acima da diagonal merecem uma inspeção caso a caso: uma hipótese é que poucas releases concentrem muitos commits antigos.

## 3.3 RQ 03 — Change failure rate

![CFR (a) e (b)](../analise/saida/figuras/fig04_rq03_cfr.png)

**Como ler.**
- É uma curva acumulada. Para cada valor de CFR no eixo horizontal, a altura da curva é a % de repositórios com CFR até aquele valor.
- Quanto mais cedo a curva sobe, mais repositórios têm taxa de falha baixa.
- As linhas verticais são as fronteiras DORA (15%, 30% e 45%). O ponto marca quantos repositórios são Elite (≤ 15%).

**Resultado.** Os dois proxies contam histórias opostas:
- Pela **falha de CI**, CFR (a), **84% dos repositórios são Elite**, com mediana de 5,6%.
- Pela **release corrigida em até 7 dias**, CFR (b), só **37%** são Elite, com mediana de 25%. Além disso, 23% dos repositórios têm CFR (b) igual a zero, o degrau vertical no início da curva laranja.

Para a discussão: o CFR (a) mede a falha do *pipeline*, não a falha em produção. Testes instáveis e falhas corrigidas antes do merge entram como falha. O CFR (b) depende da heurística de corretiva, e a v0 provavelmente o infla.

## 3.4 RQ 04 — Tempo de recuperação

![Tempo de recuperação](../analise/saida/figuras/fig05_rq04_recuperacao.png)

**Como ler.**
- É a mesma lógica de curva acumulada, com a mediana do tempo de recuperação de cada repositório no eixo horizontal, em escala log.
- Os pontos marcados respondem diretamente "que % dos repositórios se recupera em menos de X".

**Resultado.**
- A mediana é de **2,8 horas**.
- **27%** se recuperam em menos de 1 hora (Elite), **83%** em menos de 1 dia e **97%** em menos de 1 semana.
- Dos 20.077 episódios de falha, só **0,7% foram censurados**, ou seja, não se recuperaram até o fim da janela. Esses episódios estão espalhados por 74 repositórios.

## 3.5 Classificação DORA (combinação de referência C1)

![Perfil DORA](../analise/saida/figuras/fig06_perfil_dora.png)

**Como ler.**
- Cada barra soma 100% dos repositórios, divididos pela categoria DORA de cada métrica.
- O azul mais escuro é Elite e o mais claro é Low.
- **Geral** é a classificação final do enunciado: a mediana dos pontos das quatro métricas (Elite = 4 … Low = 1), arredondada para baixo.

**Resultado.**
- **Metade da amostra é Medium (50%) e 35% é High.** Só 8% é Elite e 7% é Low.
- Cada métrica puxa para um lado diferente:
  - o **CFR (a)** quase todo em Elite puxa para cima;
  - a **frequência**, com 79% entre Medium e Low, puxa para baixo;
  - o **lead time** está espalhado pelas quatro categorias.

## 3.6 RQ 05 — Velocidade × estabilidade

![Velocidade × estabilidade](../analise/saida/figuras/fig07_rq05_velocidade_estabilidade.png)

**Como ler.**
- Cada ponto é um repositório, com a frequência de deploy no eixo horizontal (escala log) e o CFR no vertical.
- O ρ de Spearman vai de −1 a 1: perto de 0 indica ausência de relação monotônica, e valores positivos indicam que o CFR sobe junto com a frequência.

**Resultado.**
- **Pelo CI: ρ = 0,18** (p = 0,002; n = 300). A correlação é estatisticamente significativa, mas **fraca**. Na prática, publicar mais não se associa a quebrar mais o CI.
- **Pela entrega: ρ = 0,60** (p < 0,001). A correlação é **forte**, mas em boa parte é um artefato da definição: quem publica muitas releases tem, por construção, mais chance de que uma delas seja uma "corretiva" publicada em até 7 dias.

Para a discussão: o resultado com o proxy de CI é coerente com a afirmação do DORA de que velocidade e estabilidade não são *trade-off*. O resultado com o proxy de entrega não deve ser lido como evidência do contrário antes da heurística validada (#138). Em nenhum dos dois casos a correlação implica causalidade.

## 3.7 RQ 06 — Características associadas ao desempenho

![Fatores](../analise/saida/figuras/fig08_rq06_fatores.png)

**Como ler.**
- Cada célula cruza uma característica do repositório (linha) com uma métrica (coluna).
- O valor é o tamanho de efeito **ε² = H/(n−1)** do teste de Kruskal-Wallis: quanto da variação da métrica a característica explica. A referência é < 0,01 desprezível, < 0,06 pequeno, < 0,14 médio e ≥ 0,14 grande.
- Os valores em **negrito com \*** continuam significativos depois da correção de Holm para os 24 testes.
- Linguagem considera as 6 linguagens com pelo menos 15 repositórios. Os demais fatores estão divididos em quartis.

**Resultado.**

| Fator | Q1 → Q4 | Lead time (a) Q1 → Q4 | Frequência Q1 → Q4 | CFR (b) Q1 → Q4 |
| :--- | :--- | :--- | :--- | :--- |
| Idade | ≤ 2 anos → > 10,9 anos | 2,0 → 28,5 dias | 0,67 → 0,23 por semana | 57% → 10% |
| Contribuidores | ≤ 48 → > 338 | 4,7 → 18,5 dias | sem efeito | 37% → 18% |
| Estrelas | quartis | 6,1 → 18,4 dias | sem efeito | sem efeito |

- **A idade é o fator com maior efeito.** Para o lead time o efeito é grande (ε² = 0,25). Repositórios com até 2 anos publicam com mais frequência e mais rápido, com lead time mediano de 2 dias contra 28,5 nos mais antigos. Eles também têm mais releases corretivas.
- **Equipes maiores têm lead time maior** (ε² entre 0,11 e 0,14, efeito médio).
- **A linguagem não tem efeito significativo** em nenhuma métrica depois da correção de Holm.
- **O CFR (a) e o tempo de recuperação não se associam a nenhum dos quatro fatores.**

Para a discussão: idade, contribuidores e estrelas são correlacionados entre si, já que projetos antigos tendem a ser maiores e mais populares. O teste não separa esses efeitos. Uma hipótese é que projetos jovens estejam em fase de iteração rápida, com muitas releases de *patch*.

## 3.8 RQ 07 — Sensibilidade à definição operacional

![Sensibilidade](../analise/saida/figuras/fig09_rq07_sensibilidade.png)

**Como ler.**
- **À esquerda:** a distribuição das categorias DORA gerais em cada combinação de definições.
- **À direita:** para cada par de combinações, a % de repositórios que **ficou na mesma categoria**, **subiu** ou **desceu**, e o κ de Cohen ponderado linear, em que 1 é concordância perfeita.

| Combinação | Unidade de deploy | Lead time | CFR |
| :--- | :--- | :--- | :--- |
| C1 (referência) | release | (a) | (a) |
| C2 | release + pré-release | (b) | (b) [PRELIMINAR] |
| C3 | tag | (b) | (a) |

**Resultado.**
- **Entre 28% e 36% dos repositórios mudam de categoria** só por trocar a definição.
- A concordância é **moderada**: κ = 0,42 entre C1 e C2, 0,54 entre C2 e C3, e 0,63 entre C1 e C3.
- A direção das mudanças segue o componente trocado:
  - em **C2**, 23% descem e 13% sobem, porque o CFR (b) é mais severo que o (a);
  - em **C3**, 23% sobem e só 4% descem, porque tags são mais frequentes que releases e o lead time (b) é menor.

Para a discussão: a classificação DORA de um repositório **não é robusta à definição operacional**. As comparações entre estudos que usam proxies diferentes precisam ser feitas com cautela. A RQ07 final (#142) deve recalcular C2 com a heurística validada.

---

## 3.9 Comparação entre amostras [PENDENTE]

A amostra 2 tem 300 repositórios. Ela usa a mesma janela e os mesmos filtros da amostra 1, mas foi sorteada com outra semente e exclui os repositórios da amostra 1 (`config-amostra2.yaml`). A comparação entra aqui quando a coleta terminar, com duas figuras:
- curvas acumuladas sobrepostas por métrica, com Mann-Whitney, delta de Cliff e correção de Holm;
- medianas com intervalo de confiança de 95% por bootstrap.

Para gerá-las: `python -m analise --comparar data/amostra2/dataset_dora.csv`.
