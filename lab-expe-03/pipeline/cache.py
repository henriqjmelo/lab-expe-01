from __future__ import annotations

import gzip
import hashlib
import json
import os
import threading
from pathlib import Path
from typing import Any


class CacheDisco:
    def __init__(self, diretorio: str | Path) -> None:
        self.diretorio = Path(diretorio)
        self.acertos = 0
        self.faltas = 0
        self._trava = threading.Lock()

    def _caminho(self, chave: str) -> Path:
        resumo = hashlib.sha256(chave.encode("utf-8")).hexdigest()
        return self.diretorio / resumo[:2] / f"{resumo}.json.gz"

    def ler(self, chave: str) -> dict[str, Any] | None:
        caminho = self._caminho(chave)
        try:
            with gzip.open(caminho, "rt", encoding="utf-8") as f:
                entrada = json.load(f)
        except FileNotFoundError:
            entrada = None
        except (OSError, ValueError):
            entrada = None
        with self._trava:
            if entrada is None:
                self.faltas += 1
            else:
                self.acertos += 1
        return entrada

    def gravar(self, chave: str, entrada: dict[str, Any]) -> None:
        caminho = self._caminho(chave)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        temporario = caminho.with_suffix(f".tmp{os.getpid()}-{threading.get_ident()}")
        with gzip.open(temporario, "wt", encoding="utf-8") as f:
            json.dump(entrada, f)
        os.replace(temporario, caminho)
