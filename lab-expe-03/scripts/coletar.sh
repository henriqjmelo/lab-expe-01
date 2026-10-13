#!/usr/bin/env bash
# Coleta completa supervisionada (issue #139).
#
# - Mantem o Mac acordado com caffeinate (-i: sem sono por inatividade, -s: sem
#   sono do sistema enquanto estiver na tomada, -m: disco). A tela pode apagar.
#   Em Linux/sem caffeinate roda direto.
# - Se o pipeline cair (erro transitorio persistente, queda de rede, crash),
#   espera e roda de novo: o cache em disco faz a retomada sem repetir chamadas.
#   Espera 1 min, 2 min, 4 min... ate 15 min entre tentativas.
# - Para quando o pipeline termina (saida 0) ou quando e interrompido (Ctrl+C / kill).
#
# Uso (de dentro de lab-expe-03):
#   export GITHUB_TOKEN=ghp_...
#   nohup scripts/coletar.sh > /dev/null 2>&1 &
#   tail -f .cache/coleta.log
set -u
cd "$(dirname "$0")/.."

: "${GITHUB_TOKEN:?Defina GITHUB_TOKEN antes de rodar}"
PYTHON="${PYTHON:-python}"
CONFIG="${CONFIG:-config.yaml}"
LOG="${LOG:-.cache/coleta.log}"
ESPERA_INICIAL="${ESPERA_INICIAL:-60}"
ESPERA_MAX=900

mkdir -p "$(dirname "$LOG")"

if command -v caffeinate >/dev/null 2>&1; then
    ACORDADO=(caffeinate -ims)
else
    ACORDADO=()
fi

parar=0
trap 'parar=1; kill -TERM "$filho" 2>/dev/null' INT TERM

espera=$ESPERA_INICIAL
tentativa=1
while true; do
    echo "=== $(date '+%F %T') execucao $tentativa" >> "$LOG"
    inicio=$(date +%s)
    ${ACORDADO[@]+"${ACORDADO[@]}"} "$PYTHON" -m pipeline --config "$CONFIG" >> "$LOG" 2>&1 &
    filho=$!
    wait "$filho"
    codigo=$?
    # Rodou bem por mais de 10 min antes de cair: volta a espera para o inicio.
    [ $(( $(date +%s) - inicio )) -gt 600 ] && espera=$ESPERA_INICIAL

    if [ "$codigo" -eq 0 ]; then
        echo "=== $(date '+%F %T') coleta concluida" >> "$LOG"
        exit 0
    fi
    if [ "$parar" -eq 1 ] || [ "$codigo" -eq 130 ]; then
        echo "=== $(date '+%F %T') interrompida (saida $codigo)" >> "$LOG"
        exit "$codigo"
    fi

    echo "=== $(date '+%F %T') saida $codigo; nova tentativa em ${espera}s" >> "$LOG"
    sleep "$espera" &
    filho=$!
    wait "$filho"
    [ "$parar" -eq 1 ] && exit 130
    espera=$(( espera * 2 > ESPERA_MAX ? ESPERA_MAX : espera * 2 ))
    tentativa=$(( tentativa + 1 ))
done
