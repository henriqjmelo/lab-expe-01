# Mineração de métricas DORA em repositórios open-source populares

**Laboratório de Experimentação de Software** · Engenharia de Software, 6º período
Guilherme Costa · Henrique Jardim Melo · Gabriel Afonso

> Documento consolidado, gerado por `python artigo/montar.py`. Não editar diretamente:
> altere as seções em `artigo/0N-*.md` e rode o script de novo.

---

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

---

# 2. Metodologia

> Rascunho da issue #139, a ser revisado por Henrique e Gabriel antes de ir para o Overleaf. Os números da coleta são os do `data/` desta versão. O único item em aberto são as datas exatas da janela, a confirmar com o professor.

## 2.1 Fonte de dados

Os dados vêm da API pública do GitHub e foram coletados por um script próprio do grupo, sem bibliotecas prontas de acesso à API. O script usa a API REST para busca, releases, comparações entre releases e workflow runs, e a GraphQL para as tags com data. O pipeline inteiro roda com um único comando (`python -m pipeline --config config.yaml`). Cada resposta da API fica em cache local, então interromper a coleta e rodá-la de novo continua de onde parou e reproduz o mesmo dataset sem novas chamadas. O cliente HTTP respeita os cabeçalhos de rate limit e repete com *backoff* exponencial as respostas 5xx e as falhas de rede.

## 2.2 Janela de observação

A janela tem 12 meses, de **1º de outubro de 2025 a 30 de setembro de 2026** **[PENDENTE: confirmar com as datas fixadas pelo professor]**. Isso dá aproximadamente 52,1 semanas. Só entram nas métricas as releases publicadas e os workflow runs criados dentro dela. A exceção é a release imediatamente anterior a uma release da janela, que é usada como base para obter os commits incluídos, mesmo estando fora.

## 2.3 Seleção dos repositórios e funil

A busca cobriu repositórios com mais de 1.000 estrelas, não arquivados e com *push* depois do início da janela. Como cada consulta devolve no máximo 1.000 resultados, ela foi fatiada em nove faixas de estrelas. Os candidatos foram embaralhados com semente fixa e avaliados nessa ordem até a amostra chegar a 300, de modo que ela não se concentre nos mais estrelados de cada faixa. Os filtros, aplicados do mais barato ao mais caro, são: (i) usa GitHub Actions; (ii) tem ao menos 5 releases publicadas, sem pré-release, na janela; (iii) tem ao menos 50 workflow runs válidos disparados por *push* no *default branch*.

**Tabela 1 — Funil de seleção** (`data/funil.csv`).

| Etapa | Restantes | Descartados | Motivo |
| :--- | ---: | ---: | :--- |
| Candidatos da busca | 8.457 | — | — |
| Avaliados (ordem aleatória) | 1.108 | 7.349 | alvo de 300 já atingido |
| Usam GitHub Actions | 937 | 171 | nenhum workflow cadastrado |
| ≥ 5 releases na janela | 399 | 538 | menos de 5 releases |
| ≥ 50 runs válidos | 300 | 99 | menos de 50 runs em `push` |

O filtro mais restritivo é o de releases: **57% dos repositórios que usam Actions publicaram menos de 5 releases em 12 meses**, o que indica que muitos projetos populares entregam por *rolling release*, publicação direta em registros de pacotes ou sem versionamento formal. Como cada faixa contribui no máximo com seus 1.000 mais estrelados, a amostra fica deslocada para repositórios populares: mediana de 9.485 estrelas (IQR 2.844–28.694).

## 2.4 Definições operacionais

Seguem a seção 3 do enunciado, comum à turma. **Deploy** é release publicada (`draft = false`), sem pré-release, datada por `published_at`. **Execuções de CI** são workflow runs do *default branch* com `event = push`; `success` conta como sucesso, `failure`, `timed_out` e `startup_failure` como falha, e os demais valores são ignorados.

- **Frequência (RQ01):** deploys na janela ÷ semanas da janela.
- **Lead time (RQ02):** os commits de cada deploy D vêm de `compare/{anterior}...{D}`. Variante **(a)**, por release: `data(D) − commit mais antigo de D`, com mediana entre deploys. Variante **(b)**, por commit: `data(D) − data de cada commit`, com mediana de todos. Ficam fora o primeiro deploy da história, os *compare* 404 e os com mais de 1.000 commits ou recusados pela API — quase sempre comparações entre linhas de versão distintas, que não representam o que entrou no deploy.
- **CFR (RQ03):** variante **(a)**, falhas ÷ (falhas + sucessos) de CI; variante **(b)**, o deploy falhou se um deploy corretivo saiu em até 7 dias, com os últimos 7 dias da janela fora do denominador (censura). O dataset usa a heurística **v0** (SemVer: sobe só o *patch*). Outras três foram implementadas e comparadas: **v1** (metade dos commits é `fix`/`revert`), **v2** (v0 e no máximo 3 commits) e **v3** (v0, v1 ou tag com `hotfix`/`patch`). As quatro divergem muito entre si — a v0 marca 8.186 releases como corretivas, a v1 apenas 1.479 — o que já indicava a necessidade de validação humana. A escolha final está na seção 2.7: **nenhuma atinge o F1 mínimo**, e a v0 foi mantida como referência.
- **Recuperação (RQ04):** runs agrupados por workflow e ordenados por `run_started_at`. Um episódio começa na primeira falha após um sucesso e termina no sucesso seguinte, com duração `updated_at(sucesso) − run_started_at(1ª falha)`; o valor do repositório é a mediana dos episódios fechados. Episódios sem sucesso até o fim da janela são **censurados** e contados à parte. Falhas anteriores ao primeiro sucesso não abrem episódio.

## 2.5 Variantes para a análise de sensibilidade (RQ 07)

As métricas de velocidade e o CFR (b) são calculados para três unidades de deploy:

| Unidade | Definição | Data |
| :--- | :--- | :--- |
| `release` (referência) | Release publicada sem pré-release | `published_at` |
| `release_pre` | Release publicada, incluindo pré-releases | `published_at` |
| `tag` | Tag do repositório | Data de autoria do commit apontado |

Para não esgotar a cota, o lead time de uma unidade não é calculado quando ela tem mais de 300 deploys na janela. Isso acontece sobretudo com tags em monorepos. Esses casos ficam marcados na coluna `lt_<unidade>_omitido`. As combinações C1–C3 da RQ 07 são montadas a partir dessas colunas na S03 (#142).

## 2.6 Dataset e viés de seleção

O dataset final (`data/dataset_dora.csv`) tem uma linha por repositório, com os metadados da RQ06, as métricas em todas as variantes e as contagens de qualidade da coleta. Cada coluna está descrita em `data/DICIONARIO.md`.

A amostra 1 tem 300 repositórios em 27 linguagens, idade mediana de 5,8 anos (IQR 2,0–10,9) e 142 contribuidores medianos (IQR 50–335); a coleta somou 17.217 releases e 833.582 workflow runs válidos. Perdas conhecidas: 244 releases ficaram fora do lead time por *compare* acima de 1.000 commits ou recusado pela API, 8 por *compare* 404, 7 repositórios tiveram o lead time omitido por excederem 300 releases na janela, e 139 de 20.077 episódios de falha ficaram censurados.

O viés de seleção foi medido comparando os aceitos com cada etapa de descarte (Mann-Whitney e delta de Cliff para estrelas e idade, qui-quadrado para linguagem, com Holm). **Os aceitos têm mais estrelas que os descartados** (9.484,5 contra 2.969,5; δ = 0,292, efeito pequeno; p < 0,001) e são ligeiramente mais jovens (δ = −0,116, desprezível; p = 0,016), e a distribuição de linguagens difere (p < 0,001). O filtro de Actions é o mais seletivo (δ de estrelas = 0,357). A amostra caracteriza, portanto, **projetos populares, ativos e que publicam releases com frequência** — não o ecossistema open-source em geral.

Dois testes de sanidade não encontraram diferença: os 1.108 candidatos avaliados contra os 7.349 não avaliados (δ ≤ 0,017; p = 1) e a A1 contra a A2 (δ ≤ 0,019; p = 1). A ordem de avaliação e a composição das amostras não introduzem viés adicional, o que não remove o viés dos critérios de inclusão (seção 5.3). Tudo se regenera com `python -m analise.caracterizacao`.

## 2.7 Validação manual (amostra-ouro)

**Sorteio.** Foram sorteados 60 repositórios da amostra 1 com semente fixa (`sample(n=60, random_state=42)`) e, para cada um, até 5 releases da janela com um `random.Random(42)` novo por repositório, num total de 300 releases. O sorteio é reprodutível por `python -m analise.amostra_ouro` e a lista está em `validacao/amostra_ouro_repos.csv` e `validacao/amostra_ouro_releases.csv`.

**Rotulagem independente.** Os três integrantes rotularam sozinhos, sem consultar os demais nem ver a saída da heurística, três dimensões: (i) tipo do projeto; (ii) se as releases representam entregas reais ao usuário; (iii) se cada release sorteada é corretiva. São 360 julgamentos por pessoa, 1.080 no total, em `validacao/rotulos_<nome>_*.csv`.

**Concordância.** Medida pelo kappa de Fleiss por dimensão (Tabela 4), interpretada segundo Landis e Koch (1977). A concordância bruta é reportada junto porque o kappa desconta a concordância esperada por acaso e, quando uma categoria domina, pode colapsar mesmo com acordo alto — é o que ocorre em `releases_reais`.

**Tabela 4 — Concordância entre os três avaliadores.**

| Dimensão | n | κ de Fleiss | Interpretação | Os 3 iguais | Maioria 2/3 | Categoria dominante |
| :--- | ---: | ---: | :--- | ---: | ---: | :--- |
| Tipo do projeto | 60 | 0,872 | quase perfeita | 86,7% | 100% | aplicação/serviço (41,7%) |
| Releases são entrega real | 60 | 0,157 | leve | 90,0% | 98,3% | sim (95,6%) |
| Release é corretiva | 300 | 0,504 | moderada | 71,0% | 100% | não (73,4%) |

O κ de 0,157 em `releases_reais` **não** significa desacordo: os três concordaram em 90% dos repositórios. Significa que quase todos os repositórios receberam o mesmo rótulo (`sim` em 95,6% dos julgamentos), de modo que o acaso já explicaria quase toda a concordância observada. A medida é pouco informativa nessa dimensão, e a leitura correta é a concordância bruta.

O κ de 0,504 em `corretiva` é o número que importa, e é apenas moderado. Três pessoas lendo as mesmas notas de release e a mesma lista de commits divergiram em 29% dos casos. A prevalência de "sim" variou de 16,7% a 37,3% entre avaliadores. Isso é evidência direta de que **o próprio conceito de "release corretiva" é ambíguo**, e não apenas difícil de automatizar.

**Consenso.** Resolvido por maioria de 2 em 3, com o protocolo em `validacao/PROTOCOLO.md`. Houve maioria em 100% das releases e dos tipos de projeto; apenas 1 repositório ficou sem maioria em `releases_reais` e segue marcado para decisão em reunião. O gabarito final tem 78 releases corretivas e 222 não corretivas (26,0% de prevalência), em `validacao/consenso_releases.csv`.

**Avaliação da heurística.** Quatro versões foram testadas contra o consenso (Tabela 5). **Nenhuma atinge o F1 mínimo de 0,70 exigido pelo enunciado.**

**Tabela 5 — Heurística de release corretiva contra o gabarito humano (n = 300).**

| Versão | Regra | Precisão | Recall | F1 |
| :--- | :--- | ---: | ---: | ---: |
| v0 `semver_patch` | sobe só o *patch* da versão | 36,5% | 69,2% | 0,478 |
| v1 `mensagens` | ≥ metade dos commits é `fix:`/revert | 94,4% | 21,8% | 0,354 |
| v2 `patch_poucos_commits` | v0 **e** ≤ 3 commits | 59,5% | 28,2% | 0,383 |
| **v3 `combinada`** | v0 **ou** v1 **ou** tag com `hotfix`/`patch` | 37,7% | 73,1% | **0,498** |

A v0, que gerou o `cfr_b_release` de todo o dataset, tem **precisão de 36,5%**: de cada três releases que ela marca como corretivas, duas não são, segundo o consenso humano. A v1 inverte o erro — precisão de 94,4% com recall de 21,8%, ou seja, quando acusa quase sempre acerta, mas deixa passar quatro de cada cinco correções reais. A v3, melhor por F1, supera a v0 por apenas 0,020, e as duas produzem medianas de CFR (b) praticamente iguais (25,0% em ambas).

Por isso **a v0 foi mantida como definição de referência**: trocá-la pela v3 exigiria recalcular as três amostras sem ganho de validade mensurável. A decisão e seu custo estão registrados aqui e discutidos na seção 5.1, onde a validade de construto do CFR (b) deixa de ser uma suspeita e passa a ser um resultado medido. As quatro versões e o detalhamento estão em `validacao/heuristica_versoes.md` e `validacao/avaliacao_heuristica.csv`.

---

# 3. Resultados

Todas as métricas são resumidas por **mediana e IQR** (1º–3º quartil), como pede o enunciado e como a seção 3.7.5 demonstra ser necessário. Os resultados aparecem no escopo pedido (300 repositórios da amostra 1) e na amostra estendida, para mostrar que não dependem do sorteio.

O CFR (b) usa a heurística v0 de release corretiva, **reprovada na validação contra o gabarito humano** (F1 = 0,478, precisão 36,5%; seção 2.7). Foi mantida por ser a melhor disponível sem recoletar, e todo resultado marcado **[NÃO VALIDADO]** deve ser lido com essa ressalva.

**Tabela 3 — Resumo das métricas.** Mediana [IQR].

| Métrica | n (300 / 900) | 300 | 900 |
| :--- | :--- | :--- | :--- |
| Frequência de deploy (releases/semana) | 300 / 900 | 0,35 [0,19 – 0,81] | 0,35 [0,19 – 0,84] |
| Lead time (a), por release (dias) | 293 / 873 | 13,2 [3,1 – 37,3] | 12,0 [3,0 – 37,4] |
| Lead time (b), por commit (dias) | 293 / 873 | 8,8 [2,8 – 29,4] | 9,0 [2,5 – 28,1] |
| CFR (a), proxy de CI | 300 / 900 | 5,6% [2,2% – 11,2%] | 5,3% [2,2% – 11,2%] |
| CFR (b), proxy de entrega [NÃO VALIDADO] | 300 / 900 | 25,0% [5,2% – 56,5%] | 25,0% [6,2% – 50,3%] |
| Tempo de recuperação (horas) | 278 / 834 | 2,8 [0,9 – 11,9] | 3,1 [0,9 – 17,3] |

Ficam sem lead time os repositórios com mais de 300 releases na janela, cujo cálculo foi omitido para preservar a cota da API (7 na A1, 27 no total). Ficam sem tempo de recuperação os que não tiveram nenhum episódio de falha fechado (22 na A1, 66 no total).

**Leitura geral:** ao triplicar a amostra, **todas as medianas ficam praticamente no mesmo lugar**, dentro do intervalo de confiança do escopo de 300. O detalhe está na seção 3.7.1. As figuras se regeneram com `python -m analise`.

---

## 3.1 RQ 01 a RQ 04 — as quatro métricas

Os valores centrais estão na Tabela 3. Em síntese:

**Frequência (RQ01).** Mediana de 0,35 release por semana, cerca de uma a cada 20 dias. Quase metade dos repositórios é **Medium** (entre uma por mês e uma por semana) e um terço é **Low**. Só 2% alcançam Elite. Projetos que entregam continuamente sem publicar releases ficam subestimados por construção, e os que não chegam a 5 releases já caíram no funil.

**Lead time (RQ02).** Medianas de 13,2 dias pela variante (a) e 8,8 pela (b). Em **65% dos repositórios a (b) é menor**. A razão é estrutural: a (a) mede desde o commit *mais antigo* de cada release, e um único commit esquecido puxa a release inteira para cima; a (b) usa a mediana de todos os commits, e a maioria entra perto da publicação. Quando cada release tem poucos commits, as duas convergem.

**Change failure rate (RQ03).** Os dois proxies contam histórias opostas. Pela falha de CI, **84% dos repositórios são Elite** (mediana 5,6%). Pela release corretiva em até 7 dias, só **37%** (mediana 25,0%), e 23% têm CFR (b) igual a zero. O CFR (a) mede falha de *pipeline* — teste instável entra como falha; o CFR (b) depende da heurística corretiva, reprovada na seção 2.7.

**Recuperação (RQ04).** Mediana de 2,8 horas. Recuperam-se em menos de 1 hora 27% dos repositórios, em menos de 1 dia 83%, em menos de 1 semana 97%. Os episódios censurados são 0,7% de 20.077.

![Change failure rate pelos dois proxies](../analise/saida/600/figuras/fig04_rq03_cfr.png)

**Como ler.** Curva acumulada: para cada valor de CFR no eixo horizontal, a altura é a proporção de repositórios com CFR até ali. Quanto mais cedo a curva sobe, menor a taxa de falha. As verticais são as fronteiras DORA (15%, 30%, 45%). As duas curvas separadas são o resultado: o proxy escolhido domina a resposta da RQ03.

## 3.2 Classificação DORA (combinação de referência)

![Perfil DORA por métrica](../analise/saida/600/figuras/fig06_perfil_dora.png)

**Como ler.** Cada barra soma 100% dos repositórios, divididos pela categoria DORA daquela métrica; o tom mais escuro é Elite. "Geral" é a classificação final do enunciado: mediana dos pontos das quatro métricas, arredondada para baixo.

| Classificação geral | Elite | High | Medium | Low |
| :--- | ---: | ---: | ---: | ---: |
| 300 repositórios | 8% | 35% | 50% | 7% |
| 600 repositórios | 7% | 36% | 48% | 9% |

Metade é Medium e um terço é High. Cada métrica puxa para um lado: o CFR (a), quase todo em Elite, puxa para cima; a frequência, com ~80% entre Medium e Low, puxa para baixo; o lead time se espalha pelas quatro.

## 3.3 RQ 05 — Velocidade × estabilidade

![Frequência de deploy contra taxa de falha](../analise/saida/600/figuras/fig07_rq05_velocidade_estabilidade.png)

**Como ler.** Cada ponto é um repositório: frequência de deploy no eixo horizontal (escala log), CFR no vertical. O ρ de Spearman vai de −1 a 1; perto de zero indica ausência de relação monotônica.

| Correlação com a frequência | 300 | 600 |
| :--- | :--- | :--- |
| CFR (a), proxy de CI | ρ = 0,18 (p = 0,002) | ρ = 0,12 (p = 0,004) |
| CFR (b), proxy de entrega [NÃO VALIDADO] | ρ = 0,60 (p < 0,001) | ρ = 0,56 (p < 0,001) |

Pelo CI a correlação é significativa mas **fraca**, e diminui com a amostra maior: publicar mais não se associa a quebrar mais o pipeline, o que é coerente com a tese do DORA. Pela entrega é **forte** — mas a seção 3.7 mostra que isso é artefato da definição, não achado. Em nenhum dos casos correlação implica causalidade.

## 3.4 RQ 06 — Características associadas ao desempenho

![Tamanho de efeito por fator e métrica](../analise/saida/600/figuras/fig08_rq06_fatores.png)

**Como ler.** Cada célula cruza uma característica do repositório com uma métrica. O valor é o tamanho de efeito ε² = H/(n−1) do Kruskal-Wallis: quanto da variação da métrica aquela característica explica (< 0,01 desprezível, < 0,06 pequeno, < 0,14 médio, ≥ 0,14 grande). Em negrito, os que sobrevivem à correção de Holm sobre os 24 testes.

**A idade é o fator de maior efeito** (ε² = 0,21–0,25 no lead time, efeito grande): repositórios de até 2 anos têm lead time mediano de 2,0 dias contra 28,5 nos mais antigos, e publicam quase três vezes mais (0,67 contra 0,23 release/semana). Equipes maiores têm lead time maior (ε² 0,08–0,14). O **CFR (a) não se associa a nenhum fator**.

**A linguagem só fica significativa com 600 repositórios** — com 300 não sobrevivia a Holm. Lead time mediano: TypeScript 7,1 dias, JavaScript 8,9, Python 11,5, Rust 14,1, Go 16,7, Java 22,9, C 35,3, C++ 60,6. É um exemplo didático de **poder estatístico**: o efeito existia, mas 300 repositórios divididos em seis grupos não bastavam para detectá-lo após a correção.

**Controlando os fatores entre si**, a leitura muda. Idade, contribuidores e estrelas são correlacionados (ρ de 0,07 a 0,59; VIF entre 1,2 e 1,9, abaixo do corte de 5). Na correlação parcial de Spearman, a **idade resiste** (ρ parcial 0,34 no lead time, −0,39 na frequência, −0,34 no CFR (b), todas p < 0,001) e é o maior coeficiente padronizado da regressão log-log (0,52; IC 95% [0,38; 0,65]). Já **contribuidores perde** a associação com o lead time (ρ parcial 0,10, p = 0,17). **Estrelas** não tem associação parcial com nenhuma métrica. Parte do efeito de "equipes maiores" é, portanto, efeito da idade.

## 3.5 RQ 07 — Sensibilidade à definição operacional

Três combinações de definições operacionais: **C1** (release, lead time a, CFR a), **C2** (release + pré-release, b, b) e **C3** (tag, b, a).

| Par | Mudam de categoria (300 → 600) | κ ponderado (300 → 600) |
| :--- | :--- | :--- |
| C1 × C2 | 36% → 35% | 0,42 → 0,46 |
| C1 × C3 | 28% → 28% | 0,63 → 0,64 |
| C2 × C3 | 33% → 34% | 0,54 → 0,53 |

**Entre 28% e 36% dos repositórios mudam de categoria só por trocar a definição**, e a proporção não varia de 300 para 600 — não é ruído amostral. Em C2, cerca de 23% descem e 13% sobem, porque o CFR (b) é mais severo; em C3, 23% sobem e 5% descem, porque tags são mais frequentes que releases. A classificação DORA de um repositório **não é robusta à definição operacional**, o que exige cautela ao comparar estudos que usam proxies diferentes.

## 3.6 RQ 08 (bônus) — Evolução temporal

O enunciado sugere séries trimestrais com Mann-Kendall, mas com 4 pontos esse teste nunca alcança p < 0,05 — o menor p bilateral possível com n = 4 é 0,089, qualquer que seja a série. A análise usa a **série mensal** (12 pontos), com Mann-Kendall por repositório e métrica e correção de Benjamini-Hochberg sobre os 250 a 600 testes de cada métrica.

| Métrica | p bruto < 0,05 | Significativo após FDR | Dados insuficientes |
| :--- | :---: | :---: | :---: |
| Frequência | 16,8% | 0% | 0% |
| Lead time (a) | 16,7% | 0% | 50,2% |
| CFR (a) | 13,2% | 0,17% (1 repo) | 19,2% |
| Recuperação | 16,5% | 0% | 59,7% |

O teste bruto "encontra" tendência em 13% a 17% dos repositórios, acima dos 5% esperados por acaso. **Após o FDR, só 1 dos 600 sobrevive.** É o retrato de por que a correção de múltiplos testes importa: a aparência de um em cada seis repositórios mudando vira quase inteiramente ruído quando se testa centenas ao mesmo tempo. Não há melhora nem piora sistemática ao longo do ano; a conclusão defensável é metodológica.

## 3.7 Análises complementares (além do escopo pedido)

O estudo foi estendido a 900 repositórios em três amostras independentes, com análises de validade que o enunciado não pede. Seguem só as conclusões; o material completo está em `analise/saida/` e em `docs/base-teorica.md`.

**Reprodutibilidade.** A1 e A2 são estatisticamente indistinguíveis nas seis métricas (todos |δ| < 0,07, nenhum p significativo). De 300 a 900, todas as medianas caem dentro do IC de 300 e os intervalos estreitam de 21% a 51%.

**O CFR (b) mede cadência, não falha.** Quem publica mais tem mais oportunidade de ter uma release seguida por outra em 7 dias. Condicionando pela oportunidade, **a correlação com a frequência cai de 0,604 para −0,039** (p = 0,52). Confusão por tamanho foi testada e descartada (o ρ cai no máximo 0,059). É a mesma conclusão que a precisão de 36,5% da heurística já indicava, por via independente.

**As faixas quase não discriminam.** ε² de 0,008 (estrelas) e 0,022 (contribuidores), nenhum sobrevivendo a Holm; o que elas separam bem são as variáveis que as definem (CFR (b), ε² = 0,379, perto do controle tautológico de 0,403). Um índice contínuo por posto percentílico mostra que **as faixas retêm 63,2% da variância**, com 8,2% dos pares entre faixas invertidos.

**Por que mediana e IQR.** Nenhuma métrica passa em teste de normalidade e a média chega a 5,7× a mediana. A contagem de releases tem dispersão 493× a da Poisson. A recuperação segue Weibull com β mediano 0,557 e β < 1 em 87,8% dos repositórios — **taxa decrescente**, o que invalida o modelo exponencial. O Teorema do Limite Central só se aproxima perto de n = 300 nesta população.

**O DORA é uma lente entre outras.** Contra medidas de fluxo por pull request (CHAOSS, SPACE), nenhum par chega a ρ = 0,7, e **CFR (b) × aceitação de PR fica em 0,044** (não significativo). Trocando o proxy de falha, o mesmo conjunto aparece como 99% Elite (reverts), 84% (CI) ou 38% (release corretiva).

**Uma medida que não se reproduz.** A cobertura da API de Deployments varia entre as três amostras (31,3%, 41,7%, 43,3%; p = 0,0048) sem causa identificada — evidência negativa de confiabilidade, e contraste que dá credibilidade à positiva acima.

---

# 4. Discussão

Esta seção confronta as hipóteses informais da seção 1.4 com o que os dados mostraram, e discute o que surpreendeu. As hipóteses foram reconstruídas depois da coleta, não pré-registradas; a seção 1.5 explica o registro e a seção 5.4 trata disso como ameaça à validade de conclusão.

## 4.0 Placar das hipóteses

| # | Hipótese (seção 1.4) | Resultado | Veredito |
| :--- | :--- | :--- | :--- |
| **H01** | ≥ 1 release/semana | mediana 0,35 release/semana, ≈ 1 a cada 20 dias | **Refutada** |
| **H02** | Lead time em dias; (a) > (b) | mediana (a) 13,2 d e (b) 8,8 d | **Confirmada** |
| **H03** | CFR < 15% nas duas variantes e convergentes | (a) 5,3%; (b) 25,0% — divergem por ≈ 5× | **Refutada** |
| **H04** | Recuperação < 24 h | mediana 2,8 h | **Confirmada** |
| **H05** | Correlação frequência × CFR nula ou negativa | ρ = +0,18 em (a) e +0,60 em (b) | **Refutada** |
| **H06** | Fatores do repositório com efeito ao menos pequeno | ε² = 0,008 (estrelas) e 0,022 (contribuidores), nenhum sobrevive a Holm | **Refutada** |
| **H07** | < 20% mudam de faixa entre definições | 27,7% a 36,0% mudam | **Refutada** |

Cinco refutadas, duas confirmadas. As duas que se confirmaram são as menos informativas: a H02 porque sua segunda metade estava dada na dica do enunciado, e a H04 porque o limiar de 24 h era frouxo. As cinco que caíram são as que carregam o conteúdo deste artigo — e a H05, em particular, caiu de um jeito que obrigou a reinterpretar a própria métrica (seção 3.7.3).

## 4.1 O que confirmou a expectativa

**A entrega é mais lenta do que o discurso sobre CI/CD sugere.** Mediana de 0,35 release por semana — uma a cada vinte dias. Projetos open-source populares com Actions configurado não entregam continuamente; entregam em ciclos, e a faixa Elite é ocupada por uma minoria.

**As distribuições são fortemente assimétricas.** Nenhuma das cinco métricas passa em teste de normalidade e a média do lead time chega a quase seis vezes a mediana. A exigência de reportar mediana e IQR deixou de ser convenção e virou resultado demonstrado.

## 4.2 O que surpreendeu

**A heurística de falha reprovou na validação humana.** Nenhuma das quatro versões alcança o F1 mínimo de 0,70; a que gerou o dataset fica em 0,478, com precisão de 36,5%. A expectativa era que errasse alguma coisa, não que errasse dois terços das vezes em que acusa. Mais revelador é o κ de 0,504 entre os avaliadores e a prevalência de "sim" variando de 16,7% a 37,3%: **o problema não é só a regra automática ser ruim, é o conceito ser ambíguo para humanos também.** Uma heurística não pode ser mais precisa que a definição que tenta capturar. Isso recontextualiza a RQ03 — a divergência entre o CFR (a) e o (b) não é um caso de dois proxies válidos medindo coisas diferentes, mas de um proxy razoável contra um que não sobrevive à validação.

**A classificação DORA discrimina muito pouco.** As faixas não separam popularidade (ε² = 0,008) nem contribuidores (ε² = 0,022). O que separam bem são as próprias variáveis que as definem, perto do controle tautológico. Nesta amostra, a classificação é em grande medida uma relabelagem de variáveis contínuas, e o índice contínuo mostra que o corte em faixas descarta mais de um terço da informação.

**DORA e fluxo por PR são constructos distintos.** O par mais direto compartilha 10% da variância, e CFR (b) contra aceitação de PR não tem associação alguma (ρ = 0,044). A consequência é incômoda: **o DORA é *uma* medida de desempenho de engenharia, não *a* medida**, e uma lente igualmente legítima ordena os mesmos repositórios de forma substancialmente diferente.

**A recuperação não tem taxa constante.** O ajuste de Weibull dá β mediano de 0,557, com β < 1 em 87,8% dos repositórios: quanto mais tempo um episódio dura, menor a chance de terminar no instante seguinte. Duas populações com o mesmo MTTR mediano podem ter dinâmicas opostas, e a mediana não distingue.

## 4.3 O que o estudo não consegue responder

Duas perguntas ficam fora de alcance pela mesma causa: **todo o processo é medido por proxies do próprio GitHub**, sem desfecho externo de qualidade. Não há como avaliar **previsibilidade** — se as métricas preveem incidente em produção, satisfação de usuário ou custo de manutenção — nem **poder discriminante contra qualidade**: o resultado negativo da seção 3.7 mostra que as faixas não separam popularidade nem tamanho de equipe, o que é informativo, mas não equivale a dizer que não separam qualidade.

---

# 5. Ameaças à validade

Taxonomia de Cook & Campbell, na adaptação de Wohlin et al. para engenharia de software. Cada ameaça é classificada em **mitigada**, **parcialmente mitigada** ou **aberta**, e apoiada nos resultados da validação manual (seção 2.7) e das análises de validade (seções 3.5 e 3.7).

## 5.1 Validade de construto — *medimos o que achamos que medimos?*

| Ameaça | Situação | Evidência |
| :--- | :--- | :--- |
| **Release não é deploy** | aberta, por construção | O GitHub não registra implantação. A API de Deployments cobre só 38,8% dos 900 repositórios, com cobertura que varia entre amostras (seção 3.7.8). É a limitação mais importante do trabalho. |
| **A heurística de release corretiva não é válida** | **aberta, agora quantificada** | Contra o gabarito humano, nenhuma das quatro versões atinge F1 = 0,70; a que gerou o dataset tem precisão de 36,5% (seção 2.7). |
| **O CFR (b) está acoplado à cadência** | **confirmada e medida** | A suspeita foi testada: ao condicionar pela oportunidade de observação, ρ cai de 0,604 para −0,039 (p = 0,52). O CFR (b) mede, em boa parte, ritmo de publicação (seção 3.7.3). |
| **Falha de CI não é falha em produção** | parcialmente mitigada | Os dois proxies diferem por quase cinco vezes (5,3% × 25,0%). Mitigação: reportar as duas variantes lado a lado, nunca escolher uma. |
| **Mono-método** | parcialmente mitigada | Tudo vem da API do GitHub. Mitigação: medir os mesmos constructos por PRs e issues (CHAOSS, SPACE). Nenhum par alcança ρ = 0,7 (seção 3.7.6). |
| **Ausência de desfecho externo** | aberta | Não há incidente em produção, satisfação de usuário nem custo de manutenção. Impede avaliar previsibilidade e restringe o poder discriminante a atributos observáveis, não a qualidade. |

As duas primeiras linhas mudaram de natureza neste trabalho: eram suspeitas e passaram a ser **resultados medidos**. Isso não as mitiga — ao contrário, confirma que o CFR (b) deve ser lido como indicador de cadência, não de falha.

## 5.2 Validade interna — *há fatores não controlados?*

| Ameaça | Situação | Evidência |
| :--- | :--- | :--- |
| **Tamanho e popularidade como confusão** | **mitigada** | Testada por dois caminhos: estratificação em quartis e correlação parcial de Spearman. O ρ de 0,562 cai no máximo 0,059 na parcial, e os doze estratos mantêm o sinal (0,381–0,698). As faixas também não separam estrelas (ε² = 0,008) nem contribuidores (ε² = 0,022). |
| **Repositórios antigos acumulam releases** | parcialmente mitigada | Idade é o único atributo independente que as faixas separam (ε² = 0,109). As métricas são normalizadas pela janela, o que limita a acumulação, e a idade entra como fator na RQ06. |
| **Heterogeneidade da população** | documentada, não mitigável | Índice de dispersão de 493× em relação à Poisson (seção 3.7.5). Quatro faixas fixas não capturam essa estrutura. |

## 5.3 Validade externa — *vale além da amostra?*

| Ameaça | Situação | Evidência |
| :--- | :--- | :--- |
| **Amostra de repositórios populares** | aberta, por desenho | ≥ 1.000 estrelas, ≥ 5 releases e ≥ 50 runs. **Nada aqui se generaliza para projetos corporativos, pequenos ou sem CI/CD estabelecido.** |
| **Sobrevivência do funil** | documentada | Dos 8.457 candidatos, poucos chegam à amostra; o filtro de releases é o mais severo. Funil e caracterização dos descartados em 2.6 e 3.7.1. |
| **Estabilidade entre amostras** | **mitigada para as métricas DORA** | Três amostras sem repositório em comum produzem estimativas sobrepostas nas seis métricas, com ICs estreitando 21%–51% (seção 3.7.1). |
| **…mas não para medidas auxiliares** | aberta | A cobertura da API de Deployments varia entre amostras de forma detectável (p = 0,0048) e sem causa identificada. |
| **Janela única** | aberta | 12 meses. A RQ08 não encontrou tendência interna, mas outro período pode dar outros valores absolutos. |

## 5.4 Validade de conclusão — *a estatística é adequada?*

| Ameaça | Situação | Evidência |
| :--- | :--- | :--- |
| **Hipóteses reconstruídas, não pré-registradas** | **aberta** | Ver abaixo. |
| **Múltiplas comparações** | mitigada | Holm em todas as famílias de testes; FDR na RQ08, onde apenas 1 de 600 repositórios mantém tendência após a correção. |
| **Pressupostos de normalidade** | mitigada | Nenhuma métrica passa em Shapiro-Wilk (p entre 10⁻¹⁴ e 10⁻³³). Todos os testes são não paramétricos e as estimativas são medianas com IQR. |
| **Poder em subgrupos** | parcialmente mitigada | O TLC só se aproxima perto de n = 300 nesta população (seção 3.7.5), e os subgrupos da RQ06 são menores. Mitigação: testes não paramétricos e relato obrigatório de tamanho de efeito. A linguagem na RQ06, que só fica significativa com 600, ilustra ganho de poder e não mudança de fenômeno. |
| **Dados censurados** | mitigada | Episódios sem recuperação na janela e releases dos últimos 7 dias ficam fora dos denominadores, com a proporção censurada reportada. |
| **Truncamento da paginação** | documentada | Atinge ~3% dos PRs e 8%–10% dos deployments, marcado por repositório; as medidas afetadas são lidas como limite inferior. |

**Sobre as hipóteses.** As da seção 1.4 foram escritas em 20/10/2026, com os resultados já disponíveis (seção 1.5). Isso abre espaço para HARKing e para viés na escolha do que reportar. Três coisas limitam o dano sem eliminá-lo: cada hipótese declara a origem da expectativa, e nenhuma foi derivada dos dados; cinco das sete foram refutadas, o oposto do padrão que HARKing produz; e as decisões analíticas sensíveis têm justificativa verificável sem olhar os dados — a série mensal da RQ08, por exemplo, decorre de um fato aritmético do teste de Mann-Kendall (com n = 4 o menor p bilateral possível é ≈ 0,089). Ainda assim não há como provar, depois do fato, qual era a expectativa. **Uma replicação deste desenho deve registrar as hipóteses antes da coleta.**

---

# 6. Replicação cruzada

> **Seção pendente da entrega final.** O professor sorteia, para cada grupo, o pipeline de outro grupo da turma. Esta seção só pode ser escrita depois do sorteio e da execução.

## 6.1 O que esta seção deve conter

Conforme a seção 9 do enunciado, o grupo **replicador** deve registrar aqui:

1. **Execução do pipeline do grupo sorteado usando apenas o README**, sobre uma subamostra de 30 repositórios do dataset original, sem pedir ajuda ao grupo autor. Travar é um resultado a registrar, não um fracasso a esconder.
2. **Comparação com o CSV original:** diferença relativa por métrica e percentual de repositórios com a mesma classificação DORA. Pequenas diferenças são esperadas, porque os repositórios continuam recebendo commits e as datas de coleta diferem.
3. **Issues abertas no repositório do grupo autor**, com evidências: comando executado, mensagem de erro, valores esperados e obtidos.
4. **Resposta:** o estudo foi reproduzível? O que impediu ou dificultou?

Responsáveis: execução pelo Henrique (#143), comparação e abertura de issues pelo Gabriel (#144).

## 6.2 O lado autor: o que está pronto para quem nos replicar

Os três datasets, os eventos por repositório e as medidas auxiliares estão versionados no Git, com cada coluna descrita em `data/DICIONARIO.md`: quem replicar **não precisa gastar cota de API nem as ~15 h de coleta**. A execução é por comando único (`python -m pipeline` e `python -m analise`), com dependências fixadas.

O cache da coleta (vários GB) **não** vai para o Git, então reexecutar sobre os dados versionados é reprodutível, mas **recoletar do zero não é** — depende do estado corrente da API. É a limitação mais provável de aparecer na replicação, e está declarada. Os demais pontos frágeis conhecidos são a exigência de `GITHUB_TOKEN`, o consumo de cota numa recoleta completa, a mudança natural das métricas entre datas de coleta e a cobertura instável da API de Deployments (seção 3.7).

## 6.3 Link do repositório e do Projects

- Repositório: `https://github.com/henriqjmelo/lab-expe-01`
- GitHub Projects: https://github.com/users/henriqjmelo/projects/2
