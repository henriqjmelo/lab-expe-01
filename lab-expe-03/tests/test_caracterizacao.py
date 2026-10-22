import numpy as np
import pandas as pd

from analise.caracterizacao import comparar_amostras, magnitude_delta, situacao_candidatos


def test_situacao_candidatos_classifica_aceitos_descartados_e_nao_avaliados():
    candidatos = pd.DataFrame({
        "full_name": ["a/aceito", "b/actions", "c/releases", "d/runs", "e/pendente"],
        "estrelas": [100, 90, 80, 70, 60],
    })
    aceitos = pd.DataFrame({"owner": ["a"], "repo": ["aceito"]})
    descartes = pd.DataFrame({
        "full_name": ["b/actions", "c/releases", "d/runs"],
        "etapa": ["com_actions", "min_5_releases", "min_50_runs"],
    })

    resultado = situacao_candidatos(candidatos, aceitos, descartes)

    assert resultado["situacao"].tolist() == [
        "aceito", "descartado_com_actions", "descartado_min_5_releases",
        "descartado_min_50_runs", "nao_avaliado",
    ]


def test_comparacao_a1_a2_aplica_holm_e_cliff_delta():
    a1 = pd.DataFrame({
        "estrelas": [1, 2, 3, 4], "criado_em": ["2020-01-01"] * 4,
        "linguagem": ["Python"] * 4,
    })
    a2 = pd.DataFrame({
        "estrelas": [100, 110, 120, 130], "criado_em": ["2025-01-01"] * 4,
        "linguagem": ["Rust"] * 4,
    })

    resultado = comparar_amostras(a1, a2)
    estrelas = resultado.set_index("variavel").loc["Estrelas"]
    idade = resultado.set_index("variavel").loc["Idade (anos)"]

    assert estrelas["p"] < 0.05
    assert abs(estrelas["delta_cliff"]) >= 0.474
    assert estrelas["p_holm"] >= estrelas["p"]
    assert idade["p_holm"] >= idade["p"]


def test_delta_de_cliff_desprezivel_para_amostras_identicas():
    amostra = pd.DataFrame({
        "estrelas": [10, 20, 30, 40], "idade_anos": [1, 2, 3, 4],
        "linguagem": ["Go", "Rust", "Python", "Java"],
    })

    resultado = comparar_amostras(amostra, amostra)

    assert np.isclose(resultado.loc[resultado["variavel"] == "Estrelas", "delta_cliff"].iloc[0], 0)
    assert magnitude_delta(0.0) == "desprezivel"