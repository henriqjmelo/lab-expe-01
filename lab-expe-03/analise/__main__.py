from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from analise import estatisticas as est
from analise import graficos as g


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m analise")
    ap.add_argument("--dados", type=Path, default=Path("data/dataset_dora.csv"))
    ap.add_argument("--funil", type=Path, default=Path("data/funil.csv"))
    ap.add_argument("--comparar", type=Path, help="dataset de uma segunda amostra")
    ap.add_argument("--saida", type=Path, default=Path("analise/saida"))
    args = ap.parse_args(argv)

    g.estilo()
    df = est.carregar(args.dados)
    figuras, tabelas = args.saida / "figuras", args.saida / "tabelas"
    tabelas.mkdir(parents=True, exist_ok=True)

    resumo = est.resumo(df)
    dist = est.distribuicao_categorias(df)
    rq05 = est.rq05(df)
    rq06 = est.rq06(df)
    completos, rq07 = est.rq07(df)
    for nome, tabela in (("resumo", resumo), ("perfil_dora", dist), ("rq05_spearman", rq05),
                         ("rq06_kruskal", rq06), ("rq07_pares", rq07), ("rq07_categorias", completos)):
        tabela.to_csv(tabelas / f"{nome}.csv", index=False)

    gerados = [
        g.fig_funil(pd.read_csv(args.funil), figuras / "fig01_funil.png"),
        g.fig_rq01(df, figuras / "fig02_rq01_frequencia.png"),
        g.fig_rq02(df, figuras / "fig03_rq02_lead_time.png"),
        g.fig_rq03(df, figuras / "fig04_rq03_cfr.png"),
        g.fig_rq04(df, figuras / "fig05_rq04_recuperacao.png"),
        g.fig_perfil(dist, figuras / "fig06_perfil_dora.png"),
        g.fig_rq05(df, rq05, figuras / "fig07_rq05_velocidade_estabilidade.png"),
        g.fig_rq06(rq06, figuras / "fig08_rq06_fatores.png"),
        g.fig_rq07(completos, rq07, figuras / "fig09_rq07_sensibilidade.png"),
    ]

    if args.comparar:
        b = est.carregar(args.comparar)
        comparacao = est.mann_whitney_amostras(df, b)
        comparacao.to_csv(tabelas / "comparacao_amostras.csv", index=False)
        gerados += [
            g.fig_comparacao_ecdf(df, b, comparacao, figuras / "fig10_amostras_ecdf.png"),
            g.fig_comparacao_medianas(df, b, figuras / "fig11_amostras_medianas.png"),
        ]

    for caminho in gerados:
        print(caminho)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
