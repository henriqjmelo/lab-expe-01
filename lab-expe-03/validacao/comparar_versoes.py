from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from metricas.cfr import Deploy, Heuristica, cfr_entrega
from metricas.corretiva import VERSOES, ConstrutorHeuristica, MensagensPorTag

INICIO, FIM = "2025-10-01T00:00:00Z", "2026-10-01T00:00:00Z"


def mensagens_por_tag_do_grupo(commits: pd.DataFrame, owner: str, repo: str, tags: list[str]) -> MensagensPorTag:
    do_repo = commits[(commits["owner"] == owner) & (commits["repo"] == repo)]
    agrupado = do_repo.groupby("tag_name")["mensagem"].apply(list)
    return {tag: agrupado.get(tag, []) for tag in tags}


def marcacoes_por_release(
    releases: pd.DataFrame,
    commits: pd.DataFrame,
    construtor_heuristica: ConstrutorHeuristica,
) -> pd.DataFrame:
    rel = releases[~releases["prerelease"]]
    linhas = []
    for (owner, repo), grupo in rel.groupby(["owner", "repo"], sort=False):
        grupo = grupo.sort_values("published_at")
        mensagens_por_tag = mensagens_por_tag_do_grupo(commits, owner, repo, grupo["tag_name"].tolist())
        heuristica: Heuristica = construtor_heuristica(mensagens_por_tag)
        anterior: Deploy | None = None
        for r in grupo.itertuples():
            atual = Deploy(r.tag_name, r.published_at)
            linhas.append({"owner": owner, "repo": repo, "tag_name": r.tag_name,
                            "marcada": heuristica(atual, anterior)})
            anterior = atual
    return pd.DataFrame(linhas)


def cfr_b_por_repositorio(
    releases: pd.DataFrame,
    commits: pd.DataFrame,
    construtor_heuristica: ConstrutorHeuristica,
    inicio: str = INICIO,
    fim: str = FIM,
) -> pd.DataFrame:
    rel = releases[~releases["prerelease"]]
    linhas = []
    for (owner, repo), grupo in rel.groupby(["owner", "repo"], sort=False):
        grupo = grupo.sort_values("published_at")
        mensagens_por_tag = mensagens_por_tag_do_grupo(commits, owner, repo, grupo["tag_name"].tolist())
        heuristica: Heuristica = construtor_heuristica(mensagens_por_tag)
        deploys = [Deploy(r.tag_name, r.published_at) for r in grupo.itertuples()]
        resultado = cfr_entrega(deploys, inicio, fim, heuristica)
        linhas.append({
            "owner": owner, "repo": repo,
            "cfr_b": resultado["cfr"],
            "n_avaliadas": resultado["n_avaliadas"],
            "n_falharam": resultado["n_falharam"],
            "n_censuradas": resultado["n_censuradas"],
            "n_corretivas": resultado["n_corretivas"],
        })
    return pd.DataFrame(linhas)


def resumo_por_versao(releases: pd.DataFrame, commits: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for nome, construtor in VERSOES.items():
        tabela = cfr_b_por_repositorio(releases, commits, construtor)
        v = tabela["cfr_b"].dropna()
        linhas.append({
            "versao": nome, "n_repositorios": len(v),
            "mediana_cfr_b": v.median() if len(v) else None,
            "q1": v.quantile(0.25) if len(v) else None,
            "q3": v.quantile(0.75) if len(v) else None,
            "total_corretivas": int(tabela["n_corretivas"].sum()),
        })
    return pd.DataFrame(linhas)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m validacao.comparar_versoes")
    ap.add_argument("--eventos", type=Path, default=Path("data/eventos"))
    ap.add_argument("--saida", type=Path, default=Path("validacao"))
    args = ap.parse_args(argv)

    releases = pd.read_csv(args.eventos / "releases.csv")
    commits = pd.read_csv(args.eventos / "commits_releases.csv.gz")

    resumo = resumo_por_versao(releases, commits)
    args.saida.mkdir(parents=True, exist_ok=True)
    destino = args.saida / "comparacao_versoes.csv"
    resumo.to_csv(destino, index=False)
    print(resumo.to_string(index=False))
    print(destino)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
