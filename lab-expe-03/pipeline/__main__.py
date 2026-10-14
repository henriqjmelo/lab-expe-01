import os
import sys

from pipeline.executar import main

codigo = main()
sys.stdout.flush()
sys.stderr.flush()
os._exit(codigo)
