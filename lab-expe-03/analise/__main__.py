from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from analise import caracterizacao as car
from analise import estatisticas as est
from analise import graficos as g


def gerar(df: pd.DataFrame, funil: pd.DataFrame | None, pasta: Path, rotulo: str) -> list[Path]:
    g.ROTULO_AMOSTRA = rotulo
    figuras, tabelas = pasta / "figuras", pasta / "tabelas"
    tabelas.mkdir(parents=True, exist_ok=True)

    resumo = est.resumo(df)
    dist = est.distribuicao_categorias(df)
    rq05 = est.rq05(df)
    rq06 = est.rq06(df)
    completos, rq07 = est.rq07(df)
    for nome, tabela in (("resumo", resumo), ("perfil_dora", dist), ("rq05_spearman", rq05),
                         ("rq06_kruskal", rq06), ("rq07_pares", rq07), ("rq07_categorias", completos)):
        tabela.to_csv(tabelas / f"{nome}.csv", index=False)

    gerados = [] if funil is None else [g.fig_funil(funil, figuras / "fig01_funil.png")]
    gerados += [
        g.fig_rq01(df, figuras / "fig02_rq01_frequencia.png"),
        g.fig_rq02(df, figuras / "fig03_rq02_lead_time.png"),
        g.fig_rq03(df, figuras / "fig04_rq03_cfr.png"),
        g.fig_rq04(df, figuras / "fig05_rq04_recuperacao.png"),
        g.fig_perfil(dist, figuras / "fig06_perfil_dora.png"),
        g.fig_rq05(df, rq05, figuras / "fig07_rq05_velocidade_estabilidade.png"),
        g.fig_rq06(rq06, figuras / "fig08_rq06_fatores.png"),
        g.fig_rq07(completos, rq07, figuras / "fig09_rq07_sensibilidade.png"),
    ]
    if "cfr_c_revert" in df.columns:
        est.resumo_alternativas(df).to_csv(tabelas / "medidas_alternativas.csv", index=False)
        gerados += [
            g.fig_cfr_proxies(df, figuras / "fig13_cfr_proxies.png"),
            g.fig_feedback_ci(df, figuras / "fig14_feedback_ci.png"),
            g.fig_distribuicao_trabalho(df, figuras / "fig15_distribuicao_trabalho.png"),
        ]
    return gerados


def tabela_estimativas(niveis: list[tuple[str, pd.DataFrame]]) -> pd.DataFrame:
    linhas = []
    for (coluna, rotulo) in est.METRICAS:
        linha = {"metrica": rotulo}
        for nome, df in niveis:
            v = df[coluna].dropna()
            lo, hi = est.ic_bootstrap_mediana(v)
            linha |= {f"n_{nome}": len(v), f"mediana_{nome}": v.median(), f"q1_{nome}": v.quantile(0.25),
                      f"q3_{nome}": v.quantile(0.75), f"ic_lo_{nome}": lo, f"ic_hi_{nome}": hi}
        linhas.append(linha)
    return pd.DataFrame(linhas)


def acumular(a1: pd.DataFrame, extras: list[pd.DataFrame]) -> list[tuple[str, pd.DataFrame, str]]:
    niveis = [(str(len(a1)), a1, "A1")]
    acumulado = a1
    for i, extra in enumerate(extras, start=2):
        acumulado = pd.concat([acumulado, extra], ignore_index=True)
        niveis.append((str(len(acumulado)), acumulado, " + ".join(f"A{j}" for j in range(1, i + 1))))
    return niveis


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m analise")
    ap.add_argument("--dados", type=Path, default=Path("data/dataset_dora.csv"))
    ap.add_argument("--funil", type=Path, default=Path("data/funil.csv"))
    ap.add_argument("--extra", type=Path, nargs="*",
                    default=[Path("data/amostra2/dataset_dora.csv"),
                             Path("data/amostra3/dataset_dora.csv")],
                    help="datasets das amostras seguintes (A2, A3...), somados a amostra 1")
    ap.add_argument("--saida", type=Path, default=Path("analise/saida"))
    args = ap.parse_args(argv)

    g.estilo()
    a1 = est.carregar_com_alternativas(args.dados)
    gerados = gerar(a1, pd.read_csv(args.funil), args.saida, f"Amostra 1 · n = {len(a1)}")

    extras = [est.carregar_com_alternativas(p) for p in args.extra if p.exists()]
    if extras:
        niveis = acumular(a1, extras)
        for rotulo_n, acumulado, nomes in niveis[1:]:
            gerados += gerar(acumulado, None, args.saida / rotulo_n, f"{nomes} · n = {rotulo_n}")

        comparacao = args.saida / "comparacao"
        (comparacao / "tabelas").mkdir(parents=True, exist_ok=True)
        figuras = comparacao / "figuras"
        g.ROTULO_AMOSTRA = ""
        faixa = "_".join(r for r, _, _ in niveis)
        tabela_estimativas([(r, d) for r, d, _ in niveis]).to_csv(
            comparacao / "tabelas" / f"estimativas_{faixa}.csv", index=False)
        legenda = " · ".join(f"{r} = {nomes}" for r, _, nomes in niveis)
        gerados.append(g.fig_comparacao_medianas(
            [(r, d) for r, d, _ in niveis], figuras / f"fig12_convergencia_{faixa}.png",
            titulo=f"As estimativas se mantêm de {niveis[0][0]} para {niveis[-1][0]} repositórios?",
            sub=f"Mediana com IC de 95% (bootstrap) · {legenda}",
        ))
        a2 = extras[0]
        teste = est.mann_whitney_amostras(a1, a2)
        teste.to_csv(comparacao / "tabelas" / "a1_x_a2_mann_whitney.csv", index=False)
        gerados += [
            g.fig_comparacao_ecdf(a1, a2, teste, figuras / "fig10_a1_x_a2_ecdf.png"),
            g.fig_comparacao_medianas(
                [("A1", a1), ("A2", a2)], figuras / "fig11_a1_x_a2_medianas.png",
                titulo="Amostras independentes: medianas da A1 × A2",
                sub="Mediana com IC de 95% (bootstrap) · A1 = amostra 1, A2 = amostra 2 (sem repositórios em comum)",
            ),
        ]
        funil_a2 = args.extra[0].parent / "funil.csv"
        if funil_a2.exists():
            g.ROTULO_AMOSTRA = f"Amostra 2 · n = {len(a2)}"
            gerados.append(g.fig_funil(pd.read_csv(funil_a2), figuras / "fig01b_funil_a2.png"))

    gerados += car.executar(
        args.dados.parent / "candidatos.csv", args.dados, args.dados.parent / "descartes.csv",
        args.extra[0] if args.extra and args.extra[0].exists() else Path("data/amostra2/dataset_dora.csv"),
        args.saida / "caracterizacao",
    )

    for caminho in gerados:
        print(caminho)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
