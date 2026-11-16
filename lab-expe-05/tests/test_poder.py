"""A simulacao de poder - o reuso direto do Lab04.

Estes testes conferem as duas coisas que a simulacao precisa acertar: quando
nao ha efeito, o teste erra na taxa que promete (alfa); quando ha, ele acha.
"""
import pytest

from analysis import poder


def test_sem_efeito_a_taxa_de_rejeicao_bate_com_alfa():
    r = poder.erro_tipo_i(n=30, cv=0.05, repeticoes=10_000)
    # margem de Monte Carlo com 10 mil repeticoes: ~0,4 p.p.
    assert r["welch"] == pytest.approx(0.05, abs=0.006)
    assert r["mann_whitney"] == pytest.approx(0.05, abs=0.006)


def test_o_poder_cresce_com_o_n():
    t = poder.tabela(cvs=(0.05,), ns=(20, 30, 40, 50), repeticoes=3000)
    valores = t.sort_values("n")["poder_welch_alfa"].tolist()
    assert valores == sorted(valores)
    assert valores[0] < valores[-1]


def test_o_poder_cai_quando_o_ruido_sobe():
    t = poder.tabela(cvs=(0.02, 0.05, 0.08), ns=(30,), repeticoes=3000)
    valores = t.sort_values("cv")["poder_welch_alfa"].tolist()
    assert valores == sorted(valores, reverse=True)


def test_a_correcao_de_holm_custa_poder():
    t = poder.tabela(cvs=(0.05,), ns=(30,), repeticoes=3000).iloc[0]
    assert t["poder_welch_holm_pior"] < t["poder_welch_alfa"]


def test_o_welch_tem_mais_poder_que_o_mann_whitney_em_dado_lognormal():
    """O preco de nao supor distribuicao: alguns pontos de poder."""
    t = poder.tabela(cvs=(0.05,), ns=(30,), repeticoes=3000).iloc[0]
    assert t["poder_mw_alfa"] < t["poder_welch_alfa"]


def test_reproduz_os_numeros_do_plano_de_analise():
    """Fixa a tabela da secao 9.2 do plano: se mudar, o documento mente."""
    t = poder.tabela(cvs=(0.05, 0.08), ns=(30,)).set_index(["cv", "n"])
    assert t.loc[(0.05, 30), "poder_welch_alfa"] == pytest.approx(0.960, abs=0.002)
    assert t.loc[(0.05, 30), "poder_welch_holm_pior"] == pytest.approx(0.778, abs=0.002)
    assert t.loc[(0.08, 30), "poder_welch_holm_pior"] == pytest.approx(0.274, abs=0.002)


def test_n_necessario_cresce_com_o_cv():
    assert poder.n_para_poder(0.02, repeticoes=1500) <= poder.n_para_poder(0.05, repeticoes=1500)
