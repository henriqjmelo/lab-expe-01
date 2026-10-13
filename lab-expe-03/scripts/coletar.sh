#!/usr/bin/env bash
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
