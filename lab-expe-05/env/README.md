# Ambiente de coleta — Lab05

## Estado desta versão

O ambiente está descrito, mas ainda **não foi validado por execução em Docker**. O Docker CLI está instalado no Mac usado nesta tarefa, porém o processo não conseguiu acessar o socket do Docker Desktop (`operation not permitted`). Nenhum `docker pull`, build, benchmark ou coleta foi iniciado.

A máquina observada é um MacBookAir10,1 com Apple Silicon (`arm64`), macOS 14.8.1, 8 CPUs visíveis e 16 GiB de RAM. Uma checagem anterior registrou cerca de 16 GiB livres; uma nova checagem em 27/11/2026 com `df -h` registrou 15 GiB livres no volume. Esse Mac é candidato, mas ainda não foi confirmado como máquina oficial: faltam acesso ao daemon, a alocação atual de recursos da VM Linux e a capacidade pós-extração. O pacote oficial DaCapo 23.11-MR2-Chopin está listado como um ZIP de 6,3 GB antes da extração; não foi baixado e a listagem do tamanho expandido ainda precisa ser verificada.

Os padrões do Compose são **provisórios**: 4 CPUs e 6 GiB para o contêiner. Eles mantêm as duas condições iguais e cabem, em princípio, numa VM Docker Desktop com pelo menos 6 GiB disponíveis, mas não foram testados. Antes de iniciar o piloto, verificar que a memória da VM excede o limite do contêiner e que o limite do contêiner excede o heap máximo mais o overhead nativo da JVM. Se algum benchmark não couber, rever os limites e registrá-los no contrato antes da coleta completa.

## Imagem base

O Dockerfile usa a imagem oficial `eclipse-temurin:25-jdk-noble` fixada ao índice OCI multiarch `sha256:4ddc1a8bdaf283421df5487411aff10b797ccf1e06a339041005114c8f489b5c`. Para `linux/arm64/v8`, o Docker Hub listava o manifesto filho `sha256:085011b2dc37370a0bf7b5770b8f222271b6cd0cbe198bad5868583660ef14cb`. A Adoptium reportou Temurin `25.0.5.1+2-LTS` para Linux ARM64, build publicado em 20/11/2026. Pinagem consultada em 26/11/2026; confirmar no runtime com `java -version` e gravar o digest resolvido antes de qualquer run.

## Preparação

1. Abra o Docker Desktop e confirme a alocação de CPU, memória e disco da VM Linux. A documentação do Docker Desktop informa que, no macOS, o limite de memória é alocado à VM. Registre também a versão do Docker Engine/Desktop e a implementação de virtualização.
2. Confirme o espaço disponível antes de obter o ZIP oficial DaCapo. O tamanho publicado é 6,3 GB; verifique o tamanho extraído com a listagem do ZIP e reserve espaço adicional para imagem, logs e CSV. Não faça o download se a extração e a reserva não couberem.
3. Obtenha a versão `23.11-MR2-chopin` na página oficial de downloads, confira o SHA-256 oficial e extraia-a em `env/artifacts/`. O diretório é local e ignorado pelo Git. Identifique o `.jar` exato dentro do arquivo; ainda não se presume o nome/caminho interno do JAR.
4. Fixe antes do piloto o caminho do JAR e a versão/opções de linha de comando no contrato e em `docs/05-benchmarks.md`.
5. Construa e confira a configuração, sem iniciar experimentos:

```bash
cd lab-expe-05
docker compose -f env/compose.yaml config
docker compose -f env/compose.yaml build benchmark
```

6. Confirme o runtime e gere a diferença de flags:

```bash
docker compose -f env/compose.yaml run --rm --no-deps --entrypoint java benchmark -version
bash env/capture-flags.sh
```

7. Antes do piloto, capture `docker version`, `docker info` (CPU/RAM disponíveis para o daemon), `sw_vers`, `sysctl hw.model`, `sysctl hw.ncpu`, memória física, `pmset -g batt` e o plano de energia. No macOS, `lscpu` e `free -h` não descrevem diretamente o host; qualquer saída desses comandos dentro do contêiner deve ser identificada como visão da VM/contêiner, não como hardware bare metal.

## Execução

O serviço `benchmark` é único para G1 e ZGC. Os limites `cpus` e `mem_limit` vêm de uma mesma configuração Compose; a condição é escolhida por variável de ambiente passada pelo script de coleta. `network_mode: none` impede que a execução abra conexões externas. A imagem e os dados são montados somente para leitura quando não precisam ser gravados; CSV, saída bruta e log de GC ficam no volume `data/`.

A máquina deve ficar na tomada, com o modo de baixo consumo desligado e sem atualizações nem tarefas pesadas. Registrar no diário qualquer uso concorrente, pausa, superaquecimento ou reinicialização. No Docker Desktop para macOS, os contêineres executam sobre uma VM Linux; os resultados representam essa combinação de host Apple Silicon, macOS, Docker Desktop e VM, não um servidor Linux bare metal.

## Reprodutibilidade pendente

Antes de marcar o ambiente como aprovado, é preciso concluir a confirmação do hardware/VM, executar `java -version` no contêiner, comprovar G1 e ZGC nos logs, gerar `env/flags.diff`, confirmar o digest no runtime e permitir que outra pessoa faça o preflight do zero. Até lá, os valores acima são uma configuração candidata, não evidência de benchmark.
