# Revisão cruzada e gates de entrega

## Checklist técnico de B

- [ ] Confirmar que contrato, `env/benchmarks.json`, runner e README usam os mesmos nomes, heaps, iterações, limites e unidade de p99.
- [ ] Conferir `docker compose config`, build por digest, `java -version`, flags e logs dos dois coletores no host aprovado.
- [ ] Confirmar preflight de disco antes de obter o ZIP, checksum do JAR e caminho exato do artefato.
- [ ] Executar smoke tests por benchmark/coletor/heap; conferir validação DaCapo, OOM, parser, p99, CPU, RSS e pausa máxima.
- [ ] Validar CSV por bloco; confirmar arquivos brutos/logs apontados, contagens e ausência de duplicatas.
- [ ] Revisar que falhas permanecem registradas e que nenhum valor sintético entrou em `pilot.csv`, `full.csv` ou `clean.csv`.
- [ ] Reexecutar instruções em clone limpo; verificar `make all` e o modo de dados reais separadamente.
- [ ] Conferir citações, versões, checksums, licença dos artefatos e as quatro ameaças à validade.
- [ ] Cronometrar bloco B em 3 minutos; revisar speaker notes e perguntas cruzadas.

## Revisão pelos colegas

A revisão de B deve ser feita por C conforme o contrato. Solicitar a C a conferência do schema e dos paths no pipeline. Solicitar a A a revisão do desenho, da métrica de latência e do vínculo com o contrato. Registrar cada comentário e sua resolução antes de mover as issues para Done.

## Gates para marcar issues

#223 só fecha após ambiente e flags validados no runtime. #224 só fecha após seleção e heaps aprovados por piloto sem OOM. #225 requer piloto real, CSV validado e revisão de C. #229 depende de coleta completa; #230 depende de validação, congelamento e publicação dos dados reais. #239 depende de `make all` reproduzível em clone limpo e integração do pipeline C2. #240 pode ser rascunho, mas não deve conter resultados inventados. #245 exige pacote final e manifesto; a tag não é criada antecipadamente. #248 exige roteiro e slides; #250 exige ensaio realizado e cronometrado; #251 exige revisão de A e C e conferência dos números reais.

## Situação atual

Documentos, proposta de runner e deck podem ser preparados localmente. Preflight Docker, piloto, coleta completa, validação/versionamento dos dados, ensaio com o trio, aprovação cruzada e tag de release continuam pendentes.