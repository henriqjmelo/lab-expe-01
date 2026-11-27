# Ética e reprodutibilidade

## Escopo e limites éticos

O objeto de estudo é a JVM Temurin/OpenJDK em execução, comparando G1 e ZGC sobre workloads locais da suíte DaCapo. O estudo não minera commits, issues, pull requests nem código-fonte de um repositório público como objeto de pesquisa. Também não executa teste de carga em serviços de terceiros, não envia tráfego para serviços externos e não coleta dados pessoais. O serviço Compose usa `network_mode: none` durante os runs; o download do artefato ocorre separadamente, a partir da fonte oficial, antes da execução.

A suíte inclui cargas sintéticas que representam aplicações/workloads. Os resultados não serão descritos como desempenho de uma implantação real específica nem como medição de usuários. A aplicação só será chamada de “latência sensível” quando a definição e a métrica fornecidas por DaCapo sustentarem essa classificação.

## Licenças e artefatos

A distribuição Eclipse Temurin contém binários OpenJDK licenciados sob GPLv2 com Classpath Exception; a documentação da imagem oficial identifica essa licença. A página de metadados do DaCapo 23.11-MR2-Chopin no Zenodo identifica Apache License 2.0. Como o pacote agrega benchmarks e dependências de terceiros, manter também os avisos e licenças incluídos no ZIP, sem assumir que uma licença única substitui as licenças de cada componente. Os arquivos binários grandes não são versionados no Git; os links oficiais, versão, checksum verificado e caminho local devem constar de `env/README.md` e do manifesto da coleta.

## Controles de reprodutibilidade

A imagem base é identificada por tag, digest OCI multiarch e plataforma; a versão do JDK deve ser confirmada com `java -version` dentro do contêiner. A versão exata do DaCapo, o caminho do JAR, as opções de linha de comando, as flags de JVM, os limites de CPU/memória, o heap e o número de iterações devem ser congelados antes da coleta completa. O mesmo serviço Compose executa as duas condições com os mesmos recursos; a única troca deliberada é o coletor e o heap definidos pelo tratamento.

Cada run deve gravar timestamp UTC, host/arquitetura, digest, configuração do tratamento, semente e caminhos dos arquivos brutos/logs. A ordem é randomizada dentro de blocos, e o diário registra interrupções, lacunas, condições da máquina e qualquer desvio. Logs e CSV são validados pelo esquema antes de serem usados. Exclusões seguem somente a regra pré-registrada no plano de análise; valores extremos válidos não são removidos.

## Máquina e limites ainda não confirmados

A máquina examinada em 26/11/2026 é um MacBookAir10,1 ARM64 com macOS 14.8.1, 8 CPUs visíveis e 16 GiB de RAM. Ela tinha cerca de 16 GiB livres no volume do projeto; o ZIP oficial do DaCapo está listado com 6,3 GB antes da extração. O Docker CLI está instalado, mas a conexão ao daemon foi negada por `operation not permitted`. Por isso não foram feitos `pull`, build, testes de JDK, validação de flags, piloto ou coleta. A máquina oficial de coleta ainda não foi aprovada.

A configuração Compose sugere provisoriamente 4 CPUs e 6 GiB de RAM para o contêiner. Esses limites não foram executados nem devem ser tratados como decisão final. O limite de memória precisa comportar o maior `-Xmx` aprovado mais overhead nativo; a VM Docker Desktop precisa, por sua vez, ter memória suficiente para o contêiner e o sistema. Os valores finais, versão do Docker/Desktop, digest efetivamente executado, estado de energia e condição de tomada serão registrados depois que a equipe selecionar a máquina e concluir o preflight.

Como Docker Desktop no macOS executa contêineres Linux sobre uma VM Linux, virtualização, compartilhamento de arquivos e gestão térmica/energia do notebook são ameaças à validade interna e externa. O estudo deve reportar essa plataforma literalmente e não generalizar os resultados para host Linux bare metal sem replicação.

## Situação da execução

**Nenhum dado de piloto ou completo foi coletado nesta versão.** Não criar ou preencher `pilot.csv`, `full.csv`, `clean.csv`, resultados estatísticos ou checksums de dados a partir de valores sintéticos. Dados de teste do pipeline dos demais papéis, quando integrados, devem permanecer rotulados como sintéticos e fora das entregas de coleta.

## Fontes

- Eclipse Adoptium, *Container Images*: https://adoptium.net/installation/containers
- Docker Hub, *eclipse-temurin Official Image*: https://hub.docker.com/_/eclipse-temurin
- DaCapo, *Past Releases*: https://www.dacapobench.org/download
- Zenodo, *DaCapo Benchmarks, version 23.11-MR2-chopin*: https://zenodo.org/records/14717394
- Docker, *Resource constraints*: https://docs.docker.com/engine/containers/resource_constraints/
- Docker, *Change your Docker Desktop settings*: https://docs.docker.com/desktop/settings-and-maintenance/settings/
