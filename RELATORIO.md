# Relatorio: caracteristicas de repositorios populares

## 1. Introducao e hipoteses

Este estudo analisa um conjunto de 990 repositorios publicos com maior numero de estrelas no GitHub. O objetivo e observar sinais de maturidade, atividade de contribuicao, frequencia de atualizacao, linguagens predominantes e tratamento de issues.

As hipoteses informais usadas para orientar a analise foram:

- **Issue #10 (RQ01/RQ02):** repositorios mais antigos tendem a acumular mais pull requests aceitos, pois tiveram mais tempo para receber contribuicoes externas.
- **Issue #11 (RQ03/RQ04):** repositorios populares permanecem ativos, com atualizacoes recentes, mas a frequencia de releases pode variar conforme o tipo de projeto e seu processo de versionamento.
- **Issue #12 (RQ05/RQ06):** as linguagens primarias mais frequentes devem acompanhar linguagens populares no ecossistema, e repositorios populares devem apresentar uma proporcao elevada de issues fechadas.

As hipoteses sao direcionadoras e nao implicam causalidade. A popularidade foi operacionalizada pelo numero de estrelas, e o recorte observado representa o estado do dataset coletado, nao uma amostra aleatoria de todos os projetos do GitHub.

## 2. Metodologia de coleta

Os dados foram coletados por meio da API GraphQL oficial do GitHub, usando `requests` e consultas GraphQL manuais. A consulta unificada busca repositorios por `stars:>1 sort:stars-desc` e pagina os resultados ate formar o conjunto analisado.

Para cada repositorio foram coletados:

- `nameWithOwner` e `stargazerCount`;
- `createdAt` e `pushedAt`;
- pull requests com estado `MERGED`;
- total de releases publicadas;
- `primaryLanguage`;
- issues fechadas e total de issues.

O resultado foi armazenado em `data/repositorios.csv`. As validacoes usam somente a biblioteca padrao do Python: verificam valores nulos, limites e inconsistencias basicas. Outliers numericos sao identificados pelo limite superior do intervalo interquartil (IQR), calculado como `Q3 + 1,5 * IQR`. Datas sao convertidas para objetos com fuso UTC antes da verificacao.

A validacao do dataset encontrou 990 repositorios, sem nulos em `createdAt` e `pullRequests`. Foram identificados 123 outliers em pull requests aceitos. Em RQ05, 85 repositorios nao possuem linguagem primaria informada. Em RQ06, a mediana da razao de issues fechadas foi 0,8751; 42 repositorios possuem zero issues totais, e nenhum apresentou mais issues fechadas que issues totais.

## 3. Resultados e discussao por RQ

A analise usa como data de referencia o `pushedAt` mais recente do dataset, 21/08/2026, que corresponde ao momento da coleta. Usar a data corrente faria os valores de idade e de tempo sem atualizacao mudarem a cada execucao do script.

### RQ01 — Sistemas populares sao maduros/antigos?

Metrica: idade do repositorio em anos, a partir de `createdAt`.

| Estatistica | Valor |
| :--- | ---: |
| Mediana | 7,7 anos |
| Media | 7,6 anos |
| Minimo | 0,0 ano |
| Maximo | 18,4 anos |
| Q1 | 3,5 anos |
| Q3 | 11,3 anos |

Distribuicao por faixa:

| Faixa | Repositorios | Percentual |
| :--- | ---: | ---: |
| Menos de 5 anos | 322 | 32,5% |
| De 5 a 10 anos | 328 | 33,1% |
| De 10 a 15 anos | 291 | 29,4% |
| 15 anos ou mais | 49 | 4,9% |

Grafico: `graficos/rq01_idade.png`.

**Discussao.** A mediana de 7,7 anos indica que os repositorios mais populares tendem a ser projetos ja estabelecidos, e nao lancamentos recentes. Cerca de dois tercos da amostra tem 5 anos ou mais. Ainda assim, a resposta nao e absoluta: um terco dos repositorios tem menos de 5 anos, o que mostra que ganhar volume de estrelas nao depende necessariamente de muito tempo de existencia. O maximo de 18,4 anos e coerente com o limite da propria plataforma, que foi lancada em 2008.

### RQ02 — Sistemas populares recebem muita contribuicao externa?

Metrica: total de pull requests aceitas, no estado `MERGED`.

| Estatistica | Valor |
| :--- | ---: |
| Mediana | 768 |
| Media | 4.259 |
| Minimo | 0 |
| Maximo | 103.403 |
| Q1 | 175 |
| Q3 | 3.426 |

Vinte repositorios nao possuem nenhuma pull request aceita.

Grafico: `graficos/rq02_pull_requests.png`. O histograma usa intervalos e eixo horizontal em escala logaritmica, porque a distribuicao vai de zero a mais de cem mil e, em escala linear, quase toda a amostra se concentraria na primeira barra. Os vinte repositorios sem nenhuma PR aceita ficam fora do grafico, ja que nao ha logaritmo de zero, mas continuam contabilizados na tabela.

**Discussao.** A distancia entre mediana e media, 768 contra 4.259, mostra que a contribuicao externa e bastante concentrada: um grupo pequeno de projetos acumula um volume muito alto de PRs aceitas e puxa a media para cima, enquanto metade da amostra fica abaixo de 768. A resposta a RQ depende de onde se olha. Em termos medianos, o volume de contribuicao e expressivo, mas dizer que sistemas populares em geral recebem muita contribuicao externa esconde a assimetria da distribuicao.

### RQ01 e RQ02 — hipotese versus resultado

A hipotese informal registrada na issue #10 dizia que repositorios mais antigos tendem a acumular mais pull requests aceitas, por terem tido mais tempo de receber contribuicoes externas. Cruzando as duas metricas por faixa de idade:

| Faixa de idade | Repositorios | Mediana de PRs aceitas |
| :--- | ---: | ---: |
| Menos de 5 anos | 322 | 453 |
| De 5 a 10 anos | 328 | 778 |
| De 10 a 15 anos | 291 | 1.067 |
| 15 anos ou mais | 49 | 1.740 |

O resultado acompanha a hipotese: a mediana de PRs aceitas cresce em todas as faixas conforme a idade aumenta, sem excecao. Cabem duas ressalvas. A primeira e que o crescimento nao e proporcional ao tempo: entre a faixa mais nova e a mais antiga a idade se multiplica bem mais do que as 3,8 vezes observadas na mediana de PRs, o que sugere que o tempo explica parte do fenomeno, mas nao ele todo. A segunda e que o cruzamento mostra associacao, nao causa. Fatores como o tipo de projeto, o tamanho da comunidade e a politica de contribuicao de cada repositorio nao foram controlados e podem estar por tras do mesmo padrao.

## 4. Configuracao do processo

O trabalho foi organizado em issues independentes, com uma branch por entrega e commits iniciados pelo numero da issue. O fluxo adotado foi:

`Backlog -> To Do -> Doing -> In Review -> Done`

Cada issue deve ser vinculada ao GitHub Projects v2. Ao iniciar uma tarefa, seu card deve ser movido para `Doing`; apos a revisao e o merge, deve ser movido para `Done`. O projeto utilizado e o projeto de usuario numero 1 de `henriqjmelo`.

As consultas do GitHub usam exclusivamente `requests` e GraphQL manual. Nao foram utilizadas bibliotecas de terceiros para a API do GitHub. O token e carregado por `GITHUB_TOKEN` a partir do ambiente ou de `.env`, que permanece fora do controle de versao.

## 5. Limites da analise

A contagem de releases (RQ03) e truncada pela propria API do GitHub, que nao retorna valores acima de 1000 em `releases.totalCount`. No dataset, 23 dos 990 repositorios (2,3%) aparecem com exatamente 1000 releases, o que significa que o total real deles e maior — nao foi possivel saber quanto. A verificacao foi feita consultando `repository(...)` diretamente, fora da busca paginada: `vercel/next.js`, `electron/electron` e `home-assistant/core` retornam exatamente 1000, enquanto `facebook/react` retorna 132, um valor real abaixo do teto. A mediana de RQ03 nao e afetada, ja que a maior parte da distribuicao esta longe do limite, mas o valor maximo e a analise de extremos ficam subestimados. Esse truncamento tambem tende a enviesar a RQ07 na comparacao de releases por linguagem, porque os projetos que batem no teto se concentram no ecossistema JavaScript/TypeScript.

A coleta reuniu 990 repositorios em vez dos 1000 previstos pelo enunciado. A diferenca vem do proprio ranking mudando durante os minutos que a paginacao leva pra terminar: como a busca e ordenada por estrelas em tempo real, repositorios podem entrar ou sair das primeiras posicoes entre uma pagina e outra. O numero se repetiu (990) em duas coletas separadas, o que sugere um limite proprio da API pra essa consulta, nao uma falha aleatoria.

O ranking e dinamico e pode mudar durante a coleta. Campos nulos, especialmente `primaryLanguage`, podem refletir repositorios sem linguagem dominante definida pelo GitHub. Outliers nao sao erros automaticamente: projetos muito grandes podem legitimamente concentrar contribuicoes ou issues. Por fim, a razao de issues fechadas nao mede tempo de resolucao nem qualidade da manutencao.
