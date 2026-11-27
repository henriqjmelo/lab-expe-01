# Método, ambiente e coleta — rascunho

## Pergunta e escopo

O estudo compara G1 e ZGC geracional no Temurin JDK 25 quanto ao tempo da iteração, latência de cauda e uso de recursos, em cargas da suíte DaCapo. O objeto é a JVM executada no contêiner. O grupo não minera commits, issues, pull requests ou código-fonte de um repositório como objeto de pesquisa, nem envia carga a serviços de terceiros.

## Ambiente

A configuração candidata usa Docker Desktop em Mac Apple Silicon, com um contêiner Linux, Temurin JDK 25 e limites provisórios de 4 CPUs e 6 GiB. A imagem base é identificada por digest e a plataforma planejada é `linux/arm64/v8`. O contêiner terá rede desativada durante o benchmark. A versão DaCapo proposta é 23.11-MR2-Chopin, obtida da distribuição oficial. [1] [2]

O pacote listado pela página de download tem 6,3 GB antes da extração. Antes de baixar, é necessário confirmar espaço para o ZIP, os arquivos extraídos, a imagem e os logs. A comparação de flags `PrintFlagsFinal`, a versão exata de `java -version` e o digest resolvido no runtime serão anexados após o preflight, ainda não executado. [1] [3]

## Desenho

O desenho candidato contém dois coletores, dois níveis de heap e quatro benchmarks, totalizando 16 células. Cada bloco contém uma execução por célula, em ordem aleatória por semente registrada. O piloto tem cinco blocos (80 invocações); N = 30 permanece provisório para a coleta completa (480 invocações). As execuções completas não começam antes da aprovação dos benchmarks, dos heaps, da compatibilidade e do preflight.

Os benchmarks propostos são Cassandra e Spring para latência e BioJava e PMD para cargas finitas de lote. JME e H2O são reservas. A seleção e os mínimos de heap ainda não foram confirmados no alvo; os valores de referência publicados não substituem uma sondagem local. A descrição e os gates estão em [05-benchmarks.md](05-benchmarks.md). [4]

## Medições

Uma unidade experimental é uma invocação nova da JVM. A configuração candidata usa `-n 5` e mede a quinta iteração, após quatro aquecimentos do harness. O tempo sai da linha `PASSED in ... msec`. Para Cassandra e Spring, a proposta para `lat_p99_ms` é o p99 `simple` reportado em microssegundos, convertido para milissegundos; relatórios metered são preservados como diagnóstico separado. Essa definição precisa de confirmação do grupo antes da coleta. [5] [6]

O log `-Xlog:gc*` fornece as pausas e a confirmação do coletor. CPU user+sys e pico de RSS são capturados do processo Java no contêiner. Runs com OOM, falha de validação ou erro de contêiner permanecem registrados com motivo; nenhuma falha será silenciosamente descartada.

## Reprodutibilidade e situação

Os dados seguem `docs/00-contrato.md`. A coleta pretendida é retomável por `run_id`; cada bloco concluído será validado e a limpeza não removerá falhas nem valores extremos válidos. O manifesto da versão final deverá registrar comandos, versões, digest, checksums, parâmetros, logs e hash dos dados. A tag `data-v1` só será criada depois de dados reais completos e validados.

**Resultados:** ainda indisponíveis. Nenhum piloto ou coleta completa foi executado. O processo não conseguiu acessar o daemon Docker (`operation not permitted`), o pacote não foi baixado e não existe `pilot.csv`, `full.csv` ou `clean.csv` real. Os valores do Compose e a seleção de workloads permanecem provisórios.

## Referências

[1]: https://www.dacapobench.org/download "DaCapo past releases"
[2]: https://github.com/dacapobench/dacapobench/releases/tag/v23.11-MR2-chopin "DaCapo v23.11-MR2-Chopin release"
[3]: https://hub.docker.com/_/eclipse-temurin "Eclipse Temurin Official Image"
[4]: https://www.dacapobench.org/assets/pdf/dacapo-asplos-2025-with-appendix.pdf "The DaCapo Benchmarks for Java"
[5]: https://raw.githubusercontent.com/dacapobench/dacapobench/v23.11-MR2-chopin/benchmarks/harness/src/org/dacapo/harness/Callback.java "DaCapo MR2 iteration callback"
[6]: https://raw.githubusercontent.com/dacapobench/dacapobench/v23.11-MR2-chopin/benchmarks/harness/src/org/dacapo/harness/LatencyReporter.java "DaCapo MR2 latency reporter"
