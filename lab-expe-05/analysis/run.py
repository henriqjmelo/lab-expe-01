"""Comando unico do pipeline de analise.

    python analysis/run.py --entrada data/sintetico.csv
    python analysis/run.py --entrada data/pilot.csv
    python analysis/run.py --entrada data/processed/clean.csv --n 30

Troca-se o arquivo de entrada e nada mais: o pipeline le o esquema do
contrato, nao nomes de coluna proprios. As saidas vao para os caminhos que o
contrato (secao 4) promete a A e a B.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from analysis import descritiva, graficos, interacao, io_dados, poder, testes  # noqa: E402

LIMIAR_CV = 0.05   # plano B do contrato, secao 8


def executar(entrada: Path, saida_tabelas: Path, saida_figuras: Path, *,
             n: int | None = None, com_poder: bool = True, bootstrap: bool = True) -> dict:
    df = io_dados.carregar(entrada, n=n)
    validos, falhas = io_dados.aplicar_exclusao(df)
    saida_tabelas.mkdir(parents=True, exist_ok=True)
    saida_figuras.mkdir(parents=True, exist_ok=True)

    tab_descritiva = descritiva.tabela(validos, falhas)
    tab_descritiva.to_csv(saida_tabelas / "descritiva.csv", index=False)

    tab_testes = testes.confirmatorios(validos, bootstrap=bootstrap)
    tab_testes.to_csv(saida_tabelas / "testes.csv", index=False)

    tab_expl = testes.exploratorios(validos, bootstrap=bootstrap)
    tab_expl.to_csv(saida_tabelas / "exploratorias.csv", index=False)

    tab_inter, _ = interacao.tabela(validos)
    tab_inter.to_csv(saida_tabelas / "interacao.csv", index=False)

    tab_poder = poder.tabela() if com_poder else None
    if tab_poder is not None:
        tab_poder.to_csv(saida_tabelas / "poder.csv", index=False)

    figuras = [
        graficos.distribuicao_por_celula(validos, saida_figuras, "exec_ms"),
        graficos.efeitos_com_ic(tab_testes, saida_figuras),
        graficos.ecdf_latencia(validos, saida_figuras),
        graficos.interacao_gc_heap(validos, saida_figuras),
    ]
    if tab_poder is not None:
        figuras.append(graficos.curva_de_poder(tab_poder, saida_figuras))

    return {
        "entrada": entrada,
        "linhas": len(df),
        "validos": len(validos),
        "falhas": len(falhas),
        "descritiva": tab_descritiva,
        "testes": tab_testes,
        "exploratorias": tab_expl,
        "interacao": tab_inter,
        "poder": tab_poder,
        "figuras": [f for f in figuras if f],
        "cv_acima": descritiva.celulas_acima_do_limiar(tab_descritiva, LIMIAR_CV),
    }


def _relatar(r: dict) -> None:
    t = r["testes"]
    print(f"\nentrada: {r['entrada']}")
    print(f"  {r['linhas']} invocacoes | {r['validos']} validas | {r['falhas']} excluidas por falha registrada")

    rodaram = t[t['p'].notna()] if not t.empty else t
    print(f"\nConfirmatorios: {len(rodaram)} testes na familia do Holm "
          f"(sem poder: {len(t) - len(rodaram)})")
    for linha in rodaram.itertuples():
        marca = "*" if linha.significativo else " "
        print(f"  {marca} {linha.metrica:<14} {linha.benchmark:<10} h={linha.heap_mult:<4g} "
              f"{linha.teste:<13} razao={linha.razao:6.3f} "
              f"[{linha.razao_ic_baixo:6.3f}; {linha.razao_ic_alto:6.3f}]  "
              f"p={linha.p:.2e} -> Holm {linha.p_corrigido:.2e}"
              f"{'' if linha.concordam else '  (!) testes discordam'}")

    e = r["exploratorias"]
    if not e.empty:
        n_sig = int(e["significativo"].sum())
        print(f"\nExploratorias (BH, FDR 0,05): {len(e)} testes, {n_sig} com indicio. "
              f"Nenhuma conclusao do trabalho se apoia nelas.")

    rq2 = interacao.resumo_rq2(r["interacao"])
    veredito = "HA interacao" if rq2.get("ha_interacao") else "sem evidencia de interacao"
    print(f"\nRQ2 (GC x heap): {veredito}"
          + (f" | {rq2['termo']}: razao de razoes {rq2['razao_de_razoes']:.4f}, p={rq2['p']:.2e}"
             if "termo" in rq2 else "")
          + (f" | R2 {rq2['r2']:.3f}" if rq2.get("r2") is not None else ""))

    acima = r["cv_acima"]
    if acima.empty:
        print(f"\nPlano B: nenhuma celula com CV acima de {LIMIAR_CV:.0%} no exec_ms.")
    else:
        print(f"\nPlano B: {len(acima)} celula(s) com CV acima de {LIMIAR_CV:.0%} no exec_ms:")
        for linha in acima.itertuples():
            print(f"    {linha.gc:<4} {linha.benchmark:<10} h={linha.heap_mult:<4g} CV={linha.cv:.1%}")

    print("\nfiguras: " + ", ".join(f.name for f in r["figuras"]))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Pipeline de analise do Lab05 (docs/04-plano-analise.md).")
    ap.add_argument("--entrada", type=Path, default=RAIZ / "data" / "sintetico.csv")
    ap.add_argument("--tabelas", type=Path, default=RAIZ / "results" / "tabelas")
    ap.add_argument("--figuras", type=Path, default=RAIZ / "results" / "figures")
    ap.add_argument("--n", type=int, help="blocos esperados por celula (checagem extra do contrato)")
    ap.add_argument("--sem-poder", action="store_true", help="pula a simulacao de poder (mais rapido)")
    ap.add_argument("--sem-bootstrap", action="store_true", help="pula os IC por bootstrap (mais rapido)")
    a = ap.parse_args(argv)

    try:
        r = executar(a.entrada, a.tabelas, a.figuras, n=a.n,
                     com_poder=not a.sem_poder, bootstrap=not a.sem_bootstrap)
    except io_dados.DadosInvalidos as erro:
        print(f"analise interrompida: {erro}", file=sys.stderr)
        return 1
    _relatar(r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
