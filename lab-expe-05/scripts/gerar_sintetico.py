"""Gera dados sinteticos no esquema do contrato, com efeitos conhecidos.

O pipeline de analise e construido e testado antes de existir dado real. Este
script produz um CSV identico em forma ao que a coleta vai produzir, mas com os
efeitos *injetados por nos*, de modo que os testes possam conferir se a analise
recupera o que foi plantado (e se respeita o alfa quando nao ha efeito nenhum).

Uso:
    python scripts/gerar_sintetico.py                      # 30 blocos em data/sintetico.csv
    python scripts/gerar_sintetico.py --blocos 5 --saida data/sintetico-piloto.csv
    python scripts/gerar_sintetico.py --sem-efeito         # tudo com razao 1,0 (checa o alfa)

Os nomes dos benchmarks e os niveis de heap sao PROVISORIOS: quem decide e a
issue S01-B2. O pipeline nao depende deles (le o que vier no CSV), entao trocar
aqui nao quebra nada a jusante.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
SEMENTE_PADRAO = 42
BLOCOS_PADRAO = 30

# --- o mundo que estamos fingindo ----------------------------------------------
# tipo "latencia": reporta lat_p99_ms. tipo "vazao": lat_p99_ms fica vazia (isso
# e dado, nao erro - o contrato, secao 3, diz isso explicitamente).
BENCHMARKS = {
    "cassandra": {"exec_g1_ms": 1800.0, "p99_g1_ms": 12.0, "heap_min_mb": 512, "tipo": "latencia"},
    "tomcat": {"exec_g1_ms": 2400.0, "p99_g1_ms": 9.0, "heap_min_mb": 256, "tipo": "latencia"},
    "h2": {"exec_g1_ms": 3200.0, "p99_g1_ms": None, "heap_min_mb": 1024, "tipo": "vazao"},
    "xalan": {"exec_g1_ms": 950.0, "p99_g1_ms": None, "heap_min_mb": 256, "tipo": "vazao"},
}
HEAPS = (1.5, 3.0)

# Razao ZGC/G1 do tempo de execucao. Repare que ela MUDA com o heap em tres dos
# quatro benchmarks: e isso que o modelo de interacao do RQ2 tem de enxergar.
# O xalan e plano de proposito, para o teste nao passar por acidente.
EFEITO_EXEC = {
    ("cassandra", 1.5): 1.03, ("cassandra", 3.0): 1.01,
    ("tomcat", 1.5): 1.04, ("tomcat", 3.0): 1.02,
    ("h2", 1.5): 1.10, ("h2", 3.0): 1.06,
    ("xalan", 1.5): 1.08, ("xalan", 3.0): 1.08,
}
# Razao ZGC/G1 do p99: abaixo de 1 porque o ZGC reduz a cauda. E a troca que a
# pergunta de pesquisa descreve: paga-se tempo para ganhar latencia.
EFEITO_P99 = {
    ("cassandra", 1.5): 0.70, ("cassandra", 3.0): 0.75,
    ("tomcat", 1.5): 0.65, ("tomcat", 3.0): 0.72,
}
EFEITO_PAUSA = 0.05   # pausa maxima do ZGC e uma fracao da do G1
EFEITO_CPU = 1.12     # coleta concorrente custa CPU
EFEITO_RSS = 1.15     # e memoria

CV = {
    "exec_ms": 0.04,
    "lat_p99_ms": 0.12,       # a cauda e mais barulhenta que o tempo total
    "gc_pause_max_ms": 0.20,
    "cpu_s": 0.05,
    "rss_peak_mb": 0.03,
}
BASE_G1 = {"gc_pause_max_ms": 180.0, "cpu_s": 14.0, "rss_peak_mb": 900.0}

DERIVA_POR_BLOCO = 0.001   # 0,1% por bloco: a maquina esquenta ao longo da coleta
TAXA_FALHA = 0.01          # OOM ocasional do ZGC no heap menor

JDK = "openjdk 25.0.1 2025-10-21 LTS"
IMAGEM = "sha256:0000000000000000000000000000000000000000000000000000000000000000"
HOST = "sintetico"
CPUS = 4
ITERACOES = 10


def _lognormal(rng: np.random.Generator, media: float, cv: float, tamanho=None) -> np.ndarray | float:
    """Sorteia lognormal com a MEDIA pedida e o CV pedido.

    A correcao -sigma^2/2 existe para que a media da lognormal seja exatamente
    `media`. Sem ela, a media sairia inflada e a razao recuperada pelos testes
    nao bateria com a razao injetada.
    """
    sigma = np.sqrt(np.log(1 + cv**2))
    return rng.lognormal(np.log(media) - sigma**2 / 2, sigma, size=tamanho)


def gerar(blocos: int = BLOCOS_PADRAO, semente: int = SEMENTE_PADRAO, sem_efeito: bool = False) -> pd.DataFrame:
    """Devolve um DataFrame no esquema do contrato, com 16 celulas x `blocos` linhas."""
    rng = np.random.default_rng(semente)
    celulas = [(gc, heap, bench) for bench in BENCHMARKS for heap in HEAPS for gc in ("G1", "ZGC")]
    t0 = datetime(2026, 11, 20, 12, 0, 0, tzinfo=timezone.utc)
    linhas = []

    for rep in range(1, blocos + 1):
        semente_bloco = int(rng.integers(0, 2**31 - 1))
        ordem = np.random.default_rng(semente_bloco).permutation(len(celulas))
        deriva = 1 + DERIVA_POR_BLOCO * (rep - 1)

        for passo, idx in enumerate(ordem):
            gc, heap, bench = celulas[idx]
            info = BENCHMARKS[bench]
            zgc = gc == "ZGC"
            um = 1.0

            r_exec = um if (sem_efeito or not zgc) else EFEITO_EXEC[(bench, heap)]
            exec_ms = float(_lognormal(rng, info["exec_g1_ms"] * r_exec * deriva, CV["exec_ms"]))

            if info["p99_g1_ms"] is None:
                p99 = ""
            else:
                r_p99 = um if (sem_efeito or not zgc) else EFEITO_P99[(bench, heap)]
                p99 = round(float(_lognormal(rng, info["p99_g1_ms"] * r_p99, CV["lat_p99_ms"])), 3)

            r_pausa = um if (sem_efeito or not zgc) else EFEITO_PAUSA
            r_cpu = um if (sem_efeito or not zgc) else EFEITO_CPU
            r_rss = um if (sem_efeito or not zgc) else EFEITO_RSS
            pausa = float(_lognormal(rng, BASE_G1["gc_pause_max_ms"] * r_pausa, CV["gc_pause_max_ms"]))
            cpu = float(_lognormal(rng, BASE_G1["cpu_s"] * r_cpu * deriva, CV["cpu_s"]))
            rss = float(_lognormal(rng, BASE_G1["rss_peak_mb"] * r_rss, CV["rss_peak_mb"]))

            # Falha so no ZGC com heap menor: e o cenario plausivel (coleta
            # concorrente precisa de folga). Serve para exercitar a regra de
            # exclusao do plano de analise, que so exclui por falha registrada.
            falhou = bool(zgc and heap == min(HEAPS) and not sem_efeito and rng.random() < TAXA_FALHA)

            i_heap = HEAPS.index(heap) + 1
            run_id = f"{gc}-h{i_heap}-r{rep:02d}-{bench}"
            linhas.append({
                "run_id": run_id,
                "rep": rep,
                "timestamp": (t0 + timedelta(minutes=len(celulas) * (rep - 1) + passo)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "host": HOST,
                "jdk_version": JDK,
                "image_digest": IMAGEM,
                "gc": gc,
                "cpus": CPUS,
                "heap_mult": heap,
                "heap_mb": int(info["heap_min_mb"] * heap),
                "benchmark": bench,
                "iterations": ITERACOES,
                "exec_ms": "" if falhou else round(exec_ms, 3),
                "lat_p99_ms": "" if falhou else p99,
                "gc_pause_max_ms": "" if falhou else round(pausa, 3),
                "cpu_s": "" if falhou else round(cpu, 3),
                "rss_peak_mb": "" if falhou else round(rss, 3),
                "failed": int(falhou),
                "failure_reason": "oom" if falhou else "",
                "seed": semente_bloco,
                "raw_file": f"raw/sintetico/{run_id}.txt",
                "gc_log_file": f"raw/sintetico/{run_id}.gc.log",
            })

    return pd.DataFrame(linhas)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Gera dados sinteticos no esquema do contrato do Lab05.")
    ap.add_argument("--blocos", type=int, default=BLOCOS_PADRAO, help="repeticoes por celula (padrao 30)")
    ap.add_argument("--semente", type=int, default=SEMENTE_PADRAO)
    ap.add_argument("--saida", type=Path, default=RAIZ / "data" / "sintetico.csv")
    ap.add_argument("--sem-efeito", action="store_true",
                    help="todas as razoes ZGC/G1 iguais a 1,0 (para conferir o erro tipo I)")
    a = ap.parse_args(argv)

    df = gerar(a.blocos, a.semente, a.sem_efeito)
    a.saida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.saida, index=False)
    print(f"{len(df)} linhas ({len(df) // a.blocos} celulas x {a.blocos} blocos) -> {a.saida}")
    if not a.sem_efeito:
        print(f"falhas injetadas: {int(df['failed'].sum())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
