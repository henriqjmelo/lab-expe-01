"""Change failure rate (RQ 03), variantes (a) proxy de CI e (b) proxy de entrega.

(a) falhas / (falhas + sucessos) sobre todos os workflow runs validos do
    repositorio, todos os workflows juntos. Classificacao por `conclusion`
    conforme a secao 3 do ENUNCIADO.md.

(b) release R falhou se for seguida, em ate 7 dias, por uma release corretiva.
    CFR = releases que falharam / releases avaliadas. Releases dos ultimos 7
    dias da janela ficam fora do denominador (censura).

A heuristica de "corretiva" e da issue #138 (Gabriel). Enquanto ela nao chega,
o pipeline usa `corretiva_semver_patch` (v0): so o patch do SemVer subiu em
relacao a release anterior. A funcao de CFR (b) recebe a heuristica como
parametro, entao trocar de versao nao mexe aqui.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

SUCESSO = "sucesso"
FALHA = "falha"
IGNORADO = "ignorado"

CONCLUSOES_FALHA = frozenset({"failure", "timed_out", "startup_failure"})

PRAZO_CORRECAO = timedelta(days=7)

_SEMVER = re.compile(r"^[^\d]*(\d+)\.(\d+)(?:\.(\d+))?")


def classificar_conclusao(conclusion: str | None) -> str:
    if conclusion == "success":
        return SUCESSO
    if conclusion in CONCLUSOES_FALHA:
        return FALHA
    # cancelled, skipped, neutral, action_required, stale, vazio e qualquer valor novo da API.
    return IGNORADO


def cfr_ci(conclusoes: list[str | None]) -> dict:
    """Variante (a). Recebe o campo `conclusion` de cada workflow run."""
    classes = [classificar_conclusao(c) for c in conclusoes]
    sucessos = classes.count(SUCESSO)
    falhas = classes.count(FALHA)
    validos = sucessos + falhas
    return {
        "n_validos": validos,
        "n_sucessos": sucessos,
        "n_falhas": falhas,
        "n_ignorados": classes.count(IGNORADO),
        "cfr": falhas / validos if validos else None,
    }


@dataclass
class Deploy:
    tag_name: str
    published_at: str


def _parse(data: str) -> datetime:
    return datetime.fromisoformat(data.replace("Z", "+00:00"))


def versao_semver(tag: str) -> tuple[int, int, int] | None:
    """'v1.2.3', '1.2', 'release-2.0.1' -> (maior, menor, patch). None se nao for SemVer."""
    achado = _SEMVER.match(tag.strip())
    if not achado:
        return None
    maior, menor, patch = achado.groups()
    return int(maior), int(menor), int(patch or 0)


def corretiva_semver_patch(release: Deploy, anterior: Deploy | None) -> bool:
    """Heuristica v0: mesma versao maior.menor da anterior e patch maior."""
    if anterior is None:
        return False
    atual, previa = versao_semver(release.tag_name), versao_semver(anterior.tag_name)
    if atual is None or previa is None:
        return False
    return atual[:2] == previa[:2] and atual[2] > previa[2]


Heuristica = Callable[[Deploy, "Deploy | None"], bool]


def marcar_corretivas(deploys: list[Deploy], heuristica: Heuristica = corretiva_semver_patch) -> list[bool]:
    """Uma flag por deploy (lista em ordem cronologica), comparando com o deploy anterior."""
    return [heuristica(d, deploys[i - 1] if i else None) for i, d in enumerate(deploys)]


def cfr_entrega(
    deploys: list[Deploy],
    inicio: str,
    fim: str,
    heuristica: Heuristica = corretiva_semver_patch,
) -> dict:
    """Variante (b). `deploys` e o historico em ordem cronologica (pode incluir
    deploys fora da janela: a anterior de uma release da janela importa para a
    heuristica, e uma corretiva logo depois do fim nao conta porque esta fora
    dos dados coletados)."""
    deploys = sorted(deploys, key=lambda d: d.published_at)
    corretivas = marcar_corretivas(deploys, heuristica)
    ini, fim_dt = _parse(inicio), _parse(fim)
    limite_avaliacao = fim_dt - PRAZO_CORRECAO

    avaliadas = falharam = censuradas = 0
    for i, deploy in enumerate(deploys):
        data = _parse(deploy.published_at)
        if not (ini <= data < fim_dt):
            continue
        if data >= limite_avaliacao:
            censuradas += 1
            continue
        avaliadas += 1
        prazo = data + PRAZO_CORRECAO
        if any(
            corretivas[j] and data < _parse(deploys[j].published_at) <= prazo
            for j in range(i + 1, len(deploys))
        ):
            falharam += 1

    na_janela = [i for i, d in enumerate(deploys) if ini <= _parse(d.published_at) < fim_dt]
    return {
        "n_avaliadas": avaliadas,
        "n_falharam": falharam,
        "n_censuradas": censuradas,
        "n_corretivas": sum(1 for i in na_janela if corretivas[i]),
        "cfr": falharam / avaliadas if avaliadas else None,
    }
