from __future__ import annotations

import re

TIPOS = ("feat", "fix", "perf", "refactor", "docs", "test", "ci", "build", "chore", "style", "revert")

_CONVENCIONAL = re.compile(r"^(?P<tipo>[a-zA-Z]+)(\([^)]*\))?!?:\s")
_REVERT_GIT = re.compile(r'^Revert\s+"')

LIMIAR_ADOCAO = 0.5


def tipo_commit(mensagem: str | None) -> str | None:
    texto = (mensagem or "").strip()
    if _REVERT_GIT.match(texto):
        return "revert"
    achado = _CONVENCIONAL.match(texto)
    if not achado:
        return None
    tipo = achado.group("tipo").lower()
    return tipo if tipo in TIPOS else None


def distribuicao_trabalho(mensagens: list[str | None], limiar: float = LIMIAR_ADOCAO) -> dict:
    tipos = [tipo_commit(m) for m in mensagens]
    n = len(tipos)
    convencionais = [t for t in tipos if t is not None]
    nc = len(convencionais)

    def fracao(tipo: str) -> float | None:
        return convencionais.count(tipo) / nc if nc else None

    return {
        "n_commits": n,
        "prop_convencional": nc / n if n else None,
        "adota_convencional": (nc / n >= limiar) if n else False,
        "prop_fix": fracao("fix"),
        "prop_feat": fracao("feat"),
        "prop_revert": tipos.count("revert") / n if n else None,
    }
