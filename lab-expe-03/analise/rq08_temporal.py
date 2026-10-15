from __future__ import annotations

import argparse
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pymannkendall as mk
from statsmodels.stats.multitest import multipletests

from analise import graficos as g
from metricas.cfr import FALHA, SUCESSO, cfr_ci, classificar_conclusao
from metricas.frequencia import semanas_da_janela
from metricas.recuperacao import Run

MINIMO_PONTOS_MENSAL = 8

METRICAS_TEMPORAIS = (
    ("frequencia", "Frequência", True),
    ("lead_time_a", "Lead time (a)", False),
    ("cfr_a", "CFR (a)", False),
    ("recuperacao", "Recuperação", False),
)


def _parse(data: str) -> datetime:
    return datetime.fromisoformat(data.replace("Z", "+00:00"))


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def _somar_mes(dt: datetime) -> datetime:
    ano, mes = (dt.year + 1, 1) if dt.month == 12 else (dt.year, dt.month + 1)
    return dt.replace(year=ano, month=mes)


def meses_da_janela(inicio: str, fim: str) -> list[tuple[str, str, str]]:
    atual, limite = _parse(inicio), _parse(fim)
    periodos = []
    while atual < limite:
        proximo = min(_somar_mes(atual), limite)
        periodos.append((atual.strftime("%Y-%m"), _iso(atual), _iso(proximo)))
        atual = proximo
    return periodos


def trimestres_da_janela(inicio: str, fim: str) -> list[tuple[str, str, str]]:
    meses = meses_da_janela(inicio, fim)
    trimestres = []
    for i in range(0, len(meses), 3):
        bloco = meses[i : i + 3]
        if bloco:
            trimestres.append((f"T{i // 3 + 1}", bloco[0][1], bloco[-1][2]))
    return trimestres


def periodo_de(data: str, periodos: list[tuple[str, str, str]]) -> str | None:
    d = _parse(data)
    for rotulo, inicio, fim in periodos:
        if _parse(inicio) <= d < _parse(fim):
            return rotulo
    return None


def serie_frequencia(datas: list[str], periodos: list[tuple[str, str, str]]) -> dict[str, float]:
    contagem = {rotulo: 0 for rotulo, _, _ in periodos}
    for data in datas:
        rotulo = periodo_de(data, periodos)
        if rotulo is not None:
            contagem[rotulo] += 1
    return {
        rotulo: contagem[rotulo] / semanas_da_janela(inicio, fim)
        for rotulo, inicio, fim in periodos
    }


def serie_lead_time(releases: list[dict], periodos: list[tuple[str, str, str]]) -> dict[str, float | None]:
    baldes: dict[str, list[float]] = {rotulo: [] for rotulo, _, _ in periodos}
    for r in releases:
        if r.get("ignorada") or pd.isna(r.get("lt_a_dias")):
            continue
        rotulo = periodo_de(r["published_at"], periodos)
        if rotulo is not None:
            baldes[rotulo].append(float(r["lt_a_dias"]))
    return {r: (statistics.median(v) if v else None) for r, v in baldes.items()}


def serie_cfr(conclusoes_com_data: list[tuple[str, str | None]], periodos: list[tuple[str, str, str]]) -> dict[str, float | None]:
    baldes: dict[str, list[str | None]] = {rotulo: [] for rotulo, _, _ in periodos}
    for data, conclusao in conclusoes_com_data:
        rotulo = periodo_de(data, periodos)
        if rotulo is not None:
            baldes[rotulo].append(conclusao)
    return {r: cfr_ci(v)["cfr"] for r, v in baldes.items()}


def _episodios_com_inicio(runs: list[Run]) -> list[tuple[str, float]]:
    episodios: list[tuple[str, float]] = []
    houve_sucesso = False
    inicio_episodio: str | None = None
    for run in sorted(runs, key=lambda r: r.run_started_at):
        classe = classificar_conclusao(run.conclusion)
        if classe == FALHA:
            if houve_sucesso and inicio_episodio is None:
                inicio_episodio = run.run_started_at
        elif classe == SUCESSO:
            if inicio_episodio is not None:
                duracao = (_parse(run.updated_at) - _parse(inicio_episodio)).total_seconds() / 3600
                episodios.append((inicio_episodio, duracao))
                inicio_episodio = None
            houve_sucesso = True
    return episodios


def serie_recuperacao(runs: list[Run], periodos: list[tuple[str, str, str]]) -> dict[str, float | None]:
    por_workflow: dict[int, list[Run]] = defaultdict(list)
    for run in runs:
        por_workflow[run.workflow_id].append(run)
    baldes: dict[str, list[float]] = {rotulo: [] for rotulo, _, _ in periodos}
    for runs_wf in por_workflow.values():
        for inicio_episodio, duracao in _episodios_com_inicio(runs_wf):
            rotulo = periodo_de(inicio_episodio, periodos)
            if rotulo is not None:
                baldes[rotulo].append(duracao)
    return {r: (statistics.median(v) if v else None) for r, v in baldes.items()}


def classificar_tendencia(valores: list[float | None], melhora_se_sobe: bool, minimo_pontos: int = MINIMO_PONTOS_MENSAL) -> dict:
    completos = [v for v in valores if pd.notna(v)]
    if len(completos) < minimo_pontos:
        return {"status": "insuficiente", "p": None, "tendencia": None, "n": len(completos)}
    resultado = mk.original_test(completos)
    sobe, desce = resultado.trend == "increasing", resultado.trend == "decreasing"
    if (sobe and melhora_se_sobe) or (desce and not melhora_se_sobe):
        status = "melhora"
    elif (desce and melhora_se_sobe) or (sobe and not melhora_se_sobe):
        status = "piora"
    else:
        status = "sem_tendencia"
    return {"status": status, "p": resultado.p, "tendencia": resultado.trend, "n": len(completos)}


def carregar_eventos(pasta: Path) -> dict[str, pd.DataFrame]:
    return {
        "releases": pd.read_csv(pasta / "releases.csv"),
        "lead_time": pd.read_csv(pasta / "lead_time_releases.csv"),
        "runs": pd.read_csv(pasta / "runs.csv.gz"),
    }


def series_por_repositorio(eventos: dict[str, pd.DataFrame], owner: str, repo: str, periodos: list[tuple[str, str, str]]) -> dict[str, dict[str, float | None]]:
    releases = eventos["releases"]
    rel = releases[(releases["owner"] == owner) & (releases["repo"] == repo) & (~releases["prerelease"]) & (releases["na_janela"])]
    lt = eventos["lead_time"]
    ltr = lt[(lt["owner"] == owner) & (lt["repo"] == repo)]
    runs = eventos["runs"]
    rr = runs[(runs["owner"] == owner) & (runs["repo"] == repo)]

    series_runs = [Run(int(l.workflow_id), l.conclusion, l.run_started_at, l.updated_at, int(l.run_attempt)) for l in rr.itertuples()]

    return {
        "frequencia": serie_frequencia(rel["published_at"].tolist(), periodos),
        "lead_time_a": serie_lead_time(ltr.to_dict("records"), periodos),
        "cfr_a": serie_cfr(list(zip(rr["run_started_at"], rr["conclusion"])), periodos),
        "recuperacao": serie_recuperacao(series_runs, periodos),
    }


def matriz_longa(eventos: dict[str, pd.DataFrame], repositorios: list[tuple[str, str]], periodos: list[tuple[str, str, str]]) -> pd.DataFrame:
    linhas = []
    for owner, repo in repositorios:
        series = series_por_repositorio(eventos, owner, repo, periodos)
        for coluna, rotulo, _ in METRICAS_TEMPORAIS:
            for periodo, _, _ in periodos:
                linhas.append({"owner": owner, "repo": repo, "coluna": coluna, "metrica": rotulo,
                                "periodo": periodo, "valor": series[coluna][periodo]})
    return pd.DataFrame(linhas)


def tabela_tendencias_de_matriz(longa: pd.DataFrame, periodos: list[tuple[str, str, str]], minimo_pontos: int = MINIMO_PONTOS_MENSAL) -> pd.DataFrame:
    ordem = [r for r, _, _ in periodos]
    melhora_por_coluna = {c: m for c, _, m in METRICAS_TEMPORAIS}
    linhas = []
    for (owner, repo, coluna, metrica), grupo in longa.groupby(["owner", "repo", "coluna", "metrica"], sort=False):
        valores = grupo.set_index("periodo")["valor"].reindex(ordem).tolist()
        r = classificar_tendencia(valores, melhora_por_coluna[coluna], minimo_pontos)
        linhas.append({"owner": owner, "repo": repo, "metrica": metrica, "coluna": coluna, **r})
    tabela = pd.DataFrame(linhas)
    testados = tabela[tabela["status"] != "insuficiente"].copy()
    testados["p_fdr"] = np.nan
    testados["p_holm"] = np.nan
    for metrica, grupo in testados.groupby("metrica"):
        testados.loc[grupo.index, "p_fdr"] = multipletests(grupo["p"], method="fdr_bh")[1]
        testados.loc[grupo.index, "p_holm"] = multipletests(grupo["p"], method="holm")[1]
    return tabela.merge(testados[["owner", "repo", "metrica", "p_fdr", "p_holm"]], on=["owner", "repo", "metrica"], how="left")


def resumo_tendencias(tabela: pd.DataFrame, alfa: float = 0.05) -> pd.DataFrame:
    linhas = []
    for metrica in dict.fromkeys(tabela["metrica"]):
        grupo = tabela[tabela["metrica"] == metrica]
        significativo = grupo["p_fdr"] < alfa
        status_sig = np.where(significativo, grupo["status"], np.where(grupo["status"] == "insuficiente", "insuficiente", "sem_tendencia"))
        n = len(grupo)
        linhas.append({
            "metrica": metrica, "n": n,
            "melhora": float((status_sig == "melhora").mean()),
            "piora": float((status_sig == "piora").mean()),
            "sem_tendencia": float((status_sig == "sem_tendencia").mean()),
            "insuficiente": float((grupo["status"] == "insuficiente").mean()),
        })
    return pd.DataFrame(linhas)


def trajetoria_mediana(longa: pd.DataFrame, periodos: list[tuple[str, str, str]]) -> pd.DataFrame:
    ordem = [r for r, _, _ in periodos]
    linhas = []
    for (metrica, periodo), grupo in longa.groupby(["metrica", "periodo"], observed=True):
        v = grupo["valor"].dropna()
        linhas.append({"metrica": metrica, "periodo": periodo, "n": len(v),
                        "mediana": v.median() if len(v) else np.nan,
                        "q1": v.quantile(0.25) if len(v) else np.nan,
                        "q3": v.quantile(0.75) if len(v) else np.nan})
    tabela = pd.DataFrame(linhas)
    tabela["periodo"] = pd.Categorical(tabela["periodo"], categories=ordem, ordered=True)
    return tabela.sort_values(["metrica", "periodo"]).reset_index(drop=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m analise.rq08_temporal")
    ap.add_argument("--inicio", default="2025-10-01T00:00:00Z")
    ap.add_argument("--fim", default="2026-10-01T00:00:00Z")
    ap.add_argument("--eventos", type=Path, default=Path("data/eventos"))
    ap.add_argument("--repos", type=Path, default=Path("data/dataset_dora.csv"))
    ap.add_argument("--extra-eventos", type=Path, nargs="*", default=[Path("data/amostra2/eventos")])
    ap.add_argument("--extra-repos", type=Path, nargs="*", default=[Path("data/amostra2/dataset_dora.csv")])
    ap.add_argument("--saida", type=Path, default=Path("analise/saida"))
    args = ap.parse_args(argv)

    g.estilo()
    meses = meses_da_janela(args.inicio, args.fim)
    tabelas = args.saida / "tabelas"
    tabelas.mkdir(parents=True, exist_ok=True)
    figuras = args.saida / "figuras"
    figuras.mkdir(parents=True, exist_ok=True)

    grupos = [("A1", args.eventos, args.repos)]
    for e, r in zip(args.extra_eventos, args.extra_repos):
        if e.exists() and r.exists():
            grupos.append(("A2", e, r))

    acumulado_eventos = None
    gerados = []
    for nome, pasta_eventos, caminho_repos in grupos:
        eventos = carregar_eventos(pasta_eventos)
        if acumulado_eventos is None:
            acumulado_eventos = {k: [v] for k, v in eventos.items()}
            repos = pd.read_csv(caminho_repos)[["owner", "repo"]]
            acumulado_repos = [repos]
        else:
            for k in acumulado_eventos:
                acumulado_eventos[k].append(eventos[k])
            acumulado_repos.append(pd.read_csv(caminho_repos)[["owner", "repo"]])

        todos_repos = list(pd.concat(acumulado_repos, ignore_index=True).itertuples(index=False, name=None))
        todos_eventos = {k: pd.concat(v, ignore_index=True) for k, v in acumulado_eventos.items()}
        rotulo_amostra = f"{nome} · n = {len(todos_repos)}" if nome == "A1" else f"A1 + A2 · n = {len(todos_repos)}"

        longa = matriz_longa(todos_eventos, todos_repos, meses)
        tabela = tabela_tendencias_de_matriz(longa, meses)
        resumo = resumo_tendencias(tabela)
        trajetoria = trajetoria_mediana(longa, meses)
        sufixo = len(todos_repos)
        tabela.to_csv(tabelas / f"rq08_tendencias_{sufixo}.csv", index=False)
        resumo.to_csv(tabelas / f"rq08_resumo_{sufixo}.csv", index=False)
        trajetoria.to_csv(tabelas / f"rq08_trajetoria_{sufixo}.csv", index=False)

        g.ROTULO_AMOSTRA = rotulo_amostra
        trimestres = trimestres_da_janela(args.inicio, args.fim)
        gerados.append(fig_barras_tendencia(resumo, figuras / f"fig17_rq08_tendencia_{sufixo}.png"))
        gerados.append(fig_trajetoria(trajetoria, trimestres, figuras / f"fig18_rq08_trajetoria_{sufixo}.png"))

    for caminho in gerados:
        print(caminho)
    return 0


def fig_barras_tendencia(resumo: pd.DataFrame, destino: Path):
    import matplotlib.pyplot as plt

    cores = {"melhora": "#1baf7a", "sem_tendencia": "#c3c2b7", "piora": "#eb6834", "insuficiente": "#e1e0d9"}
    ordem = ("melhora", "sem_tendencia", "piora", "insuficiente")
    fig, ax = plt.subplots(figsize=(g.LARGURA, 2.6))
    for i, (_, linha) in enumerate(resumo.iterrows()):
        esquerda = 0.0
        for chave in ordem:
            w = float(linha[chave])
            ax.barh(i, w, left=esquerda, height=0.6, color=cores[chave], linewidth=0)
            if w >= 0.08:
                ax.text(esquerda + w / 2, i, g.fmt_pct(w), ha="center", va="center", fontsize=8, color="#0b0b0b")
            esquerda += w
    ax.set_yticks(range(len(resumo)), resumo["metrica"])
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    g.cabecalho(ax, "A maioria dos repositórios não mostra tendência mensal clara",
                "% de repositórios por classificação (Mann-Kendall, série mensal, FDR por métrica)")
    return g.salvar(fig, destino)


def fig_trajetoria(trajetoria: pd.DataFrame, trimestres: list[tuple[str, str, str]], destino: Path):
    import matplotlib.pyplot as plt

    metricas = list(dict.fromkeys(trajetoria["metrica"]))
    fig, eixos = plt.subplots(1, len(metricas), figsize=(g.LARGURA, 2.8))
    for eixo, metrica in zip(eixos, metricas):
        sub = trajetoria[trajetoria["metrica"] == metrica].reset_index(drop=True)
        x = range(len(sub))
        eixo.fill_between(x, sub["q1"], sub["q3"], color=g.SERIE[0], alpha=0.18, linewidth=0)
        eixo.plot(x, sub["mediana"], color=g.SERIE[0], linewidth=1.6, marker="o", markersize=3)
        for i in range(3, len(sub), 3):
            eixo.axvline(i - 0.5, color=g.GRADE, linewidth=0.8, zorder=0)
        eixo.set_xticks(list(x)[::3], [t for t, _, _ in trimestres])
        eixo.set_title(metrica, fontsize=8.5, pad=4)
        eixo.tick_params(axis="x", labelsize=7.5)
    fig.tight_layout(rect=(0, 0, 1, 0.84))
    g.cabecalho(eixos[0], "Como as métricas se movem ao longo da janela, mês a mês",
                "Mediana entre repositórios com IQR sombreado · linhas verticais marcam os trimestres do enunciado", folga=20)
    return g.salvar(fig, destino)


if __name__ == "__main__":
    raise SystemExit(main())
