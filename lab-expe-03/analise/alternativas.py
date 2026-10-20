from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from metricas.ci import cfr_ci_com_reexecucoes, tempo_feedback
from metricas.colaboracao import Deployment, PullRequest, metricas_bugs, metricas_deploys, metricas_prs
from metricas.fluxo import distribuicao_trabalho
from metricas.recuperacao import Run
from metricas.revert import CommitDeRelease, ReleaseAvaliavel, cfr_revert

FIM_JANELA = "2026-10-01T00:00:00Z"
SEMANAS_JANELA = 365 / 7

COLUNAS_GRAPHQL = (
    "owner", "repo",
    "n_prs_mergeados", "prs_mergeados_semana", "lt_pr_mediana_horas", "primeira_resposta_mediana_horas",
    "prop_prs_sem_resposta", "taxa_aceitacao_pr",
    "n_bugs_fechados", "resolucao_bug_mediana_horas",
    "n_deploys_producao", "usa_deployments", "df_deploy_semana", "cfr_d_deploy", "recuperacao_deploy_mediana_horas",
    "truncado_prs", "truncado_issues", "truncado_deployments",
)

COLUNAS = (
    "owner", "repo",
    "cfr_a", "cfr_a_reexec", "taxa_reexecucao", "n_reexecutados_sucesso", "n_reexecutados_falha",
    "feedback_mediana_min",
    "cfr_c_revert", "cfr_c_n_avaliadas", "cfr_c_n_revertidas", "cfr_c_n_censuradas",
    "n_commits_releases", "prop_convencional", "adota_convencional", "prop_fix", "prop_feat", "prop_revert",
)


def _reverte(valor) -> list[str]:
    return [s for s in str(valor).split(";") if s] if isinstance(valor, str) else []


def medidas_do_repositorio(runs: pd.DataFrame, lead_time: pd.DataFrame, commits: pd.DataFrame) -> dict:
    lista_runs = [
        Run(r.workflow_id, r.conclusion if isinstance(r.conclusion, str) else None, r.run_started_at, r.updated_at,
            run_attempt=int(r.run_attempt), head_sha=str(r.head_sha))
        for r in runs.itertuples()
    ]
    ci = cfr_ci_com_reexecucoes(lista_runs)
    feedback = tempo_feedback(lista_runs)

    releases = [ReleaseAvaliavel(r.tag_name, r.published_at, avaliavel=not bool(r.ignorada)) for r in lead_time.itertuples()]
    lista_commits = [CommitDeRelease(c.sha, c.tag_name, _reverte(c.reverte_sha)) for c in commits.itertuples()]
    revert = cfr_revert(releases, lista_commits, FIM_JANELA)
    fluxo = distribuicao_trabalho(commits["mensagem"].tolist())

    return {
        "cfr_a": ci["cfr"],
        "cfr_a_reexec": ci["cfr_com_reexecucoes"],
        "taxa_reexecucao": ci["taxa_reexecucao"],
        "n_reexecutados_sucesso": ci["n_reexecutados_sucesso"],
        "n_reexecutados_falha": ci["n_reexecutados_falha"],
        "feedback_mediana_min": feedback["mediana_minutos"],
        "cfr_c_revert": revert["cfr"],
        "cfr_c_n_avaliadas": revert["n_avaliadas"],
        "cfr_c_n_revertidas": revert["n_revertidas"],
        "cfr_c_n_censuradas": revert["n_censuradas"],
        "n_commits_releases": fluxo["n_commits"],
        "prop_convencional": fluxo["prop_convencional"],
        "adota_convencional": fluxo["adota_convencional"],
        "prop_fix": fluxo["prop_fix"],
        "prop_feat": fluxo["prop_feat"],
        "prop_revert": fluxo["prop_revert"],
    }


def calcular(pasta_amostra: Path) -> pd.DataFrame:
    repos = pd.read_csv(pasta_amostra / "repositorios.csv")
    eventos = pasta_amostra / "eventos"
    runs = pd.read_csv(eventos / "runs.csv.gz")
    lead_time = pd.read_csv(eventos / "lead_time_releases.csv")
    commits = pd.read_csv(eventos / "commits_releases.csv.gz", dtype={"reverte_sha": str, "mensagem": str})
    grupos = {nome: dict(iter(df.groupby(["owner", "repo"]))) for nome, df in
              (("runs", runs), ("lead_time", lead_time), ("commits", commits))}
    vazio = {"runs": runs.iloc[0:0], "lead_time": lead_time.iloc[0:0], "commits": commits.iloc[0:0]}
    linhas = []
    for owner, repo in repos.itertuples(index=False):
        partes = {nome: grupos[nome].get((owner, repo), vazio[nome]) for nome in grupos}
        linhas.append({"owner": owner, "repo": repo, **medidas_do_repositorio(**partes)})
    return pd.DataFrame(linhas, columns=COLUNAS)


def _texto(valor) -> str:
    return valor if isinstance(valor, str) else ""


def calcular_graphql(pasta_amostra: Path) -> pd.DataFrame:
    repos = pd.read_csv(pasta_amostra / "repositorios.csv")
    pasta = pasta_amostra / "graphql"
    prs = pd.read_csv(pasta / "prs.csv.gz")
    issues = pd.read_csv(pasta / "issues.csv.gz")
    deploys = pd.read_csv(pasta / "deployments.csv.gz")
    resumo = pd.read_csv(pasta / "resumo.csv").set_index(["owner", "repo"])
    grupos = {nome: dict(iter(df.groupby(["owner", "repo"]))) for nome, df in
              (("prs", prs), ("issues", issues), ("deploys", deploys))}
    linhas = []
    for owner, repo in repos.itertuples(index=False):
        g = {nome: grupos[nome].get((owner, repo)) for nome in grupos}
        lista_prs = [] if g["prs"] is None else [
            PullRequest(p.estado, p.created_at, _texto(p.merged_at), _texto(p.closed_at), _texto(p.primeira_resposta_at))
            for p in g["prs"].itertuples()
        ]
        lista_issues = [] if g["issues"] is None else [
            (i.created_at, i.closed_at, bool(i.eh_bug)) for i in g["issues"].itertuples()
        ]
        lista_deploys = [] if g["deploys"] is None else [
            Deployment(d.created_at, _texto(d.environment), _texto(d.state), _texto(d.status))
            for d in g["deploys"].itertuples()
        ]
        trunc = resumo.loc[(owner, repo)] if (owner, repo) in resumo.index else {}
        linhas.append({
            "owner": owner, "repo": repo,
            **metricas_prs(lista_prs, SEMANAS_JANELA),
            **metricas_bugs(lista_issues),
            **metricas_deploys(lista_deploys, SEMANAS_JANELA),
            **{k: bool(trunc[k]) if len(trunc) else None for k in ("truncado_prs", "truncado_issues", "truncado_deployments")},
        })
    return pd.DataFrame(linhas, columns=COLUNAS_GRAPHQL)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m analise.alternativas")
    ap.add_argument("pastas", type=Path, nargs="*",
                    default=[Path("data"), Path("data/amostra2"), Path("data/amostra3")])
    args = ap.parse_args(argv)
    for pasta in args.pastas:
        tabela = calcular(pasta)
        tabela.to_csv(pasta / "medidas_alternativas.csv", index=False)
        print(f"{pasta / 'medidas_alternativas.csv'}: {len(tabela)} repositorios")
        if (pasta / "graphql" / "resumo.csv").exists():
            graphql = calcular_graphql(pasta)
            graphql.to_csv(pasta / "medidas_graphql.csv", index=False)
            print(f"{pasta / 'medidas_graphql.csv'}: {len(graphql)} repositorios")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
