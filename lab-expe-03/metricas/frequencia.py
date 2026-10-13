"""Deployment frequency (RQ 01), issue #139.

Releases publicadas na janela / numero de semanas da janela (~= 52,1 para 12
meses). A mesma funcao serve para as tres unidades de deploy da RQ 07: release,
release + pre-release e tag - quem escolhe a lista de datas e o chamador.
"""

from __future__ import annotations

from datetime import datetime


def _parse(data: str) -> datetime:
    return datetime.fromisoformat(data.replace("Z", "+00:00"))


def semanas_da_janela(inicio: str, fim: str) -> float:
    return (_parse(fim) - _parse(inicio)).total_seconds() / (7 * 86400)


def na_janela(data: str | None, inicio: str, fim: str) -> bool:
    if not data:
        return False
    return _parse(inicio) <= _parse(data) < _parse(fim)


def frequencia_semanal(datas_deploy: list[str], inicio: str, fim: str) -> float:
    """Deploys por semana. Datas fora da janela nao contam."""
    n = sum(1 for d in datas_deploy if na_janela(d, inicio, fim))
    return n / semanas_da_janela(inicio, fim)
