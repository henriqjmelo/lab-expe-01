import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for caminho in (RAIZ, RAIZ / "scripts"):
    if str(caminho) not in sys.path:
        sys.path.insert(0, str(caminho))
