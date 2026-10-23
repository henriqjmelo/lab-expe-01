# 1. Introdução

> Rascunho da issue #134, a ser revisado por Henrique e Gabriel antes de ir para o Overleaf.

## 1.1 Contexto

As quatro métricas DORA — frequência de deploy, lead time for changes, change failure rate e tempo de recuperação — viraram o vocabulário padrão para falar de desempenho de entrega de software. Elas vêm do programa de pesquisa *DevOps Research and Assessment*, que as derivou de levantamentos com milhares de profissionais e as organizou em faixas de desempenho (Elite, High, Medium, Low). A tese central desse programa é que velocidade e estabilidade **não** são um trade-off: as equipes de melhor desempenho vão bem nas quatro métricas ao mesmo tempo.

Essas métricas foram definidas para equipes que controlam o próprio pipeline de produção e sabem, por definição operacional interna, o que conta como "deploy" e o que conta como "falha em produção". Repositórios open-source no GitHub não oferecem nenhuma das duas coisas. Não há registro de deploy, não há registro de incidente e não há alguém para perguntar. O que existe são **rastros**: releases publicadas, execuções de workflow do GitHub Actions, commits, tags e comparações entre releases.

## 1.2 Problema

Medir DORA em repositórios open-source, portanto, não é aplicar uma definição: é **escolher proxies** e assumir o custo dessa escolha. Uma release é um deploy? Uma execução de CI que falha é uma falha em produção? Uma release de *patch* publicada três dias depois da anterior é a correção de um defeito, ou é rotina de atualização de dependência?

Cada resposta a essas perguntas é uma hipótese não verificada sobre a relação entre um atributo interno, que se consegue contar, e um atributo externo, que é o que de fato interessa. É nesse ponto que este trabalho se separa de uma aplicação direta do enunciado. Calcular as quatro métricas em uma amostra grande é a parte mecânica. A parte que decide se os números significam alguma coisa é perguntar **o quanto os proxies escolhidos são medidas válidas** — se concordam com o julgamento humano, se sobrevivem à troca da definição operacional, se se reproduzem em amostras independentes e se as faixas DORA separam de fato grupos distintos de repositórios.

## 1.3 Objetivo e questões de pesquisa

O objetivo é minerar as métricas DORA de repositórios populares que usam GitHub Actions e, em paralelo, avaliar a validade das medidas usadas. O escopo inicial do enunciado é de 300 repositórios; este trabalho o estende para **900**, em três amostras independentes de 300 (A1, A2 e A3), justamente para poder testar reprodutibilidade.

As sete questões de pesquisa são:

| RQ | Pergunta |
| :--- | :--- |
| **RQ01** | Qual a frequência de deploys dos repositórios populares que usam CI/CD? |
| **RQ02** | Qual o tempo entre um commit e seu respectivo deploy? |
| **RQ03** | Qual a taxa de falha das mudanças entregues por esses repositórios? |
| **RQ04** | Qual o tempo de recuperação após uma execução de CI/CD com falha? |
| **RQ05** | Repositórios com maior frequência de deploy apresentam maior ou menor taxa de falha? |
| **RQ06** | Quais características dos repositórios estão associadas a um melhor desempenho DORA? |
| **RQ07** | O quanto a classificação DORA depende da definição operacional escolhida? |

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

O protocolo correto registra as hipóteses **antes** da coleta. Neste trabalho isso não aconteceu. O Lab03 começou em 08/10/2026, o primeiro dataset entrou no repositório em 13/10/2026 e as hipóteses acima só foram escritas e versionadas em **20/10/2026**, com os resultados já disponíveis ao grupo. Elas são, portanto, **reconstruídas**, não pré-registradas, e o leitor deve tratá-las como tal.

Para que a reconstrução não seja só uma racionalização do que foi encontrado, cada hipótese declara de onde veio a expectativa, e nenhuma foi derivada dos resultados. O leitor pode auditar isso pelo saldo: **cinco das sete foram refutadas** pelos dados (seção 4). Hipóteses escritas depois de ver o resultado tendem a acertar; estas, na maioria, erram — inclusive em direções que custaram retrabalho ao grupo, como a H05, que motivou a análise da seção 3.13.

Isso está registrado também na seção 5 (ameaças à validade), como limitação de conclusão.

## 1.6 Contribuições

1. Um **dataset público de 900 repositórios** (três amostras independentes de 300) com as quatro métricas DORA e suas variantes, mais os eventos brutos (releases, commits por release, workflow runs) que permitem recalcular tudo.
2. Uma **avaliação de validade das medidas** segundo os seis critérios da IEEE 1061, e não só o cálculo das métricas: correlação, rastreamento, consistência, previsibilidade, poder discriminante e confiabilidade.
3. A demonstração de que o **CFR na variante (b) mede cadência de publicação, não falha** — a correlação com a frequência de deploy desaparece ao condicionar pela oportunidade de observar uma release corretiva (seção 3.13).
4. A evidência de que as **faixas DORA não têm poder discriminante** nesta população e a proposta de um **índice contínuo** que preserva a informação que o corte em faixas descarta (seções 3.12 e 3.15).
5. Um **ajuste de distribuições** às métricas (Poisson, binomial negativa, Weibull, normal) que mostra por que a média e o desvio-padrão não devem ser usados aqui, e a verificação empírica de que o Teorema do Limite Central precisa de n ≈ 300, não de n = 30, para estes dados (seções 3.9 e 3.14).

## 1.7 Organização

A seção 2 descreve a metodologia: fonte de dados, janela, seleção, definições operacionais e validação manual. A seção 3 apresenta os resultados das sete RQs e as análises adicionais de validade. A seção 4 confronta as hipóteses acima com o que os dados mostraram. A seção 5 discute as ameaças à validade segundo as quatro categorias de Cook e Campbell. A seção 6 descreve o pacote de replicação.
