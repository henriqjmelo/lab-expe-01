"""Primitivas estatisticas do plano de analise: efeito, bootstrap e correcoes.

Nada aqui conhece o Lab05: sao funcoes puras sobre arrays, para poderem ser
testadas isoladamente contra referencias conhecidas.
"""
from __future__ import annotations

import numpy as np
from scipy import stats

SEMENTE_BOOTSTRAP = 42
REAMOSTRAS = 10_000


def hedges_g(a: np.ndarray, b: np.ndarray) -> float:
    """Efeito padronizado a - b, com a correcao de amostra pequena.

    O d de Cohen usa o desvio combinado; o g de Hedges multiplica por J, que
    corrige o vies que o d tem com n pequeno. Com n = 30 por grupo a correcao e
    de ~1,3%, mas e de graca.
    """
    na, nb = len(a), len(b)
    gl = na + nb - 2
    s = np.sqrt(((na - 1) * np.var(a, ddof=1) + (nb - 1) * np.var(b, ddof=1)) / gl)
    if s == 0:
        return 0.0
    d = (np.mean(a) - np.mean(b)) / s
    j = 1 - 3 / (4 * gl - 1)
    return float(d * j)


def cliff_delta(a: np.ndarray, b: np.ndarray) -> float:
    """P(a > b) - P(a < b), em [-1, 1]. Nao supoe distribuicao nenhuma.

    E o companheiro natural do Mann-Whitney: a estatistica U e exatamente a
    contagem de pares em que a > b, e o delta e essa contagem normalizada.
    """
    a = np.asarray(a)[:, None]
    b = np.asarray(b)[None, :]
    return float(((a > b).sum() - (a < b).sum()) / (a.size * b.size))


def razao_media_geometrica(zgc: np.ndarray, g1: np.ndarray) -> float:
    """Razao ZGC/G1 das medias geometricas - o efeito pratico no caminho do Welch."""
    return float(np.exp(np.mean(np.log(zgc)) - np.mean(np.log(g1))))


def razao_mediana(zgc: np.ndarray, g1: np.ndarray) -> float:
    """Razao ZGC/G1 das medianas - o efeito pratico no caminho do Mann-Whitney."""
    return float(np.median(zgc) / np.median(g1))


def _jackknife(zgc: np.ndarray, g1: np.ndarray, estat) -> np.ndarray:
    """Valores da estatistica deixando uma observacao de fora por vez.

    Em duas amostras, o jackknife percorre as duas e junta os resultados: e
    dali que sai a aceleracao do BCa, que corrige a assimetria da distribuicao
    da estatistica.
    """
    fora_zgc = [estat(np.delete(zgc, i), g1) for i in range(len(zgc))]
    fora_g1 = [estat(zgc, np.delete(g1, i)) for i in range(len(g1))]
    return np.asarray(fora_zgc + fora_g1, dtype=float)


def ic_bootstrap_bca(
    zgc: np.ndarray,
    g1: np.ndarray,
    estat=razao_media_geometrica,
    conf: float = 0.95,
    reamostras: int = REAMOSTRAS,
    semente: int = SEMENTE_BOOTSTRAP,
) -> tuple[float, float, float]:
    """Devolve (estimativa, limite inferior, limite superior) pelo percentil BCa.

    BCa = bias-corrected and accelerated. O percentil simples supoe que a
    distribuicao bootstrap e centrada e simetrica; uma razao de medias nao e
    nenhuma das duas coisas. O BCa corrige as duas, e por isso e o metodo
    pre-registrado no plano.
    """
    zgc = np.asarray(zgc, dtype=float)
    g1 = np.asarray(g1, dtype=float)
    ponto = estat(zgc, g1)

    rng = np.random.default_rng(semente)
    i_z = rng.integers(0, len(zgc), size=(reamostras, len(zgc)))
    i_g = rng.integers(0, len(g1), size=(reamostras, len(g1)))
    reps = np.array([estat(zgc[a], g1[b]) for a, b in zip(i_z, i_g)], dtype=float)
    reps = reps[np.isfinite(reps)]
    if reps.size == 0:
        return ponto, float("nan"), float("nan")

    fracao = float((reps < ponto).mean())
    if fracao in (0.0, 1.0):  # distribuicao degenerada: cai no percentil simples
        baixo, alto = np.percentile(reps, [(1 - conf) / 2 * 100, (1 + conf) / 2 * 100])
        return ponto, float(baixo), float(alto)

    z0 = stats.norm.ppf(fracao)
    jack = _jackknife(zgc, g1, estat)
    desvio = jack.mean() - jack
    denominador = 6 * (np.sum(desvio**2) ** 1.5)
    a = 0.0 if denominador == 0 else float(np.sum(desvio**3) / denominador)

    z_baixo, z_alto = stats.norm.ppf([(1 - conf) / 2, (1 + conf) / 2])
    def ajusta(z):
        return stats.norm.cdf(z0 + (z0 + z) / (1 - a * (z0 + z)))
    p_baixo, p_alto = ajusta(z_baixo) * 100, ajusta(z_alto) * 100
    if not np.isfinite(p_baixo) or not np.isfinite(p_alto) or p_baixo >= p_alto:
        p_baixo, p_alto = (1 - conf) / 2 * 100, (1 + conf) / 2 * 100
    baixo, alto = np.percentile(reps, [p_baixo, p_alto])
    return ponto, float(baixo), float(alto)


def holm(ps: list[float]) -> list[float]:
    """Correcao de Holm-Bonferroni. Controla o FWER e nunca rejeita menos que Bonferroni.

    Ordena os p do menor para o maior e multiplica o k-esimo por (m - k + 1):
    o primeiro por m, o segundo por m-1, e assim por diante. O passo de maximo
    acumulado garante monotonicidade (um p maior nunca sai menor que um menor).
    """
    ps = np.asarray(ps, dtype=float)
    m = len(ps)
    if m == 0:
        return []
    ordem = np.argsort(ps)
    ajustados = np.maximum.accumulate(ps[ordem] * np.arange(m, 0, -1))
    saida = np.empty(m)
    saida[ordem] = np.minimum(ajustados, 1.0)
    return [float(x) for x in saida]


def benjamini_hochberg(ps: list[float]) -> list[float]:
    """Correcao BH (FDR). Usada so na familia exploratoria.

    Holm controla a chance de QUALQUER falso positivo; BH controla a PROPORCAO
    esperada de falsos positivos entre as rejeicoes. Para levantar pistas, que
    e o papel das exploratorias, controlar FDR e o certo - e e menos
    conservador, o que e aceitavel porque nenhuma conclusao do trabalho se
    apoia nelas.
    """
    ps = np.asarray(ps, dtype=float)
    m = len(ps)
    if m == 0:
        return []
    ordem = np.argsort(ps)
    escalados = ps[ordem] * m / np.arange(1, m + 1)
    ajustados = np.minimum.accumulate(escalados[::-1])[::-1]
    saida = np.empty(m)
    saida[ordem] = np.minimum(ajustados, 1.0)
    return [float(x) for x in saida]
