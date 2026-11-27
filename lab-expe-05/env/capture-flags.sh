#!/usr/bin/env bash
set -euo pipefail

ENV_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$ENV_DIR/compose.yaml"
HEAP_MB="${LAB05_FLAG_HEAP_MB:-1024}"

if ! [[ "$HEAP_MB" =~ ^[1-9][0-9]*$ ]]; then
  echo "LAB05_FLAG_HEAP_MB deve ser um inteiro positivo; recebido: $HEAP_MB" >&2
  exit 2
fi

command -v docker >/dev/null || { echo "docker CLI não encontrado" >&2; exit 2; }

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

for gc in G1 ZGC; do
  case "$gc" in
    G1) collector_flag='-XX:+UseG1GC' ;;
    ZGC) collector_flag='-XX:+UseZGC' ;;
  esac
  docker compose -f "$COMPOSE_FILE" run --rm --no-deps \
    --entrypoint java benchmark \
    "$collector_flag" "-Xms${HEAP_MB}m" "-Xmx${HEAP_MB}m" \
    -XX:+PrintFlagsFinal -version >"$tmp_dir/$gc.txt" 2>&1
  grep -Eq 'openjdk version|OpenJDK Runtime Environment|OpenJDK 64-Bit Server VM' "$tmp_dir/$gc.txt" || {
    echo "A saída do JDK não confirmou inicialização para $gc; saída capturada abaixo:" >&2
    cat "$tmp_dir/$gc.txt" >&2
    exit 1
  }
done

{
  printf '# Saída gerada por env/capture-flags.sh em %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf '# Imagem base: eclipse-temurin:25-jdk-noble@sha256:4ddc1a8bdaf283421df5487411aff10b797ccf1e06a339041005114c8f489b5c\n'
  printf '# Heap usado para comparação: -Xms%sm = -Xmx%sm\n' "$HEAP_MB" "$HEAP_MB"
  printf '# Diff textual das saídas completas de -XX:+PrintFlagsFinal. Revisar e explicar diferenças do coletor antes da coleta.\n'
  diff -u "$tmp_dir/G1.txt" "$tmp_dir/ZGC.txt" || status=$?
  if [[ "${status:-0}" -gt 1 ]]; then
    exit "$status"
  fi
} > "$ENV_DIR/flags.diff"

echo "Atualizado: $ENV_DIR/flags.diff"
