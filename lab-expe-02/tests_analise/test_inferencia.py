"""Testes de src/inferencia.py com entradas SINTETICAS, so para checar o codigo.

Nenhum valor daqui e dado do experimento. Os numeros foram escolhidos para que o
resultado correto seja conhecido de antemao (postos calculados a mao).
Rodar da pasta lab-expe-02: python -m pytest tests_analise
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import inferencia as inf  # noqa: E402


def trial(kata, trat, valor, campo="tempo_s", censurado=0):
    return {"kata": kata, "tratamento": trat, campo: valor, "censurado": censurado}


def seis_pares_todos_menores():
    trials = []
    for i, kata in enumerate(("k1", "k2", "k3", "k4", "k5", "k6"), start=1):
        trials.append(trial(kata, "com-ia", 100 * i))
        trials.append(trial(kata, "sem-ia", 100 * i + 10 * i))
    return trials


def test_pares_usam_mediana_por_kata():
    trials = [
        trial("k1", "com-ia", 10), trial("k1", "sem-ia", 30),
        trial("k1", "sem-ia", 50), trial("k1", "sem-ia", 90),
    ]
    pares, sem_par = inf.montar_pares(trials, "tempo_s")
    assert sem_par == []
    assert pares[0]["com_ia"] == 10 and pares[0]["sem_ia"] == 50 and pares[0]["diferenca"] == -40


def test_kata_com_um_so_tratamento_nao_forma_par():
    pares, sem_par = inf.montar_pares([trial("k1", "com-ia", 10), trial("k2", "sem-ia", 20)], "tempo_s")
    assert pares == [] and sem_par == ["k1", "k2"]


def test_seis_pares_na_mesma_direcao_chegam_ao_p_minimo():
    pares, _ = inf.montar_pares(seis_pares_todos_menores(), "tempo_s")
    r = inf.testar(pares, "less")
    assert r["n_pares"] == 6
    assert abs(r["p_valor"] - 0.015625) < 1e-4
    assert r["rank_biserial"] == -1.0


def test_bilateral_com_seis_pares_da_0_03125():
    pares, _ = inf.montar_pares(seis_pares_todos_menores(), "tempo_s")
    assert abs(inf.testar(pares, "two-sided")["p_valor"] - 0.03125) < 1e-4


def test_direcao_contraria_nao_rejeita():
    pares, _ = inf.montar_pares(seis_pares_todos_menores(), "tempo_s")
    assert inf.testar(pares, "greater")["p_valor"] > 0.9


def test_poucos_pares_nao_chamam_o_teste():
    trials = seis_pares_todos_menores()[:8]  # 4 katas
    pares, _ = inf.montar_pares(trials, "tempo_s")
    r = inf.testar(pares, "less")
    assert r["p_valor"] == "" and "sem teste" in r["conclusao"]


def test_diferencas_todas_nulas_nao_chamam_o_teste():
    trials = []
    for kata in ("k1", "k2", "k3", "k4", "k5", "k6"):
        trials += [trial(kata, "com-ia", 2100), trial(kata, "sem-ia", 2100)]
    pares, _ = inf.montar_pares(trials, "tempo_s")
    assert "todas as diferencas sao nulas" in inf.testar(pares, "less")["conclusao"]


def test_censura_e_contada_nos_pares():
    trials = seis_pares_todos_menores()
    trials[1]["censurado"] = 1
    pares, _ = inf.montar_pares(trials, "tempo_s")
    assert sum(p["trials_censurados"] for p in pares) == 1


def test_trial_sem_metrica_fica_fora_do_par():
    trials = [trial("k1", "com-ia", None, "mi"), trial("k1", "sem-ia", 50.0, "mi")]
    pares, sem_par = inf.montar_pares(trials, "mi")
    assert pares == [] and sem_par == ["k1"]
