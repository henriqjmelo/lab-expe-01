# Bloco B — roteiro cronometrado (3 min)

Deck: **Lab05 — Bloco B: ambiente, coleta e validade**, 5 páginas em 16:9, produzido no Slides (recurso `manus-resource://manus-slides/deck/lab05-bloco-b-ambiente-coleta-e--mwyfnyq4-bcd02dd2`). A fala está nas speaker notes de cada página, com marcação de tempo; este arquivo é a cópia local do roteiro, para o caso de o Slides não carregar.

O bloco cobre o que a issue #248 pede: pergunta e caminho, ambiente e coleta, reaproveitado × novo e as quatro ameaças à validade, em três minutos.

## Tempos

| Trecho | Tempo | Página | Conteúdo |
| :--- | :--- | :--- | :--- |
| Abertura | 0:00–0:10 | Capa | Recorte do bloco e aviso de que não há resultado |
| Pergunta e desenho | 0:10–0:55 | Pergunta e caminho experimental | Pergunta, 2×2×4, 16 células, 80 e 480 runs, 12 testes |
| Ambiente | 0:55–1:40 | Ambiente descrito, ainda não validado | Host, VM, runtime, estado de prontidão |
| Reuso | 1:40–2:20 | Reaproveitado × novo | Práticas dos Labs 01–04 e componentes novos |
| Validade | 2:20–3:00 | Ameaças à validade e próximos gates | Interna, construto, externa, conclusão e gates |

## Fala

**0:00–0:10 — Capa.** Bom dia. Este bloco cobre ambiente, coleta, o que veio dos labs anteriores e as ameaças à validade. São três minutos. Nada aqui é resultado: é o caminho e o que ainda falta.

**0:10–0:55 — Pergunta e caminho experimental.** A pergunta é direta: o ZGC reduz pausas e latência de cauda, mas a que custo em vazão, CPU e memória? E esse custo muda quando o heap dobra? O desenho é fatorial: dois coletores, dois níveis de heap, 2× e 4× o mínimo de cada carga, e quatro benchmarks, dois de latência e dois de lote. São dezesseis células; um bloco é uma passada completa, em ordem sorteada. O piloto tem cinco blocos, oitenta invocações. A coleta completa usa N igual a trinta, quatrocentas e oitenta invocações. O plano prevê doze testes confirmatórios, com Holm. Os workloads são candidatos: Cassandra e Spring para latência, BioJava e PMD para lote. Os mínimos de heap ainda não foram medidos.

**0:55–1:40 — Ambiente.** O ambiente está descrito, mas não validado. O host é um MacBook Air ARM64 com macOS 14.8.1, oito CPUs e dezesseis gibibytes. Os contêineres rodam numa VM Linux do Docker Desktop, com quatro CPUs e seis gibibytes provisórios. A imagem é Temurin 25, fixada por digest. O que falta é justamente o que importa. O daemon Docker não respondeu: deu operation not permitted. Não houve build, não houve run. Também não baixamos o DaCapo. O ZIP tem seis vírgula três gigabytes e o volume tem quinze gibibytes livres, mas o tamanho extraído não foi medido. Então não existe CSV, nem piloto, nem resultado. Qualquer número hoje seria invenção.

**1:40–2:20 — Reaproveitado × novo.** O que veio dos labs anteriores é método, não dado. Do Lab01 e do Lab02, a disciplina de versionar dados, escrever protocolo e registrar desvios. Do Lab03, o pipeline retomável, os testes e a separação entre coleta e análise. Do Lab04, os pins de dependência e a análise a partir de dados explícitos. O que é novo: o contêiner Temurin 25 com digest e flags, o DaCapo Chopin, o heap mínimo por benchmark, as dezesseis células, a captura de GC, CPU e RSS e o CSV do contrato. Nenhum número dos Labs 01 a 04 entra como medição do Lab05.

**2:20–3:00 — Validade.** Quatro ameaças, com o que já controlamos e o que falta. Validade interna: a mesma imagem, os mesmos limites e a ordem sorteada por bloco ajudam, mas a VM compartilha o host. Construto: tempo da iteração e p99 estão definidos no contrato, só que a variante simple do p99 ainda não foi aprovada pelo grupo. Validade externa: vamos declarar a plataforma, macOS com Docker e ARM64, sem generalizar para Linux bare metal. Mas os heaps e as quatro cargas não estão validados. Conclusão: N igual a trinta, alfa de cinco por cento e Holm sobre doze testes, mas o poder depende do piloto. Os gates são preflight, sondagem de heaps, piloto e, só então, a coleta com a tag data-v1.

## Arquivos de origem por página

| Página | Números ou afirmações | Arquivo |
| :--- | :--- | :--- |
| Pergunta e caminho experimental | pergunta, 16 células, 8 + 4 testes, N = 30, 5 blocos, workloads e reservas | [../docs/00-contrato.md](../docs/00-contrato.md), [../docs/05-benchmarks.md](../docs/05-benchmarks.md) |
| Ambiente descrito, ainda não validado | host, VM, limites, digest, espaço em disco, estado do daemon | [../env/README.md](../env/README.md), [../docs/00-etica-reprodutibilidade.md](../docs/00-etica-reprodutibilidade.md) |
| Reaproveitado × novo | o que veio de cada lab e o que é novo | [../docs/10-mapa-labs.md](../docs/10-mapa-labs.md) |
| Ameaças à validade e próximos gates | quatro ameaças, controles, lacunas e gates | [../docs/00-contrato.md](../docs/00-contrato.md), [../docs/00-etica-reprodutibilidade.md](../docs/00-etica-reprodutibilidade.md), [../docs/05-benchmarks.md](../docs/05-benchmarks.md) |

## O que este bloco não afirma

Não há diferença de tempo, de p99, de CPU ou de memória entre G1 e ZGC, porque nenhuma medição foi feita. Os números citados são do desenho experimental: 16 células, 80 runs no piloto, 480 na coleta provisória, 12 testes confirmatórios, 4 CPUs, 6 GiB, 15 GiB livres, ZIP de 6,3 GB. Nenhum deles é resultado de benchmark.

## Ensaio

Os tempos acima são nominais. Depois do ensaio cronometrado, registrar a duração real por trecho em [../docs/12-ensaio.md](../docs/12-ensaio.md); se passar de 3:00, cortar repetição, não as ressalvas.
