from __future__ import annotations

import http.client
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterator
from typing import Any

from pipeline.cache import CacheDisco

API_URL = "https://api.github.com"
API_VERSION = "2022-11-28"
POR_PAGINA = 100

MAX_TENTATIVAS = 5
BACKOFF_INICIAL = 1.0

FOLGA_RESET = 1.0

PRAZO_RESPOSTA = 120.0
TAMANHO_BLOCO = 64 * 1024

ESPERA_LIMITE_SECUNDARIO = 60.0

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


def pagina_menor(url: str) -> str | None:
    partes = urllib.parse.urlsplit(url)
    consulta = dict(urllib.parse.parse_qsl(partes.query))
    por_pagina = int(consulta.get("per_page", 30))
    novo = {100: 25, 25: 5}.get(por_pagina)
    if novo is None:
        return None
    pagina = int(consulta.get("page", 1))
    consulta["per_page"] = str(novo)
    consulta["page"] = str((pagina - 1) * por_pagina // novo + 1)
    return urllib.parse.urlunsplit(partes._replace(query=urllib.parse.urlencode(consulta)))


class GitHubClient:
    def __init__(
        self,
        token: str | None = None,
        *,
        base_url: str = API_URL,
        max_tentativas: int = MAX_TENTATIVAS,
        backoff_inicial: float = BACKOFF_INICIAL,
        timeout: float = 30.0,
        prazo_resposta: float = PRAZO_RESPOSTA,
        abrir: Callable[..., Any] = urllib.request.urlopen,
        dormir: Callable[[float], None] = time.sleep,
        agora: Callable[[], float] = time.time,
        cache: CacheDisco | None = None,
    ) -> None:
        self.token = token if token is not None else ler_token()
        self.base_url = base_url.rstrip("/")
        self.max_tentativas = max_tentativas
        self.backoff_inicial = backoff_inicial
        self.timeout = timeout
        self.prazo_resposta = prazo_resposta
        self._abrir = abrir
        self._dormir = dormir
        self._agora = agora
        self.cache = cache
        self.ultima_atividade = time.monotonic()
        self.pausado_ate = 0.0

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
        self,
        caminho: str,
        params: dict[str, Any] | None = None,
        *,
        corpo: dict[str, Any] | None = None,
        chave_cache: str | None = None,
    ) -> tuple[Any, dict[str, str]]:
        url = self.montar_url(caminho, params)
        chave = chave_cache or url
        if self.cache is not None:
            guardada = self.cache.ler(chave)
            if guardada is not None:
                self.ultima_atividade = time.monotonic()
                if guardada.get("status") in (404, 422):
                    mensagem = guardada.get("mensagem") or "Not Found"
                    raise GitHubAPIError(guardada["status"], url, f"{mensagem} (cache)")
                link = guardada.get("link")
                return guardada.get("corpo"), ({"Link": link} if link else {})

        dados = json.dumps(corpo).encode() if corpo is not None else None
        espera = self.backoff_inicial
        espera_secundario = ESPERA_LIMITE_SECUNDARIO

        for tentativa in range(1, self.max_tentativas + 1):
            requisicao = urllib.request.Request(url, data=dados, headers=self._cabecalhos())
            try:
                with self._abrir(requisicao, timeout=self.timeout) as resposta:
                    headers = dict(resposta.headers.items())
                    bruto = self._ler_com_prazo(resposta, url)
                self.ultima_atividade = time.monotonic()
            except urllib.error.HTTPError as erro:
                self.ultima_atividade = time.monotonic()
                headers = dict(erro.headers.items()) if erro.headers else {}
                if self._limite_estourado(erro.code, headers):
                    self._esperar_reset(headers)
                    continue
                mensagem = _mensagem_erro(erro)
                if erro.code in (403, 429) and "rate limit" in mensagem.lower():
                    self._pausar(espera_secundario)
                    espera_secundario *= 2
                    continue
                if erro.code >= 500 and tentativa < self.max_tentativas:
                    self._pausar(espera)
                    espera *= 2
                    continue
                if erro.code in (404, 422) and self.cache is not None:
                    self.cache.gravar(chave, {"status": erro.code, "mensagem": mensagem})
                raise GitHubAPIError(erro.code, url, mensagem) from erro
            except (http.client.HTTPException, OSError) as erro:
                if tentativa < self.max_tentativas:
                    self._pausar(espera)
                    espera *= 2
                    continue
                raise GitHubAPIError(0, url, str(erro)) from erro

            self._respeitar_cota(headers)
            try:
                conteudo = json.loads(bruto) if bruto else None
            except ValueError as erro:
                if tentativa < self.max_tentativas:
                    self._pausar(espera)
                    espera *= 2
                    continue
                raise GitHubAPIError(0, url, f"resposta truncada: {erro}") from erro
            if self.cache is not None and not (isinstance(conteudo, dict) and conteudo.get("errors")):
                self.cache.gravar(
                    chave, {"status": 200, "corpo": conteudo, "link": headers.get("Link")}
                )
            return conteudo, headers

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
            try:
                dados, headers = self.requisitar(url)
            except GitHubAPIError as erro:
                menor = pagina_menor(url) if erro.status in (502, 503, 504) else None
                if menor is None:
                    raise
                url = menor
                continue
            itens = dados.get(chave, []) if chave else dados
            yield from itens or []
            url = proxima_pagina(headers.get("Link"))

    def _ler_com_prazo(self, resposta: Any, url: str) -> bytes:
        limite = time.monotonic() + self.prazo_resposta
        partes = []
        while True:
            bloco = resposta.read(TAMANHO_BLOCO)
            if not bloco:
                return b"".join(partes)
            partes.append(bloco)
            if time.monotonic() > limite:
                raise TimeoutError(f"resposta de {url} passou de {self.prazo_resposta:.0f} s")

    def graphql(self, consulta: str, variaveis: dict[str, Any] | None = None) -> Any:
        corpo = {"query": consulta, "variables": variaveis or {}}
        chave = "graphql:" + json.dumps(corpo, sort_keys=True)
        dados, _ = self.requisitar("/graphql", corpo=corpo, chave_cache=chave)
        return dados

    def rate_limit(self) -> dict[str, Any]:
        cache, self.cache = self.cache, None
        try:
            return self.get("/rate_limit")
        finally:
            self.cache = cache

    @staticmethod
    def _limite_estourado(status: int, headers: dict[str, str]) -> bool:
        if status not in (403, 429):
            return False
        return headers.get("X-RateLimit-Remaining") == "0" or "Retry-After" in headers

    def _esperar_reset(self, headers: dict[str, str]) -> None:
        if "Retry-After" in headers:
            self._pausar(float(headers["Retry-After"]))
            return
        reset = float(headers.get("X-RateLimit-Reset", self._agora()))
        self._pausar(max(reset - self._agora(), 0.0) + FOLGA_RESET)

    def _pausar(self, segundos: float) -> None:
        self.pausado_ate = max(self.pausado_ate, time.monotonic() + segundos)
        self._dormir(segundos)

    def _respeitar_cota(self, headers: dict[str, str]) -> None:
        if headers.get("X-RateLimit-Remaining") == "0":
            self._esperar_reset(headers)


def _mensagem_erro(erro: urllib.error.HTTPError) -> str:
    try:
        return json.loads(erro.read()).get("message", "")
    except (ValueError, AttributeError, OSError):
        return erro.reason or ""
