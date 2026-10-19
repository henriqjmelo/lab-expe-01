from __future__ import annotations

from collections.abc import Callable

from metricas.cfr import Deploy, Heuristica, corretiva_semver_patch
from metricas.fluxo import tipo_commit

MensagensPorTag = dict[str, list[str | None]]
ConstrutorHeuristica = Callable[[MensagensPorTag], Heuristica]

LIMIAR_PROP_FIX = 0.5
LIMITE_POUCOS_COMMITS = 3
PALAVRAS_TAG_CORRETIVA = ("hotfix", "patch")


def _tipos(mensagens: list[str | None]) -> list[str | None]:
    return [tipo_commit(m) for m in mensagens]


def construir_corretiva_mensagens(limiar_prop: float = LIMIAR_PROP_FIX) -> ConstrutorHeuristica:
    def construtor(mensagens_por_tag: MensagensPorTag) -> Heuristica:
        def heuristica(release: Deploy, anterior: Deploy | None) -> bool:
            if anterior is None:
                return False
            mensagens = mensagens_por_tag.get(release.tag_name, [])
            if not mensagens:
                return False
            tipos = _tipos(mensagens)
            sinalizados = sum(1 for t in tipos if t in ("fix", "revert"))
            return sinalizados / len(tipos) >= limiar_prop
        return heuristica
    return construtor


def construir_corretiva_patch_e_poucos_commits(limite_commits: int = LIMITE_POUCOS_COMMITS) -> ConstrutorHeuristica:
    def construtor(mensagens_por_tag: MensagensPorTag) -> Heuristica:
        def heuristica(release: Deploy, anterior: Deploy | None) -> bool:
            if not corretiva_semver_patch(release, anterior):
                return False
            n = len(mensagens_por_tag.get(release.tag_name, []))
            return 0 < n <= limite_commits
        return heuristica
    return construtor


def construir_corretiva_nome_da_tag() -> ConstrutorHeuristica:
    def construtor(_mensagens_por_tag: MensagensPorTag) -> Heuristica:
        def heuristica(release: Deploy, anterior: Deploy | None) -> bool:
            if anterior is None:
                return False
            nome = release.tag_name.lower()
            return any(palavra in nome for palavra in PALAVRAS_TAG_CORRETIVA)
        return heuristica
    return construtor


def construir_corretiva_combinada(limiar_prop: float = LIMIAR_PROP_FIX) -> ConstrutorHeuristica:
    por_mensagem = construir_corretiva_mensagens(limiar_prop)
    por_nome = construir_corretiva_nome_da_tag()

    def construtor(mensagens_por_tag: MensagensPorTag) -> Heuristica:
        heuristica_mensagem = por_mensagem(mensagens_por_tag)
        heuristica_nome = por_nome(mensagens_por_tag)

        def heuristica(release: Deploy, anterior: Deploy | None) -> bool:
            return (
                corretiva_semver_patch(release, anterior)
                or heuristica_mensagem(release, anterior)
                or heuristica_nome(release, anterior)
            )
        return heuristica
    return construtor


VERSOES: dict[str, ConstrutorHeuristica] = {
    "v0_semver_patch": lambda _mensagens_por_tag: corretiva_semver_patch,
    "v1_mensagens": construir_corretiva_mensagens(),
    "v2_patch_poucos_commits": construir_corretiva_patch_e_poucos_commits(),
    "v3_combinada": construir_corretiva_combinada(),
}
