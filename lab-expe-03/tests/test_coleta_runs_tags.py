"""Testes de pipeline/coleta_runs.py e pipeline/coleta_tags.py (issue #139)."""

from __future__ import annotations

from datetime import date

from pipeline.coleta_runs import coletar_runs, intervalos_mensais
from pipeline.coleta_tags import listar_tags_graphql


def bruto(i, conclusion="success", dia="2025-01-05"):
    return {
        "id": i, "workflow_id": 7, "conclusion": conclusion,
        "run_started_at": f"{dia}T10:00:00Z", "created_at": f"{dia}T10:00:00Z",
        "updated_at": f"{dia}T10:05:00Z",
    }


class ClienteRuns:
    """requisitar() responde pela faixa `created`; `totais` simula meses acima do teto."""

    def __init__(self, por_faixa, totais=None, paginas_extra=None):
        self.por_faixa = por_faixa
        self.totais = totais or {}
        self.paginas_extra = paginas_extra or {}
        self.faixas = []

    def requisitar(self, caminho, params=None):
        if params is None:  # URL de proxima pagina
            return {"workflow_runs": self.paginas_extra[caminho]}, {}
        faixa = params["created"]
        self.faixas.append(faixa)
        runs = self.por_faixa.get(faixa, [])
        headers = {}
        if faixa in self.paginas_extra:
            headers = {"Link": f'<{faixa}>; rel="next"'}
        return {"total_count": self.totais.get(faixa, len(runs)), "workflow_runs": runs}, headers


def test_intervalos_mensais_cobrem_a_janela_sem_buraco():
    fatias = intervalos_mensais(date(2025, 10, 1), date(2026, 9, 30))
    assert len(fatias) == 12
    assert fatias[0] == (date(2025, 10, 1), date(2025, 10, 31))
    assert fatias[4] == (date(2026, 2, 1), date(2026, 2, 28))
    assert fatias[-1] == (date(2026, 9, 1), date(2026, 9, 30))


def test_intervalos_mensais_janela_comecando_no_meio_do_mes():
    assert intervalos_mensais(date(2025, 1, 15), date(2025, 2, 10)) == [
        (date(2025, 1, 15), date(2025, 1, 31)),
        (date(2025, 2, 1), date(2025, 2, 10)),
    ]


def test_coleta_mes_a_mes_com_filtros_e_paginacao():
    cliente = ClienteRuns(
        {"2025-01-01..2025-01-31": [bruto(1)], "2025-02-01..2025-02-28": [bruto(2, "failure")]},
        paginas_extra={"2025-01-01..2025-01-31": [bruto(3, "cancelled")]},
    )
    r = coletar_runs(cliente, "o", "r", "main", date(2025, 1, 1), date(2025, 2, 28))
    assert [run.conclusion for run in r.runs] == ["success", "cancelled", "failure"]
    assert r.meses_no_teto == 0
    assert cliente.faixas == ["2025-01-01..2025-01-31", "2025-02-01..2025-02-28"]


def test_mes_acima_do_teto_e_dividido_e_contado():
    cliente = ClienteRuns(
        {
            "2025-01-01..2025-01-16": [bruto(1)],
            "2025-01-17..2025-01-31": [bruto(2)],
        },
        totais={"2025-01-01..2025-01-31": 1500},
    )
    r = coletar_runs(cliente, "o", "r", "main", date(2025, 1, 1), date(2025, 1, 31))
    assert len(r.runs) == 2
    assert r.meses_no_teto == 1
    assert r.dias_truncados == 0


def test_dia_unico_acima_do_teto_fica_truncado():
    cliente = ClienteRuns({}, totais={"2025-01-01..2025-01-01": 1200})
    r = coletar_runs(cliente, "o", "r", "main", date(2025, 1, 1), date(2025, 1, 1))
    assert r.dias_truncados == 1
    assert r.meses_no_teto == 1


def test_run_sem_run_started_at_usa_created_at():
    b = bruto(1)
    b["run_started_at"] = None
    cliente = ClienteRuns({"2025-01-01..2025-01-31": [b]})
    r = coletar_runs(cliente, "o", "r", "main", date(2025, 1, 1), date(2025, 1, 31))
    assert r.runs[0].run_started_at == "2025-01-05T10:00:00Z"


class ClienteGraphQL:
    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.variaveis = []

    def graphql(self, consulta, variaveis):
        self.variaveis.append(variaveis)
        return self.respostas.pop(0)


def pagina(nodes, proxima=None):
    return {"data": {"repository": {"refs": {
        "pageInfo": {"hasNextPage": proxima is not None, "endCursor": proxima},
        "nodes": nodes,
    }}}}


def test_tags_graphql_leve_e_anotada_paginadas_e_ordenadas():
    leve = {"name": "v2", "target": {"__typename": "Commit", "oid": "b", "authoredDate": "2025-02-01T00:00:00Z"}}
    anotada = {"name": "v1", "target": {"__typename": "Tag", "target": {
        "__typename": "Commit", "oid": "a", "authoredDate": "2025-01-01T00:00:00Z"}}}
    arvore = {"name": "estranha", "target": {"__typename": "Tree"}}
    cliente = ClienteGraphQL([pagina([leve, arvore], "c1"), pagina([anotada])])

    tags = listar_tags_graphql(cliente, "o", "r")
    assert [t["name"] for t in tags] == ["v1", "v2"]
    assert tags[0] == {"name": "v1", "sha": "a", "data": "2025-01-01T00:00:00Z"}
    assert cliente.variaveis[1]["cursor"] == "c1"


def test_tags_graphql_repositorio_inexistente():
    assert listar_tags_graphql(ClienteGraphQL([{"data": {"repository": None}}]), "o", "r") == []


def test_meses_em_paralelo_dao_o_mesmo_resultado_que_sequencial():
    por_faixa = {
        "2025-01-01..2025-01-31": [bruto(1, dia="2025-01-05")],
        "2025-02-01..2025-02-14": [bruto(2, "failure", dia="2025-02-03")],
        "2025-02-15..2025-02-28": [bruto(3, dia="2025-02-20")],
        "2025-03-01..2025-03-31": [bruto(4, "cancelled", dia="2025-03-09")],
    }
    totais = {"2025-02-01..2025-02-28": 1500}
    seq = coletar_runs(ClienteRuns(por_faixa, totais), "o", "r", "main", date(2025, 1, 1), date(2025, 3, 31))
    par = coletar_runs(
        ClienteRuns(por_faixa, totais), "o", "r", "main", date(2025, 1, 1), date(2025, 3, 31), threads=3
    )
    assert par.runs == seq.runs
    assert [r.run_started_at[:10] for r in par.runs] == ["2025-01-05", "2025-02-03", "2025-02-20", "2025-03-09"]
    assert (par.meses_no_teto, par.dias_truncados) == (seq.meses_no_teto, seq.dias_truncados) == (1, 0)
