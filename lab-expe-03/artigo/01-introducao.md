# 1. Introdução

> Rascunho da issue #134, a ser revisado por Henrique e Gabriel antes de ir para o Overleaf.

## 1.1 Contexto e problema

As quatro métricas DORA — frequência de deploy, lead time for changes, change failure rate e tempo de recuperação — viraram o vocabulário padrão para falar de desempenho de entrega de software, e sua tese central é que velocidade e estabilidade não são um trade-off. Elas foram definidas, porém, para equipes que controlam o próprio pipeline de produção e sabem, por definição operacional interna, o que conta como "deploy" e o que conta como "falha em produção".

Repositórios open-source no GitHub não oferecem nenhuma das duas coisas. Não há registro de implantação, não há registro de incidente e não há a quem perguntar. O que existe são rastros: releases publicadas, execuções de workflow, commits e tags. Medir DORA aqui, portanto, não é aplicar uma definição — é **escolher proxies** e herdar o erro de cada escolha. Uma release é um deploy? Uma execução de CI que falha é uma falha em produção? Uma release de *patch* publicada três dias depois da anterior corrige um defeito, ou é rotina?

Cada resposta é uma hipótese não verificada ligando um atributo interno, que se consegue contar, a um atributo externo, que é o que interessa. Calcular as quatro métricas numa amostra grande é a parte mecânica; a parte que decide se os números significam alguma coisa é perguntar **o quanto os proxies são medidas válidas** — se concordam com julgamento humano, se sobrevivem à troca da definição, se se reproduzem em amostras independentes e se as faixas separam grupos distintos.

## 1.2 Objetivo e questões de pesquisa

O objetivo é minerar as métricas DORA de repositórios populares que usam GitHub Actions e, em paralelo, avaliar a validade das medidas. O escopo do enunciado é de 300 repositórios; este trabalho o estende para **900**, em três amostras independentes, para poder testar reprodutibilidade.

| RQ | Pergunta |
| :--- | :--- |
| **RQ01** | Qual a frequência de deploys dos repositórios populares que usam CI/CD? |
| **RQ02** | Qual o tempo entre um commit e seu respectivo deploy? |
| **RQ03** | Qual a taxa de falha das mudanças entregues? |
| **RQ04** | Qual o tempo de recuperação após uma execução de CI/CD com falha? |
| **RQ05** | Maior frequência de deploy se associa a maior ou menor taxa de falha? |
| **RQ06** | Quais características dos repositórios se associam a melhor desempenho? |
| **RQ07** | O quanto a classificação DORA depende da definição operacional? |

A RQ08 (bônus) trata da evolução temporal das métricas dentro da janela.

## 1.4 Hipóteses informais

Uma hipótese por RQ, com a origem de cada uma declarada. "Origem" diz de onde veio a expectativa — não dos dados deste trabalho (ver a nota de registro em 1.5).

| # | Hipótese | Origem da expectativa |
| :--- | :--- | :--- |
| **H01** | Os repositórios entregam com alta frequência: mediana de **pelo menos uma release por semana**. | O programa DORA trata entrega frequente como marca de maturidade, e o critério de inclusão (≥ 5 releases e ≥ 50 workflow runs na janela) já seleciona projetos ativos. |
| **H02** | O lead time mediano fica **na casa dos dias, não das horas**, e a variante (a), por release, é **sistematicamente maior** que a (b), por commit. | A primeira parte vem do contraste entre o padrão Elite do DORA (< 1 dia) e o ritmo assíncrono e voluntário do open source. A segunda vem da própria dica do enunciado na RQ02: um commit antigo "esquecido" numa release faz a (a) explodir e pouco afeta a (b). |
| **H03** | A taxa de falha fica **abaixo de 15%** nas duas variantes, e as duas chegam a **valores próximos**. | 15% é o limiar DORA que separa Elite/High do resto. A expectativa de convergência vem de supor que as duas variantes medem o mesmo construto por caminhos diferentes — que é exatamente a suposição que o trabalho precisa testar. |
| **H04** | O tempo mediano de recuperação fica **abaixo de 24 horas**. | Um pipeline de CI quebrado bloqueia todo mundo que depende dele; a expectativa é que consertá-lo seja prioridade imediata. O padrão Elite do DORA é menos de uma hora. |
| **H05** | A correlação entre frequência de deploy e CFR é **nula ou negativa**. | É a tese central do DORA, citada no próprio enunciado da RQ05: velocidade e estabilidade não são um trade-off, e quem entrega mais não falha mais. |
| **H06** | Repositórios mais populares, com mais contribuidores e mais antigos têm **desempenho DORA melhor**, com efeito ao menos pequeno (ε² ≥ 0,01). | Mais gente e mais maturidade deveriam significar mais automação, mais processo e mais disciplina de release. |
| **H07** | A classificação DORA é **majoritariamente estável** à definição operacional: **menos de 20%** dos repositórios mudam de faixa entre duas combinações. | Se as faixas medem um atributo real do repositório, e não um artefato do proxy, trocar a definição não deveria reclassificar a maioria. |

## 1.5 Nota sobre o registro das hipóteses

O protocolo correto registra as hipóteses **antes** da coleta, e aqui isso não aconteceu: o Lab03 começou em 08/10/2026, o primeiro dataset entrou em 13/10/2026 e as hipóteses acima foram escritas em **20/10/2026**, com os resultados já disponíveis. Elas são **reconstruídas**, não pré-registradas.

Para que a reconstrução não seja racionalização do que foi encontrado, cada hipótese declara a origem da expectativa, e nenhuma foi derivada dos resultados. O leitor audita isso pelo saldo: **cinco das sete foram refutadas** (seção 4). Hipóteses escritas depois do resultado tendem a acertar; estas, na maioria, erram. A seção 5.4 trata disso como ameaça aberta.

## 1.6 Contribuições

Um **dataset público de 900 repositórios** com as quatro métricas e os eventos brutos; uma **avaliação de validade** segundo os seis critérios da IEEE 1061, e não apenas o cálculo das métricas; a demonstração, por duas vias independentes, de que **o CFR na variante (b) não mede falha** (seções 2.7 e 3.7); a evidência de que as **faixas DORA não têm poder discriminante** nesta população, com um índice contínuo como alternativa; e um **ajuste de distribuições** que mostra por que média e desvio-padrão não se aplicam aqui.

As seções seguintes tratam de metodologia e validação manual (2), resultados das RQs e análises de validade (3), hipóteses contra resultados (4), ameaças à validade (5) e pacote de replicação (6).
