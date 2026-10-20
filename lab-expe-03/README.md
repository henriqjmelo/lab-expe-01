# Laboratório 03 — Mineração de Métricas DORA

> **Disciplina:** Laboratório de Experimentação de Software
> **Curso:** Engenharia de Software (6º Período — Noite)
> **Professor:** Danilo Maia
> **Pontuação:** 20 pontos (+1 de bônus pela RQ 08)

---

## Integrantes do Grupo

* Henrique Jardim Melo
* Gabriel Afonso
* Guilherme Costa

---

## Links Importantes

* Repositório: `https://github.com/henriqjmelo/lab-expe-01`
* GitHub Projects (v2): `https://github.com/users/henriqjmelo/projects/1`
* Artigo (template SBC/Overleaf): `<preencher>`

---

## Contexto

As métricas DORA (*DevOps Research and Assessment*), popularizadas pelo livro *Accelerate* (Forsgren, Humble & Kim, 2018), são o padrão de mercado para medir o desempenho de entrega de software:

| Métrica | O que mede | Dimensão |
| :--- | :--- | :--- |
| **Deployment frequency** | Com que frequência a equipe coloca mudanças em produção | Velocidade |
| **Lead time for changes** | Tempo entre o commit e a mudança estar em produção | Velocidade |
| **Change failure rate** | Proporção de deploys que causam falha e exigem intervenção | Estabilidade |
| **Tempo de recuperação** | Tempo para se recuperar de um deploy que falhou (antigo MTTR; *failed deployment recovery time* desde 2023) | Estabilidade |

Em 2024 o DORA acrescentou a *deployment rework rate*, tratada aqui como bônus (RQ 08).

Neste laboratório, o grupo **minera** essas métricas a partir de dados públicos de repositórios open-source reais que usam CI/CD com GitHub Actions.

### O problema central: proxies

O GitHub não registra "deploy em produção" nem "falha em produção". As métricas são **inferidas** por proxies: *release publicada* ≈ deploy; *workflow run com falha* ≈ falha. Por isso, além de calcular as métricas, o grupo:

1. **valida** os critérios automáticos contra julgamento humano (amostra-ouro); e
2. **mede o quanto as conclusões mudam** quando a definição da métrica muda (RQ 07).

A pergunta passa a ser também *"o quanto podemos confiar nesse valor?"*.

**Leitura recomendada:** [DORA — the four keys](https://dora.dev/guides/dora-metrics-four-keys/) · [DORA Quick Check](https://dora.dev/quickcheck/) · [Histórico das métricas](https://dora.dev/insights/dora-metrics-history/)

---

## Definições Operacionais (comuns a toda a turma)

| Item | Regra |
| :--- | :--- |
| **Janela de observação** | 12 meses, datas fixadas pelo professor na abertura da S01. Só entram releases e workflow runs criados dentro da janela. |
| **Branch** | Apenas o *default branch* (`default_branch` da API). |
| **Deploy** | Release publicada (`draft = false`). Pré-releases e tags sem release ficam fora da definição principal — são variantes na RQ 07. |
| **Data do commit** | `commit.author.date` (rebase/squash distorcem — registrar como ameaça). |
| **Execuções de CI** | Só workflow runs do default branch com `event = push`. |
| **Inclusão mínima** | ≥ 5 releases **e** ≥ 50 workflow runs válidos na janela. Descartes vão para o funil. |
| **Censura** | Evento final que não ocorre na janela (ex.: falha não recuperada) é **censurado**, não descartado, e a quantidade é reportada. |

Classificação pelo campo `conclusion` do workflow run:

| `conclusion` | Tratamento |
| :--- | :--- |
| `success` | Sucesso |
| `failure`, `timed_out`, `startup_failure` | Falha |
| `cancelled`, `skipped`, `neutral`, `action_required`, `stale`, vazio | **Ignorar** |

---

## Coleta de Dados

Script **próprio** do grupo via API REST e/ou GraphQL — **não é permitido** usar bibliotecas prontas de acesso à API do GitHub (ex.: PyGithub). Bibliotecas de análise (pandas, SciPy, statsmodels, scikit-learn, pymannkendall) são permitidas.

| Dado | Endpoint (REST) | Cuidado |
| :--- | :--- | :--- |
| Candidatos | `GET /search/repositories?q=stars:>1000` | Máx. 1.000 resultados por consulta — fatiar por faixa de estrelas ou linguagem. |
| Workflows | `GET /repos/{owner}/{repo}/actions/workflows` | `total_count = 0` → descartar antes de gastar chamadas. |
| Releases | `GET /repos/{owner}/{repo}/releases` | Campos `draft`, `prerelease`, `published_at`, `tag_name`. |
| Tags (RQ 07) | `GET /repos/{owner}/{repo}/tags` | Sem data: usar a data do commit apontado. |
| Commits entre releases | `GET /repos/{owner}/{repo}/compare/{base}...{head}` | Sem paginação retorna no máx. 250 commits. |
| Workflow runs | `GET /repos/{owner}/{repo}/actions/runs?branch=…&event=push&created=…` | Máx. 1.000 por consulta — dividir a janela por mês e conferir o teto. |
| Rate limit | `GET /rate_limit` | Não consome cota. |

* **Rate limit:** respeitar `X-RateLimit-Remaining` / `X-RateLimit-Reset`.
* **Paginação:** seguir o cabeçalho `Link` (`rel="next"`) até o fim.
* **Contribuidores:** `GET /contributors?per_page=1&anon=true` e ler a última página no `Link`.

---

## Execução do pipeline

Pré-requisitos: Python 3.12 e um token do GitHub (só leitura de repositórios públicos), exportado como `GITHUB_TOKEN`. O token **nunca** vai para o repositório: `.env` e `lab-expe-03/.cache/` estão no `.gitignore`.

```bash
cd lab-expe-03
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export GITHUB_TOKEN=ghp_...
python -m pipeline --config config.yaml
```

O comando único faz a seleção (busca fatiada por estrelas → tem Actions → ≥ 5 releases → ≥ 50 runs válidos), coleta tudo e grava:

| Arquivo | Conteúdo |
| :--- | :--- |
| `data/dataset_dora.csv` | Uma linha por repositório com todas as métricas e variantes — colunas em [`data/DICIONARIO.md`](data/DICIONARIO.md) |
| `data/funil.csv` | Funil de seleção (etapa, restantes, descartados, motivo) |
| `data/descartes.csv` | Cada repositório descartado e o motivo |
| `data/repositorios.csv` | `owner,repo` da amostra final |

* **Configuração** (`config.yaml`): janela, alvo da amostra (300), semente, faixas de estrelas, critérios de inclusão e caminhos.
* **Cache e retomada:** toda resposta da API fica em `.cache/github/` (JSON + gzip). Depois de `Ctrl+C` ou queda, rode o mesmo comando: o que já foi baixado não é pedido de novo. Com o cache completo, a reexecução reproduz o dataset sem gastar cota.
* **Coleta longa (recomendado):** `nohup scripts/coletar.sh > /dev/null 2>&1 &` e acompanhar com `tail -f .cache/coleta.log`. O script mantém o Mac acordado com `caffeinate` (a tela pode apagar; com a tampa fechada só continua na tomada com monitor externo) e, se o pipeline cair, roda de novo sozinho com espera crescente (1, 2, 4… até 15 min), retomando pelo cache. Use `PYTHON=.venv/bin/python` se o Python do ambiente virtual não estiver ativo.
* **Tolerância a falhas:** cada chamada HTTP tem até 8 tentativas com *backoff* (5xx, queda de rede, resposta cortada). Cada repositório tem mais 3 tentativas (30 s, 60 s, 120 s). Erro transitório que persiste **não descarta** o repositório: a execução para com código 75, grava os CSVs parciais e o supervisor retoma depois. Erro permanente (404, 451, 409) descarta com `erro_api`; erro inesperado repetido descarta com `erro_inesperado` e o *traceback* vai para o log. Os CSVs são regravados a cada 10 repositórios aceitos.
* **Rate limit:** o cliente lê `X-RateLimit-Remaining`/`X-RateLimit-Reset` e dorme até o reset; limite secundário e erros 5xx/rede têm *backoff* exponencial. A coleta completa leva várias horas por causa da cota de 5.000 chamadas/hora.
* **Testes:** `python -m pytest --cov=metricas --cov-report=term-missing` (o CI em `.github/workflows/lab03-testes.yml` exige ≥ 80%).

---

## Questões de Pesquisa

Em todas as RQs, reportar **mediana e IQR** (não média e desvio-padrão).

| RQ | Pergunta | Métrica / Método |
| :--- | :--- | :--- |
| **RQ 01** | Qual a frequência de deploys dos repositórios populares que usam CI/CD? | Releases na janela ÷ semanas (≈ 52,1) |
| **RQ 02** | Qual o tempo entre um commit e seu respectivo deploy? | Lead time — variantes **(a) por release** e **(b) por commit** |
| **RQ 03** | Qual a taxa de falha das mudanças entregues? | CFR — variantes **(a) proxy de CI** e **(b) proxy de entrega** |
| **RQ 04** | Qual o tempo de recuperação após uma execução de CI/CD com falha? | Duração dos episódios de falha por workflow (horas) |
| **RQ 05** | Maior frequência de deploy implica maior ou menor taxa de falha? | Spearman (ρ, p, n) entre RQ 01 e RQ 03 (a) e (b) |
| **RQ 06** | Que características dos repositórios se associam a melhor desempenho DORA? | Kruskal-Wallis / Mann-Whitney + Holm + tamanho de efeito |
| **RQ 07** | O quanto a classificação DORA depende da definição operacional? | % que muda de categoria + kappa de Cohen ponderado |
| **RQ 08** *(bônus)* | Rework rate **ou** evolução temporal | Releases corretivas ÷ total **ou** Mann-Kendall por trimestre |

### RQ 02 — Lead time

Para cada release R, obter os commits via `compare/{release anterior}...{R}` (a anterior pode estar fora da janela; se R for a primeira da história, ignorar).

* **(a) Por release:** `data de R − commit mais antigo de R`; valor do repositório = mediana entre releases.
* **(b) Por commit:** `data de R − data do commit` para cada commit; valor do repositório = mediana de todos os commits.

*Exemplo:* `v1.1` (15/03) com commits de 02/03, 10/03 e 14/03 → (a) 13 dias; (b) contribui com 13, 5 e 1 dias. O artigo deve explicar por que as variantes divergem.

### RQ 03 — Change failure rate

* **(a) Proxy de CI:** `falhas ÷ (falhas + sucessos)`. Mede falha de *pipeline*, não de produção — discutir.
* **(b) Proxy de entrega:** release R falhou se seguida em até **7 dias** por uma **release corretiva**. CFR = `releases que falharam ÷ releases avaliadas`.
  * Heurística de "corretiva" definida pelo grupo (ex.: só muda o *patch* do SemVer e/ou commits com `revert`, `hotfix`, `fix`) e **validada** na amostra-ouro.
  * Releases dos últimos 7 dias da janela ficam fora do denominador (censura).

### RQ 04 — Tempo de recuperação

Ordenar as execuções de **um mesmo workflow**. Um episódio começa na primeira falha após um sucesso e termina no próximo sucesso: `updated_at do sucesso − run_started_at da primeira falha`. Valor do repositório = mediana dos episódios de todos os workflows. Episódios sem fim na janela são censurados — reportar a proporção.

### RQ 05 — Velocidade × estabilidade

Spearman com `scipy.stats.spearmanr`, separadamente para CFR (a) e (b), com gráfico de dispersão (escala log se necessário). Discutir a afirmação do DORA de que velocidade e estabilidade **não** são *trade-off* — correlação não implica causalidade.

### RQ 06 — Fatores associados

1. Escolher **≥ 3 fatores**: linguagem, popularidade (quartis de estrelas), contribuidores (quartis), idade (quartis), tipo do projeto (rotulado na amostra-ouro).
2. Kruskal-Wallis por fator × métrica (Mann-Whitney se 2 grupos).
3. Corrigir p-valores com **Holm** (`multipletests(method='holm')`).
4. Tamanho de efeito: **ε² = H / (n − 1)** (Kruskal-Wallis) ou **Cliff's delta** δ = 2·U₁ / (n₁·n₂) − 1 (|δ| < 0,147 desprezível; < 0,33 pequeno; < 0,474 médio; ≥ 0,474 grande).

### RQ 07 — Análise de sensibilidade

1. Montar **≥ 3 combinações** de definições, por exemplo:

   | Combinação | Unidade de deploy | Lead time | CFR |
   | :--- | :--- | :--- | :--- |
   | C1 (referência) | release | (a) | (a) |
   | C2 | release + pré-release | (b) | (b) |
   | C3 | tag | (b) | (a) |

2. Classificar cada repositório em Elite / High / Medium / Low em cada combinação.
3. Para cada par (C1×C2, C1×C3, C2×C3): % que mudou de categoria e `cohen_kappa_score(..., weights='linear')`.
4. Discutir se as conclusões das RQ 01–06 são robustas.

### Tabela de referência DORA (fixa para a disciplina)

| Métrica | Elite | High | Medium | Low |
| :--- | :--- | :--- | :--- | :--- |
| Deployment frequency | ≥ 7/semana | ≥ 1 e < 7/semana | ≥ 1/mês e < 1/semana | < 1/mês |
| Lead time (mediana) | < 1 dia | 1 dia a < 1 semana | 1 semana a < 30 dias | ≥ 30 dias |
| Change failure rate | ≤ 15% | > 15% e ≤ 30% | > 30% e ≤ 45% | > 45% |
| Tempo de recuperação (mediana) | < 1 hora | 1 hora a < 1 dia | 1 dia a < 1 semana | ≥ 1 semana |

**Classificação geral:** Elite = 4, High = 3, Medium = 2, Low = 1 por métrica; categoria = **mediana dos 4 valores, arredondada para baixo**. Ex.: (4, 3, 3, 1) → 3 → **High**.

### RQ 08 — Bônus (+1 ponto, escolher uma)

* **Rework rate:** releases corretivas (RQ 03 b) ÷ total de releases; discutir a diferença para o CFR (b).
* **Evolução temporal:** métricas por trimestre e teste de Mann-Kendall (`pymannkendall`) por repositório; reportar a proporção com tendência significativa em cada direção.

---

## Validação Manual (Amostra-Ouro) — S02

1. **Sortear 60 repositórios** da amostra final com semente fixa (ex.: `df.sample(n=60, random_state=42)`).
2. **Rotular de forma independente** (sem consultar os demais nem ver a saída da heurística), em planilha própria:
   * (i) tipo do projeto: biblioteca/framework, aplicação/serviço, ferramenta CLI ou outro;
   * (ii) se as releases representam entregas reais ao usuário: sim / não / incerto;
   * (iii) para **5 releases sorteadas** por repositório, se a release é corretiva (sim/não).
3. **Kappa de Fleiss** por dimensão (`aggregate_raters` + `fleiss_kappa`, statsmodels). Interpretação Landis & Koch (1977): 0,41–0,60 moderada; 0,61–0,80 substancial; 0,81–1 quase perfeita.
4. **Consenso** dos casos divergentes, com protocolo de desempate registrado no repositório.
5. **Avaliar a heurística corretiva** contra o consenso: precisão, recall e F1 (`precision_recall_fscore_support`). **F1 < 0,70 → refinar e reavaliar**, documentando cada versão testada.

### Rótulos possíveis

Estes são os **únicos** valores aceitos. Qualquer outro valor quebra o cálculo do kappa.

| Dimensão | Coluna | Valores aceitos |
| :--- | :--- | :--- |
| (i) Tipo do projeto | `tipo_projeto` | `biblioteca_framework` · `aplicacao_servico` · `ferramenta_cli` · `outro` |
| (ii) Releases são entrega real | `releases_reais` | `sim` · `nao` · `incerto` |
| (iii) Release é corretiva | `corretiva` | `sim` · `nao` |

**Como decidir cada uma:**

| Valor | Critério |
| :--- | :--- |
| `biblioteca_framework` | outro código o importa como dependência |
| `aplicacao_servico` | roda como aplicação, serviço, daemon ou desktop |
| `ferramenta_cli` | a interface principal é um comando que uma pessoa digita |
| `outro` | documentação, spec, awesome-list, dataset, material de estudo |
| `releases_reais = sim` | a release é o mecanismo de distribuição: publica em npm/PyPI/crates, anexa binários, tem changelog para o usuário |
| `releases_reais = nao` | as tags são contabilidade interna (bot a cada merge, sem notas) ou o projeto distribui por outro caminho |
| `releases_reais = incerto` | não deu para decidir — **use de verdade**; forçar `sim`/`nao` distorce o kappa |
| `corretiva = sim` | o objetivo **principal** da release é corrigir defeito recente: notas dominadas por fixes, revert, hotfix, correção de regressão ou vulnerabilidade da versão anterior |
| `corretiva = nao` | há feature, API nova ou breaking change de peso; é release periódica de rotina; ou só bump de dependência, docs, CI, chore |

Projeto que é biblioteca **e** CLI (eslint, black, ruff): decida por como a maioria consome. Release com feature relevante + três fixes é `nao`; com dez fixes e um ajuste de texto é `sim`. A palavra que resolve o empate é **principal**.

**Dois cuidados que decidem se a validação vale alguma coisa:**

1. **Não rotule pelo número da versão.** A heurística automática usa exatamente isso (`2.3.0 → 2.3.1`). Rotular por SemVer produz F1 ≈ 1 sem ter medido nada. O enunciado manda ler as *release notes* e a lista de commits.
2. **Não conte prefixos `fix:`.** É o que uma das versões da heurística faz; copiar a regra torna a validação circular. Julgue o propósito da release como um todo.

Pelo mesmo motivo, não abra `validacao/heuristica_versoes.md`, `metricas/corretiva.py` nem a coluna `cfr_b_release` antes de terminar: os três revelam a resposta do script.

### Planilhas

Geradas a partir de `data/dataset_dora.csv` (amostra 1) e `data/eventos/`, com sorteio determinístico (`random_state=42`, e um `random.Random(42)` novo por repositório para as releases). Os três arquivos de rótulo são idênticos antes de preencher: mesmo sorteio, mesmos itens, julgamento independente.

| Arquivo | Linhas | Para quê |
| :--- | :---: | :--- |
| `validacao/amostra_ouro_repos.csv` | 60 | referência do sorteio: url, linguagem, estrelas, descrição, topics |
| `validacao/amostra_ouro_releases.csv` | 300 | referência do sorteio: url, data, nº de commits, mensagens dos commits |
| `validacao/modelo_rotulos_repos.csv` | 60 | molde vazio |
| `validacao/modelo_rotulos_releases.csv` | 300 | molde vazio |
| `validacao/rotulos_<nome>_repos.csv` | 60 | **preencher** `tipo_projeto` e `releases_reais` |
| `validacao/rotulos_<nome>_releases.csv` | 300 | **preencher** `corretiva` |

`<nome>` ∈ {`guilherme`, `henrique`, `gabriel`}. São **360 julgamentos por pessoa**, não divididos entre os três: o kappa compara o que as três pessoas disseram sobre o **mesmo** item.

As mensagens de commit de cada release já vêm na coluna `commits` (até 20, com contagem do excedente), então a maioria das releases se resolve lendo a linha, sem abrir o navegador. **31 releases vêm com `n_commits = 0`** — primeiras releases do histórico ou falhas do `compare` da API — e nessas é preciso abrir o link. A coluna `n_reverts` conta commits que revertem outro (26 releases): sinal forte de corretiva, mas não decisivo sozinho.

---

## Requisitos de Engenharia do Pipeline

Na entrega final, **outro grupo** executa o pipeline seguindo apenas este README.

* **Um único comando** (ex.: `python -m pipeline --config config.yaml`); token lido de `GITHUB_TOKEN`, **nunca** commitado.
* **Cache local e retomada:** cada resposta da API salva em disco (JSON ou SQLite); reexecutar continua de onde parou.
* **Rate limit e erros:** espera automática pela cota; erros 5xx com *backoff* exponencial (1 s, 2 s, 4 s, 8 s…).
* **Testes com pytest** das funções de lead time, CFR, tempo de recuperação e classificação DORA, com *fixtures* e casos de borda (release sem commits novos, falha censurada, repositório com uma release, runs `cancelled`). **Cobertura ≥ 80%** do módulo de métricas (`pytest --cov=metricas --cov-report=term-missing`).
* **CI do grupo** rodando os testes a cada push (`.github/workflows/testes.yml`).
* **Funil de seleção** gerado automaticamente (candidatos → com Actions → critério mínimo → amostra final).
* **Dicionário de dados** de cada coluna dos CSVs: nome, tipo, unidade e fórmula/origem na API.

---

## Relatório Final (Artigo)

Formato de artigo científico no [template SBC (Overleaf)](https://www.overleaf.com/latex/templates/sbc-conferences-template/blbxwjwzdngr), **máx. 10 páginas**, escrito uma seção por sprint (base do artigo do Lab04):

1. **Introdução** com uma hipótese informal por RQ, escrita **antes** de ver os dados;
2. **Metodologia:** fonte de dados, funil, janela, definições operacionais e variantes, protocolo de validação manual;
3. **Resultados por RQ:** mediana, IQR e classificação DORA, em tabelas e gráficos;
4. **Discussão:** hipóteses vs. resultados;
5. **Ameaças à validade** (Wohlin et al.): construto, interna, externa e de conclusão, apoiadas na validação manual e na análise de sensibilidade;
6. **Replicação cruzada**;
7. Link do repositório/GitHub Projects.

---

## Replicação Cruzada (Entrega Final)

O professor sorteia para cada grupo o pipeline de **outro grupo**. O grupo replicador:

1. **Executa** o pipeline usando apenas o README, sobre 30 repositórios do dataset original, sem ajuda do grupo autor;
2. **Compara** com o CSV original: diferença relativa por métrica e % de repositórios com a mesma classificação DORA;
3. **Abre Issues** no repositório do grupo autor com evidências (comando, erro, valores esperados e obtidos);
4. **Registra** o resultado na seção "Replicação cruzada" do próprio artigo.

O grupo autor responde a cada Issue recebida até o prazo final (corrigindo ou justificando) e as adiciona ao próprio GitHub Projects.

---

## Processo de Desenvolvimento

### Contribuição individual por sprint

Em **toda sprint (S01, S02, S03 e entrega final)**, cada integrante deve ser **Assignee de ao menos uma Issue com artefato de código commitado** (script, teste, notebook ou análise), e não apenas de Issues de escrita. A ausência de commits atribuíveis a um integrante em uma sprint **zera a parcela individual** daquele integrante na sprint.

### Sugestão de divisão de papéis por sprint (não obrigatória)

| Sprint | A | B | C |
| :--- | :--- | :--- | :--- |
| **S01** | Seleção de repositórios, funil e metadados (estrelas, linguagem, contribuidores, idade) | Releases/tags, commits entre releases + funções e testes de lead time | Workflow runs (subdivisão mensal), cache/rate limit + funções e testes de CFR (a) e recuperação |
| **S02** | Concordância (Fleiss) e consolidação do consenso | Implementação e refinamento da heurística corretiva (CFR b) | Coleta completa, consolidação do dataset e dicionário de dados |
| **S03** | RQ 01 a 04 e classificação DORA de referência (C1) | RQ 05 e RQ 06 | RQ 07 e, se houver, bônus RQ 08 |
| **Final** | Executa o pipeline do outro grupo e registra problemas | Compara resultados e abre Issues de divergência | Trata as Issues recebidas no próprio pipeline |

Na S02, os três rotulam a amostra-ouro de forma independente, cada um com sua Issue e seu arquivo de rótulos commitado. Na S03, cada análise é um notebook ou script próprio, reexecutável a partir do CSV. Ameaças à validade e revisão final do artigo são feitas pelos três.

---

## Entregáveis e Pontuação

| Sprint | Entregável | Pontos |
| :--- | :--- | :---: |
| **Lab03S01** | Pipeline de coleta para **100 repositórios** (seleção + funil; releases, commits entre releases e workflow runs na janela; cache/retomada e rate limit) + testes unitários com *fixtures* + CI do grupo. Artigo: **introdução com hipóteses**. | 5 |
| **Lab03S02** | Amostra final com **≥ 300 repositórios** após filtros, métricas em todas as variantes, CSV com dicionário de dados, validação manual (60 repositórios, Fleiss, P/R/F1). Artigo: **metodologia**. | 5 |
| **Lab03S03** | Análise das RQ 01 a 07: descritiva + classificação DORA, correlações (RQ 05), testes com tamanho de efeito e Holm (RQ 06), sensibilidade (RQ 07). Artigo: **resultados e discussão**. | 5 |
| **Entrega final** | Replicação cruzada (2) + resposta às Issues recebidas (1) + artigo completo com ameaças à validade e relato da replicação (2). | 5 |
| **Bônus** | RQ 08 | +1 |
| | **Total** | **20 (+1)** |

**Prazo final:** conforme cronograma da disciplina.

---

## Regras de Avaliação do GitHub Projects

* Desconto de **até 10% da nota da sprint** por qualidade insuficiente do uso do GitHub Projects (WIP não respeitado, Issues sem Assignee, cartões desatualizados, ausência de evolução semanal).
* A correção é feita a partir do GitHub Projects: **commits sem referência ao número da Issue correspondente não serão considerados.**
* As Issues recebidas do grupo replicador também devem ser adicionadas ao Project.

---

## Referências

* Forsgren, N.; Humble, J.; Kim, G. *Accelerate: The Science of Lean Software and DevOps*. IT Revolution, 2018.
* DORA. [Relatórios *Accelerate State of DevOps*](https://dora.dev/research/) e [guia das métricas](https://dora.dev/guides/dora-metrics-four-keys/).
* Wohlin, C. et al. *Experimentation in Software Engineering*. Springer, 2012.
* Romano, J. et al. *Appropriate statistics for ordinal level data*. 2006.
* Landis, J. R.; Koch, G. G. *The measurement of observer agreement for categorical data*. Biometrics, 1977.
