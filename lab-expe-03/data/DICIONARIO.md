# Dicionário de dados — Lab03

Arquivos gerados por `python -m pipeline --config config.yaml` (issue #139). Todas as datas da API estão em UTC. A janela de observação vem de `config.yaml` (`janela.inicio` a `janela.fim`, inclusive). Um evento entra na janela se `inicio 00:00Z <= data < (fim + 1 dia) 00:00Z`.

Células vazias significam "não calculável", e não zero. Exemplos: lead time sem nenhuma release avaliável, CFR sem denominador, recuperação sem episódio fechado.

## `dataset_dora.csv`

Uma linha por repositório da amostra final, ordenada por `owner`/`repo`.

### Metadados (RQ 06)

| Coluna | Tipo | Unidade | Fórmula / origem na API |
| :--- | :--- | :--- | :--- |
| `owner` | texto | — | `GET /search/repositories` → `items[].owner.login` |
| `repo` | texto | — | `items[].name` |
| `estrelas` | inteiro | estrelas | `items[].stargazers_count`, no momento da busca |
| `linguagem` | texto | — | `items[].language` (vazio se o GitHub não detectou) |
| `default_branch` | texto | — | `items[].default_branch` |
| `criado_em` | data-hora ISO 8601 | — | `items[].created_at` |
| `idade_anos` | decimal | anos | `(janela.fim − criado_em) / 365,25` |
| `contribuidores` | inteiro | pessoas | `GET /repos/{o}/{r}/contributors?per_page=1&anon=true` → número da página `rel="last"` do `Link`. Vazio quando a API responde 403 por lista grande demais |

### Métricas por unidade de deploy (RQ 01, 02, 03 b e 07)

As colunas abaixo se repetem para cada unidade `<u>`:

| `<u>` | Unidade de deploy | Origem |
| :--- | :--- | :--- |
| `release` | Release publicada sem pré-release (**definição principal**) | `GET /repos/{o}/{r}/releases`, com `draft = false`, `prerelease = false`; data = `published_at` |
| `release_pre` | Release publicada, incluindo pré-releases (variante RQ 07) | Mesma origem, com `draft = false`; data = `published_at` |
| `tag` | Tag (variante RQ 07) | GraphQL `repository.refs(refPrefix: "refs/tags/")`; data = `authoredDate` do commit apontado (tags anotadas são seguidas até o commit) |

| Coluna | Tipo | Unidade | Fórmula / origem |
| :--- | :--- | :--- | :--- |
| `n_<u>` | inteiro | deploys | Deploys da unidade dentro da janela |
| `df_<u>_semana` | decimal | deploys/semana | **Deployment frequency (RQ 01).** `n_<u> / semanas da janela` (≈ 52,1 para 12 meses) |
| `lt_a_<u>_dias` | decimal | dias | **Lead time (a), por release (RQ 02).** Para cada deploy D na janela: `data(D) − min(commit.author.date)` dos commits de `GET /compare/{anterior}...{D}`. O valor é a mediana entre os deploys |
| `lt_b_<u>_dias` | decimal | dias | **Lead time (b), por commit (RQ 02).** `data(D) − commit.author.date` para cada commit de cada deploy. O valor é a mediana de todos os commits |
| `lt_<u>_n_avaliadas` | inteiro | deploys | Deploys que entraram no lead time (a). Ficam fora: o primeiro da história, compare 404, compare grande demais e deploy sem commit novo |
| `lt_<u>_compare_404` | inteiro | deploys | Deploys ignorados porque o compare respondeu 404 (tag apagada ou reescrita) |
| `lt_<u>_compare_grande` | inteiro | deploys | Deploys ignorados porque o compare tinha mais de 1.000 commits (`total_commits`), ou porque a API respondeu 422 "diff is taking too long to generate". Em geral é comparação entre linhas diferentes, como `v10.x → v11.x` ou pacotes distintos de um monorepo |
| `lt_<u>_omitido` | booleano | — | `True` quando `n_<u>` passou de `coleta.max_compares_por_unidade` (300). Nesse caso o lead time da unidade não foi calculado, para preservar a cota |
| `cfr_b_<u>` | decimal 0–1 | proporção | **CFR (b), proxy de entrega (RQ 03).** `deploys que falharam / deploys avaliados`. D falhou se houve um deploy **corretivo** em até 7 dias depois dele |
| `cfr_b_<u>_n_avaliadas` | inteiro | deploys | Denominador do CFR (b): deploys da janela, menos os dos últimos 7 dias |
| `cfr_b_<u>_n_censuradas` | inteiro | deploys | Deploys dos últimos 7 dias da janela, fora do denominador (censura) |
| `n_corretivas_<u>` | inteiro | deploys | Deploys da janela marcados como corretivos. Numerador da *rework rate* (RQ 08) |

A heurística de "corretiva" na versão atual é a **v0**: a versão SemVer mantém o `maior.menor` do deploy anterior e sobe o `patch`. Tags fora do SemVer nunca são corretivas. A heurística validada na amostra-ouro (issue #138) vai substituir a v0 e deve ser registrada aqui com a versão.

### Métricas dos workflow runs (RQ 03 a e RQ 04)

Origem: `GET /repos/{o}/{r}/actions/runs?branch={default_branch}&event=push&created=AAAA-MM-DD..AAAA-MM-DD`, consultado mês a mês. Um mês com mais de 1.000 resultados é dividido ao meio até caber.

Classificação por `conclusion`:
- **sucesso:** `success`
- **falha:** `failure`, `timed_out`, `startup_failure`
- **ignorado:** os demais, inclusive vazio

| Coluna | Tipo | Unidade | Fórmula / origem |
| :--- | :--- | :--- | :--- |
| `n_runs_validos` | inteiro | runs | `n_runs_sucesso + n_runs_falha` |
| `n_runs_sucesso` | inteiro | runs | Runs com `conclusion = success` |
| `n_runs_falha` | inteiro | runs | Runs com `conclusion` em `failure`, `timed_out`, `startup_failure` |
| `n_runs_ignorados` | inteiro | runs | Demais runs (`cancelled`, `skipped`, `neutral`, `action_required`, `stale`, vazio) |
| `cfr_a` | decimal 0–1 | proporção | **CFR (a), proxy de CI (RQ 03).** `n_runs_falha / n_runs_validos`, com todos os workflows juntos |
| `recuperacao_mediana_horas` | decimal | horas | **Tempo de recuperação (RQ 04).** Os runs são separados por `workflow_id` e ordenados por `run_started_at`. Um episódio vai da 1ª falha depois de um sucesso até o próximo sucesso, com duração `updated_at(sucesso) − run_started_at(1ª falha)`. O valor é a mediana dos episódios fechados de todos os workflows |
| `n_episodios` | inteiro | episódios | Episódios fechados + censurados |
| `n_episodios_censurados` | inteiro | episódios | Episódios sem sucesso até o fim da janela |
| `prop_episodios_censurados` | decimal 0–1 | proporção | `n_episodios_censurados / n_episodios` |
| `meses_no_teto_runs` | inteiro | meses | Meses da janela com mais de 1.000 runs, que precisaram ser subdivididos |
| `dias_truncados_runs` | inteiro | dias | Dias isolados ainda acima de 1.000 runs. Esses dias têm dados incompletos (só os 1.000 devolvidos) |

## `funil.csv`

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `etapa` | texto | `candidatos_busca` → `avaliados` → `com_actions` → `min_5_releases` → `min_50_runs` → `amostra_final` |
| `restantes` | inteiro | Repositórios que seguem depois da etapa |
| `descartados` | inteiro | Repositórios descartados na etapa |
| `motivo` | texto | Critério de descarte. Indica também quantos descartes vieram de erro da API |

## `descartes.csv`

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `full_name` | texto | `owner/repo` |
| `etapa` | texto | Etapa do funil em que saiu |
| `motivo` | texto | `sem_actions`, `menos_de_5_releases`, `menos_de_50_runs_validos`, `erro_api` (erro permanente da API: 404, 451, 409...) ou `erro_inesperado` (dado fora do formato esperado, repetido nas 3 tentativas) |
| `detalhe` | texto | Contagem que reprovou o repositório (releases ou runs válidos na janela), ou a mensagem do erro |

## `repositorios.csv`

Colunas `owner` e `repo` da amostra final. É a entrada de `pipeline/executar_lead_time.py` (#135).

## `candidatos.csv`

Todos os candidatos devolvidos pela busca (`GET /search/repositories`, fatiada por estrelas), comuns às amostras 1 e 2. Gerado por `python -m pipeline.exportar --candidatos data/candidatos.csv`.

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `full_name`, `owner`, `repo` | texto | identificação do repositório |
| `estrelas` | inteiro | `stargazers_count` no momento da busca |
| `linguagem` | texto | `language` (vazio se não detectada) |
| `default_branch` | texto | branch padrão |
| `criado_em` | data-hora ISO 8601 | `created_at` |

A situação de cada candidato numa amostra vem do cruzamento com o `repositorios.csv` (aceito) e o `descartes.csv` (descartado, com a etapa) da amostra. Os demais candidatos não foram avaliados, porque o alvo de 300 foi atingido antes.

## `eventos/` (um diretório por amostra: `data/eventos/` = A1, `data/amostra2/eventos/` = A2, `data/amostra3/eventos/` = A3)

Eventos por repositório da amostra, exportados do cache da coleta por `python -m pipeline.exportar --config <config> --saida <diretório>`. Servem para análises por período (RQ08), heurísticas sobre commits (#138, #154) e qualquer recálculo, sem precisar coletar de novo. Os arquivos `.csv.gz` são lidos direto pelo `pd.read_csv`.

### `releases.csv`

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `owner`, `repo` | texto | repositório |
| `tag_name` | texto | tag da release |
| `published_at` | data-hora ISO 8601 | publicação (releases em rascunho ficam de fora) |
| `prerelease` | booleano | `prerelease` da API |
| `na_janela` | booleano | `published_at` dentro da janela de observação |

Inclui as releases anteriores à janela (servem de "release anterior" no lead time e na heurística corretiva).

### `lead_time_releases.csv`

Uma linha por release (sem pré-release) publicada na janela, com os commits desde a release anterior (`compare`).

| Coluna | Tipo | Unidade | Descrição |
| :--- | :--- | :--- | :--- |
| `owner`, `repo`, `tag_name`, `published_at` | — | — | release |
| `n_commits` | inteiro | commits | commits da release |
| `lt_a_dias` | decimal | dias | `published_at − commit mais antigo` (vazio se ignorada ou sem commits) |
| `lt_b_mediana_dias` | decimal | dias | mediana de `published_at − data de cada commit` |
| `ignorada` | booleano | — | primeira release da história, compare 404 ou com mais de 1.000 commits |

Repositórios com lead time omitido (mais de 300 releases na janela) não aparecem.

### `commits_releases.csv.gz`

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `owner`, `repo`, `tag_name` | texto | release que inclui o commit |
| `sha` | texto | SHA do commit |
| `data` | data-hora ISO 8601 | `commit.author.date` |
| `mensagem` | texto | primeira linha da mensagem (até 300 caracteres) |
| `reverte_sha` | texto | SHA(s) citados em `This reverts commit <sha>` no corpo da mensagem, separados por `;` (vazio se não for revert) |

### `runs.csv.gz`

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `owner`, `repo` | texto | repositório |
| `workflow_id` | inteiro | workflow do GitHub Actions |
| `conclusion` | texto | `conclusion` da API |
| `classe` | texto | `sucesso`, `falha` (`failure`, `timed_out`, `startup_failure`) ou `ignorado` |
| `run_started_at`, `updated_at` | data-hora ISO 8601 | início e última atualização do run |
| `run_attempt` | inteiro | tentativa exibida pela API (a última). `> 1` indica que o run foi reexecutado |
| `head_sha` | texto | commit testado pelo run |

Só os runs de `push` no default branch, criados na janela.

## `medidas_alternativas.csv` (um por amostra: `data/` = A1, `data/amostra2/` = A2, `data/amostra3/` = A3)

Medidas alternativas às do DORA (issue #154), calculadas dos `eventos/` por `python -m analise.alternativas`. Uma linha por repositório da amostra.

| Coluna | Tipo | Unidade | Fórmula / origem |
| :--- | :--- | :--- | :--- |
| `owner`, `repo` | texto | — | repositório |
| `cfr_a` | decimal 0–1 | proporção | CFR (a), igual ao do `dataset_dora.csv` (conferência) |
| `cfr_a_reexec` | decimal 0–1 | proporção | **CFR (a+), limite pessimista.** `(falhas + runs reexecutados que terminaram em sucesso) / runs válidos`. A API devolve só a última tentativa de cada run, então um run que falhou e passou ao ser reexecutado aparece como sucesso no CFR (a) |
| `taxa_reexecucao` | decimal 0–1 | proporção | runs válidos com `run_attempt > 1` / runs válidos |
| `n_reexecutados_sucesso`, `n_reexecutados_falha` | inteiro | runs | runs reexecutados por resultado final |
| `feedback_mediana_min` | decimal | minutos | **Ciclo de feedback do CI** (DevEx): mediana de `updated_at − run_started_at` dos runs válidos |
| `cfr_c_revert` | decimal 0–1 | proporção | **CFR (c), por revert.** Releases que tiveram algum commit revertido (`This reverts commit <sha>`) por um commit de uma release **posterior**, publicada em até 30 dias, dividido pelas releases avaliadas. Releases dos últimos 30 dias da janela ficam fora (censura) |
| `cfr_c_n_avaliadas`, `cfr_c_n_revertidas`, `cfr_c_n_censuradas` | inteiro | releases | componentes do CFR (c) |
| `n_commits_releases` | inteiro | commits | commits das releases da janela |
| `prop_convencional` | decimal 0–1 | proporção | commits cuja primeira linha segue Conventional Commits (`tipo(escopo)!: ...`) ou é `Revert "..."` |
| `adota_convencional` | booleano | — | `prop_convencional >= 0,5` |
| `prop_fix`, `prop_feat` | decimal 0–1 | proporção | `fix` e `feat` entre os commits convencionais |
| `prop_revert` | decimal 0–1 | proporção | commits de revert entre todos os commits |

## `graphql/` (um diretório por amostra: `data/graphql/` = A1, `data/amostra2/graphql/` = A2, `data/amostra3/graphql/` = A3)

Eventos brutos coletados pela API GraphQL (issue #155) por `python -m pipeline.coleta_graphql`. A cota do GraphQL é separada da REST, então esta coleta roda em paralelo com a das amostras. Paginação por cursor, com limite por repositório — quando ele é atingido, a linha correspondente em `resumo.csv` marca o truncamento.

### `prs.csv.gz` — um PR por linha

| Coluna | Tipo | Fórmula / origem |
| :--- | :--- | :--- |
| `owner`, `repo` | texto | repositório |
| `number` | inteiro | número do PR |
| `estado` | texto | `merged`, `closed` ou `open` |
| `created_at` | data-hora ISO 8601 | abertura do PR |
| `merged_at` | data-hora ISO 8601 | merge, vazio se não mergeado |
| `closed_at` | data-hora ISO 8601 | fechamento, vazio se aberto |
| `primeira_resposta_at` | data-hora ISO 8601 | primeira review ou comentário de alguém **que não é o autor**; vazio se ninguém respondeu |

### `issues.csv.gz` — uma issue por linha

| Coluna | Tipo | Fórmula / origem |
| :--- | :--- | :--- |
| `number` | inteiro | número da issue |
| `created_at`, `closed_at` | data-hora ISO 8601 | abertura e fechamento |
| `labels` | texto | labels separadas por vírgula |
| `eh_bug` | booleano | alguma label casa com o padrão de bug (`bug`, `type: bug`, `kind/bug`...) |

### `deployments.csv.gz` — um deployment por linha

| Coluna | Tipo | Fórmula / origem |
| :--- | :--- | :--- |
| `created_at` | data-hora ISO 8601 | criação do deployment |
| `environment` | texto | ambiente declarado (`production`, `preview`, `staging`...) |
| `state` | texto | estado do deployment |
| `status` | texto | último status: `SUCCESS`, `FAILURE`, `ERROR`, `INACTIVE`... |
| `status_at` | data-hora ISO 8601 | momento do último status |

### `resumo.csv` — uma linha por repositório

Contagens brutas (`prs_mergeados`, `prs_fechados`, `issues_fechadas`, `issues_bug`, `deployments`, `deployments_total`) e os três indicadores de truncamento da paginação (`truncado_prs`, `truncado_issues`, `truncado_deployments`).

## `medidas_graphql.csv` (um por amostra: `data/` = A1, `data/amostra2/` = A2, `data/amostra3/` = A3)

Agregação por repositório dos eventos de `graphql/`, gerada por `python -m analise.alternativas`. Medidas de fluxo e colaboração nos padrões CHAOSS, Flow Framework e SPACE — independentes de releases e do CI.

| Coluna | Tipo | Unidade | Fórmula / origem |
| :--- | :--- | :--- | :--- |
| `owner`, `repo` | texto | — | repositório |
| `n_prs_mergeados` | inteiro | PRs | PRs mergeados na janela |
| `prs_mergeados_semana` | decimal | PRs/semana | `n_prs_mergeados ÷ semanas da janela` (≈ 52,1) |
| `lt_pr_mediana_horas` | decimal | horas | **Lead time por PR** (CHAOSS): mediana de `merged_at − created_at` |
| `primeira_resposta_mediana_horas` | decimal | horas | **Tempo até a primeira resposta** (CHAOSS): mediana de `primeira_resposta_at − created_at` |
| `prop_prs_sem_resposta` | decimal 0–1 | proporção | PRs sem nenhuma resposta de terceiro |
| `taxa_aceitacao_pr` | decimal 0–1 | proporção | `mergeados ÷ (mergeados + fechados sem merge)` |
| `n_bugs_fechados` | inteiro | issues | issues com label de bug fechadas na janela |
| `resolucao_bug_mediana_horas` | decimal | horas | **Recuperação por issue de bug**: mediana de `closed_at − created_at` |
| `n_deploys_producao` | inteiro | deployments | deployments em ambiente de produção |
| `usa_deployments` | booleano | — | o repositório usa a API de Deployments de forma utilizável |
| `df_deploy_semana` | decimal | deploys/semana | **Deployment frequency "pura"**, pela API de Deployments |
| `cfr_d_deploy` | decimal 0–1 | proporção | **CFR (d)**: deployments com status de falha ÷ deployments avaliados |
| `recuperacao_deploy_mediana_horas` | decimal | horas | mediana do tempo entre um deployment com falha e o próximo bem-sucedido |
| `truncado_prs`, `truncado_issues`, `truncado_deployments` | booleano | — | a paginação atingiu o limite para aquele tipo de evento; a medida correspondente é um limite inferior |

**Cobertura, medida nos 900:** lead time por PR 98,3%, primeira resposta 98,8%, taxa de aceitação 99,6%, resolução de bug 80,4% e **Deployments API 38,8%**. As quatro primeiras sustentam-se como medidas principais; a última entra como **subamostra de validação**, e sua cobertura varia de forma detectável entre as amostras (31,3%, 41,7% e 43,3%; qui-quadrado p = 0,0048). Ver `docs/base-teorica.md`, seção 7.1.1.
