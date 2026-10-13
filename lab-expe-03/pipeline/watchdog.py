"""Watchdog da coleta (issue #139).

Depois de uma queda de internet, conexoes TLS podem ficar penduradas: o
processo nao morre, so deixa de avancar, e o supervisor (scripts/coletar.sh)
nao percebe. O watchdog olha o cliente a cada 30 s; se nenhuma chamada terminou
ha mais de `limite` segundos e nao ha pausa legitima em andamento (espera de
cota ou backoff), chama `ao_travar` - no pipeline, encerrar com codigo 75 para
o supervisor reiniciar e retomar pelo cache.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any


class Watchdog:
    def __init__(
        self,
        cliente: Any,
        limite: float,
        ao_travar: Callable[[float], None],
        *,
        intervalo: float = 30.0,
        relogio: Callable[[], float] = time.monotonic,
    ) -> None:
        self.cliente = cliente
        self.limite = limite
        self.ao_travar = ao_travar
        self.intervalo = intervalo
        self._relogio = relogio
        self._parar = threading.Event()

    def parado_ha(self) -> float:
        """Segundos sem atividade, descontando pausas legitimas (0 durante uma pausa)."""
        agora = self._relogio()
        if agora < self.cliente.pausado_ate:
            return 0.0
        referencia = max(self.cliente.ultima_atividade, self.cliente.pausado_ate)
        return agora - referencia

    def verificar(self) -> bool:
        parado = self.parado_ha()
        if parado > self.limite:
            self.ao_travar(parado)
            return True
        return False

    def iniciar(self) -> None:
        def laco() -> None:
            while not self._parar.wait(self.intervalo):
                if self.verificar():
                    return

        threading.Thread(target=laco, name="watchdog", daemon=True).start()

    def parar(self) -> None:
        self._parar.set()
