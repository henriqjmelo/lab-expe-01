#!/usr/bin/env bash
set -Eeuo pipefail

required=(LAB05_MODE LAB05_RUN_ID LAB05_GC LAB05_BENCHMARK LAB05_HEAP_MB LAB05_ITERATIONS LAB05_SIZE LAB05_DACAPO_JAR)
for name in "${required[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "Variável obrigatória ausente: $name" >&2
    exit 2
  fi
done

if ! [[ "$LAB05_HEAP_MB" =~ ^[1-9][0-9]*$ && "$LAB05_ITERATIONS" =~ ^[1-9][0-9]*$ ]]; then
  echo "Heap e iterações devem ser inteiros positivos" >&2
  exit 2
fi
case "$LAB05_GC" in
  G1) GC_FLAG='-XX:+UseG1GC' ;;
  ZGC) GC_FLAG='-XX:+UseZGC' ;;
  *) echo "Coletor inválido: $LAB05_GC" >&2; exit 2 ;;
esac

DATA_DIR=/workspace/data
RUN_DIR="$DATA_DIR/raw/$LAB05_MODE/$LAB05_RUN_ID"
OUT="$RUN_DIR/stdout.txt"
GC_LOG="$RUN_DIR/gc.log"
LATENCY_DIR="$RUN_DIR/latency"
mkdir -p "$LATENCY_DIR"
: > "$OUT"
: > "$GC_LOG"

if [[ ! -r "$LAB05_DACAPO_JAR" ]]; then
  printf 'JAR DaCapo não encontrado ou ilegível: %s\n' "$LAB05_DACAPO_JAR" >> "$OUT"
  cat "$OUT"
  exit 0
fi

{
  printf 'run_id=%s\ncollector=%s\nbenchmark=%s\nheap_mb=%s\niterations=%s\nsize=%s\n' \
    "$LAB05_RUN_ID" "$LAB05_GC" "$LAB05_BENCHMARK" "$LAB05_HEAP_MB" "$LAB05_ITERATIONS" "$LAB05_SIZE"
  printf '%s\n' '===== java -version ====='
  java -version
  printf '%s\n' '===== DaCapo output ====='
} >> "$OUT" 2>&1

clock_ticks="$(getconf CLK_TCK 2>/dev/null || printf '100')"
if ! [[ "$clock_ticks" =~ ^[1-9][0-9]*$ ]]; then
  clock_ticks=100
fi

proc_stats() {
  local pid="$1" line rest
  local -a fields=()
  [[ -r "/proc/$pid/stat" ]] || return 1
  IFS= read -r line < "/proc/$pid/stat" || return 1
  rest="${line##*) }"
  read -r -a fields <<< "$rest"
  [[ ${#fields[@]} -ge 13 ]] || return 1
  printf '%s %s\n' "${fields[0]}" "$((fields[11] + fields[12]))"
}

peak_rss_kb() {
  local pid="$1"
  awk '/^VmHWM:/ {print $2; found=1} END {if (!found) print 0}' "/proc/$pid/status" 2>/dev/null || printf '0\n'
}

JAVA_ARGS=(
  "$GC_FLAG"
  "-Xms${LAB05_HEAP_MB}m"
  "-Xmx${LAB05_HEAP_MB}m"
  "-Xlog:gc*=info:file=${GC_LOG}:time,uptime,level,tags"
  -jar "$LAB05_DACAPO_JAR"
  --latency-csv
  --latency-hdr
  --latency-metered
  --log-directory "$LATENCY_DIR"
  -n "$LAB05_ITERATIONS"
  -s "$LAB05_SIZE"
  "$LAB05_BENCHMARK"
)

{
  printf '%s\n' '===== Java command (shell-escaped) ====='
  printf 'java'
  printf ' %q' "${JAVA_ARGS[@]}"
  printf '\n'
} >> "$OUT"

java "${JAVA_ARGS[@]}" >> "$OUT" 2>&1 &
java_pid=$!
max_rss_kb=0
cpu_ticks=0
while [[ -r "/proc/$java_pid/stat" ]]; do
  if stats="$(proc_stats "$java_pid" 2>/dev/null)"; then
    read -r state ticks <<< "$stats"
    if [[ "$ticks" =~ ^[0-9]+$ ]]; then cpu_ticks="$ticks"; fi
  fi
  rss="$(peak_rss_kb "$java_pid")"
  if [[ "$rss" =~ ^[0-9]+$ ]] && (( rss > max_rss_kb )); then max_rss_kb="$rss"; fi
  [[ "${state:-}" == Z ]] && break
  sleep 0.1
 done
set +e
wait "$java_pid"
java_status=$?
set -e

cpu_seconds="$(awk -v ticks="$cpu_ticks" -v hz="$clock_ticks" 'BEGIN {printf "%.6f", ticks / hz}')"
printf '__LAB05_JAVA_EXIT_CODE__=%s\n' "$java_status" >> "$OUT"
printf '__LAB05_CPU_S__=%s\n' "$cpu_seconds" >> "$OUT"
printf '__LAB05_RSS_KB__=%s\n' "$max_rss_kb" >> "$OUT"
cat "$OUT"
# A falha do benchmark é registrada no CSV pelo orquestrador; não a confundir com erro do Docker.
exit 0
