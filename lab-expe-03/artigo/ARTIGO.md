# Mineração de métricas DORA em repositórios open-source populares

**Laboratório de Experimentação de Software** · Engenharia de Software, 6º período
Guilherme Costa · Henrique Jardim Melo · Gabriel Afonso

> Documento consolidado, gerado por `python artigo/montar.py`. Não editar diretamente:
> altere as seções em `artigo/0N-*.md` e rode o script de novo.

---

# 1. Introdução

> Rascunho da issue #134, a ser revisado por Henrique e Gabriel antes de ir para o Overleaf.

## 1.1 Contexto e problema

As quatro métricas DORA — frequência de deploy, lead time for changes, change failure rate e tempo de recuperação — viraram o vocabulário padrão para falar de desempenho de entrega de software. Vêm do programa *DevOps Research and Assessment*, que as derivou de levantamentos com milhares de profissionais e as organizou em faixas (Elite, High, Medium, Low). Sua tese central é que velocidade e estabilidade **não** são um trade-off.

Essas métricas foram definidas para equipes que controlam o próprio pipeline de produção e sabem, por definição operacional interna, o que conta como "deploy" e o que conta como "falha em produção". Repositórios open-source no GitHub não oferecem nenhuma das duas coisas. Não há registro de deploy, não há registro de incidente e não há a quem perguntar. O que existe são **rastros**: releases publicadas, execuções de workflow, commits, tags e comparações entre releases.

Medir DORA aqui, portanto, não é aplicar uma definição: é **escolher proxies** e assumir o custo dessa escolha. Uma release é um deploy? Uma execução de CI que falha é uma falha em produção? Uma release de *patch* publicada três dias depois da anterior corrige um defeito, ou é rotina de atualização de dependência?

Cada resposta é uma hipótese não verificada sobre a relação entre um atributo interno, que se consegue contar, e um atributo externo, que é o que interessa. É nesse ponto que este trabalho se separa de uma aplicação direta do enunciado. Calcular as quatro métricas numa amostra grande é a parte mecânica. A parte que decide se os números significam alguma coisa é perguntar **o quanto os proxies escolhidos são medidas válidas** — se concordam com o julgamento humano, se sobrevivem à troca da definição operacional, se se reproduzem em amostras independentes e se as faixas DORA separam de fato grupos distintos.

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

O protocolo correto registra as hipóteses **antes** da coleta, e aqui isso não aconteceu: o Lab03 começou em 08/10/2026, o primeiro dataset entrou em 13/10/2026 e as hipóteses acima foram escritas em **20/10/2026**, com os resultados já disponíveis. Elas são **reconstruídas**, não pré-registradas.

Para que a reconstrução não seja racionalização do que foi encontrado, cada hipótese declara a origem da expectativa, e nenhuma foi derivada dos resultados. O leitor audita isso pelo saldo: **cinco das sete foram refutadas** (seção 4). Hipóteses escritas depois do resultado tendem a acertar; estas, na maioria, erram. A seção 5.4 trata disso como ameaça aberta.

## 1.6 Contribuições

1. **Dataset público de 900 repositórios** (três amostras independentes de 300) com as quatro métricas DORA, suas variantes e os eventos brutos que permitem recalcular tudo.
2. **Avaliação de validade das medidas** segundo os seis critérios da IEEE 1061, e não apenas o cálculo das métricas.
3. A demonstração, por duas vias independentes, de que **o CFR na variante (b) não mede falha**: a heurística reprova contra o gabarito humano (F1 = 0,478, precisão 36,5%) e a correlação com a frequência de deploy desaparece ao condicionar pela oportunidade de observação (seções 2.7 e 3.10.3).
4. A evidência de que as **faixas DORA não têm poder discriminante** nesta população, e um **índice contínuo** que preserva a informação descartada pelo corte em faixas (seções 3.10.4 e 3.10.7).
5. Um **ajuste de distribuições** que mostra por que média e desvio-padrão não se aplicam aqui, incluindo a verificação de que o Teorema do Limite Central precisa de n ≈ 300, não de n = 30 (seção 3.10.5).

## 1.7 Organização

Seção 2: metodologia e validação manual. Seção 3: resultados das RQs e análises de validade. Seção 4: hipóteses contra resultados. Seção 5: ameaças à validade. Seção 6: pacote de replicação.

---

# 2. Metodologia

> Rascunho da issue #139, a ser revisado por Henrique e Gabriel antes de ir para o Overleaf. Os números da coleta são os do `data/` desta versão. O único item em aberto são as datas exatas da janela, a confirmar com o professor.

## 2.1 Fonte de dados

Os dados vêm da API pública do GitHub e foram coletados por um script próprio do grupo, sem bibliotecas prontas de acesso à API. O script usa a API REST para busca, releases, comparações entre releases e workflow runs, e a GraphQL para as tags com data. O pipeline inteiro roda com um único comando (`python -m pipeline --config config.yaml`). Cada resposta da API fica em cache local, então interromper a coleta e rodá-la de novo continua de onde parou e reproduz o mesmo dataset sem novas chamadas. O cliente HTTP respeita os cabeçalhos de rate limit e repete com *backoff* exponencial as respostas 5xx e as falhas de rede.

## 2.2 Janela de observação

A janela tem 12 meses, de **1º de outubro de 2025 a 30 de setembro de 2026** **[PENDENTE: confirmar com as datas fixadas pelo professor]**. Isso dá aproximadamente 52,1 semanas. Só entram nas métricas as releases publicadas e os workflow runs criados dentro dela. A exceção é a release imediatamente anterior a uma release da janela, que é usada como base para obter os commits incluídos, mesmo estando fora.

## 2.3 Seleção dos repositórios e funil

1. **Candidatos.** Foi usada a busca de repositórios com mais de 1.000 estrelas, não arquivados e com *push* depois do início da janela. Como cada consulta devolve no máximo 1.000 resultados, a busca foi fatiada em nove faixas de estrelas (1.000–1.199, 1.200–1.499, 1.500–1.999, 2.000–2.999, 3.000–4.999, 5.000–9.999, 10.000–19.999, 20.000–49.999 e ≥ 50.000).
2. **Ordem de avaliação.** Os candidatos foram embaralhados com semente fixa (42) e avaliados nessa ordem até a amostra chegar a 300 repositórios. Isso evita que a amostra fique concentrada nos repositórios mais estrelados de cada faixa.
3. **Filtros**, aplicados do mais barato para o mais caro:
   - (i) usa GitHub Actions (`actions/workflows` com `total_count > 0`);
   - (ii) tem ≥ 5 releases publicadas, sem pré-release, na janela;
   - (iii) tem ≥ 50 workflow runs válidos (`success` ou falha) disparados por `push` no *default branch* na janela.

O funil é gerado automaticamente pelo pipeline (`data/funil.csv`), e cada descarte fica registrado com o motivo em `data/descartes.csv`.

**Tabela 1 — Funil de seleção** (`data/funil.csv`).

| Etapa | Restantes | Descartados | Motivo do descarte |
| :--- | ---: | ---: | :--- |
| Candidatos da busca | 8.457 | — | — |
| Avaliados (ordem aleatória, até o alvo) | 1.108 | 7.349 | não avaliados: alvo de 300 já atingido |
| Usam GitHub Actions | 937 | 171 | nenhum workflow cadastrado |
| ≥ 5 releases na janela | 399 | 538 | menos de 5 releases publicadas (sem pré-release) |
| ≥ 50 runs válidos na janela | 300 | 99 | menos de 50 runs válidos em `push` no *default branch* |
| **Amostra final** | **300** | 0 | — |

O filtro mais restritivo é o de releases: 57% dos repositórios que usam Actions publicaram menos de 5 releases em 12 meses. Isso indica que muitos projetos populares entregam por outros meios, como *rolling release*, publicação direta em registros de pacotes ou ausência de versionamento formal. Esse ponto é retomado nas ameaças à validade.

Como cada faixa de estrelas contribui com no máximo 1.000 candidatos, os mais estrelados de cada faixa, a amostra fica deslocada para repositórios mais populares do que uma amostra uniforme de todos os repositórios com mais de 1.000 estrelas. A mediana é de 9.485 estrelas (IQR 2.844–28.694).

## 2.4 Definições operacionais

Todas as definições seguem a seção 3 do enunciado, comum à turma. Em resumo:

- **Deploy:** release publicada (`draft = false`), sem pré-release na definição principal. A data do deploy é `published_at`.
- **Data do commit:** `commit.author.date`.
- **Execuções de CI:** workflow runs do *default branch* com `event = push`. São consultadas mês a mês, e um mês com mais de 1.000 resultados é dividido ao meio recursivamente até caber. A classificação usa o campo `conclusion`:
  - `success` conta como sucesso;
  - `failure`, `timed_out` e `startup_failure` contam como falha;
  - os demais valores são ignorados.

Métricas por repositório:

- **Deployment frequency (RQ 01):** deploys na janela ÷ semanas da janela.
- **Lead time (RQ 02):** os commits de cada deploy D vêm de `compare/{deploy anterior}...{D}`, paginado.
  - (a) Por release: `data(D) − commit mais antigo de D`. O valor do repositório é a mediana entre os deploys.
  - (b) Por commit: `data(D) − data de cada commit`. O valor do repositório é a mediana de todos os commits.
  - Ficam fora do cálculo, e são contados à parte:
    - o primeiro deploy da história;
    - os *compare* com resposta 404 (tag apagada ou reescrita);
    - os *compare* com mais de 1.000 commits, ou que a API se recusa a gerar (HTTP 422, *diff* demorado demais). Esse último critério é do grupo: são quase sempre comparações entre linhas de versão diferentes ou entre pacotes distintos de um monorepo, intercalados por data, e não representam o que entrou no deploy.
- **Change failure rate (RQ 03):**
  - (a) Proxy de CI: falhas ÷ (falhas + sucessos), com todos os workflows juntos.
  - (b) Proxy de entrega: o deploy D falhou se um deploy **corretivo** foi publicado em até 7 dias depois dele. Deploys dos últimos 7 dias da janela ficam fora do denominador (censura). O dataset desta versão usa a heurística **v0** (SemVer: mantém `maior.menor` do deploy anterior e sobe só o `patch`). Três outras versões foram implementadas e comparadas de forma descritiva na amostra 1 (`validacao/comparar_versoes.py`, `validacao/heuristica_versoes.md`):
    - **v1 mensagens:** corretiva se pelo menos metade dos commits da release tem prefixo `fix`/`revert` (Conventional Commits).
    - **v2 patch + poucos commits:** v0 **e** a release tem no máximo 3 commits.
    - **v3 combinada:** v0 **ou** v1 **ou** o nome da tag contém `hotfix`/`patch`.

    As quatro divergem muito entre si — a v0 marca 8.186 releases como corretivas, a v1 apenas 1.479 — o que por si só já indicava que a validação contra julgamento humano era necessária. A escolha final foi decidida na seção 2.7: **nenhuma atinge o F1 mínimo**, e a v0 foi mantida como referência.
- **Tempo de recuperação (RQ 04):** os runs são agrupados por workflow e ordenados por `run_started_at`.
  - Um episódio começa na primeira falha depois de um sucesso e termina no sucesso seguinte, com duração `updated_at(sucesso) − run_started_at(1ª falha)`. O valor do repositório é a mediana dos episódios fechados, em horas.
  - Episódios sem sucesso até o fim da janela são **censurados**: não entram na mediana, mas são contados, e a proporção é reportada por repositório.
  - Falhas no início da janela, antes do primeiro sucesso, não abrem episódio, porque não é possível saber quando a falha começou.

## 2.5 Variantes para a análise de sensibilidade (RQ 07)

As métricas de velocidade e o CFR (b) são calculados para três unidades de deploy:

| Unidade | Definição | Data |
| :--- | :--- | :--- |
| `release` (referência) | Release publicada sem pré-release | `published_at` |
| `release_pre` | Release publicada, incluindo pré-releases | `published_at` |
| `tag` | Tag do repositório | Data de autoria do commit apontado |

Para não esgotar a cota, o lead time de uma unidade não é calculado quando ela tem mais de 300 deploys na janela. Isso acontece sobretudo com tags em monorepos. Esses casos ficam marcados na coluna `lt_<unidade>_omitido`. As combinações C1–C3 da RQ 07 são montadas a partir dessas colunas na S03 (#142).

## 2.6 Dataset

O dataset final (`data/dataset_dora.csv`) tem uma linha por repositório. Ele traz os metadados usados na RQ 06 (estrelas, linguagem, idade e número de contribuidores), as métricas de cada unidade de deploy e as contagens de qualidade da coleta:

- releases ignoradas por *compare* 404 ou grande demais;
- meses que bateram o teto de 1.000 runs;
- episódios censurados.

Cada coluna está descrita em `data/DICIONARIO.md`, com nome, tipo, unidade e fórmula ou campo de origem na API.

A amostra final tem **300 repositórios** em 27 linguagens. As mais frequentes são TypeScript (61), Python (55), Go (49), Rust (28), C++ (20) e JavaScript (19). A idade mediana é de 5,8 anos (IQR 2,0–10,9), e o número mediano de contribuidores é 142 (IQR 50–335). A coleta somou 17.217 releases, 28.792 tags e 833.582 workflow runs válidos na janela. A Tabela 2 resume a qualidade da coleta.

**Tabela 2 — Contagens de qualidade da coleta.**

| Ocorrência | Quantidade |
| :--- | :--- |
| Repositórios com algum mês acima de 1.000 runs (subdividido) | 34 |
| Dias ainda acima de 1.000 runs após a subdivisão (dados incompletos) | 19 dias em 4 repositórios |
| Releases ignoradas no lead time por *compare* 404 | 8 |
| Releases ignoradas no lead time por *compare* com mais de 1.000 commits ou que a API não conseguiu gerar (422) | 244 |
| Repositórios com lead time de release omitido (mais de 300 releases na janela) | 7 |
| Episódios de falha de CI censurados (sem recuperação até o fim da janela) | 139 de 20.077, em 74 repositórios |

**Caracterização e viés de seleção.** A Tabela 3 resume os metadados da A1 e da amostra acumulada A1+A2; o detalhamento por linguagem está em `analise/saida/caracterizacao/`.

**Tabela 3 — Metadados das amostras.** Mediana (Q1–Q3).

| Amostra | Repositórios | Estrelas | Idade (anos) | Contribuidores |
| :--- | ---: | :--- | :--- | :--- |
| A1 | 300 | 9.484,5 (2.858,5–28.636) | 5,79 (1,96–10,89) | 142 (50,25–335) |
| A1+A2 | 600 | 9.500 (2.878,75–29.144,5) | 6,24 (2,43–10,17) | 150 (52–343) |

O viés de seleção foi medido comparando os aceitos com cada etapa de descarte, por Mann-Whitney e delta de Cliff para estrelas e idade, qui-quadrado para linguagem, com correção de Holm. **Os aceitos têm mais estrelas que os descartados** (9.484,5 contra 2.969,5; δ = 0,292, efeito pequeno; p < 0,001) e são ligeiramente mais jovens (5,79 contra 7,88 anos; δ = −0,116, desprezível; p = 0,016), e a distribuição de linguagens difere (p < 0,001). O filtro de Actions é o mais seletivo (δ de estrelas = 0,357); o de releases associa-se a estrelas, idade e linguagem (p ≤ 0,001); o de runs mostra diferenças menores mas detectáveis (p ≤ 0,017). A amostra caracteriza, portanto, **projetos populares, ativos e que publicam releases com frequência** — não o ecossistema open-source em geral.

Dois testes de sanidade não encontraram diferença: os 1.108 candidatos avaliados contra os 7.349 não avaliados (δ ≤ 0,017; p = 1 em estrelas, idade e linguagem) e a A1 contra a A2 (δ ≤ 0,019; p = 1). A ordem de avaliação e a composição das duas amostras, portanto, não introduzem viés adicional — o que não remove o viés dos critérios de inclusão, tratado na seção 5.3.

![Distribuições de estrelas e idade entre aceitos e descartados](../analise/saida/caracterizacao/figuras/distribuicoes_estrelas_idade.png)

**Como ler.** Proporção acumulada de repositórios por estrelas (esquerda) e idade (direita), separada entre a amostra aceita e cada etapa de descarte. Deslocamento horizontal indica diferença de distribuição; eixos em escala logarítmica, com o `n` de cada grupo na legenda.

![Distribuição de linguagens entre aceitos e descartados](../analise/saida/caracterizacao/figuras/distribuicao_linguagens.png)

**Como ler.** Cada barra é um grupo do funil e soma 100%, com as oito linguagens mais frequentes entre os aceitos e a categoria "Outras". A inferência correspondente está no parágrafo acima.

Tudo isso se regenera sem acesso à API com `python -m analise.caracterizacao`.

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

Todas as métricas são resumidas por **mediana e IQR** (1º–3º quartil), como pede o enunciado e como a seção 3.10.5 demonstra ser necessário. Os resultados aparecem no escopo pedido (300 repositórios da amostra 1) e na amostra estendida, para mostrar que não dependem do sorteio.

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

**Leitura geral:** ao triplicar a amostra, **todas as medianas ficam praticamente no mesmo lugar**, dentro do intervalo de confiança do escopo de 300. O detalhe está na seção 3.10.1. As figuras se regeneram com `python -m analise`.

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

- **A idade é o fator de maior efeito**, e isso se mantém com a amostra maior (ε² 0,25 → 0,21 no lead time, efeito grande). Repositórios de até 2 anos publicam mais rápido e com mais frequência: lead time mediano de 2 dias contra 28,5 nos mais antigos.
- **Equipes maiores têm lead time maior** (ε² 0,08–0,14, efeito médio).
- **A linguagem só fica significativa com 600.** Com 300 não sobrevivia a Holm; com 600 aparece no lead time (ε² = 0,10), na frequência e no CFR (b). Lead time mediano: TypeScript 7,1 dias, JavaScript 8,9, Python 11,5, Rust 14,1, Go 16,7, Java 22,9, C 35,3, C++ 60,6. É exemplo clássico de **poder estatístico** — o efeito existia, mas 300 repositórios em 6 grupos não bastavam para detectá-lo após a correção.
- **O CFR (a) não se associa a nenhum fator.**

### O efeito se mantém controlando os demais fatores?

![RQ06, robustez](../analise/saida/figuras/fig16_rq06_robustez.png)

Idade, contribuidores, estrelas e linguagem são correlacionados entre si — projetos em C/C++ tendem a ser mais antigos, e projetos antigos tendem a ser maiores. O Kruskal-Wallis univariado não separa esses efeitos, então cada fator foi testado controlando os demais.

A correlação entre os fatores contínuos é moderada (estrelas × contribuidores ρ = 0,59; contribuidores × idade ρ = 0,44; estrelas × idade ρ = 0,07) e o VIF fica entre 1,2 e 1,9, abaixo do corte de 5: a multicolinearidade não impede a separação.

- **Idade** resiste ao controle: ρ parcial = 0,34 no lead time (a), −0,39 na frequência, −0,34 no CFR (b), todas com p ajustado < 0,001. Na regressão log-log é o maior coeficiente padronizado (0,52; IC 95% [0,38; 0,65]).
- **Contribuidores** perde a associação com o lead time ao controlar idade e estrelas: ρ parcial cai para 0,10 (p = 0,17, n.s.). A associação com a frequência se mantém (ρ parcial = 0,21).
- **Estrelas** não tem associação parcial significativa com nenhuma métrica.

**A leitura muda:** parte do efeito de "equipes maiores" que o teste univariado atribuía aos contribuidores é, na verdade, efeito da idade. Repositórios antigos acumulam contribuidores e têm lead time maior por razões que não se reduzem ao tamanho da equipe. É associação, não causalidade — maturidade do processo de release e dívida técnica são explicações não medidas.

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

Os repositórios melhoram ou pioram nas métricas DORA ao longo dos 12 meses da janela?

**Armadilha estatística, resolvida antes do resultado.** O enunciado sugere séries trimestrais com Mann-Kendall. Com 4 pontos, esse teste nunca alcança p < 0,05 — o menor p bilateral possível com n = 4 é ≈ 0,089, qualquer que seja a série. A análise principal usa a **série mensal** (12 pontos), onde o teste tem poder; o recorte trimestral fica como leitura visual na Figura 18.

![RQ08, tendência](../analise/saida/figuras/fig17_rq08_tendencia_600.png)

![RQ08, trajetória](../analise/saida/figuras/fig18_rq08_trajetoria_600.png)

**Como ler.** Mann-Kendall por repositório e métrica, mês a mês, exigindo ao menos 8 dos 12 meses com dado. São 250 a 600 testes por métrica, corrigidos por **Benjamini-Hochberg (FDR)** — com tantos testes simultâneos o Holm fica conservador demais. A Figura 18 traz a mediana mensal entre repositórios, com a faixa Q1–Q3 sombreada.

**Resultado, com 600 repositórios.**

| Métrica | p bruto < 0,05 | Significativo após FDR | Dados insuficientes |
| :--- | :---: | :---: | :---: |
| Frequência | 16,8% | 0% | 0% |
| Lead time (a) | 16,7% | 0% | 50,2% |
| CFR (a) | 13,2% | 0,17% (1 repo, piora) | 19,2% |
| Recuperação | 16,5% | 0% | 59,7% |

O teste bruto "encontra" tendência em 13% a 17% dos repositórios — bem acima dos 5% esperados por acaso, o que sugere oscilação mensal real. **Após o FDR, só 1 dos 600 sobrevive.** É o retrato didático de por que a correção de múltiplos testes importa: a aparência de 1 em cada 6 repositórios mudando vira quase inteiramente ruído quando se testa centenas ao mesmo tempo.

Os "dados insuficientes" altos em lead time e recuperação (50% e 60%) vêm de repositórios que não publicam release nem têm falha em 8 dos 12 meses. Frequência nunca é insuficiente porque zero release no mês é um valor válido, não um dado faltante.

A Figura 18 mostra um salto na mediana de frequência no último mês (≈ 0,23 → ≈ 0,47 release/semana). Nenhum teste sustenta isso como tendência, e o padrão é compatível com viés de seleção: o critério de inclusão favorece repositórios com releases próximas do fim da coleta. Fica como limitação, não como achado.

Para a discussão: **não há melhora nem piora sistemática** ao longo do ano. A conclusão defensável é metodológica — com 12 meses e centenas de repositórios, a correção de múltiplos testes consome quase todo o poder disponível para detectar tendência individual.

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

Cinco refutadas, duas confirmadas. As duas que se confirmaram são as menos informativas: a H02 porque sua segunda metade estava dada na dica do enunciado, e a H04 porque o limiar de 24 h era frouxo. As cinco que caíram são as que carregam o conteúdo deste artigo — e a H05, em particular, caiu de um jeito que obrigou a reinterpretar a própria métrica (seção 3.10.3).

## 4.1 O que confirmou a expectativa

**A entrega é bem mais lenta do que o discurso sobre CI/CD sugere.** A mediana de frequência fica em 0,35 release por semana nos 900 repositórios, ou aproximadamente uma release a cada vinte dias. Projetos open-source populares com GitHub Actions configurado não entregam continuamente; entregam em ciclos. A faixa Elite do DORA, que exige entrega diária ou mais, é ocupada por uma minoria pequena.

**As distribuições são fortemente assimétricas à direita.** Era a expectativa, e os dados a confirmam com folga: nenhuma das cinco métricas passa em teste de normalidade, e a média do lead time chega a ser quase seis vezes a mediana. A exigência do enunciado de reportar mediana e IQR deixou de ser convenção e passou a ser um resultado demonstrado (seção 3.10.5).

**Os dois proxies de CFR discordam.** A taxa de falha medida por CI (5,3%) e a medida por release corretiva (25,0%) diferem por um fator de quase cinco. Elas não medem a mesma coisa — falha de pipeline não é falha em produção — e a divergência confirma que a escolha de proxy domina o resultado da RQ03.

## 4.2 O que surpreendeu

### A classificação DORA discrimina muito pouco

A expectativa era que as faixas Elite/High/Medium/Low separassem repositórios em dimensões reconhecíveis. Elas não separam. Contra popularidade (ε² = 0,008) e número de contribuidores (ε² = 0,022), a classificação não tem poder discriminante algum, e nenhuma das duas sobrevive à correção de Holm.

O que as faixas separam bem são **variantes alternativas das próprias métricas que as definem** — o CFR (b) alcança ε² = 0,379, perto do controle tautológico de 0,403. Isso é validade convergente, não discriminância. A leitura honesta é que a classificação DORA, nesta amostra, é em grande medida uma relabelagem de variáveis contínuas, e não um agrupamento com significado externo.

Esse achado conversa com a superdispersão encontrada na contagem de releases (índice 493×): a população é tão heterogênea em ritmo de entrega que quatro faixas fixas não capturam a estrutura real.

### A heurística de falha reprovou na validação humana

O resultado mais duro do trabalho veio da amostra-ouro. Três pessoas rotularam 300 releases de forma independente, e **nenhuma das quatro versões da heurística de release corretiva alcança o F1 mínimo de 0,70** exigido pelo enunciado. A melhor fica em 0,498; a que gerou o dataset, em 0,478, com precisão de 36,5%.

A expectativa era que a heurística errasse alguma coisa. Não era que errasse dois terços das vezes em que acusa.

Mais revelador ainda é o κ de Fleiss de 0,504 entre os avaliadores humanos, e a prevalência de "sim" variando de 16,7% a 37,3% entre eles. **O problema não é só que a regra automática é ruim: é que o conceito é ambíguo para humanos também.** Uma heurística não pode ser mais precisa que a definição que tenta capturar.

Isso recontextualiza a RQ03 inteira. A divergência entre o CFR (a) e o CFR (b) não é um caso de dois proxies válidos que medem coisas diferentes — é um proxy razoavelmente bem definido (falha de CI) contra um proxy que não sobrevive à validação.

### DORA e fluxo por PR são constructos distintos

A expectativa implícita em boa parte da literatura é que medidas de desempenho convirjam — que um time "rápido" apareça rápido em qualquer lente. Não acontece. O par mais direto, lead time por release contra lead time por PR, compartilha **10% da variância** (ρ = 0,319, n = 574), e o CFR por release contra a taxa de aceitação de PR não tem associação alguma (ρ = 0,044, p = 0,288 após Holm).

A consequência é incômoda: **o DORA não é *a* medida de desempenho de engenharia, é *uma* medida.** Uma lente igualmente legítima — o fluxo por pull request, nos padrões CHAOSS e SPACE — ordena os mesmos repositórios de maneira substancialmente diferente.

### A recuperação não tem taxa constante

A métrica de recuperação é reportada como mediana, o que trata todos os episódios como equivalentes. O ajuste de Weibull mostra que não são: forma mediana β = 0,557, com β < 1 em **87,8%** dos repositórios. Isso é **taxa de recuperação decrescente** — quanto mais tempo um episódio dura, menor a chance de terminar no instante seguinte. Falhas curtas se resolvem rápido; o episódio que se arrasta tende a se arrastar muito mais. Duas populações com o mesmo MTTR mediano podem ter dinâmicas opostas, e a mediana não distingue.

### A regra "n ≥ 30" não vale aqui

Com assimetria populacional de 8,26, a distribuição amostral da média ainda tem assimetria 1,53 em n = 30, e só se aproxima da normal perto de n = 300. A consequência recai sobre a RQ06: os testes por subgrupo operam exatamente onde a aproximação não vale, o que reforça os testes não paramétricos e o relato obrigatório de tamanho de efeito.

## 4.3 O que o tamanho da amostra mudou

Triplicar de 300 para 900 **não alterou nenhuma conclusão qualitativa** das RQ01–RQ05 nem da RQ07: todas as medianas caíram dentro do IC de 300 e os intervalos estreitaram de 21% a 51%. A exceção é a RQ06, onde a linguagem passa a ter efeito significativo — ganho de poder, não mudança de fenômeno.

Houve um resultado na direção oposta: a cobertura da API de Deployments **varia de forma detectável entre as três amostras** (31,3%, 41,7%, 43,3%; p = 0,0048), sem que perfil ou linguagem expliquem. O mesmo desenho que confirma a robustez das métricas DORA detecta a fragilidade de uma medida auxiliar — e é esse contraste que dá credibilidade ao primeiro resultado.

## 4.4 O que o estudo não consegue responder

Duas perguntas ficam estruturalmente fora de alcance pela mesma causa: **todo o processo é medido por proxies do próprio GitHub**, sem desfecho externo de qualidade.

**Previsibilidade.** Não há como verificar se as métricas preveem algo que interesse — incidente em produção, satisfação de usuário, custo de manutenção — porque nenhum desses desfechos existe nos dados.

**Poder discriminante contra qualidade.** Pelo mesmo motivo, só se avalia se as faixas separam atributos observáveis, não se separam alta de baixa qualidade. O resultado negativo da seção 3.10.4 mostra que elas não separam popularidade nem tamanho de equipe — o que é informativo, mas não equivale a dizer que não separam qualidade.

---

# 5. Ameaças à validade

Taxonomia de Cook & Campbell, na adaptação de Wohlin et al. para engenharia de software. Cada ameaça é classificada em **mitigada**, **parcialmente mitigada** ou **aberta**, e apoiada nos resultados da validação manual (seção 2.7) e das análises de validade (seções 3.8 e 3.10).

## 5.1 Validade de construto — *medimos o que achamos que medimos?*

| Ameaça | Situação | Evidência |
| :--- | :--- | :--- |
| **Release não é deploy** | aberta, por construção | O GitHub não registra implantação. A API de Deployments cobre só 38,8% dos 900 repositórios, com cobertura que varia entre amostras (seção 3.10.8). É a limitação mais importante do trabalho. |
| **A heurística de release corretiva não é válida** | **aberta, agora quantificada** | Contra o gabarito humano, nenhuma das quatro versões atinge F1 = 0,70; a que gerou o dataset tem precisão de 36,5% (seção 2.7). |
| **O CFR (b) está acoplado à cadência** | **confirmada e medida** | A suspeita foi testada: ao condicionar pela oportunidade de observação, ρ cai de 0,604 para −0,039 (p = 0,52). O CFR (b) mede, em boa parte, ritmo de publicação (seção 3.10.3). |
| **Falha de CI não é falha em produção** | parcialmente mitigada | Os dois proxies diferem por quase cinco vezes (5,3% × 25,0%). Mitigação: reportar as duas variantes lado a lado, nunca escolher uma. |
| **Mono-método** | parcialmente mitigada | Tudo vem da API do GitHub. Mitigação: medir os mesmos constructos por PRs e issues (CHAOSS, SPACE). Nenhum par alcança ρ = 0,7 (seção 3.10.6). |
| **Ausência de desfecho externo** | aberta | Não há incidente em produção, satisfação de usuário nem custo de manutenção. Impede avaliar previsibilidade e restringe o poder discriminante a atributos observáveis, não a qualidade. |

As duas primeiras linhas mudaram de natureza neste trabalho: eram suspeitas e passaram a ser **resultados medidos**. Isso não as mitiga — ao contrário, confirma que o CFR (b) deve ser lido como indicador de cadência, não de falha.

## 5.2 Validade interna — *há fatores não controlados?*

| Ameaça | Situação | Evidência |
| :--- | :--- | :--- |
| **Tamanho e popularidade como confusão** | **mitigada** | Testada por dois caminhos: estratificação em quartis e correlação parcial de Spearman. O ρ de 0,562 cai no máximo 0,059 na parcial, e os doze estratos mantêm o sinal (0,381–0,698). As faixas também não separam estrelas (ε² = 0,008) nem contribuidores (ε² = 0,022). |
| **Repositórios antigos acumulam releases** | parcialmente mitigada | Idade é o único atributo independente que as faixas separam (ε² = 0,109). As métricas são normalizadas pela janela, o que limita a acumulação, e a idade entra como fator na RQ06. |
| **Heterogeneidade da população** | documentada, não mitigável | Índice de dispersão de 493× em relação à Poisson (seção 3.10.5). Quatro faixas fixas não capturam essa estrutura. |

## 5.3 Validade externa — *vale além da amostra?*

| Ameaça | Situação | Evidência |
| :--- | :--- | :--- |
| **Amostra de repositórios populares** | aberta, por desenho | ≥ 1.000 estrelas, ≥ 5 releases e ≥ 50 runs. **Nada aqui se generaliza para projetos corporativos, pequenos ou sem CI/CD estabelecido.** |
| **Sobrevivência do funil** | documentada | Dos 8.457 candidatos, poucos chegam à amostra; o filtro de releases é o mais severo. Funil e caracterização dos descartados em 2.6 e 3.10.1. |
| **Estabilidade entre amostras** | **mitigada para as métricas DORA** | Três amostras sem repositório em comum produzem estimativas sobrepostas nas seis métricas, com ICs estreitando 21%–51% (seção 3.10.1). |
| **…mas não para medidas auxiliares** | aberta | A cobertura da API de Deployments varia entre amostras de forma detectável (p = 0,0048) e sem causa identificada. |
| **Janela única** | aberta | 12 meses. A RQ08 não encontrou tendência interna, mas outro período pode dar outros valores absolutos. |

## 5.4 Validade de conclusão — *a estatística é adequada?*

| Ameaça | Situação | Evidência |
| :--- | :--- | :--- |
| **Hipóteses reconstruídas, não pré-registradas** | **aberta** | Ver abaixo. |
| **Múltiplas comparações** | mitigada | Holm em todas as famílias de testes; FDR na RQ08, onde apenas 1 de 600 repositórios mantém tendência após a correção. |
| **Pressupostos de normalidade** | mitigada | Nenhuma métrica passa em Shapiro-Wilk (p entre 10⁻¹⁴ e 10⁻³³). Todos os testes são não paramétricos e as estimativas são medianas com IQR. |
| **Poder em subgrupos** | parcialmente mitigada | O TLC só se aproxima perto de n = 300 nesta população (seção 3.10.5), e os subgrupos da RQ06 são menores. Mitigação: testes não paramétricos e relato obrigatório de tamanho de efeito. A linguagem na RQ06, que só fica significativa com 600, ilustra ganho de poder e não mudança de fenômeno. |
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

## 6.2 O lado autor: o que já está pronto para quem for nos replicar

O grupo autor precisa responder às issues recebidas (#145). Independente do sorteio, os pontos abaixo determinam se este pipeline é replicável, e valem ser conferidos antes:

**Dados versionados, sem necessidade de recoleta.** Os três datasets, os eventos por repositório e as medidas GraphQL estão no Git. Quem replicar não precisa gastar cota de API nem as ~15 h de coleta: `data/DICIONARIO.md` documenta cada coluna de cada arquivo.

**O cache não vai para o Git.** O diretório `.cache/` tem vários GB e existe apenas na máquina de quem coletou. Isso significa que **a recoleta a partir do zero não é bit a bit reprodutível** — ela depende do estado corrente da API. Reexecutar sobre os dados versionados é; recoletar não é. É a limitação mais provável de aparecer na replicação, e está declarada.

**Comando único.** `python -m pipeline --config config.yaml` para a coleta e `python -m analise` para figuras e tabelas, com as dependências fixadas em `requirements.txt` e `requirements-analise.txt`.

**Pontos frágeis conhecidos**, que provavelmente gerarão issues:

| Ponto | Por quê |
| :--- | :--- |
| Token do GitHub | o pipeline exige `GITHUB_TOKEN` no ambiente; sem ele, falha de imediato |
| Cota de API | uma recoleta completa consome a cota de 5.000 chamadas/hora por horas seguidas |
| Datas de coleta diferentes | repositórios recebem commits novos; as métricas mudam entre execuções |
| API de Deployments | cobertura instável entre amostras (seção 3.10.8), o que pode produzir divergência legítima |

## 6.3 Link do repositório e do Projects

- Repositório: `https://github.com/henriqjmelo/lab-expe-01`
- GitHub Projects: https://github.com/users/henriqjmelo/projects/2
