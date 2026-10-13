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
    n = sum(1 for d in datas_deploy if na_janela(d, inicio, fim))
    return n / semanas_da_janela(inicio, fim)
