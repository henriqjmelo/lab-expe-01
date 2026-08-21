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

## 3. Configuracao do processo

O trabalho foi organizado em issues independentes, com uma branch por entrega e commits iniciados pelo numero da issue. O fluxo adotado foi:

`Backlog -> To Do -> Doing -> In Review -> Done`

Cada issue deve ser vinculada ao GitHub Projects v2. Ao iniciar uma tarefa, seu card deve ser movido para `Doing`; apos a revisao e o merge, deve ser movido para `Done`. O projeto utilizado e o projeto de usuario numero 1 de `henriqjmelo`.

As consultas do GitHub usam exclusivamente `requests` e GraphQL manual. Nao foram utilizadas bibliotecas de terceiros para a API do GitHub. O token e carregado por `GITHUB_TOKEN` a partir do ambiente ou de `.env`, que permanece fora do controle de versao.

## 4. Limites da analise

O ranking e dinamico e pode mudar durante a coleta. Campos nulos, especialmente `primaryLanguage`, podem refletir repositorios sem linguagem dominante definida pelo GitHub. Outliers nao sao erros automaticamente: projetos muito grandes podem legitimamente concentrar contribuicoes ou issues. Por fim, a razao de issues fechadas nao mede tempo de resolucao nem qualidade da manutencao.
