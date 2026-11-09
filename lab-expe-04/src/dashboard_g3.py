from __future__ import annotations


def renderizar(st, graficos, formatar_numero) -> object:
    st.pyplot(graficos.figura_g3(), width="stretch")
    erro_i = graficos.tabela_erro_tipo_i()
    taxas_a = erro_i[erro_i["situacao"] == "A"].set_index("teste")["taxa_005"]
    taxas_b = erro_i[erro_i["situacao"] == "B"].set_index("teste")["taxa_005"]
    st.markdown(
        f"**Leitura do G3.** Com H₀ verdadeira (r = 0), o erro tipo I ficou entre "
        f"{formatar_numero(erro_i['taxa_005'].min() * 100, 2)}% e "
        f"{formatar_numero(erro_i['taxa_005'].max() * 100, 2)}% nas duas situações, próximo do nível nominal de 5% "
        f"e dentro da margem visual de ±0,4 ponto percentual. Na situação A: Pearson "
        f"{formatar_numero(taxas_a['Pearson'] * 100, 2)}%, Spearman "
        f"{formatar_numero(taxas_a['Spearman'] * 100, 2)}%; na B: Pearson "
        f"{formatar_numero(taxas_b['Pearson'] * 100, 2)}%, Spearman "
        f"{formatar_numero(taxas_b['Spearman'] * 100, 2)}%."
    )
    return erro_i
