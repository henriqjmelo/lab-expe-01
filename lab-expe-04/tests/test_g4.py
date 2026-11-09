import matplotlib.pyplot as plt
import pandas as pd

from src.graficos import curvas_do_g4, troca_de_vantagem


def simulacao(taxas: dict) -> pd.DataFrame:
    """taxas: {(situacao, teste): {r_latente: taxa_005}} -> o formato dos results/situacao_*.csv."""
    linhas = [
        {"situacao": situacao, "teste": teste, "r_latente": r, "taxa_005": taxa,
         "taxa_001": taxa / 3, "n": 30, "repeticoes": 10_000}
        for (situacao, teste), por_efeito in taxas.items()
        for r, taxa in por_efeito.items()
    ]
    return pd.DataFrame(linhas)


def test_situacoes_com_os_mesmos_numeros_viram_uma_curva_so():
    # E o caso do Spearman: exp() nao muda os postos, entao A e B dao o mesmo resultado.
    dados = simulacao({
        ("A", "Pearson"): {0.0: 0.05, 0.5: 0.82},
        ("B", "Pearson"): {0.0: 0.05, 0.5: 0.48},
        ("A", "Spearman"): {0.0: 0.05, 0.5: 0.77},
        ("B", "Spearman"): {0.0: 0.05, 0.5: 0.77},
    })
    curvas = curvas_do_g4(dados)
    por_teste = {c["teste"]: c for c in curvas if len(c["situacoes"]) > 1}

    assert len(curvas) == 3, "o Spearman nao pode virar duas linhas sobrepostas"
    assert por_teste["Spearman"]["situacoes"] == ["A", "B"]
    assert "idênticas" in por_teste["Spearman"]["rotulo"]
    assert "Pearson" not in por_teste


def test_situacoes_diferentes_continuam_com_uma_curva_cada():
    dados = simulacao({
        ("A", "Pearson"): {0.0: 0.05, 0.5: 0.82},
        ("B", "Pearson"): {0.0: 0.05, 0.5: 0.48},
    })
    curvas = curvas_do_g4(dados)

    assert len(curvas) == 2
    assert {c["traco"] for c in curvas} == {"-", "--"}


def test_troca_de_vantagem_acha_o_primeiro_efeito_em_que_o_spearman_passa():
    dados = simulacao({
        ("B", "Pearson"): {0.0: 0.05, 0.1: 0.09, 0.2: 0.15, 0.3: 0.23},
        ("B", "Spearman"): {0.0: 0.05, 0.1: 0.07, 0.2: 0.16, 0.3: 0.33},
    })
    assert troca_de_vantagem(dados, "B") == 0.2


def test_troca_de_vantagem_e_none_quando_o_pearson_vence_sempre():
    dados = simulacao({
        ("A", "Pearson"): {0.0: 0.05, 0.1: 0.08, 0.5: 0.82},
        ("A", "Spearman"): {0.0: 0.05, 0.1: 0.07, 0.5: 0.77},
    })
    assert troca_de_vantagem(dados, "A") is None


def test_figura_g4_usa_os_csvs_do_repositorio():
    from src.graficos import figura_g4

    figura = figura_g4()
    try:
        eixo = figura.axes[0]
        rotulos = [t.get_text() for t in eixo.get_legend().get_texts()]
        assert len(rotulos) == len(eixo.lines) - 3  # 3 linhas de referencia: α, 80% e a virada
    finally:
        plt.close(figura)
