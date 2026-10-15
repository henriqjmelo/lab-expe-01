# 2. Metodologia

> Rascunho da issue #139, a ser revisado por Henrique e Gabriel antes de ir para o Overleaf. Os números da coleta são os do `data/` desta versão. Os trechos marcados com **[PENDENTE]** dependem das issues #137 (kappa) e #138 (F1 da heurística) ou das datas da janela.

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

    | Versão | Mediana do CFR (b) | IQR | Releases marcadas corretivas |
    | :--- | :---: | :---: | :---: |
    | v0 (semver) | 25,0% | 5,2% – 56,5% | 8.186 |
    | v1 (mensagens) | 0,0% | 0,0% – 12,6% | 1.479 |
    | v2 (patch + poucos commits) | 2,4% | 0,0% – 21,6% | 1.903 |
    | v3 (combinada) | 25,0% | 6,0% – 57,2% | 8.597 |

    A v0 sozinha já marca um quarto das releases como corretivas, bem acima do CFR (a) (mediana 2,6%, seção 3.1); a v1, baseada só na mensagem do commit, é bem mais conservadora. **[PENDENTE: escolher a versão final (#138) a partir da precisão, recall e F1 contra a amostra-ouro, quando o consenso da #137 existir, e atualizar esta tabela e o dataset.]**
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

A amostra final tem **300 repositórios** em 27 linguagens. As mais frequentes são TypeScript (61), Python (55), Go (49), Rust (28), C++ (20) e JavaScript (19). A idade mediana é de 5,8 anos (IQR 2,0–10,9), e o número mediano de contribuidores é 142 (IQR 49–337). A coleta somou 17.217 releases, 28.792 tags e 833.582 workflow runs válidos na janela. A Tabela 2 resume a qualidade da coleta.

**Tabela 2 — Contagens de qualidade da coleta.**

| Ocorrência | Quantidade |
| :--- | :--- |
| Repositórios com algum mês acima de 1.000 runs (subdividido) | 34 |
| Dias ainda acima de 1.000 runs após a subdivisão (dados incompletos) | 19 dias em 4 repositórios |
| Releases ignoradas no lead time por *compare* 404 | 8 |
| Releases ignoradas no lead time por *compare* com mais de 1.000 commits ou que a API não conseguiu gerar (422) | 244 |
| Repositórios com lead time de release omitido (mais de 300 releases na janela) | 7 |
| Episódios de falha de CI censurados (sem recuperação até o fim da janela) | 139 de 20.077, em 74 repositórios |

## 2.7 Validação manual (amostra-ouro)

1. **Sorteio.** Foram sorteados 60 repositórios da amostra final com semente fixa. **[PENDENTE: semente e lista (#137).]**
2. **Rotulagem independente.** Cada integrante rotulou sozinho, sem consultar os demais nem ver a saída da heurística, três dimensões:
   - (i) tipo do projeto (biblioteca/framework, aplicação/serviço, ferramenta CLI ou outro);
   - (ii) se as releases representam entregas reais ao usuário (sim/não/incerto);
   - (iii) para 5 releases sorteadas por repositório, se a release é corretiva.
3. **Concordância.** Foi medida pelo kappa de Fleiss por dimensão e interpretada segundo Landis e Koch (1977). **[PENDENTE: valores de κ (#137).]**
4. **Consenso.** As divergências foram resolvidas por consenso, seguindo o protocolo de desempate registrado no repositório.
5. **Avaliação da heurística.** A heurística de release corretiva foi avaliada contra o consenso por precisão, recall e F1. Com F1 < 0,70, ela foi refinada e reavaliada, e cada versão foi documentada. **[PENDENTE: P/R/F1 por versão (#138).]**
