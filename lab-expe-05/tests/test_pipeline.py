"""Pipeline de ponta a ponta sobre dados sinteticos de efeito conhecido.

A pergunta que estes testes respondem e: "se a resposta certa fosse X, a
analise diria X?". Com dado real nunca se sabe; com dado sintetico, sim.
"""
import numpy as np
import pandas as pd
import pytest

from analysis import io_dados, run, testes
from scripts import gerar_sintetico as gs

# Colunas que o plano de analise (secao 11) promete em results/tabelas/testes.csv.
COLUNAS_TESTES = {
    "metrica", "benchmark", "heap_mult", "n_g1", "n_zgc", "teste", "estatistica", "p",
    "p_corrigido", "efeito", "efeito_valor", "razao", "razao_ic_baixo", "razao_ic_alto",
    "papel", "shapiro_g1", "shapiro_zgc", "levene_p", "teste_sensibilidade",
    "p_sensibilidade", "concordam", "correcao", "k_familia", "significativo",
}


@pytest.fixture(scope="module")
def entrada(tmp_path_factory):
    caminho = tmp_path_factory.mktemp("dados") / "sintetico.csv"
    gs.gerar(blocos=30, semente=42).to_csv(caminho, index=False)
    return caminho


@pytest.fixture(scope="module")
def resultado(entrada, tmp_path_factory):
    saida = tmp_path_factory.mktemp("saida")
    return run.executar(entrada, saida / "tabelas", saida / "figuras",
                        n=30, com_poder=False), saida


def test_escreve_os_arquivos_dos_caminhos_do_contrato(resultado):
    _, saida = resultado
    esperados = {"descritiva.csv", "testes.csv", "exploratorias.csv", "interacao.csv"}
    assert esperados <= {p.name for p in (saida / "tabelas").iterdir()}
    assert {p.suffix for p in (saida / "figuras").iterdir()} == {".png"}


def test_a_tabela_de_testes_tem_as_colunas_prometidas(resultado):
    r, _ = resultado
    assert COLUNAS_TESTES <= set(r["testes"].columns)


def test_sao_12_testes_confirmatorios(resultado):
    """8 pares de tempo + 4 de p99, exatamente o que o contrato conta."""
    r, _ = resultado
    t = r["testes"]
    assert len(t) == 12
    assert (t["metrica"] == "exec_ms").sum() == 8
    assert (t["metrica"] == "lat_p99_ms").sum() == 4
    assert t["k_familia"].unique().tolist() == [12]
    assert t["correcao"].unique().tolist() == ["holm"]


def test_recupera_todas_as_razoes_injetadas(resultado):
    """O IC de cada par tem de conter o efeito que foi plantado."""
    r, _ = resultado
    t = r["testes"]
    esperado = {("exec_ms", b, h): v for (b, h), v in gs.EFEITO_EXEC.items()}
    esperado |= {("lat_p99_ms", b, h): v for (b, h), v in gs.EFEITO_P99.items()}
    assert len(esperado) == 12

    for linha in t.itertuples():
        alvo = esperado[(linha.metrica, linha.benchmark, linha.heap_mult)]
        assert linha.razao_ic_baixo <= alvo <= linha.razao_ic_alto, (
            f"{linha.metrica} {linha.benchmark} h={linha.heap_mult}: "
            f"injetado {alvo}, IC [{linha.razao_ic_baixo:.3f}; {linha.razao_ic_alto:.3f}]"
        )


def test_detecta_os_efeitos_grandes_depois_do_holm(resultado):
    """Os 4 pares de p99 (reducao de 25% a 35%) nao podem passar batido."""
    r, _ = resultado
    p99 = r["testes"][r["testes"]["metrica"] == "lat_p99_ms"]
    assert p99["significativo"].all()
    assert (p99["razao"] < 1).all()   # o ZGC reduz a cauda, como foi plantado


def test_a_regra_de_exclusao_tira_so_o_que_falhou(resultado):
    r, _ = resultado
    assert r["validos"] + r["falhas"] == r["linhas"]
    assert r["falhas"] == 1            # a semente 42 injeta exatamente um OOM
    assert r["descritiva"]["n_falhas"].sum() > 0   # a falha e contada, nao some


def test_motivo_de_falha_fora_do_plano_e_recusado(entrada):
    df = io_dados.carregar(entrada)
    df.loc[df.index[0], ["failed", "failure_reason"]] = [1, "achei_o_numero_feio"]
    with pytest.raises(io_dados.DadosInvalidos, match="fora do plano"):
        io_dados.aplicar_exclusao(df)


def test_csv_fora_do_contrato_para_a_analise(tmp_path):
    ruim = tmp_path / "ruim.csv"
    pd.DataFrame({"tempo": [1, 2], "coletor": ["G1", "ZGC"]}).to_csv(ruim, index=False)
    with pytest.raises(io_dados.DadosInvalidos):
        io_dados.carregar(ruim)


def test_rq2_enxerga_a_interacao_plantada(resultado):
    """Em 3 dos 4 benchmarks a razao muda com o heap; o modelo tem de ver isso."""
    from analysis import interacao
    r, _ = resultado
    rq2 = interacao.resumo_rq2(r["interacao"])
    assert rq2["ha_interacao"]
    assert rq2["razao_de_razoes"] < 1    # a vantagem do G1 encolhe no heap maior


def test_sem_efeito_nenhum_par_sobrevive_ao_holm(tmp_path):
    """Com razao 1,0 em tudo, 12 testes nao deveriam acusar nada."""
    caminho = tmp_path / "nulo.csv"
    gs.gerar(blocos=30, semente=42, sem_efeito=True).to_csv(caminho, index=False)
    df, _ = io_dados.aplicar_exclusao(io_dados.carregar(caminho, n=30))
    t = testes.confirmatorios(df, bootstrap=False)
    assert len(t) == 12
    assert not t["significativo"].any()


def test_trocar_a_entrada_por_outro_arquivo_funciona(tmp_path):
    """O contrato promete que basta trocar --entrada quando o dado real chegar."""
    outro = tmp_path / "full.csv"
    gs.gerar(blocos=12, semente=11).to_csv(outro, index=False)
    saida = tmp_path / "out"
    r = run.executar(outro, saida / "tabelas", saida / "figuras", n=12,
                     com_poder=False, bootstrap=False)
    assert r["linhas"] == 16 * 12
    assert len(r["testes"]) == 12
    assert r["testes"]["k_familia"].unique().tolist() == [12]
    assert (saida / "tabelas" / "descritiva.csv").is_file()


def test_o_piloto_de_5_blocos_roda_sem_quebrar(tmp_path):
    """O contrato define o piloto como 5 blocos - abaixo do n minimo do teste.

    A S01-C3 vai rodar este mesmo pipeline nesse arquivo. Ele tem de produzir a
    descritiva e o CV (que e o que o piloto serve para decidir) e dizer, na
    tabela, que nenhum par tinha n suficiente - em vez de estourar.
    """
    piloto = tmp_path / "pilot.csv"
    gs.gerar(blocos=5, semente=11).to_csv(piloto, index=False)
    saida = tmp_path / "out"
    r = run.executar(piloto, saida / "tabelas", saida / "figuras", n=5,
                     com_poder=False, bootstrap=False)

    t = r["testes"]
    assert len(t) == 12
    assert (t["teste"] == "sem_poder").all()
    assert t["k_familia"].unique().tolist() == [0]
    assert COLUNAS_TESTES <= set(t.columns)       # o esquema nao muda
    assert not r["descritiva"].empty               # o CV, que e o objetivo do piloto
    assert (saida / "figuras" / "efeitos_ic.png").is_file()


def test_par_com_poucas_observacoes_sai_da_familia_do_holm(entrada):
    """n < 10 num grupo: o par vira 'sem_poder' e o k da familia cai."""
    df = io_dados.carregar(entrada)
    df, _ = io_dados.aplicar_exclusao(df)
    corte = (df["benchmark"] == "xalan") & (df["heap_mult"] == 1.5) & (df["gc"] == "ZGC")
    magro = pd.concat([df[~corte], df[corte].head(5)])
    t = testes.confirmatorios(magro, bootstrap=False)
    sem_poder = t[t["teste"] == "sem_poder"]
    assert len(sem_poder) == 1
    assert t["k_familia"].unique().tolist() == [11]
    assert sem_poder.iloc[0]["motivo"].startswith("n < 10")


def test_a_descritiva_traz_o_cv_de_cada_celula(resultado):
    r, _ = resultado
    d = r["descritiva"]
    assert {"n", "media", "mediana", "dp", "iqr", "minimo", "maximo", "cv",
            "media_geometrica", "n_falhas"} <= set(d.columns)
    exec_ms = d[d["metrica"] == "exec_ms"]
    assert len(exec_ms) == 16                      # uma linha por celula
    assert exec_ms["cv"].between(0, 0.12).all()    # o gerador usa CV de 4%
