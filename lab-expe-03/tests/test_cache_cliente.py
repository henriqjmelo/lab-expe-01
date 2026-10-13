"""Testes do cache em disco e da retomada no GitHubClient (issues #136 e #139)."""

from __future__ import annotations

import http.client
import io
import json
import urllib.error

import pytest

from pipeline.cache import CacheDisco
from pipeline.github_client import GitHubAPIError, GitHubClient


class RespostaFalsa:
    def __init__(self, corpo, headers=None):
        self._corpo = json.dumps(corpo).encode()
        self.headers = headers or {}

    def read(self):
        return self._corpo

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class AbrirFalso:
    def __init__(self, *respostas):
        self.respostas = list(respostas)
        self.requisicoes = []

    def __call__(self, requisicao, timeout=None):
        self.requisicoes.append(requisicao)
        resposta = self.respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


def erro_http(status, corpo=None, headers=None):
    return urllib.error.HTTPError(
        "https://api.github.com/x", status, "erro", headers or {},
        io.BytesIO(json.dumps(corpo or {"message": "erro"}).encode()),
    )


def novo_cliente(abrir, cache, esperas=None):
    return GitHubClient(
        "t", abrir=abrir, cache=cache,
        dormir=(esperas.append if esperas is not None else lambda s: None),
        agora=lambda: 0.0,
    )


def test_cache_grava_e_le(tmp_path):
    cache = CacheDisco(tmp_path)
    assert cache.ler("k") is None
    cache.gravar("k", {"status": 200, "corpo": [1, 2]})
    assert cache.ler("k") == {"status": 200, "corpo": [1, 2]}
    assert (cache.acertos, cache.faltas) == (1, 1)


def test_cache_corrompido_conta_como_falta(tmp_path):
    cache = CacheDisco(tmp_path)
    cache.gravar("k", {"a": 1})
    arquivo = next(tmp_path.rglob("*.json.gz"))
    arquivo.write_bytes(b"lixo")
    assert cache.ler("k") is None


def test_retomada_segunda_execucao_nao_chama_a_api(tmp_path):
    cache = CacheDisco(tmp_path)
    pagina1 = RespostaFalsa([1, 2], {"Link": '<https://api.github.com/x?page=2>; rel="next"'})
    pagina2 = RespostaFalsa([3])
    primeiro = AbrirFalso(pagina1, pagina2)
    assert list(novo_cliente(primeiro, cache).paginar("/x")) == [1, 2, 3]
    assert len(primeiro.requisicoes) == 2

    # "Depois do Ctrl+C": cliente novo, mesmo cache, nenhuma resposta programada.
    segundo = AbrirFalso()
    assert list(novo_cliente(segundo, cache).paginar("/x")) == [1, 2, 3]
    assert segundo.requisicoes == []


def test_404_fica_no_cache_e_continua_levantando(tmp_path):
    cache = CacheDisco(tmp_path)
    with pytest.raises(GitHubAPIError) as primeiro:
        novo_cliente(AbrirFalso(erro_http(404)), cache).get("/compare/a...b")
    assert primeiro.value.status == 404

    with pytest.raises(GitHubAPIError) as segundo:
        novo_cliente(AbrirFalso(), cache).get("/compare/a...b")
    assert segundo.value.status == 404


def test_outros_erros_nao_vao_pro_cache(tmp_path):
    cache = CacheDisco(tmp_path)
    with pytest.raises(GitHubAPIError):
        novo_cliente(AbrirFalso(erro_http(422)), cache).get("/x")
    assert novo_cliente(AbrirFalso(RespostaFalsa({"ok": 1})), cache).get("/x") == {"ok": 1}


def test_graphql_usa_post_e_cache_por_consulta(tmp_path):
    cache = CacheDisco(tmp_path)
    abrir = AbrirFalso(RespostaFalsa({"data": 1}), RespostaFalsa({"data": 2}))
    c = novo_cliente(abrir, cache)
    assert c.graphql("q", {"v": 1}) == {"data": 1}
    assert c.graphql("q", {"v": 2}) == {"data": 2}
    assert c.graphql("q", {"v": 1}) == {"data": 1}  # cache
    assert len(abrir.requisicoes) == 2
    req = abrir.requisicoes[0]
    assert req.get_method() == "POST"
    assert json.loads(req.data) == {"query": "q", "variables": {"v": 1}}


def test_rate_limit_nunca_vem_do_cache(tmp_path):
    cache = CacheDisco(tmp_path)
    abrir = AbrirFalso(RespostaFalsa({"r": 1}), RespostaFalsa({"r": 2}))
    c = novo_cliente(abrir, cache)
    assert c.rate_limit() == {"r": 1}
    assert c.rate_limit() == {"r": 2}
    assert c.cache is cache


def test_limite_secundario_sem_cabecalho_espera_e_tenta_de_novo():
    esperas = []
    abrir = AbrirFalso(
        erro_http(403, {"message": "You have exceeded a secondary rate limit."}),
        RespostaFalsa({"ok": True}),
    )
    assert novo_cliente(abrir, None, esperas).get("/x") == {"ok": True}
    assert esperas == [60.0]


def test_queda_de_rede_tem_backoff():
    esperas = []
    abrir = AbrirFalso(urllib.error.URLError("sem rede"), RespostaFalsa({"ok": True}))
    assert novo_cliente(abrir, None, esperas).get("/x") == {"ok": True}
    assert esperas == [1.0]


def test_queda_de_rede_persistente_vira_erro():
    abrir = AbrirFalso(*[urllib.error.URLError("sem rede")] * 5)
    with pytest.raises(GitHubAPIError):
        novo_cliente(abrir, None).get("/x")


def test_resposta_cortada_no_meio_tem_backoff():
    esperas = []
    abrir = AbrirFalso(http.client.IncompleteRead(b"x", 10), RespostaFalsa({"ok": True}))
    assert novo_cliente(abrir, None, esperas).get("/x") == {"ok": True}
    assert esperas == [1.0]
