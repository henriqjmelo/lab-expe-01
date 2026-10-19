from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.metrics import precision_recall_fscore_support

from metricas.corretiva import VERSOES
from validacao.comparar_versoes import marcacoes_por_release

F1_MINIMO = 0.70


def avaliar_versao(marcacoes: pd.DataFrame, consenso: pd.DataFrame) -> dict:
    comparado = consenso.merge(marcacoes, on=["owner", "repo", "tag_name"], how="inner")
    if comparado.empty:
        return {"n": 0, "precisao": None, "recall": None, "f1": None}
    y_real = (comparado["corretiva"].astype(str).str.strip().str.lower() == "sim").astype(int)
    y_previsto = comparado["marcada"].astype(int)
    precisao, recall, f1, _ = precision_recall_fscore_support(
        y_real, y_previsto, average="binary", zero_division=0
    )
    return {"n": len(comparado), "precisao": float(precisao), "recall": float(recall), "f1": float(f1)}


def avaliar_todas_as_versoes(releases: pd.DataFrame, commits: pd.DataFrame, consenso: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for nome, construtor in VERSOES.items():
        marcacoes = marcacoes_por_release(releases, commits, construtor)
        resultado = avaliar_versao(marcacoes, consenso)
        linhas.append({"versao": nome, **resultado})
    tabela = pd.DataFrame(linhas)
    tabela["atinge_f1_minimo"] = tabela["f1"] >= F1_MINIMO
    return tabela


def escolher_melhor_versao(tabela: pd.DataFrame) -> str:
    return tabela.sort_values("f1", ascending=False).iloc[0]["versao"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m validacao.avaliacao_heuristica")
    ap.add_argument("--eventos", type=Path, default=Path("data/eventos"))
    ap.add_argument("--consenso", type=Path, default=Path("validacao/consenso_releases.csv"))
    ap.add_argument("--saida", type=Path, default=Path("validacao/avaliacao_heuristica.csv"))
    args = ap.parse_args(argv)

    if not args.consenso.exists():
        print(f"{args.consenso} ainda nao existe (depende da #137). Nada a avaliar.")
        return 1

    releases = pd.read_csv(args.eventos / "releases.csv")
    commits = pd.read_csv(args.eventos / "commits_releases.csv.gz")
    consenso = pd.read_csv(args.consenso)

    tabela = avaliar_todas_as_versoes(releases, commits, consenso)
    tabela.to_csv(args.saida, index=False)
    print(tabela.to_string(index=False))
    print(f"melhor versao por F1: {escolher_melhor_versao(tabela)}")
    print(args.saida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
