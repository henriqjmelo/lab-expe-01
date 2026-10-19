from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from metricas.recuperacao import Run, episodios_do_workflow

ALFA = 0.05

METRICAS_CONTINUAS = (
    ("df_release_semana", "Frequencia de deploy"),
    ("lt_a_release_dias", "Lead time (a)"),
    ("lt_b_release_dias", "Lead time (b)"),
    ("cfr_b_release", "CFR (b)"),
    ("recuperacao_mediana_horas", "Recuperacao"),
)

ATRIBUTOS_INDEPENDENTES = (
    ("estrelas", "Estrelas"),
    ("contribuidores", "Contribuidores"),
    ("idade_anos", "Idade em anos"),
)


def _serie(valores) -> pd.Series:
    return pd.Series(valores, dtype="float64").dropna()


def dispersao(contagens) -> dict:
    v = _serie(contagens)
    n = len(v)
    media = float(v.mean())
    variancia = float(v.var(ddof=1))
    if n < 2 or media <= 0:
        return {"n": n, "media": media, "variancia": variancia, "indice": None,
                "qui2": None, "gl": None, "p": None, "compativel_poisson": None}
    indice = variancia / media
    qui2 = (n - 1) * indice
    p = float(stats.chi2.sf(qui2, n - 1))
    return {"n": n, "media": media, "variancia": variancia, "indice": indice,
            "qui2": qui2, "gl": n - 1, "p": p, "compativel_poisson": bool(p > ALFA)}


def ajuste_binomial_negativa(contagens) -> dict:
    v = _serie(contagens)
    media = float(v.mean())
    variancia = float(v.var(ddof=1))
    if len(v) < 2 or media <= 0 or variancia <= media:
        return {"n": len(v), "media": media, "variancia": variancia,
                "r": None, "p": None, "aplicavel": False}
    return {"n": len(v), "media": media, "variancia": variancia,
            "r": float(media ** 2 / (variancia - media)),
            "p": float(media / variancia), "aplicavel": True}


def ajuste_weibull(tempos) -> dict:
    v = _serie(tempos)
    v = v[v > 0]
    if len(v) < 3:
        return {"n": len(v), "forma": None, "escala": None, "regime": None}
    forma, _, escala = stats.weibull_min.fit(v.to_numpy(), floc=0)
    return {"n": len(v), "forma": float(forma), "escala": float(escala),
            "regime": _regime(float(forma))}


def _regime(forma: float) -> str:
    if forma < 0.95:
        return "decrescente"
    if forma > 1.05:
        return "crescente"
    return "constante"


def normalidade(valores) -> dict:
    v = _serie(valores)
    if len(v) < 3:
        return {"n": len(v), "assimetria": None, "w": None, "p": None, "normal": None}
    w, p = stats.shapiro(v.to_numpy())
    return {"n": len(v), "assimetria": float(stats.skew(v.to_numpy())),
            "w": float(w), "p": float(p), "normal": bool(p > ALFA)}


def centro(valores) -> dict:
    v = _serie(valores)
    if v.empty:
        return {"n": 0, "media": None, "mediana": None, "q1": None, "q3": None,
                "maximo": None, "razao_media_mediana": None}
    mediana = float(v.median())
    media = float(v.mean())
    return {"n": len(v), "media": media, "mediana": mediana,
            "q1": float(v.quantile(0.25)), "q3": float(v.quantile(0.75)),
            "maximo": float(v.max()),
            "razao_media_mediana": media / mediana if mediana > 0 else None}


def poder_discriminante(grupos: dict) -> dict:
    amostras = [_serie(v).to_numpy() for v in grupos.values()]
    amostras = [a for a in amostras if len(a) > 0]
    n = int(sum(len(a) for a in amostras))
    todos = np.concatenate(amostras) if amostras else np.empty(0)
    if len(amostras) < 2 or n < 3 or np.ptp(todos) == 0:
        return {"grupos": len(amostras), "n": n, "h": None, "p": None,
                "epsilon2": None, "discrimina": False if len(amostras) >= 2 else None}
    h, p = stats.kruskal(*amostras)
    return {"grupos": len(amostras), "n": n, "h": float(h), "p": float(p),
            "epsilon2": float(h / (n - 1)), "discrimina": bool(p < ALFA)}


def medias_amostrais(valores, tamanho: int = 50, repeticoes: int = 10000,
                     semente: int = 42) -> np.ndarray:
    v = _serie(valores).to_numpy()
    if len(v) == 0:
        return np.empty(0)
    sorteios = np.random.default_rng(semente).choice(v, size=(repeticoes, tamanho), replace=True)
    return sorteios.mean(axis=1)


def duracoes_por_repositorio(runs: pd.DataFrame) -> dict:
    saida: dict = {}
    for chave, grupo in runs.groupby(["owner", "repo"], sort=False):
        duracoes: list[float] = []
        for _, do_workflow in grupo.groupby("workflow_id", sort=False):
            lista = [Run(int(l.workflow_id), l.conclusion, l.run_started_at, l.updated_at)
                     for l in do_workflow.itertuples()]
            duracoes.extend(episodios_do_workflow(lista)[0])
        saida[chave] = duracoes
    return saida


def tabela_normalidade(df: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for coluna, rotulo in METRICAS_CONTINUAS:
        if coluna not in df:
            continue
        bruto = normalidade(df[coluna])
        positivos = _serie(df[coluna])
        positivos = positivos[positivos > 0]
        log = normalidade(np.log(positivos)) if len(positivos) >= 3 else {}
        linhas.append({"metrica": rotulo, "coluna": coluna, **bruto,
                       "assimetria_log": log.get("assimetria"), "w_log": log.get("w"),
                       "p_log": log.get("p"), "normal_log": log.get("normal")})
    return pd.DataFrame(linhas)


def tabela_centro(df: pd.DataFrame) -> pd.DataFrame:
    linhas = [{"metrica": rotulo, "coluna": coluna, **centro(df[coluna])}
              for coluna, rotulo in METRICAS_CONTINUAS if coluna in df]
    return pd.DataFrame(linhas)


def tabela_contagem(df: pd.DataFrame, coluna: str = "n_release") -> pd.DataFrame:
    disp = dispersao(df[coluna])
    nb = ajuste_binomial_negativa(df[coluna])
    return pd.DataFrame([{"coluna": coluna, **disp,
                          "nb_r": nb["r"], "nb_p": nb["p"], "nb_aplicavel": nb["aplicavel"]}])


def tabela_weibull(duracoes: dict) -> pd.DataFrame:
    linhas = []
    for (owner, repo), valores in duracoes.items():
        ajuste = ajuste_weibull(valores)
        if ajuste["forma"] is None:
            continue
        linhas.append({"owner": owner, "repo": repo, **ajuste})
    return pd.DataFrame(linhas)


def resumo_weibull(tabela: pd.DataFrame) -> pd.DataFrame:
    if tabela.empty:
        return pd.DataFrame()
    forma = tabela["forma"]
    return pd.DataFrame([{
        "n_repositorios": len(tabela),
        "forma_mediana": float(forma.median()),
        "forma_q1": float(forma.quantile(0.25)),
        "forma_q3": float(forma.quantile(0.75)),
        "prop_decrescente": float((tabela["regime"] == "decrescente").mean()),
        "prop_constante": float((tabela["regime"] == "constante").mean()),
        "prop_crescente": float((tabela["regime"] == "crescente").mean()),
    }])


def tabela_poder_discriminante(df: pd.DataFrame, faixas: pd.Series) -> pd.DataFrame:
    linhas = []
    for coluna, rotulo in ATRIBUTOS_INDEPENDENTES:
        if coluna not in df:
            continue
        grupos = {nivel: df.loc[faixas == nivel, coluna] for nivel in faixas.dropna().unique()}
        linhas.append({"atributo": rotulo, "coluna": coluna, **poder_discriminante(grupos)})
    return pd.DataFrame(linhas)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m analise.distribuicoes")
    ap.add_argument("--dataset", type=Path, default=Path("data/dataset_dora.csv"))
    ap.add_argument("--runs", type=Path, default=Path("data/eventos/runs.csv.gz"))
    ap.add_argument("--saida", type=Path, default=Path("analise/saida/tabelas"))
    args = ap.parse_args(argv)

    df = pd.read_csv(args.dataset)
    args.saida.mkdir(parents=True, exist_ok=True)

    for nome, tabela in (("distribuicoes_normalidade", tabela_normalidade(df)),
                         ("distribuicoes_centro", tabela_centro(df)),
                         ("distribuicoes_contagem", tabela_contagem(df))):
        tabela.to_csv(args.saida / f"{nome}.csv", index=False)
        print(f"{args.saida / nome}.csv: {len(tabela)} linha(s)")

    if args.runs.exists():
        duracoes = duracoes_por_repositorio(pd.read_csv(args.runs))
        por_repo = tabela_weibull(duracoes)
        por_repo.to_csv(args.saida / "distribuicoes_weibull.csv", index=False)
        resumo_weibull(por_repo).to_csv(args.saida / "distribuicoes_weibull_resumo.csv", index=False)
        print(f"{args.saida}/distribuicoes_weibull.csv: {len(por_repo)} repositorio(s)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
