#!/usr/bin/env python3
"""Analise inferencial da S03 (issues #91, #92 e #93).

Le data/trials_raw.csv (linhas gravadas por src/timer.py), junta as metricas
estaticas de cada trial e testa as hipoteses do DESENHO.md com Wilcoxon pareado.

Pareamento: por kata. Cada participante resolve cada kata uma unica vez, em um
so tratamento (PLANO em consolida.py), entao nao existe par "mesmo participante,
mesma kata, dois tratamentos". Para cada kata, a mediana dos trials com-IA e a
mediana dos trials sem-IA formam um par. Sao 6 pares (K1 a K6). Com 6 pares o
menor p bilateral possivel e 0,03125 e o menor unilateral e 0,015625. O DESENHO.md
fala em comparacao dentro de cada participante; essa formulacao nao e executavel
com 6 trials por participante e a decisao esta registrada no PROTOCOLO.md.

Testes (unilaterais, na direcao das hipoteses do DESENHO.md, alfa = 0,05):
    RQ1  tempo_s              com-IA < sem-IA   (tempo censurado entra como 2100)
    RQ2  taxa_sucesso         com-IA > sem-IA
         testes_falhando      com-IA < sem-IA   (complemento da taxa, mesma base)
    RQ3  complexidade_media   com-IA < sem-IA
         duplicacao_pct       com-IA < sem-IA
         mi, sloc, loc        bilateral, exploratorio; loc e sloc sao o controle
                              de tamanho da solucao

Saidas em data/: inferencia_pares.csv (um par por linha e por variavel) e
inferencia_testes.csv (um teste por linha). Tambem imprime uma tabela legivel.

Regras:
    - trial sem implementacao (solucao.py igual ao esqueleto) nao entra na RQ3;
    - a taxa usa o total da suite congelada como denominador;
    - kata que so tem um dos tratamentos nao forma par e fica de fora, dito na saida;
    - com menos pares do que o necessario para p <= alfa, o teste nao e feito.

Uso:
    python src/inferencia.py
    python src/inferencia.py --csv outro_trials_raw.csv --sem-metricas
"""

from __future__ import annotations

import argparse
import csv
import statistics
from pathlib import Path

from scipy import stats

from consolida import TESTES_POR_KATA, TIME_BOX_S

ALFA = 0.05

# nome, campo, direcao. "less": com-IA menor. "greater": com-IA maior. "two-sided": exploratorio.
VARIAVEIS = (
    ("RQ1", "tempo_s", "less"),
    ("RQ2", "taxa_sucesso", "greater"),
    ("RQ2", "testes_falhando", "less"),
    ("RQ3", "complexidade_media", "less"),
    ("RQ3", "duplicacao_pct", "less"),
    ("RQ3", "mi", "two-sided"),
    ("RQ3-controle", "sloc", "two-sided"),
    ("RQ3-controle", "loc", "two-sided"),
)
CAMPOS_ESTATICOS = ("complexidade_media", "duplicacao_pct", "mi", "sloc", "loc")


def raiz_lab() -> Path:
    return Path(__file__).resolve().parent.parent


def ler_trials(csv_path: Path) -> list[dict]:
    with csv_path.open(newline="", encoding="utf-8") as f:
        brutos = list(csv.DictReader(f))
    trials = []
    for linha in brutos:
        kata = linha["kata"]
        passando = int(linha["testes_passando"])
        total = TESTES_POR_KATA[kata]
        trials.append(
            {
                "integrante": linha["integrante"],
                "kata": kata,
                "tratamento": linha["tratamento"],
                "tempo_s": int(linha["tempo_s"]),
                "censurado": int(linha["censurado"]),
                "taxa_sucesso": passando / total,
                "testes_falhando": total - passando,
            }
        )
    return trials


def juntar_metricas(raiz: Path, trials: list[dict]) -> None:
    """Acrescenta as metricas estaticas com a mesma funcao usada em metricas.py."""
    from analise_parcial import sem_implementacao
    from metricas import medir

    for t in trials:
        pasta = raiz / "trials" / f"{t['integrante']}__{t['kata']}__{t['tratamento']}"
        if sem_implementacao(raiz, t["kata"], pasta):
            t.update({c: None for c in CAMPOS_ESTATICOS})
            continue
        m = medir(pasta / "solucao.py", t["integrante"], t["kata"], t["tratamento"])
        for c in CAMPOS_ESTATICOS:
            t[c] = float(m[c]) if m[c] != "" else None


def montar_pares(trials: list[dict], campo: str) -> tuple[list[dict], list[str]]:
    """Um par por kata: mediana com-IA e mediana sem-IA. Devolve tambem as katas sem par."""
    pares, sem_par = [], []
    for kata in sorted({t["kata"] for t in trials}):
        grupo = {"com-ia": [], "sem-ia": []}
        censurados = 0
        for t in trials:
            if t["kata"] == kata and t.get(campo) is not None:
                grupo[t["tratamento"]].append(t[campo])
                censurados += t["censurado"] if campo == "tempo_s" else 0
        if not grupo["com-ia"] or not grupo["sem-ia"]:
            sem_par.append(kata)
            continue
        com, sem = statistics.median(grupo["com-ia"]), statistics.median(grupo["sem-ia"])
        pares.append(
            {
                "kata": kata,
                "n_com_ia": len(grupo["com-ia"]),
                "n_sem_ia": len(grupo["sem-ia"]),
                "com_ia": com,
                "sem_ia": sem,
                "diferenca": com - sem,
                "trials_censurados": censurados,
            }
        )
    return pares, sem_par


def p_minimo(n: int, direcional: bool) -> float:
    """Menor p exato possivel com n pares sem empates e sem diferencas nulas."""
    unilateral = 0.5**n
    return unilateral if direcional else min(1.0, 2 * unilateral)


def tamanho_de_efeito(diferencas: list[float]) -> float | None:
    """Correlacao rank-biserial: (soma de postos positivos - negativos) / total. Em [-1, 1]."""
    nao_nulas = [d for d in diferencas if d != 0]
    if not nao_nulas:
        return None
    ordem = stats.rankdata([abs(d) for d in nao_nulas])
    pos = sum(r for r, d in zip(ordem, nao_nulas) if d > 0)
    neg = sum(r for r, d in zip(ordem, nao_nulas) if d < 0)
    return (pos - neg) / (pos + neg)


def testar(pares: list[dict], direcao: str) -> dict:
    """Wilcoxon pareado sobre com_ia - sem_ia. Nao chama o teste sem pares suficientes."""
    difs = [p["diferenca"] for p in pares]
    nao_nulas = [d for d in difs if d != 0]
    base = {
        "n_pares": len(pares),
        "n_diferencas_nao_nulas": len(nao_nulas),
        "mediana_com_ia": statistics.median(p["com_ia"] for p in pares) if pares else "",
        "mediana_sem_ia": statistics.median(p["sem_ia"] for p in pares) if pares else "",
        "mediana_das_diferencas": statistics.median(difs) if pares else "",
        "rank_biserial": "",
        "estatistica_w": "",
        "p_valor": "",
        "metodo": "",
        "direcao": direcao,
        "conclusao": "",
    }
    direcional = direcao != "two-sided"
    if not pares:
        base["conclusao"] = "sem teste: nenhuma kata tem trials nos dois tratamentos"
        return base
    if not nao_nulas:
        base["conclusao"] = "sem teste: todas as diferencas sao nulas"
        return base
    minimo = p_minimo(len(nao_nulas), direcional)
    if minimo > ALFA:
        base["conclusao"] = (
            f"sem teste: {len(nao_nulas)} diferencas nao nulas nao alcancam p <= {ALFA} "
            f"(p minimo possivel {minimo:.5f})"
        )
        return base
    r = stats.wilcoxon(difs, alternative=direcao, zero_method="wilcox", method="auto")
    base["rank_biserial"] = round(tamanho_de_efeito(difs), 4)
    base["estatistica_w"] = float(r.statistic)
    base["p_valor"] = round(float(r.pvalue), 5)
    # method="auto" usa a distribuicao exata sem empates e a aproximacao normal com empates.
    empates = len({abs(d) for d in nao_nulas}) < len(nao_nulas)
    base["metodo"] = "aproximacao normal (empates)" if empates else "exato"
    base["conclusao"] = (
        f"p <= {ALFA}" if float(r.pvalue) <= ALFA else f"p > {ALFA}"
    )
    return base


def analisar(trials: list[dict]) -> tuple[list[dict], list[dict]]:
    linhas_pares, linhas_testes = [], []
    for questao, campo, direcao in VARIAVEIS:
        pares, sem_par = montar_pares(trials, campo)
        for p in pares:
            linhas_pares.append({"questao": questao, "variavel": campo, **p})
        resultado = testar(pares, direcao)
        resultado.update(
            questao=questao,
            variavel=campo,
            katas_sem_par=" ".join(sem_par),
            pares_com_censura=sum(1 for p in pares if p["trials_censurados"]),
        )
        linhas_testes.append(resultado)
    return linhas_pares, linhas_testes


CAMPOS_PARES = (
    "questao", "variavel", "kata", "n_com_ia", "n_sem_ia", "com_ia", "sem_ia",
    "diferenca", "trials_censurados",
)
CAMPOS_TESTES = (
    "questao", "variavel", "direcao", "n_pares", "n_diferencas_nao_nulas",
    "mediana_com_ia", "mediana_sem_ia", "mediana_das_diferencas", "estatistica_w",
    "p_valor", "rank_biserial", "metodo", "pares_com_censura", "katas_sem_par", "conclusao",
)


def gravar(destino: Path, linhas_pares: list[dict], linhas_testes: list[dict]) -> None:
    for nome, campos, linhas in (
        ("inferencia_pares.csv", CAMPOS_PARES, linhas_pares),
        ("inferencia_testes.csv", CAMPOS_TESTES, linhas_testes),
    ):
        with (destino / nome).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
            w.writeheader()
            w.writerows(linhas)


def imprimir(linhas_testes: list[dict]) -> None:
    for t in linhas_testes:
        extra = f" | katas sem par: {t['katas_sem_par']}" if t["katas_sem_par"] else ""
        print(
            f"{t['questao']:<13}{t['variavel']:<20}pares={t['n_pares']} "
            f"p={t['p_valor'] or '-'} r={t['rank_biserial'] or '-'} -> {t['conclusao']}{extra}"
        )
    print(f"\nTime-box {TIME_BOX_S} s; alfa {ALFA}. Pareamento por kata (ver cabecalho do modulo).")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--csv", type=Path, help="trials_raw.csv alternativo (padrao: data/trials_raw.csv)")
    ap.add_argument("--sem-metricas", action="store_true", help="pula radon e jscpd (RQ1 e RQ2 apenas)")
    ap.add_argument("--saida", type=Path, help="pasta de saida (padrao: data/)")
    args = ap.parse_args()

    raiz = raiz_lab()
    trials = ler_trials(args.csv or raiz / "data" / "trials_raw.csv")
    if not args.sem_metricas:
        juntar_metricas(raiz, trials)
    else:
        for t in trials:
            t.update({c: None for c in CAMPOS_ESTATICOS})

    linhas_pares, linhas_testes = analisar(trials)
    gravar(args.saida or raiz / "data", linhas_pares, linhas_testes)
    imprimir(linhas_testes)


if __name__ == "__main__":
    main()
