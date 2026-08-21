"""Valida nulos e outliers das métricas de RQ01 e RQ02."""

import csv
import statistics
from datetime import datetime, timezone


DATA_PATH = "data/repositorios.csv"


def load_rows(path: str = DATA_PATH) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _iqr_outliers(values: list[float]) -> tuple[float, float, list[float]]:
    quartiles = statistics.quantiles(values, n=4)
    q1, q3 = quartiles[0], quartiles[2]
    upper_bound = q3 + 1.5 * (q3 - q1)
    outliers = [value for value in values if value > upper_bound]
    return upper_bound, q3 - q1, outliers


def validate_created_at(rows: list[dict]) -> None:
    values = [r["createdAt"] for r in rows if r["createdAt"] not in ("", None)]
    nulls = len(rows) - len(values)
    parsed = [datetime.fromisoformat(value.replace("Z", "+00:00")) for value in values]
    now = datetime.now(timezone.utc)

    # a metrica de RQ01 e a idade, entao os outliers sao analisados sobre ela e
    # nos dois limites: repositorios muito mais antigos ou muito mais novos que
    # o restante. Olhar so o limite superior de createdAt esconderia justamente
    # os projetos mais antigos, que sao o caso interessante aqui.
    ages = sorted((now - date).days / 365.25 for date in parsed)
    quartiles = statistics.quantiles(ages, n=4)
    q1, q3 = quartiles[0], quartiles[2]
    iqr = q3 - q1
    lower_bound, upper_bound = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    old_outliers = [age for age in ages if age > upper_bound]
    new_outliers = [age for age in ages if age < lower_bound]

    print("--- RQ01 (createdAt / idade) ---")
    print(f"nulos: {nulls}/{len(rows)}")
    print(f"data mais antiga: {min(parsed).date()} | mais recente: {max(parsed).date()}")
    print(f"datas no futuro: {sum(1 for date in parsed if date > now)}")
    print(
        f"idade em anos: min={ages[0]:.1f} max={ages[-1]:.1f} "
        f"mediana={statistics.median(ages):.1f}"
    )
    print(
        f"outliers de idade (fora de {lower_bound:.1f}-{upper_bound:.1f} anos, limite IQR): "
        f"{len(old_outliers)} mais antigos, {len(new_outliers)} mais recentes"
    )


def validate_pull_requests(rows: list[dict]) -> None:
    values = [int(r["pullRequests"]) for r in rows if r["pullRequests"] not in ("", None)]
    nulls = len(rows) - len(values)
    upper_bound, _, outliers = _iqr_outliers([float(value) for value in values])

    print("--- RQ02 (pullRequests MERGED) ---")
    print(f"nulos: {nulls}/{len(rows)}")
    print(f"min={min(values)} max={max(values)} mediana={statistics.median(values)}")
    print(f"outliers (> {upper_bound:.1f}, limite IQR): {len(outliers)} repositorios")
    print(f"repositorios sem pull request aceito: {sum(1 for value in values if value == 0)}")


if __name__ == "__main__":
    rows = load_rows()
    print(f"Total de repositorios: {len(rows)}\n")
    validate_created_at(rows)
    print()
    validate_pull_requests(rows)