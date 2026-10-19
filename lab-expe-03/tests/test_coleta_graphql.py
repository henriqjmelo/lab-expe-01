from __future__ import annotations

from datetime import date

import pytest

from pipeline.coleta_graphql import (
    ErroGraphQL,
    coletar_repositorio,
    eh_bug,
    paginar_graphql,
    primeira_resposta,
)
from pipeline.github_client import GitHubAPIError
from pipeline.repositorio import Janela

JANELA = Janela(date(2025, 1, 1), date(2025, 12, 31))


def pagina(nos, proxima=None, total=None, campo="pullRequests"):
    conexao = {"pageInfo": {"hasNextPage": proxima is not None, "endCursor": proxima}, "nodes": nos}
    if total is not None:
        conexao["totalCount"] = total
    return {"data": {"repository": {campo: conexao}}}


class ClienteFalso:
    def __init__(self, roteiro):
        self.roteiro = roteiro
        self.chamadas = []

    def graphql(self, consulta, variaveis):
        self.chamadas.append(variaveis)
        chave = ("estados" in variaveis and variaveis["estados"][0]) or (
            "issues" if "issues(" in consulta else "deployments")
        respostas = self.roteiro[chave]
        resposta = respostas.pop(0) if isinstance(respostas, list) else respostas(variaveis)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


def pr(numero, atualizado, merged=None, closed=None, autor="a", revisores=(), comentarios=()):
    return {
        "number": numero, "createdAt": "2025-03-01T00:00:00Z", "updatedAt": atualizado, "mergedAt": merged,
        "closedAt": closed, "additions": 10, "deletions": 2, "changedFiles": 1, "author": {"login": autor},
        "commits": {"totalCount": 2},
        "reviews": {"nodes": [{"createdAt": d, "author": {"login": l}} for l, d in revisores]},
        "comments": {"nodes": [{"createdAt": d, "author": {"login": l}} for l, d in comentarios]},
    }


def test_paginacao_para_quando_sai_da_janela():
    cliente = ClienteFalso({"MERGED": [
        pagina([pr(3, "2025-06-01T00:00:00Z"), pr(2, "2025-02-01T00:00:00Z")], proxima="c1"),
        pagina([pr(1, "2024-12-01T00:00:00Z"), pr(0, "2024-11-01T00:00:00Z")], proxima="c2"),
    ]})
    r = paginar_graphql(cliente, "q", {"estados": ["MERGED"]}, ("repository", "pullRequests"),
                        lambda no: no["updatedAt"] < JANELA.inicio_iso)
    assert [n["number"] for n in r.nos] == [3, 2]
    assert not r.truncado
    assert len(cliente.chamadas) == 2


def test_paginacao_trunca_no_limite_de_paginas():
    cliente = ClienteFalso({"MERGED": lambda v: pagina([pr(1, "2025-06-01T00:00:00Z")], proxima="mais")})
    r = paginar_graphql(cliente, "q", {"estados": ["MERGED"]}, ("repository", "pullRequests"),
                        lambda no: False, max_paginas=3)
    assert r.truncado and len(r.nos) == 3


def test_pagina_com_erro_e_refeita_com_tamanho_menor():
    cliente = ClienteFalso({"MERGED": [
        {"errors": [{"message": "Something went wrong"}], "data": None},
        GitHubAPIError(502, "u"),
        pagina([pr(1, "2025-06-01T00:00:00Z")]),
    ]})
    r = paginar_graphql(cliente, "q", {"estados": ["MERGED"]}, ("repository", "pullRequests"), lambda no: False)
    assert len(r.nos) == 1
    assert [c["n"] for c in cliente.chamadas] == [100, 50, 25]


def test_erro_persistente_ou_nao_transitorio_propaga():
    sempre = ClienteFalso({"MERGED": lambda v: {"errors": [{"message": "x"}], "data": None}})
    with pytest.raises(ErroGraphQL):
        paginar_graphql(sempre, "q", {"estados": ["MERGED"]}, ("repository", "pullRequests"), lambda no: False)
    proibido = ClienteFalso({"MERGED": [GitHubAPIError(401, "u")]})
    with pytest.raises(GitHubAPIError):
        paginar_graphql(proibido, "q", {"estados": ["MERGED"]}, ("repository", "pullRequests"), lambda no: False)


def test_repositorio_inexistente_devolve_vazio():
    cliente = ClienteFalso({"MERGED": [{"data": {"repository": None}}]})
    r = paginar_graphql(cliente, "q", {"estados": ["MERGED"]}, ("repository", "pullRequests"), lambda no: False)
    assert r.nos == []


def test_primeira_resposta_ignora_o_autor():
    no = pr(1, "x", autor="ana", revisores=[("ana", "2025-01-01T00:00:00Z"), ("bia", "2025-01-03T00:00:00Z")],
            comentarios=[("caio", "2025-01-02T00:00:00Z")])
    assert primeira_resposta(no) == "2025-01-02T00:00:00Z"
    assert primeira_resposta(pr(2, "x", autor="ana", comentarios=[("ana", "2025-01-02T00:00:00Z")])) is None


@pytest.mark.parametrize("labels, esperado", [
    (["bug"], True), (["type: bug"], True), (["kind/bug"], True), (["Regression"], True),
    (["debugger"], False), (["enhancement"], False), ([], False),
])
def test_eh_bug(labels, esperado):
    assert eh_bug(labels) is esperado


def test_coletar_repositorio_filtra_janela_e_resume():
    cliente = ClienteFalso({
        "MERGED": [pagina([
            pr(10, "2025-05-02T00:00:00Z", merged="2025-05-01T00:00:00Z", revisores=[("rev", "2025-04-02T00:00:00Z")]),
            pr(9, "2025-01-05T00:00:00Z", merged="2024-12-20T00:00:00Z"),
        ])],
        "CLOSED": [pagina([pr(8, "2025-03-02T00:00:00Z", closed="2025-03-01T00:00:00Z")])],
        "issues": [pagina([
            {"number": 1, "createdAt": "2025-02-01T00:00:00Z", "updatedAt": "2025-02-03T00:00:00Z",
             "closedAt": "2025-02-02T00:00:00Z", "labels": {"nodes": [{"name": "bug"}]}},
            {"number": 2, "createdAt": "2025-02-01T00:00:00Z", "updatedAt": "2025-02-03T00:00:00Z",
             "closedAt": "2025-02-02T00:00:00Z", "labels": {"nodes": []}},
        ], campo="issues")],
        "deployments": [pagina([
            {"createdAt": "2025-06-01T00:00:00Z", "environment": "production", "state": "ACTIVE",
             "latestStatus": {"state": "SUCCESS", "createdAt": "2025-06-01T00:05:00Z"}},
            {"createdAt": "2024-06-01T00:00:00Z", "environment": "production", "state": "INACTIVE", "latestStatus": None},
        ], total=2, campo="deployments")],
    })
    r = coletar_repositorio(cliente, "o", "r", "main", JANELA)
    assert [(p["number"], p["estado"]) for p in r["prs"]] == [(10, "merged"), (8, "closed")]
    assert r["prs"][0]["primeira_resposta_at"] == "2025-04-02T00:00:00Z"
    assert [i["eh_bug"] for i in r["issues"]] == [True, False]
    assert len(r["deployments"]) == 1 and r["deployments"][0]["status"] == "SUCCESS"
    assert (r["resumo"]["prs_mergeados"], r["resumo"]["prs_fechados"], r["resumo"]["issues_bug"],
            r["resumo"]["deployments_total"]) == (1, 1, 1, 2)
