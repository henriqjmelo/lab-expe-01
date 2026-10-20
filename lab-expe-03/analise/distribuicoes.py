from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

from analise import estatisticas as est
from metricas.recuperacao import Run, episodios_do_workflow

ALFA = 0.05

METRICAS_CONTINUAS = (
    ("df_release_semana", "Frequencia de deploy"),
    ("lt_a_release_dias", "Lead time (a)"),
    ("lt_b_release_dias", "Lead time (b)"),
    ("cfr_b_release", "CFR (b)"),
    ("recuperacao_mediana_horas", "Recuperacao"),
)

ATRIBUTOS_DISCRIMINANCIA = (
    ("estrelas", "Estrelas"),
    ("contribuidores", "Contribuidores"),
    ("idade_anos", "Idade em anos"),
    ("cfr_b_release", "CFR (b)"),
    ("lt_b_release_dias", "Lead time (b)"),
    ("df_release_semana", "Frequencia de deploy"),
    ("lt_a_release_dias", "Lead time (a)"),
)

NOME_FAIXA = {1: "Elite", 2: "High", 3: "Medium", 4: "Low"}

PARES_CONVERGENCIA = (
    ("lt_b_release_dias", "lt_pr_mediana_horas", "Lead time (b): por release × por PR"),
    ("lt_a_release_dias", "lt_pr_mediana_horas", "Lead time (a): por release × por PR"),
    ("df_release_semana", "prs_mergeados_semana", "Ritmo: releases × PRs por semana"),
    ("cfr_b_release", "taxa_aceitacao_pr", "Falha: CFR (b) × taxa de aceitação de PR"),
    ("recuperacao_mediana_horas", "resolucao_bug_mediana_horas", "Recuperação: CI × issue de bug"),
)

LIMIAR_MESMO_CONSTRUCTO = 0.7

CONTROLES_TAMANHO = (
    ("estrelas", "Estrelas"),
    ("contribuidores", "Contribuidores"),
    ("idade_anos", "Idade em anos"),
)

PARES_RQ05 = (
    ("df_release_semana", "cfr_a", "Frequência × CFR (a)"),
    ("df_release_semana", "cfr_b_release", "Frequência × CFR (b)"),
)

NIVEIS_QUARTIL = ("Q1", "Q2", "Q3", "Q4")


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


def tipo_do_atributo(coluna: str, colunas_da_faixa: tuple[str, ...]) -> str:
    if coluna in colunas_da_faixa:
        return "controle"
    if coluna in {c for c, _ in METRICAS_CONTINUAS}:
        return "operacionalizacao"
    return "independente"


def tabela_poder_discriminante(df: pd.DataFrame, faixas: pd.Series,
                               colunas_da_faixa: tuple[str, ...] = ()) -> pd.DataFrame:
    niveis = list(faixas.dropna().unique())
    linhas = []
    for coluna, rotulo in ATRIBUTOS_DISCRIMINANCIA:
        if coluna not in df:
            continue
        grupos = {nivel: df.loc[faixas == nivel, coluna] for nivel in niveis}
        linhas.append({"atributo": rotulo, "coluna": coluna,
                       "tipo": tipo_do_atributo(coluna, colunas_da_faixa),
                       **poder_discriminante(grupos)})
    tabela = pd.DataFrame(linhas)
    if tabela.empty:
        return tabela
    hipoteses = (tabela["tipo"] != "controle") & tabela["p"].notna()
    tabela["p_holm"] = np.nan
    if hipoteses.any():
        tabela.loc[hipoteses, "p_holm"] = multipletests(tabela.loc[hipoteses, "p"], method="holm")[1]
    tabela["separa"] = pd.array(tabela["p_holm"] < ALFA, dtype="boolean")
    tabela.loc[tabela["p_holm"].isna(), "separa"] = pd.NA
    return tabela


def faixas_dora(classificacao: pd.DataFrame, coluna: str = "geral") -> pd.Series:
    return classificacao[coluna].map(NOME_FAIXA)


def convergencia(x, y) -> dict:
    bruto = pd.DataFrame({"x": np.asarray(x, dtype="float64"),
                          "y": np.asarray(y, dtype="float64")})
    par = bruto.dropna()
    if len(par) < 3 or np.ptp(par["x"]) == 0 or np.ptp(par["y"]) == 0:
        return {"n": len(par), "rho": None, "p": None, "variancia_compartilhada": None,
                "mesmo_constructo": None}
    rho, p = stats.spearmanr(par["x"], par["y"])
    return {"n": len(par), "rho": float(rho), "p": float(p),
            "variancia_compartilhada": float(rho ** 2),
            "mesmo_constructo": bool(abs(rho) >= LIMIAR_MESMO_CONSTRUCTO)}


def juntar_medidas(dora: pd.DataFrame, graphql: pd.DataFrame) -> pd.DataFrame:
    return dora.merge(graphql, on=["owner", "repo"], how="inner")


def correlacao_parcial_spearman(x, y, z) -> dict:
    dados = pd.DataFrame({"x": np.asarray(x, dtype="float64"),
                          "y": np.asarray(y, dtype="float64"),
                          "z": np.asarray(z, dtype="float64")}).dropna()
    n = len(dados)
    if n < 5 or any(np.ptp(dados[c]) == 0 for c in ("x", "y", "z")):
        return {"n": n, "rho": None, "p": None}
    postos = dados.rank()
    rxy = float(postos["x"].corr(postos["y"]))
    rxz = float(postos["x"].corr(postos["z"]))
    ryz = float(postos["y"].corr(postos["z"]))
    denominador = np.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))
    if denominador == 0:
        return {"n": n, "rho": None, "p": None}
    parcial = (rxy - rxz * ryz) / denominador
    if abs(parcial) >= 1:
        return {"n": n, "rho": float(parcial), "p": 0.0}
    t = parcial * np.sqrt((n - 3) / (1 - parcial ** 2))
    return {"n": n, "rho": float(parcial), "p": float(2 * stats.t.sf(abs(t), n - 3))}


def cobertura_entre_amostras(por_amostra: dict) -> dict:
    nomes = [k for k, v in por_amostra.items() if len(v) > 0]
    if len(nomes) < 2:
        return {"amostras": len(nomes), "p_qui2": None, "z_tendencia": None,
                "p_tendencia": None, "difere": None, "tendencia": None}
    tabela = np.array([[int(pd.Series(por_amostra[k]).astype(bool).sum()),
                        int((~pd.Series(por_amostra[k]).astype(bool)).sum())] for k in nomes])
    if (tabela.sum(axis=0) == 0).any():
        return {"amostras": len(nomes), "p_qui2": None, "z_tendencia": None,
                "p_tendencia": None, "difere": None, "tendencia": None}
    _, p_qui2, _, _ = stats.chi2_contingency(tabela)
    n_i = tabela.sum(axis=1)
    sucessos = tabela[:, 0]
    escore = np.arange(len(nomes))
    media = sucessos.sum() / n_i.sum()
    denominador = np.sqrt(media * (1 - media) *
                          ((n_i * escore ** 2).sum() - (n_i * escore).sum() ** 2 / n_i.sum()))
    if denominador == 0:
        return {"amostras": len(nomes), "p_qui2": float(p_qui2), "z_tendencia": None,
                "p_tendencia": None, "difere": bool(p_qui2 < ALFA), "tendencia": None}
    z = float((escore * (sucessos - n_i * media)).sum() / denominador)
    p_tendencia = float(2 * stats.norm.sf(abs(z)))
    return {"amostras": len(nomes), "p_qui2": float(p_qui2), "z_tendencia": z,
            "p_tendencia": p_tendencia, "difere": bool(p_qui2 < ALFA),
            "tendencia": bool(p_tendencia < ALFA)}


def quartis(valores) -> pd.Series:
    serie = pd.Series(np.asarray(valores, dtype="float64"))
    return pd.qcut(serie, 4, labels=list(NIVEIS_QUARTIL), duplicates="drop")


def tabela_confusao(df: pd.DataFrame, x: str, y: str,
                    controles: tuple = CONTROLES_TAMANHO) -> pd.DataFrame:
    agregado = convergencia(df[x], df[y])
    linhas = [{"controle": "nenhum", "estrato": "agregado",
               "n": agregado["n"], "rho": agregado["rho"], "p": agregado["p"]}]
    for coluna, rotulo in controles:
        if coluna not in df:
            continue
        faixa = quartis(df[coluna])
        for nivel in NIVEIS_QUARTIL:
            sub = df[(faixa == nivel).to_numpy()]
            r = convergencia(sub[x], sub[y])
            linhas.append({"controle": rotulo, "estrato": nivel,
                           "n": r["n"], "rho": r["rho"], "p": r["p"]})
        parcial = correlacao_parcial_spearman(df[x], df[y], df[coluna])
        linhas.append({"controle": rotulo, "estrato": "parcial", **parcial})
    tabela = pd.DataFrame(linhas)
    tabela["par"] = f"{x} x {y}"
    return tabela


def diagnostico_confusao(tabela: pd.DataFrame) -> dict:
    agregado = tabela[tabela["estrato"] == "agregado"]["rho"].iloc[0]
    parciais = tabela[tabela["estrato"] == "parcial"]["rho"].dropna()
    estratos = tabela[tabela["estrato"].isin(NIVEIS_QUARTIL)]["rho"].dropna()
    if agregado is None or parciais.empty or estratos.empty:
        return {"rho_agregado": agregado, "maior_queda_parcial": None, "confusao": None}
    queda = float((abs(agregado) - abs(parciais)).max())
    return {
        "rho_agregado": float(agregado),
        "rho_parcial_min": float(parciais.abs().min()),
        "maior_queda_parcial": queda,
        "estratos_mesmo_sinal": bool((np.sign(estratos) == np.sign(agregado)).all()),
        "confusao": bool(queda > abs(agregado) * 0.5),
    }


def tabela_convergencia(df: pd.DataFrame,
                        pares: tuple = PARES_CONVERGENCIA) -> pd.DataFrame:
    linhas = []
    for coluna_dora, coluna_fluxo, rotulo in pares:
        if coluna_dora not in df or coluna_fluxo not in df:
            continue
        linhas.append({"par": rotulo, "dora": coluna_dora, "fluxo": coluna_fluxo,
                       **convergencia(df[coluna_dora], df[coluna_fluxo])})
    tabela = pd.DataFrame(linhas)
    if tabela.empty:
        return tabela
    validos = tabela["p"].notna()
    tabela["p_holm"] = np.nan
    if validos.any():
        tabela.loc[validos, "p_holm"] = multipletests(tabela.loc[validos, "p"], method="holm")[1]
    tabela["associacao"] = pd.array(tabela["p_holm"] < ALFA, dtype="boolean")
    tabela.loc[tabela["p_holm"].isna(), "associacao"] = pd.NA
    return tabela


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m analise.distribuicoes")
    ap.add_argument("--dataset", type=Path, default=Path("data/dataset_dora.csv"))
    ap.add_argument("--runs", type=Path, default=Path("data/eventos/runs.csv.gz"))
    ap.add_argument("--amostras", type=Path, nargs="*",
                    default=[Path("data"), Path("data/amostra2")])
    ap.add_argument("--saida", type=Path, default=Path("analise/saida/tabelas"))
    args = ap.parse_args(argv)

    df = pd.read_csv(args.dataset)
    args.saida.mkdir(parents=True, exist_ok=True)

    combinacao = est.COMBINACOES[0]
    faixas = faixas_dora(est.classificacoes(df, combinacao))
    colunas_da_faixa = (combinacao.frequencia, combinacao.lead_time, combinacao.cfr,
                        "recuperacao_mediana_horas")

    for nome, tabela in (("distribuicoes_normalidade", tabela_normalidade(df)),
                         ("distribuicoes_centro", tabela_centro(df)),
                         ("distribuicoes_contagem", tabela_contagem(df)),
                         ("distribuicoes_discriminancia",
                          tabela_poder_discriminante(df, faixas, colunas_da_faixa))):
        tabela.to_csv(args.saida / f"{nome}.csv", index=False)
        print(f"{args.saida / nome}.csv: {len(tabela)} linha(s)")

    juntadas = [juntar_medidas(pd.read_csv(p / "dataset_dora.csv"),
                               pd.read_csv(p / "medidas_graphql.csv"))
                for p in args.amostras
                if (p / "dataset_dora.csv").exists() and (p / "medidas_graphql.csv").exists()]
    if juntadas:
        conv = tabela_convergencia(pd.concat(juntadas, ignore_index=True))
        conv.to_csv(args.saida / "distribuicoes_convergencia.csv", index=False)
        print(f"{args.saida}/distribuicoes_convergencia.csv: {len(conv)} par(es), "
              f"{int(conv['n'].max())} repositorios")

    conjunto = pd.concat(juntadas, ignore_index=True) if juntadas else df
    confusao = pd.concat([tabela_confusao(conjunto, x, y) for x, y, _ in PARES_RQ05
                          if x in conjunto and y in conjunto], ignore_index=True)
    if not confusao.empty:
        confusao.to_csv(args.saida / "distribuicoes_confusao.csv", index=False)
        print(f"{args.saida}/distribuicoes_confusao.csv: {len(confusao)} linha(s)")

    if args.runs.exists():
        duracoes = duracoes_por_repositorio(pd.read_csv(args.runs))
        por_repo = tabela_weibull(duracoes)
        por_repo.to_csv(args.saida / "distribuicoes_weibull.csv", index=False)
        resumo_weibull(por_repo).to_csv(args.saida / "distribuicoes_weibull_resumo.csv", index=False)
        print(f"{args.saida}/distribuicoes_weibull.csv: {len(por_repo)} repositorio(s)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
