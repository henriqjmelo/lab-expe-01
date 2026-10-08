from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterator
from typing import Any

API_URL = "https://api.github.com"
API_VERSION = "2022-11-28"
POR_PAGINA = 100

MAX_TENTATIVAS = 5
BACKOFF_INICIAL = 1.0

FOLGA_RESET = 1.0

_LINK_NEXT = re.compile(r'<([^>]+)>\s*;\s*rel="next"')


class TokenAusenteError(RuntimeError):
    pass


class GitHubAPIError(RuntimeError):
    def __init__(self, status: int, url: str, mensagem: str = "") -> None:
        super().__init__(f"HTTP {status} em {url}: {mensagem}".rstrip(": "))
        self.status = status
        self.url = url


def ler_token(variavel: str = "GITHUB_TOKEN") -> str:
    token = os.environ.get(variavel, "").strip()
    if not token:
        raise TokenAusenteError(
            f"Defina {variavel} no ambiente (ex.: export {variavel}=ghp_...) "
            "ou num .env fora do controle de versao."
        )
    return token


def proxima_pagina(link: str | None) -> str | None:
    if not link:
        return None
    achado = _LINK_NEXT.search(link)
    return achado.group(1) if achado else None


class GitHubClient:
    def __init__(
        self,
        token: str | None = None,
        *,
        base_url: str = API_URL,
        max_tentativas: int = MAX_TENTATIVAS,
        backoff_inicial: float = BACKOFF_INICIAL,
        timeout: float = 30.0,
        abrir: Callable[..., Any] = urllib.request.urlopen,
        dormir: Callable[[float], None] = time.sleep,
        agora: Callable[[], float] = time.time,
    ) -> None:
        self.token = token if token is not None else ler_token()
        self.base_url = base_url.rstrip("/")
        self.max_tentativas = max_tentativas
        self.backoff_inicial = backoff_inicial
        self.timeout = timeout
        self._abrir = abrir
        self._dormir = dormir
        self._agora = agora

    def montar_url(self, caminho: str, params: dict[str, Any] | None = None) -> str:
        url = caminho if caminho.startswith("http") else f"{self.base_url}/{caminho.lstrip('/')}"
        if params:
            separador = "&" if "?" in url else "?"
            url = f"{url}{separador}{urllib.parse.urlencode(params)}"
        return url

    def _cabecalhos(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "lab-expe-03-dora",
        }

    def requisitar(
        self, caminho: str, params: dict[str, Any] | None = None
    ) -> tuple[Any, dict[str, str]]:
        url = self.montar_url(caminho, params)
        espera = self.backoff_inicial

        for tentativa in range(1, self.max_tentativas + 1):
            requisicao = urllib.request.Request(url, headers=self._cabecalhos())
            try:
                with self._abrir(requisicao, timeout=self.timeout) as resposta:
                    headers = dict(resposta.headers.items())
                    corpo = resposta.read()
            except urllib.error.HTTPError as erro:
                headers = dict(erro.headers.items()) if erro.headers else {}
                if self._limite_estourado(erro.code, headers):
                    self._esperar_reset(headers)
                    continue
                if erro.code >= 500 and tentativa < self.max_tentativas:
                    self._dormir(espera)
                    espera *= 2
                    continue
                raise GitHubAPIError(erro.code, url, _mensagem_erro(erro)) from erro

            self._respeitar_cota(headers)
            return (json.loads(corpo) if corpo else None), headers

        raise GitHubAPIError(0, url, f"esgotadas {self.max_tentativas} tentativas")

    def get(self, caminho: str, params: dict[str, Any] | None = None) -> Any:
        dados, _ = self.requisitar(caminho, params)
        return dados

    def paginar(
        self,
        caminho: str,
        params: dict[str, Any] | None = None,
        *,
        chave: str | None = None,
    ) -> Iterator[Any]:
        params = {"per_page": POR_PAGINA, **(params or {})}
        url: str | None = self.montar_url(caminho, params)
        while url:
            dados, headers = self.requisitar(url)
            itens = dados.get(chave, []) if chave else dados
            yield from itens or []
            url = proxima_pagina(headers.get("Link"))

    def rate_limit(self) -> dict[str, Any]:
        return self.get("/rate_limit")

    @staticmethod
    def _limite_estourado(status: int, headers: dict[str, str]) -> bool:
        if status not in (403, 429):
            return False
        return headers.get("X-RateLimit-Remaining") == "0" or "Retry-After" in headers

    def _esperar_reset(self, headers: dict[str, str]) -> None:
        if "Retry-After" in headers:
            self._dormir(float(headers["Retry-After"]))
            return
        reset = float(headers.get("X-RateLimit-Reset", self._agora()))
        self._dormir(max(reset - self._agora(), 0.0) + FOLGA_RESET)

    def _respeitar_cota(self, headers: dict[str, str]) -> None:
        if headers.get("X-RateLimit-Remaining") == "0":
            self._esperar_reset(headers)


def _mensagem_erro(erro: urllib.error.HTTPError) -> str:
    try:
        return json.loads(erro.read()).get("message", "")
    except (ValueError, AttributeError, OSError):
        return erro.reason or ""
