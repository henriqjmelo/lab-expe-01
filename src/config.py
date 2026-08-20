import os

from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise RuntimeError(
        "GITHUB_TOKEN não encontrado. Copie .env.example para .env e "
        "preencha com um token gerado em https://github.com/settings/tokens"
    )
