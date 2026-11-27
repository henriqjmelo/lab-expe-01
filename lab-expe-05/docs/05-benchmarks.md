# Benchmarks e heaps: seleção provisória

## Candidatos

A proposta para o piloto é usar `cassandra` e `spring` nas duas células de latência. DaCapo descreve Cassandra como carga orientada a requisições e Spring como fluxo de requisições sobre uma aplicação autocontida. O segundo caso não representa um serviço Spring distribuído em produção: é um workload de benchmark. O paper do DaCapo também apresenta `jme` como carga de latência, mas sua unidade é evento de frame, não requisição; por isso fica como reserva, não substitui os candidatos sem uma decisão explícita. [1]

Para as duas cargas de lote, a proposta é `biojava` e `pmd`: ambas executam trabalho finito, sem p99 nativo no protocolo da suíte. A classificação “vazão” é operacional e ainda precisa de uma unidade de trabalho fixa para interpretar vazão; até lá, a métrica confirmatória é apenas o tempo da iteração (`exec_ms`), e não se deve converter automaticamente `1/exec_ms` em operações por segundo. `h2o` fica como reserva de lote/ML, condicionado à memória e à compatibilidade com o JDK. [1] [4]

Esta escolha é documental, não experimental. A versão consultada é DaCapo 23.11-MR2-Chopin, cuja distribuição oficial é grande; nenhum JAR foi baixado e nenhum benchmark foi executado nesta máquina. A adequação dos quatro candidatos a Temurin 25 em ARM64 continua sem confirmação. [2] [3] [4]

## Heap

O paper registra referências históricas de heap mínimo para outra plataforma/configuração: Cassandra 174 MB, Spring 55 MB, BioJava 93 MB e PMD 191 MB. Esses valores aparecem em `env/benchmarks.json` como `reference_min_heap_mb`; não são os mínimos medidos no alvo do estudo e não devem ser usados como se fossem. Os campos `min_heap_mb` permanecem `null` de propósito. [1]

A proposta inicial para os dois níveis é `2×M` e `4×M`, em que `M` será o menor heap em MiB que passa a validação DaCapo no ambiente-alvo, com `-Xms=-Xmx`. A escolha dos multiplicadores e de cada `M` deve ser congelada após o piloto e registrada no contrato antes da coleta completa. Caso algum candidato precise de override de heap, flag ou propriedade específica, isso deve ser registrado e avaliado como possível ameaça à comparação.

## Métrica de latência e iterações

Para `lat_p99_ms`, a proposta é extrair o p99 da linha `simple` do DaCapo, convertendo microssegundos para milissegundos; as saídas `metered 100ms smoothing` e `metered full smoothing` ficam preservadas como diagnósticos separados e não podem ser misturadas com a coluna confirmatória. O contrato atual não distingue as variantes, então esta definição precisa ser confirmada pelo grupo antes do piloto. [5]

O comando candidato fixa `-n 5` e `-s default`: pelo harness MR2, são quatro aquecimentos seguidos de uma iteração cronometrada, cuja linha `PASSED in ... msec` fornece `exec_ms`. Essa configuração ainda depende de smoke test em cada workload e coletor no JDK 25/ARM64. [6]

## Portas antes da coleta

Antes de aceitar a seleção, é necessário localizar o JAR exato e guardar o checksum oficial; preencher `min_heap_mb` após sondagem reproduzível; validar os quatro workloads com G1 e ZGC em ambos os heaps; confirmar p99 em Cassandra e Spring; conferir o log de GC e ausência de OOM; e registrar as opções, os limites e os artefatos. Se qualquer carga falhar, a coleta completa não começa até o grupo rever a seleção ou o protocolo.

**Estado:** seis nomes avaliados; quatro candidatos e duas reservas propostos; mínimos de heap do alvo, compatibilidade JDK25/ARM64 e ausência de OOM não demonstrados. Não há resultados ou CSV de piloto.

## Referências

[1]: https://www.dacapobench.org/assets/pdf/dacapo-asplos-2025-with-appendix.pdf "The DaCapo Benchmarks for Java"
[2]: https://www.dacapobench.org/download "DaCapo past releases"
[3]: https://github.com/dacapobench/dacapobench/releases/tag/v23.11-MR2-chopin "DaCapo v23.11-MR2-Chopin release"
[4]: https://github.com/dacapobench/dacapobench/blob/v23.11-MR2-chopin/benchmarks/RELEASE_NOTES.md "DaCapo MR2 release notes"
[5]: https://raw.githubusercontent.com/dacapobench/dacapobench/v23.11-MR2-chopin/benchmarks/harness/src/org/dacapo/harness/LatencyReporter.java "DaCapo MR2 latency reporter"
[6]: https://raw.githubusercontent.com/dacapobench/dacapobench/v23.11-MR2-chopin/benchmarks/harness/src/org/dacapo/harness/Callback.java "DaCapo MR2 iteration callback"
