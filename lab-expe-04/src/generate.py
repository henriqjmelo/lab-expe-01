from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

TipoSituacao = Literal["A", "B"]
COLUNAS = ("loc", "defeitos")


def _matriz_covariancia(correlacao: float) -> np.ndarray:
    if not -1 <= correlacao <= 1:
        raise ValueError("A correlação precisa estar entre -1 e 1.")
    return np.array([[1.0, correlacao], [correlacao, 1.0]])


def gerar_normal(n: int, correlacao: float, rng: np.random.Generator) -> pd.DataFrame:
    if n < 2:
        raise ValueError("n precisa ser pelo menos 2.")
    dados = rng.multivariate_normal([0.0, 0.0], _matriz_covariancia(correlacao), size=n)
    return pd.DataFrame(dados, columns=COLUNAS)


def gerar_lognormal(
    n: int,
    correlacao: float,
    rng: np.random.Generator,
    loc_log_mu: float,
    loc_log_sigma: float,
    def_log_mu: float = 0.0,
    def_log_sigma: float = 1.0,
) -> pd.DataFrame:
    if n < 2:
        raise ValueError("n precisa ser pelo menos 2.")
    if loc_log_sigma <= 0 or def_log_sigma <= 0:
        raise ValueError("Os desvios-padrão em escala log devem ser positivos.")
    latentes = rng.multivariate_normal([0.0, 0.0], _matriz_covariancia(correlacao), size=n)
    log_loc = loc_log_mu + loc_log_sigma * latentes[:, 0]
    log_defeitos = def_log_mu + def_log_sigma * latentes[:, 1]
    return pd.DataFrame({"loc": np.exp(log_loc), "defeitos": np.exp(log_defeitos)})


def gerar_situacao(
    tipo: TipoSituacao,
    n: int,
    correlacao: float,
    rng: np.random.Generator,
    parametros: dict[str, float] | None = None,
) -> pd.DataFrame:
    if tipo == "A":
        return gerar_normal(n, correlacao, rng)
    if tipo == "B":
        if parametros is None:
            raise ValueError("A situação B exige parâmetros estimados dos dados reais.")
        return gerar_lognormal(n, correlacao, rng, **parametros)
    raise ValueError(f"Situação desconhecida: {tipo}")
