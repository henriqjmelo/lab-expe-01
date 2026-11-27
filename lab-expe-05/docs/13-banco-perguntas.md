# Banco de perguntas para a apresentação

As respostas abaixo descrevem o protocolo e seu estado. Onde aparece “provisório”, não trate a decisão como resultado nem como validação.

**Por que o objeto é a JVM e não um repositório do GitHub?** Porque o experimento executa Temurin JDK 25 com coletores explícitos e mede o software em operação. Não há mineração de commits, issues ou código-fonte como objeto do estudo, conforme a restrição do enunciado.

**O que DaCapo representa?** Uma suíte de workloads de benchmark para Java. É uma carga controlada, não uma implantação completa de uma empresa nem uma amostra de requisições reais de usuários.

**Por que `-n 5`?** Na metodologia de iteração do harness MR2, as primeiras quatro execuções são warmups e a quinta é a iteração cronometrada. Isso precisa passar por smoke test em cada workload no JDK25/ARM64 antes de ser congelado.

**Por que p99, e por que só em duas cargas?** O p99 resume a cauda da distribuição de latências quando o workload mede eventos de requisição. Cassandra e Spring são os candidatos atuais; BioJava e PMD não fornecem p99 nativo no protocolo. JME mede frames, não requisições, e por isso é reserva.

**O que significa `simple p99`?** É o percentil da latência observada por evento que o harness chama `simple`. DaCapo também gera medidas `metered`; são estimandos distintos. A coluna confirmatória única `lat_p99_ms` está proposta como `simple`, mas o grupo ainda deve aprovar essa definição.

**Como foi escolhido o heap mínimo?** Ainda não foi. Os números publicados são referências de outra plataforma. `min_heap_mb` só será preenchido após sondagem no alvo, com o JAR e a versão congelados, e validação das condições G1/ZGC.

**Por que 2× e 4× do mínimo?** É uma proposta operacional de dois níveis, não uma decisão experimental validada. O mínimo e os multiplicadores devem ser confirmados pelo grupo após o piloto e antes da coleta completa.

**Por que 16 células, mas 12 testes confirmatórios?** O fatorial tem 2 coletores × 2 heaps × 4 benchmarks = 16 combinações. Para o tempo há 8 pares G1/ZGC; para p99 há 4 pares porque só dois benchmarks têm latência. A família tem 12 testes, com Holm.

**Como tratamos OOM ou falha de validação?** A invocação permanece como linha com `failed=1` e motivo. Não é removida nem substituída silenciosamente; a análise decide exclusões conforme plano pré-registrado.

**Por que ainda não há resultados?** O daemon Docker negou acesso ao socket, o JAR não foi baixado e não foi possível confirmar espaço de extração, flags, runtime e compatibilidade JDK25/ARM64. Nenhum CSV real foi criado.

**Podemos generalizar para Linux bare metal ou serviços de produção?** Não diretamente. O alvo candidato é Docker Desktop em macOS sobre VM Linux e quatro workloads da suíte. Isso limita a validade externa; uma replicação em outro host é necessária.

**O que reaproveitamos dos Labs anteriores?** Práticas de protocolo, testes, versionamento e separação entre coleta e análise. Não reaproveitamos datasets, métricas de repositório ou simulações como evidência do Lab05; consulte [10-mapa-labs.md](10-mapa-labs.md).
