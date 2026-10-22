import numpy as np
import pandas as pd
import pytest

from analise.concordancia import calcular_kappas, consenso_rotulos


def avaliadores_repos(votos):
    return [
        pd.DataFrame({
            "full_name": [f"o/r{i}" for i in range(len(votos))],
            "tipo_projeto": [v[j] for v in votos],
            "releases_reais": ["sim"] * len(votos),
        })
        for j in range(3)
    ]


def avaliadores_releases(votos):
    return [
        pd.DataFrame({
            "full_name": [f"o/r{i}" for i in range(len(votos))], "tag_name": [f"v{i}" for i in range(len(votos))],
            "corretiva": [v[j] for v in votos],
        })
        for j in range(3)
    ]


def test_fleiss_kappa_e_um_com_concordancia_total():
    repos = avaliadores_repos([("outro", "outro", "outro")] * 4)
    releases = avaliadores_releases([("sim", "sim", "sim")] * 4)

    resultado = calcular_kappas(repos, releases)

    assert np.allclose(resultado["kappa"], 1.0)


def test_fleiss_kappa_fica_proximo_de_zero_com_rotulos_aleatorios():
    rng = np.random.default_rng(42)
    categorias = np.array(["biblioteca_framework", "aplicacao_servico", "ferramenta_cli", "outro"])
    votos = [tuple(rng.choice(categorias, size=3, replace=True)) for _ in range(300)]
    repos = avaliadores_repos(votos)
    releases = avaliadores_releases([("sim", "nao", "sim")] * 300)

    resultado = calcular_kappas(repos, releases)

    assert abs(resultado.loc[0, "kappa"]) < 0.1


def test_consenso_resolve_maioria_e_sinaliza_tres_rotulos_distintos():
    avaliadores = avaliadores_repos([
        ("outro", "outro", "biblioteca_framework"),
        ("outro", "biblioteca_framework", "ferramenta_cli"),
    ])

    resultado = consenso_rotulos(avaliadores, ["full_name"], "tipo_projeto")

    assert resultado.loc[0, "tipo_projeto"] == "outro"
    assert not resultado.loc[0, "discussao_necessaria"]
    assert resultado.loc[1, "tipo_projeto"] == ""
    assert resultado.loc[1, "discussao_necessaria"]


def test_kappa_nao_calcula_com_rotulos_pendentes():
    repos = avaliadores_repos([("", "outro", "outro")])
    releases = avaliadores_releases([("sim", "sim", "sim")])

    with pytest.raises(ValueError, match="rótulos.*vazios"):
        calcular_kappas(repos, releases)