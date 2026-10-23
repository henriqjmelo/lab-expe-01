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
