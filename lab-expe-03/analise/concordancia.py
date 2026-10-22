from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.stats.inter_rater import aggregate_raters, fleiss_kappa

ROTULOS = {
    "tipo_projeto": ("biblioteca_framework", "aplicacao_servico", "ferramenta_cli", "outro"),
    "releases_reais": ("sim", "nao", "incerto"),
    "corretiva": ("sim", "nao"),
}
AVALIADORES = ("henrique", "gabriel", "guilherme")


def _validar_avaliadores(avaliadores: list[pd.DataFrame], chave: list[str], coluna: str) -> pd.DataFrame:
    if len(avaliadores) != 3:
        raise ValueError("A análise exige exatamente três avaliadores independentes.")
    esperados = set(map(tuple, avaliadores[0][chave].itertuples(index=False, name=None)))
    alinhados = []
    categorias = ROTULOS[coluna]
    for indice, avaliador in enumerate(avaliadores):
        faltantes = set(chave + [coluna]) - set(avaliador.columns)
        if faltantes:
            raise ValueError(f"Avaliador {indice + 1}: faltam colunas {sorted(faltantes)}.")
        if avaliador.duplicated(chave).any():
            raise ValueError(f"Avaliador {indice + 1}: há chaves duplicadas em {chave}.")
        atual = set(map(tuple, avaliador[chave].itertuples(index=False, name=None)))
        if atual != esperados:
            raise ValueError(f"Avaliador {indice + 1}: itens diferentes dos demais (faltam ou sobram chaves).")
        rotulos = avaliador[coluna].fillna("").astype(str).str.strip()
        vazios = int(rotulos.eq("").sum())
        if vazios:
            raise ValueError(
                f"Avaliador {AVALIADORES[indice]}: {vazios} rótulos de '{coluna}' estão vazios; "
                "preencha-os por julgamento humano antes de calcular concordância."
            )
        invalidos = sorted(set(rotulos) - set(categorias))
        if invalidos:
            raise ValueError(f"Avaliador {AVALIADORES[indice]}: rótulos inválidos em '{coluna}': {invalidos}.")
        alinhados.append(avaliador.set_index(chave)[coluna].reindex(pd.MultiIndex.from_tuples(
            sorted(esperados), names=chave
        )))
    return pd.concat(alinhados, axis=1, keys=range(3)).reset_index()


def _kappa_dimensao(avaliadores: list[pd.DataFrame], chave: list[str], coluna: str) -> dict:
    alinhados = _validar_avaliadores(avaliadores, chave, coluna)
    categorias = ROTULOS[coluna]
    codigos = {rotulo: indice for indice, rotulo in enumerate(categorias)}
    matriz = alinhados[[0, 1, 2]].apply(lambda serie: serie.map(codigos)).to_numpy(dtype=int)
    prevalencia = np.bincount(matriz.ravel(), minlength=len(categorias)) / matriz.size
    esperado = float(np.square(prevalencia).sum())
    if esperado == 1.0 and np.all((matriz == matriz[:, :1]).all(axis=1)):
        kappa = 1.0
    else:
        contagens, _ = aggregate_raters(matriz, n_cat=len(categorias))
        kappa = float(fleiss_kappa(contagens, method="fleiss"))
    return {
        "dimensao": coluna, "n_itens": len(matriz), "kappa": kappa,
        "interpretacao": interpretar_kappa(kappa),
    }


def interpretar_kappa(kappa: float) -> str:
    if pd.isna(kappa):
        return "indefinida"
    if kappa < 0:
        return "pobre"
    if kappa <= 0.20:
        return "leve"
    if kappa <= 0.40:
        return "razoavel"
    if kappa <= 0.60:
        return "moderada"
    if kappa <= 0.80:
        return "substancial"
    return "quase_perfeita"


def calcular_kappas(
    avaliadores_repos: list[pd.DataFrame], avaliadores_releases: list[pd.DataFrame]
) -> pd.DataFrame:
    linhas = [
        _kappa_dimensao(avaliadores_repos, ["full_name"], "tipo_projeto"),
        _kappa_dimensao(avaliadores_repos, ["full_name"], "releases_reais"),
        _kappa_dimensao(avaliadores_releases, ["full_name", "tag_name"], "corretiva"),
    ]
    return pd.DataFrame(linhas)


def consenso_rotulos(
    avaliadores: list[pd.DataFrame], chave: list[str], coluna: str, decisoes: pd.DataFrame | None = None
) -> pd.DataFrame:
    alinhados = _validar_avaliadores(avaliadores, chave, coluna)
    linhas = []
    for _, linha in alinhados.iterrows():
        chave_valores = {nome: linha[nome] for nome in chave}
        votos = [linha[indice] for indice in range(3)]
        contagem = pd.Series(votos).value_counts()
        consenso = contagem.index[0] if contagem.iloc[0] >= 2 else ""
        linhas.append({
            **chave_valores, coluna: consenso,
            "discussao_necessaria": not bool(consenso),
            "justificativa": "" if consenso else "Três rótulos distintos; decisão humana em reunião necessária.",
        })
    resultado = pd.DataFrame(linhas)
    if decisoes is not None and not decisoes.empty:
        colunas_decisao = chave + [coluna, "justificativa"]
        if set(colunas_decisao) - set(decisoes.columns):
            raise ValueError(f"As decisões manuais devem conter {colunas_decisao}.")
        if decisoes.duplicated(chave).any():
            raise ValueError("Há mais de uma decisão manual para o mesmo item.")
        decisoes = decisoes[colunas_decisao].copy()
        if decisoes[coluna].isna().any() or not decisoes[coluna].isin(ROTULOS[coluna]).all():
            raise ValueError(f"As decisões manuais devem usar rótulos válidos para '{coluna}'.")
        if decisoes["justificativa"].fillna("").astype(str).str.strip().eq("").any():
            raise ValueError("Toda decisão manual precisa registrar uma justificativa.")
        resultado = resultado.drop(columns=["justificativa"]).merge(
            decisoes, on=chave, how="left", suffixes=("", "_manual")
        )
        tem_decisao = resultado[f"{coluna}_manual"].notna()
        resultado.loc[tem_decisao, coluna] = resultado.loc[tem_decisao, f"{coluna}_manual"]
        resultado.loc[tem_decisao, "discussao_necessaria"] = False
        resultado.loc[tem_decisao, "justificativa"] = resultado.loc[tem_decisao, "justificativa_manual"]
        resultado = resultado.drop(columns=[f"{coluna}_manual", "justificativa_manual"])
    return resultado


def _ler_rotulos(pasta: Path, dimensao: str) -> list[pd.DataFrame]:
    return [pd.read_csv(pasta / f"rotulos_{nome}_{dimensao}.csv", dtype=str) for nome in AVALIADORES]


def executar(pasta: Path = Path("validacao")) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    repos = _ler_rotulos(pasta, "repos")
    releases = _ler_rotulos(pasta, "releases")
    kappas = calcular_kappas(repos, releases)
    decisoes_repos = pasta / "decisoes_consenso_repos.csv"
    decisoes = pd.read_csv(decisoes_repos) if decisoes_repos.exists() else pd.DataFrame()
    consensos_repos = []
    for coluna in ("tipo_projeto", "releases_reais"):
        decisao_dimensao = decisoes[decisoes["dimensao"] == coluna].rename(columns={"rotulo": coluna})[
            ["full_name", coluna, "justificativa"]
        ] if not decisoes.empty else None
        consensos_repos.append(consenso_rotulos(repos, ["full_name"], coluna, decisao_dimensao))
    consenso_repos = consensos_repos[0].merge(
        consensos_repos[1], on="full_name", suffixes=("_tipo", "_releases")
    )
    consenso_releases = consenso_rotulos(releases, ["full_name", "tag_name"], "corretiva")
    kappas.to_csv(pasta / "kappa_fleiss.csv", index=False)
    consenso_repos.to_csv(pasta / "consenso_repos.csv", index=False)
    consenso_releases.to_csv(pasta / "consenso_releases.csv", index=False)
    return kappas, consenso_repos, consenso_releases


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m analise.concordancia")
    parser.add_argument("--pasta", type=Path, default=Path("validacao"))
    args = parser.parse_args(argv)
    kappas, consenso_repos, consenso_releases = executar(args.pasta)
    print(kappas.to_string(index=False))
    print(f"Consenso: {len(consenso_repos)} repositórios, {len(consenso_releases)} releases")
    print(f"Itens que exigem decisão manual: {int(consenso_repos['discussao_necessaria'].sum())} repositórios e "
          f"{int(consenso_releases['discussao_necessaria'].sum())} releases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())