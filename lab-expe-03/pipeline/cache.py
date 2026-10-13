"""Cache em disco das respostas da API (issue #136, usado na coleta completa da #139).

Cada resposta vira um arquivo JSON comprimido com gzip, nomeado pelo SHA-256 da
chave (URL da chamada, ou consulta + variaveis no GraphQL). Rodar o pipeline de
novo depois de um Ctrl+C ou de uma queda le do disco o que ja foi baixado e so
gasta cota com o que falta.

A gravacao e atomica (arquivo temporario + rename): uma interrupcao no meio da
escrita nunca deixa um JSON pela metade que quebraria a retomada.
"""

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
        self._trava = threading.Lock()  # contadores atualizados por varias threads

    def _caminho(self, chave: str) -> Path:
        resumo = hashlib.sha256(chave.encode("utf-8")).hexdigest()
        # Dois niveis de subpasta pra nao juntar dezenas de milhares de arquivos num diretorio so.
        return self.diretorio / resumo[:2] / f"{resumo}.json.gz"

    def ler(self, chave: str) -> dict[str, Any] | None:
        caminho = self._caminho(chave)
        try:
            with gzip.open(caminho, "rt", encoding="utf-8") as f:
                entrada = json.load(f)
        except FileNotFoundError:
            entrada = None
        except (OSError, ValueError):
            # Arquivo corrompido (nao deveria acontecer com a escrita atomica): trata como falta.
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
        # pid + thread: duas threads gravando a mesma chave nao disputam o mesmo temporario.
        temporario = caminho.with_suffix(f".tmp{os.getpid()}-{threading.get_ident()}")
        with gzip.open(temporario, "wt", encoding="utf-8") as f:
            json.dump(entrada, f)
        os.replace(temporario, caminho)
