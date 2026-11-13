import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import validate_schema as vs  # noqa: E402

BENCHES = {"h2": True, "xalan": False}  # benchmark -> tem metrica de latencia


def linha(gc="G1", bench="h2", heap="2.0", rep=1, **extra):
    r = {
        "run_id": f"{gc}-{bench}-h{heap}-r{rep:02d}", "rep": str(rep),
        "timestamp": "2026-11-20T12:00:00Z", "host": "maq1", "jdk_version": "25.0.5+8",
        "image_digest": "sha256:abc", "gc": gc, "cpus": "4", "heap_mult": heap, "heap_mb": "512",
        "benchmark": bench, "iterations": "5", "exec_ms": "1234.5",
        "lat_p99_ms": "12.3" if BENCHES.get(bench) else "", "gc_pause_max_ms": "4.2",
        "cpu_s": "9.8", "rss_peak_mb": "640.1", "failed": "0", "failure_reason": "", "seed": "42",
        "raw_file": f"raw/{gc}-{bench}-h{heap}-{rep}.txt", "gc_log_file": f"raw/{gc}-{bench}-h{heap}-{rep}.gc.log",
    }
    r.update(extra)
    return r


def df_valido(n=3):
    return pd.DataFrame([linha(gc, b, h, rep) for gc in ("G1", "ZGC") for b in BENCHES
                         for h in ("2.0", "4.0") for rep in range(1, n + 1)])


def regras(ps, gravidade="erro"):
    return {p.regra for p in ps if p.gravidade == gravidade}


def test_arquivo_valido_passa():
    assert vs.validar(df_valido(), n=3) == []


def test_coluna_faltando_e_coluna_extra():
    d = df_valido().drop(columns=["seed"])
    assert "colunas" in regras(vs.validar(d))
    d = df_valido()
    d["extra"] = "x"
    assert "colunas" in regras(vs.validar(d))


def test_gc_invalido_e_failed_invalido():
    d = df_valido()
    d.loc[0, "gc"] = "Parallel"
    d.loc[1, "failed"] = "2"
    ps = vs.validar(d)
    assert {p.coluna for p in ps if p.regra == "dominio"} == {"gc", "failed"}
    assert all(p.linha in (2, 3) for p in ps if p.regra == "dominio")


def test_run_id_duplicado_aponta_a_linha():
    d = df_valido()
    d.loc[5, "run_id"] = d.loc[0, "run_id"]
    dup = [p for p in vs.validar(d) if p.regra == "duplicata" and p.coluna == "run_id"]
    assert len(dup) == 1 and dup[0].linha == 7


def test_rep_repetido_na_mesma_celula():
    d = df_valido()
    d.loc[1, "rep"] = "1"
    d.loc[1, "run_id"] = "outro-id"
    assert any(p.coluna == "rep" for p in vs.validar(d))


def test_tipos_numericos_e_timestamp():
    d = df_valido()
    d.loc[0, "exec_ms"] = "-3"
    d.loc[1, "cpus"] = "0"
    d.loc[2, "timestamp"] = "ontem"
    d.loc[3, "heap_mult"] = "abc"
    cols = {p.coluna for p in vs.validar(d) if p.regra == "tipo"}
    assert cols == {"exec_ms", "cpus", "timestamp", "heap_mult"}


def test_run_que_falhou_pode_ter_metricas_vazias_mas_precisa_de_motivo():
    d = df_valido()
    d.loc[0, ["failed", "exec_ms", "cpu_s", "gc_pause_max_ms", "rss_peak_mb"]] = ["1", "", "", "", ""]
    assert "coerencia" in regras(vs.validar(d))  # falta failure_reason
    d.loc[0, "failure_reason"] = "OOM"
    assert vs.validar(d) == []


def test_metrica_vazia_em_run_que_nao_falhou_e_erro():
    d = df_valido()
    d.loc[0, "cpu_s"] = ""
    assert any(p.regra == "obrigatoria" and p.coluna == "cpu_s" for p in vs.validar(d))


def test_failure_reason_sem_falha_e_erro():
    d = df_valido()
    d.loc[0, "failure_reason"] = "OOM"
    assert "coerencia" in regras(vs.validar(d))


def test_latencia_vazia_so_vale_para_benchmark_sem_latencia():
    d = df_valido()
    d.loc[(d["benchmark"] == "h2") & (d["gc"] == "ZGC") & (d["rep"] == "1"), "lat_p99_ms"] = ""
    assert "latencia" in regras(vs.validar(d))


def test_contagem_por_celula_e_pareamento_dos_coletores():
    d = df_valido(3)
    assert "contagem" in regras(vs.validar(d, n=5))
    sem_zgc = d[~((d["gc"] == "ZGC") & (d["benchmark"] == "xalan") & (d["heap_mult"] == "4.0"))]
    assert "pareamento" in regras(vs.validar(sem_zgc))


def test_varios_digests_dao_aviso_mas_nao_erro():
    d = df_valido()
    d.loc[0, "image_digest"] = "sha256:outro"
    ps = vs.validar(d)
    assert regras(ps, "aviso") == {"controlada"} and regras(ps) == set()


def test_arquivo_sem_linhas():
    d = pd.DataFrame(columns=vs.COLUNAS)
    assert "vazio" in regras(vs.validar(d))


def test_coletor_registrado_deve_bater_com_o_log_de_gc(tmp_path):
    d = df_valido(1).head(2).copy()  # as duas primeiras linhas sao G1/h2/2.0 e G1/h2/4.0
    (tmp_path / "raw").mkdir()
    for k, texto in enumerate(["[0.003s][info][gc] Using G1", "[0.004s][info][gc] Using The Z Garbage Collector"]):
        (tmp_path / d.loc[k, "raw_file"]).write_text("saida")
        (tmp_path / d.loc[k, "gc_log_file"]).write_text(texto)
    # as duas linhas dizem G1 mas o log da segunda mostra ZGC
    ps = vs.validar(d, base_dir=tmp_path)
    erros_log = [p for p in ps if p.regra == "log"]
    assert len(erros_log) == 1 and erros_log[0].linha == 3 and "ZGC" in erros_log[0].mensagem


def test_arquivo_apontado_que_nao_existe(tmp_path):
    ps = vs.validar(df_valido(1).head(2), base_dir=tmp_path)
    assert {p.coluna for p in ps if p.regra == "arquivo"} == {"raw_file", "gc_log_file"}


@pytest.mark.parametrize("texto,esperado", [
    ("Using G1", "G1"), ("Using The Z Garbage Collector", "ZGC"), ("Using ZGC", "ZGC"),
    ("Using Parallel", None), ("Using G1 ... Z Garbage Collector", None),
])
def test_deteccao_do_coletor_no_log(texto, esperado):
    assert vs.coletor_no_log(texto) == esperado


def test_linha_de_comando_devolve_codigo_de_saida(tmp_path, capsys):
    ok, ruim = tmp_path / "ok.csv", tmp_path / "ruim.csv"
    df_valido().to_csv(ok, index=False)
    d = df_valido()
    d.loc[0, "gc"] = "Serial"
    d.to_csv(ruim, index=False)
    assert vs.main([str(ok), "--n", "3"]) == 0
    assert vs.main([str(ruim)]) == 1
    assert "linha 2, coluna gc" in capsys.readouterr().out


def test_timestamp_precisa_ser_data_e_hora_em_utc():
    for ruim in ["2026-11-20", "2026-11-20T12:00:00", "2026-11-20T12:00:00-03:00"]:
        d = df_valido()
        d.loc[0, "timestamp"] = ruim
        assert any(p.coluna == "timestamp" for p in vs.validar(d)), ruim
    d = df_valido()
    d.loc[0, "timestamp"] = "2026-11-20T12:00:00+00:00"
    assert vs.validar(d) == []


def test_rep_fora_do_intervalo_quando_n_e_informado():
    d = df_valido(3)
    d.loc[0, "rep"] = "9"
    d.loc[0, "run_id"] = "novo-id"
    assert any(p.regra == "intervalo" and p.linha == 2 for p in vs.validar(d, n=3))


def test_arquivo_inexistente_ou_vazio_da_mensagem_e_codigo_2(tmp_path, capsys):
    vazio = tmp_path / "vazio.csv"
    vazio.write_text("")
    assert vs.main([str(tmp_path / "nao_existe.csv")]) == 2
    assert vs.main([str(vazio)]) == 2
    saida = capsys.readouterr().out
    assert "nao encontrado" in saida and "vazio" in saida
