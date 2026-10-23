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
