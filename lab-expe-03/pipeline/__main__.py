"""Comando unico do pipeline: python -m pipeline --config config.yaml"""

import sys

from pipeline.executar import main

sys.exit(main())
