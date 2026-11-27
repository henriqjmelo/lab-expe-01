# Diário de coleta

Este arquivo é um modelo; ainda não há sessões ou resultados registrados. Copie a seção “Sessão” uma vez por bloco ou interrupção relevante. Não preencha retrospectivamente com valores estimados.

## Sessão

**Data/hora UTC:** `[preencher]`  
**Operador:** `[preencher]`  
**Modo e blocos:** `[piloto/completo; número do bloco]`  
**Máquina/arquitetura/SO:** `[preencher]`  
**Docker Desktop/Engine e virtualização:** `[preencher]`  
**CPU/memória/disco da VM:** `[preencher]`  
**Tomada, energia e temperatura percebida:** `[preencher]`  
**JDK, imagem/digest e DaCapo/checksum:** `[preencher]`  
**Flags e limites congelados:** `[preencher; apontar para env/flags.diff]`  
**CSV validado e comando usado:** `[preencher]`

**Condições concorrentes ou desvios:** `[nenhum ou descrição e intervalo]`  
**Runs interrompidos, falhos ou repetidos:** `[run_id, motivo e decisão]`  
**Arquivos brutos:** `[caminhos em data/raw/]`  
**Responsável pela conferência:** `[preencher]`

## Regra de registro

Cada invocação fica em uma linha do CSV, inclusive OOM, falha de validação ou erro do contêiner. O motivo deve ser explícito. Não remover outliers válidos nem substituir uma linha falha sem registrar a tentativa original e a decisão no diário. Os logs de GC e do harness permanecem nos arquivos brutos; este diário documenta contexto e desvios, não substitui os arquivos.

## Estado atual

Nenhum piloto ou run completo foi realizado. O daemon Docker negou acesso ao socket nesta sessão, o JAR DaCapo não foi baixado e a compatibilidade do JDK 25/ARM64 ainda está pendente.