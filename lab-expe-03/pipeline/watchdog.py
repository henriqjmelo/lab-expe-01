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
