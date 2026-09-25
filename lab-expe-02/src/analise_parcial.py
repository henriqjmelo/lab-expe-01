#!/usr/bin/env python3
"""Analise descritiva parcial do Lab02, so com trials registrados pelo timer.

Le data/trials_raw.csv (a unica fonte aceita: linhas gravadas por src/timer.py),
junta as metricas estaticas de cada trial (mesma funcao e mesmos parametros de
src/metricas.py) e gera tabelas e graficos por tratamento.

Regras aplicadas, todas visiveis na saida:
    - a taxa de sucesso usa o total da suite congelada (issue #59) como
      denominador; uma verificacao final que gravou 0/0 (falha de coleta) vira
      0 de N, e a linha e marcada com total_corrigido=1;
    - trial censurado entra com tempo = time-box e a censura fica marcada;
    - trial sem implementacao (solucao.py identico ao esqueleto da kata) nao entra
      na RQ3, porque nao ha codigo para medir;
    - nenhum teste inferencial e feito. Com trials de katas diferentes em cada
      tratamento nao existem pares validos para o Wilcoxon.

Uso:
    python src/analise_parcial.py

Quando os demais trials reais forem registrados em data/trials_raw.csv, rodar de
novo atualiza tudo. Nenhum valor e estimado ou preenchido por este script.
"""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from consolida import TESTES_POR_KATA, TIME_BOX_S  # noqa: E402
from metricas import medir  # noqa: E402

TRATAMENTOS = ("com-ia", "sem-ia")
CORES = {"com-ia": "#2a6f97", "sem-ia": "#c77d3a"}
ROTULO = {"com-ia": "com IA", "sem-ia": "sem IA"}


def raiz_lab() -> Path:
    return Path(__file__).resolve().parent.parent


def sem_implementacao(raiz: Path, kata: str, pasta: Path) -> bool:
    modelo = (raiz / "katas" / kata / "solucao.py").read_text(encoding="utf-8")
    atual = (pasta / "solucao.py").read_text(encoding="utf-8")
    return modelo.replace("\r\n", "\n").strip() == atual.replace("\r\n", "\n").strip()


def ler_trials(raiz: Path) -> list[dict]:
    with (raiz / "data" / "trials_raw.csv").open(newline="", encoding="utf-8") as f:
        brutos = list(csv.DictReader(f))

    trials = []
    for linha in brutos:
        kata = linha["kata"]
        passando = int(linha["testes_passando"])
        total_gravado = int(linha["testes_total"])
        total = TESTES_POR_KATA[kata]
        pasta = raiz / "trials" / f"{linha['integrante']}__{kata}__{linha['tratamento']}"
        trials.append(
            {
                "integrante": linha["integrante"],
                "kata": kata,
                "tratamento": linha["tratamento"],
                "ordem": int(linha["ordem"]),
                "tempo_s": int(linha["tempo_s"]),
                "censurado": int(linha["censurado"]),
                "testes_passando": passando,
                "testes_total": total,
                "total_corrigido": int(total_gravado != total),
                "taxa_sucesso": round(passando / total, 4),
                "sem_implementacao": int(sem_implementacao(raiz, kata, pasta)),
                "pasta": pasta,
            }
        )
    return trials


def juntar_metricas(raiz: Path, trials: list[dict]) -> None:
    for t in trials:
        if t["sem_implementacao"]:
            t.update(complexidade_media="", loc="", sloc="", mi="", duplicacao_pct="")
            continue
        m = medir(t["pasta"] / "solucao.py", t["integrante"], t["kata"], t["tratamento"])
        t.update({k: m[k] for k in ("complexidade_media", "loc", "sloc", "mi", "duplicacao_pct")})


def mediana_e_faixa(valores: list[float]) -> tuple[float, float, float]:
    return statistics.median(valores), min(valores), max(valores)


def resumir(trials: list[dict]) -> list[dict]:
    linhas = []
    for trat in TRATAMENTOS:
        grupo = [t for t in trials if t["tratamento"] == trat]
        if not grupo:
            continue
        tempos = [t["tempo_s"] for t in grupo]
        taxas = [t["taxa_sucesso"] for t in grupo]
        com_codigo = [t for t in grupo if not t["sem_implementacao"]]
        med_t, min_t, max_t = mediana_e_faixa(tempos)
        med_s, min_s, max_s = mediana_e_faixa(taxas)
        linha = {
            "tratamento": trat,
            "n": len(grupo),
            "verdes": sum(1 for t in grupo if t["censurado"] == 0),
            "censurados": sum(1 for t in grupo if t["censurado"] == 1),
            "tempo_mediana_s": med_t,
            "tempo_min_s": min_t,
            "tempo_max_s": max_t,
            "mediana_censurada": int(med_t >= TIME_BOX_S),
            "taxa_sucesso_mediana": round(med_s, 4),
            "taxa_sucesso_min": min_s,
            "taxa_sucesso_max": max_s,
            "n_rq3": len(com_codigo),
        }
        for campo in ("complexidade_media", "loc", "sloc", "mi", "duplicacao_pct"):
            v = [float(t[campo]) for t in com_codigo if t[campo] != ""]
            linha[f"{campo}_mediana"] = round(statistics.median(v), 3) if v else ""
        linhas.append(linha)
    return linhas


def gravar(raiz: Path, trials: list[dict], resumo: list[dict]) -> None:
    dados = raiz / "data"
    campos = [
        "integrante", "kata", "tratamento", "ordem", "tempo_s", "censurado",
        "testes_passando", "testes_total", "total_corrigido", "taxa_sucesso",
        "sem_implementacao", "complexidade_media", "loc", "sloc", "mi", "duplicacao_pct",
    ]
    with (dados / "analise_parcial_trials.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(trials, key=lambda t: (t["integrante"], t["ordem"])))
    with (dados / "analise_parcial_tratamentos.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(resumo[0].keys()))
        w.writeheader()
        w.writerows(resumo)


def _figura(largura=9, altura=4.8):
    fig, ax = plt.subplots(figsize=(largura, altura))
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    return fig, ax


def _legenda(ax):
    from matplotlib.patches import Patch

    itens = [Patch(color=CORES[t], label=ROTULO[t]) for t in TRATAMENTOS]
    ax.legend(handles=itens, frameon=False)


def grafico_tempo(trials: list[dict], destino: Path) -> None:
    fig, ax = _figura()
    ordem = sorted(trials, key=lambda t: t["ordem"])
    for i, t in enumerate(ordem):
        barra = ax.bar(i, t["tempo_s"], color=CORES[t["tratamento"]])[0]
        if t["censurado"]:
            barra.set_hatch("//")
            barra.set_edgecolor("white")
            ax.text(i, t["tempo_s"] * 1.05, "censurado", ha="center", fontsize=8)
        else:
            ax.text(i, t["tempo_s"] * 1.05, f"{t['tempo_s']} s", ha="center", fontsize=9)
    ax.set_yscale("log")
    ax.set_ylim(30, TIME_BOX_S * 2)
    ax.axhline(TIME_BOX_S, color="gray", linestyle="--", linewidth=1)
    ax.text(len(ordem) - 0.5, TIME_BOX_S * 1.05, "limite de 35 min", ha="right", fontsize=8, color="gray")
    ax.set_xticks(range(len(ordem)))
    ax.set_xticklabels([t["kata"].upper() for t in ordem])
    ax.set_ylabel("Tempo até passar em todos os testes (s, escala log)")
    ax.set_xlabel("Kata (na ordem de execução)")
    ax.set_title("Tempo por trial (Gabriel, 6 trials registrados pelo cronômetro)")
    _legenda(ax)
    fig.tight_layout()
    fig.savefig(destino, dpi=140)
    plt.close(fig)


def grafico_sucesso(trials: list[dict], destino: Path) -> None:
    fig, ax = _figura()
    ordem = sorted(trials, key=lambda t: t["ordem"])
    for i, t in enumerate(ordem):
        pct = t["taxa_sucesso"] * 100
        ax.bar(i, pct, color=CORES[t["tratamento"]])
        ax.text(i, pct + 1.5, f"{t['testes_passando']}/{t['testes_total']}", ha="center", fontsize=9)
    ax.set_ylim(0, 112)
    ax.set_xticks(range(len(ordem)))
    ax.set_xticklabels([t["kata"].upper() for t in ordem])
    ax.set_ylabel("Testes de aceitação passando (%)")
    ax.set_xlabel("Kata (na ordem de execução)")
    ax.set_title("Taxa de sucesso ao final do trial")
    _legenda(ax)
    fig.tight_layout()
    fig.savefig(destino, dpi=140)
    plt.close(fig)


def grafico_estatico(trials: list[dict], destino: Path) -> None:
    medidos = sorted((t for t in trials if not t["sem_implementacao"]), key=lambda t: t["ordem"])
    painéis = [
        ("complexidade_media", "Complexidade ciclomática média"),
        ("sloc", "Linhas de código (SLOC)"),
        ("duplicacao_pct", "Linhas duplicadas (%)"),
        ("mi", "Índice de manutenibilidade"),
    ]
    fig, eixos = plt.subplots(1, 4, figsize=(14, 4))
    for ax, (campo, titulo) in zip(eixos, painéis):
        for i, t in enumerate(medidos):
            ax.bar(i, float(t[campo]), color=CORES[t["tratamento"]])
        ax.set_xticks(range(len(medidos)))
        ax.set_xticklabels([t["kata"].upper() for t in medidos])
        ax.set_title(titulo, fontsize=10)
        ax.grid(axis="y", alpha=0.3)
        ax.set_axisbelow(True)
        if campo == "duplicacao_pct" and all(float(t[campo]) == 0 for t in medidos):
            ax.set_ylim(0, 5)
            ax.text(0.5, 0.5, "0% em todos os trials", transform=ax.transAxes,
                    ha="center", va="center", fontsize=10, color="gray")
    _legenda(eixos[0])
    fig.suptitle("Métricas estáticas por trial (trial sem implementação não entra)", fontsize=11)
    fig.tight_layout()
    fig.savefig(destino, dpi=140)
    plt.close(fig)


def main() -> int:
    raiz = raiz_lab()
    trials = ler_trials(raiz)
    juntar_metricas(raiz, trials)
    resumo = resumir(trials)
    gravar(raiz, trials, resumo)

    graficos = raiz / "graficos"
    graficos.mkdir(exist_ok=True)
    grafico_tempo(trials, graficos / "lab02_tempo_por_trial.png")
    grafico_sucesso(trials, graficos / "lab02_taxa_sucesso.png")
    grafico_estatico(trials, graficos / "lab02_metricas_estaticas.png")

    print(f"{len(trials)} trial(s) de data/trials_raw.csv")
    for t in sorted(trials, key=lambda t: t["ordem"]):
        print(
            f"  {t['integrante']} {t['kata']} {t['tratamento']}: tempo={t['tempo_s']}s "
            f"censurado={t['censurado']} {t['testes_passando']}/{t['testes_total']} "
            f"sem_impl={t['sem_implementacao']} total_corrigido={t['total_corrigido']}"
        )
    print()
    for r in resumo:
        print(r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
