"""Testes do cliente HTTP (Issue #136), sem rede: `abrir` e `dormir` sao falsos."""

from __future__ import annotations

import io
import json
import urllib.error

import pytest

from pipeline.github_client import (
    GitHubAPIError,
    GitHubClient,
    TokenAusenteError,
    ler_token,
    proxima_pagina,
)


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


def erro_http(status, headers=None, corpo=None):
    return urllib.error.HTTPError(
        "https://api.github.com/x",
        status,
        "erro",
        headers or {},
        io.BytesIO(json.dumps(corpo or {"message": "erro"}).encode()),
    )


class AbrirFalso:
    """Devolve (ou levanta) as respostas na ordem e registra as URLs pedidas."""

    def __init__(self, *respostas):
        self.respostas = list(respostas)
        self.urls = []
        self.requisicoes = []

    def __call__(self, requisicao, timeout=None):
        self.urls.append(requisicao.full_url)
        self.requisicoes.append(requisicao)
        resposta = self.respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


def cliente(abrir, esperas=None, agora=1_000.0):
    return GitHubClient(
        "token-teste",
        abrir=abrir,
        dormir=(esperas.append if esperas is not None else lambda s: None),
        agora=lambda: agora,
    )


# ------------------------------------------------------------------- token


def test_le_token_do_ambiente(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "  abc  ")
    assert ler_token() == "abc"


def test_sem_token_falha_cedo(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(TokenAusenteError):
        GitHubClient()


def test_envia_token_e_cabecalhos():
    abrir = AbrirFalso(RespostaFalsa({"ok": True}))
    cliente(abrir).get("/repos/a/b")
    req = abrir.requisicoes[0]
    assert req.get_header("Authorization") == "Bearer token-teste"
    assert req.get_header("Accept") == "application/vnd.github+json"
    assert abrir.urls == ["https://api.github.com/repos/a/b"]


# --------------------------------------------------------------- paginacao


def test_proxima_pagina_le_link():
    link = (
        '<https://api.github.com/x?page=2>; rel="next", '
        '<https://api.github.com/x?page=5>; rel="last"'
    )
    assert proxima_pagina(link) == "https://api.github.com/x?page=2"
    assert proxima_pagina('<https://api.github.com/x?page=1>; rel="prev"') is None
    assert proxima_pagina(None) is None


def test_paginar_segue_link_ate_o_fim():
    abrir = AbrirFalso(
        RespostaFalsa([1, 2], {"Link": '<https://api.github.com/r?page=2>; rel="next"'}),
        RespostaFalsa([3]),
    )
    assert list(cliente(abrir).paginar("/r")) == [1, 2, 3]
    assert abrir.urls == [
        "https://api.github.com/r?per_page=100",
        "https://api.github.com/r?page=2",
    ]


def test_paginar_com_chave_para_workflow_runs():
    abrir = AbrirFalso(RespostaFalsa({"total_count": 2, "workflow_runs": [{"id": 1}, {"id": 2}]}))
    runs = list(cliente(abrir).paginar("/actions/runs", {"event": "push"}, chave="workflow_runs"))
    assert [r["id"] for r in runs] == [1, 2]
    assert "event=push" in abrir.urls[0]


# -------------------------------------------------------------- rate limit


def test_dorme_ate_o_reset_quando_cota_zera():
    esperas = []
    abrir = AbrirFalso(
        RespostaFalsa({"ok": 1}, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1060"})
    )
    cliente(abrir, esperas, agora=1_000.0).get("/x")
    assert esperas == [61.0]  # 60 s ate o reset + 1 s de folga


def test_403_de_rate_limit_espera_e_repete():
    esperas = []
    abrir = AbrirFalso(
        erro_http(403, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1010"}),
        RespostaFalsa({"ok": 1}),
    )
    assert cliente(abrir, esperas).get("/x") == {"ok": 1}
    assert esperas == [11.0]
    assert len(abrir.urls) == 2


def test_rate_limit_secundario_usa_retry_after():
    esperas = []
    abrir = AbrirFalso(erro_http(429, {"Retry-After": "30"}), RespostaFalsa({"ok": 1}))
    cliente(abrir, esperas).get("/x")
    assert esperas == [30.0]


def test_403_que_nao_e_rate_limit_nao_repete():
    abrir = AbrirFalso(erro_http(403, {"X-RateLimit-Remaining": "4999"}))
    with pytest.raises(GitHubAPIError) as exc:
        cliente(abrir).get("/x")
    assert exc.value.status == 403


# ----------------------------------------------------------------- backoff


def test_backoff_exponencial_em_5xx():
    esperas = []
    abrir = AbrirFalso(erro_http(502), erro_http(503), erro_http(500), RespostaFalsa({"ok": 1}))
    assert cliente(abrir, esperas).get("/x") == {"ok": 1}
    assert esperas == [1.0, 2.0, 4.0]


def test_5xx_esgota_tentativas():
    esperas = []
    abrir = AbrirFalso(*[erro_http(500) for _ in range(5)])
    with pytest.raises(GitHubAPIError) as exc:
        cliente(abrir, esperas).get("/x")
    assert exc.value.status == 500
    assert esperas == [1.0, 2.0, 4.0, 8.0]


def test_404_nao_repete():
    abrir = AbrirFalso(erro_http(404, corpo={"message": "Not Found"}))
    with pytest.raises(GitHubAPIError, match="Not Found"):
        cliente(abrir).get("/x")
    assert len(abrir.urls) == 1
