import matplotlib.pyplot as plt
import pandas as pd

from src.graficos import figura_g3, tabela_erro_tipo_i


def dados_simulados() -> pd.DataFrame:
	linhas = []
	for situacao, base in (("A", 0.05), ("B", 0.052)):
		for teste, deslocamento in (("Pearson", 0.0), ("Spearman", 0.001)):
			for r, taxa05, taxa01 in (
				(0.0, base + deslocamento, 0.01 + deslocamento),
				(0.5, 0.8 - deslocamento, 0.6 - deslocamento),
			):
				linhas.append({
					"situacao": situacao, "r_latente": r, "teste": teste, "n": 30,
					"repeticoes": 10_000, "taxa_005": taxa05, "taxa_001": taxa01,
				})
	return pd.DataFrame(linhas)


def test_tabela_erro_tipo_i_seleciona_apenas_efeito_nulo():
	resultado = tabela_erro_tipo_i(dados_simulados())

	assert len(resultado) == 4
	assert set(resultado.columns) == {"situacao", "teste", "repeticoes", "taxa_005", "taxa_001"}
	assert set(resultado["situacao"]) == {"A", "B"}
	assert set(resultado["teste"]) == {"Pearson", "Spearman"}


def test_figura_g3_tem_barras_para_as_duas_situacoes():
	figura = figura_g3(dados_simulados())
	try:
		assert len(figura.axes) == 1
		assert len(figura.axes[0].patches) == 4
		assert len(figura.axes[0].lines) >= 1
	finally:
		plt.close(figura)