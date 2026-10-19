from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from analise.distribuicoes import (
    ajuste_binomial_negativa,
    ajuste_weibull,
    centro,
    dispersao,
    duracoes_por_repositorio,
    faixas_dora,
    medias_amostrais,
    normalidade,
    poder_discriminante,
    resumo_weibull,
    tabela_centro,
    tabela_contagem,
    tabela_normalidade,
    tabela_poder_discriminante,
    tabela_weibull,
    tipo_do_atributo,
)


def test_dispersao_reconhece_amostra_compativel_com_poisson():
    amostra = np.random.default_rng(7).poisson(4.0, size=400)
    r = dispersao(amostra)
    assert r["n"] == 400
    assert r["indice"] == pytest.approx(1.0, abs=0.25)
    assert r["compativel_poisson"] is True


def test_dispersao_rejeita_amostra_superdispersa():
    amostra = [1] * 150 + [500] * 150
    r = dispersao(amostra)
    assert r["indice"] > 50
    assert r["p"] < 0.05
    assert r["compativel_poisson"] is False


def test_dispersao_sem_dados_nao_quebra():
    r = dispersao([])
    assert r["n"] == 0
    assert r["indice"] is None


def test_binomial_negativa_so_se_aplica_com_superdispersao():
    assert ajuste_binomial_negativa([1] * 10 + [100] * 10)["aplicavel"] is True
    assert ajuste_binomial_negativa([3, 3, 3, 3])["aplicavel"] is False


def test_binomial_negativa_recupera_os_parametros_pelo_momento():
    r = ajuste_binomial_negativa([0, 1, 2, 10, 20, 40])
    media, variancia = r["media"], r["variancia"]
    assert r["r"] == pytest.approx(media ** 2 / (variancia - media))
    assert r["p"] == pytest.approx(media / variancia)


def test_weibull_identifica_taxa_constante_na_exponencial():
    amostra = np.random.default_rng(11).exponential(5.0, size=800)
    r = ajuste_weibull(amostra)
    assert r["forma"] == pytest.approx(1.0, abs=0.12)
    assert r["regime"] == "constante"


def test_weibull_identifica_taxa_crescente():
    amostra = np.random.default_rng(3).weibull(2.5, size=800) * 10
    assert ajuste_weibull(amostra)["regime"] == "crescente"


def test_weibull_descarta_zeros_e_poucos_dados():
    assert ajuste_weibull([0, 0, 0])["forma"] is None
    assert ajuste_weibull([1.0, 2.0])["forma"] is None


def test_normalidade_aceita_normal_e_rejeita_assimetrica():
    rng = np.random.default_rng(5)
    assert normalidade(rng.normal(10, 2, size=300))["normal"] is True
    assimetrica = normalidade(rng.lognormal(0, 1.5, size=300))
    assert assimetrica["normal"] is False
    assert assimetrica["assimetria"] > 1


def test_centro_mede_o_arrasto_da_cauda():
    r = centro([1, 1, 1, 1, 1000])
    assert r["mediana"] == 1
    assert r["razao_media_mediana"] == pytest.approx(200.8)
    assert r["maximo"] == 1000


def test_centro_sem_dados_nao_quebra():
    assert centro([])["n"] == 0


def test_poder_discriminante_separa_grupos_distintos():
    r = poder_discriminante({"a": [1, 2, 3, 4], "b": [100, 200, 300, 400]})
    assert r["discrimina"] is True
    assert r["epsilon2"] > 0.5


def test_poder_discriminante_nao_separa_grupos_iguais():
    r = poder_discriminante({"a": [1, 2, 3, 4, 5, 6], "b": [1, 2, 3, 4, 5, 6]})
    assert r["discrimina"] is False


def test_poder_discriminante_com_um_grupo_so():
    assert poder_discriminante({"a": [1, 2, 3]})["h"] is None


def test_medias_amostrais_centram_na_media_da_populacao():
    populacao = np.random.default_rng(9).lognormal(0, 1.2, size=500)
    medias = medias_amostrais(populacao, tamanho=50, repeticoes=2000, semente=1)
    assert len(medias) == 2000
    assert medias.mean() == pytest.approx(populacao.mean(), rel=0.05)
    assert medias.std() < populacao.std()


def test_medias_amostrais_sao_reprodutiveis_pela_semente():
    v = [1.0, 5.0, 9.0, 40.0]
    assert np.array_equal(medias_amostrais(v, 3, 50, 42), medias_amostrais(v, 3, 50, 42))


def test_duracoes_por_repositorio_agrupa_episodios():
    runs = pd.DataFrame([
        {"owner": "o", "repo": "r", "workflow_id": 1, "conclusion": "success",
         "run_started_at": "2026-01-01T09:00:00Z", "updated_at": "2026-01-01T09:05:00Z"},
        {"owner": "o", "repo": "r", "workflow_id": 1, "conclusion": "failure",
         "run_started_at": "2026-01-01T10:00:00Z", "updated_at": "2026-01-01T10:10:00Z"},
        {"owner": "o", "repo": "r", "workflow_id": 1, "conclusion": "success",
         "run_started_at": "2026-01-01T11:00:00Z", "updated_at": "2026-01-01T12:00:00Z"},
    ])
    duracoes = duracoes_por_repositorio(runs)
    assert duracoes[("o", "r")] == pytest.approx([2.0])


def test_tabelas_saem_com_uma_linha_por_metrica():
    df = pd.DataFrame({
        "df_release_semana": [0.2, 0.5, 1.0, 3.0, 9.0, 0.3, 0.4, 0.8],
        "lt_a_release_dias": [1.0, 4.0, 9.0, 30.0, 120.0, 2.0, 5.0, 7.0],
        "n_release": [2, 5, 9, 40, 300, 3, 4, 8],
        "estrelas": [10, 20, 30, 40, 50, 60, 70, 80],
    })
    assert len(tabela_normalidade(df)) == 2
    assert len(tabela_centro(df)) == 2
    assert len(tabela_contagem(df)) == 1
    assert tabela_contagem(df)["coluna"].iloc[0] == "n_release"


def test_tabela_normalidade_traz_tambem_o_teste_no_log():
    df = pd.DataFrame({"df_release_semana": list(np.random.default_rng(2).lognormal(0, 1, 200))})
    linha = tabela_normalidade(df).iloc[0]
    assert bool(linha["normal"]) is False
    assert bool(linha["normal_log"]) is True
    assert abs(linha["assimetria_log"]) < abs(linha["assimetria"])


def test_tabela_poder_discriminante_usa_as_faixas():
    df = pd.DataFrame({"estrelas": [1, 2, 3, 400, 500, 600],
                       "contribuidores": [1, 1, 1, 1, 1, 1]})
    faixas = pd.Series(["Low", "Low", "Low", "Elite", "Elite", "Elite"])
    tabela = tabela_poder_discriminante(df, faixas).set_index("coluna")
    assert bool(tabela.loc["estrelas", "discrimina"]) is True
    assert bool(tabela.loc["contribuidores", "discrimina"]) is False
    assert pd.isna(tabela.loc["contribuidores", "h"])


def test_resumo_weibull_agrega_os_regimes():
    por_repo = tabela_weibull({
        ("o", "a"): list(np.random.default_rng(1).exponential(4.0, size=200)),
        ("o", "b"): list(np.random.default_rng(2).weibull(3.0, size=200) * 8),
    })
    resumo = resumo_weibull(por_repo)
    assert resumo["n_repositorios"].iloc[0] == 2
    assert resumo["prop_crescente"].iloc[0] == pytest.approx(0.5)


def test_resumo_weibull_vazio():
    assert resumo_weibull(pd.DataFrame()).empty


def test_tipo_do_atributo_separa_controle_de_convergente_e_independente():
    da_faixa = ("df_release_semana", "lt_a_release_dias")
    assert tipo_do_atributo("df_release_semana", da_faixa) == "controle"
    assert tipo_do_atributo("lt_b_release_dias", da_faixa) == "operacionalizacao"
    assert tipo_do_atributo("estrelas", da_faixa) == "independente"


def test_tipo_muda_quando_a_combinacao_muda():
    assert tipo_do_atributo("lt_b_release_dias", ("lt_b_release_dias",)) == "controle"
    assert tipo_do_atributo("lt_b_release_dias", ("lt_a_release_dias",)) == "operacionalizacao"


def test_faixas_dora_traduz_os_codigos():
    faixas = faixas_dora(pd.DataFrame({"geral": [1, 2, 3, 4]}))
    assert list(faixas) == ["Elite", "High", "Medium", "Low"]


def test_discriminancia_corrige_por_holm_e_deixa_o_controle_de_fora():
    rng = np.random.default_rng(4)
    n = 80
    faixas = pd.Series(["Elite", "Low"] * (n // 2))
    df = pd.DataFrame({
        "df_release_semana": np.where(faixas == "Elite", rng.normal(9, 1, n), rng.normal(1, 1, n)),
        "estrelas": rng.normal(100, 30, n),
        "contribuidores": rng.normal(50, 10, n),
        "idade_anos": rng.normal(5, 2, n),
    })
    tabela = tabela_poder_discriminante(df, faixas, ("df_release_semana",)).set_index("coluna")

    assert tabela.loc["df_release_semana", "tipo"] == "controle"
    assert pd.isna(tabela.loc["df_release_semana", "p_holm"])
    assert pd.isna(tabela.loc["df_release_semana", "separa"])

    independentes = tabela[tabela["tipo"] == "independente"]
    assert (independentes["p_holm"] >= independentes["p"]).all()
    assert not independentes["separa"].any()


def test_discriminancia_marca_separacao_real():
    faixas = pd.Series(["Elite"] * 40 + ["Low"] * 40)
    df = pd.DataFrame({"estrelas": list(range(40)) + list(range(5000, 5040))})
    linha = tabela_poder_discriminante(df, faixas).iloc[0]
    assert linha["tipo"] == "independente"
    assert bool(linha["separa"]) is True
    assert linha["epsilon2"] > 0.5
