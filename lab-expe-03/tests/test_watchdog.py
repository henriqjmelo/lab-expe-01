from __future__ import annotations

import time

from pipeline.github_client import GitHubClient
from pipeline.watchdog import Watchdog


class ClienteFalso:
    def __init__(self, ultima_atividade=0.0, pausado_ate=0.0):
        self.ultima_atividade = ultima_atividade
        self.pausado_ate = pausado_ate


def watchdog(cliente, agora, disparos):
    return Watchdog(cliente, 600, disparos.append, relogio=lambda: agora)


def test_dispara_quando_parado_alem_do_limite():
    disparos = []
    assert watchdog(ClienteFalso(ultima_atividade=0), 601, disparos).verificar()
    assert disparos == [601]


def test_nao_dispara_dentro_do_limite():
    disparos = []
    assert not watchdog(ClienteFalso(ultima_atividade=0), 599, disparos).verificar()
    assert disparos == []


def test_pausa_de_cota_em_andamento_nao_conta_como_travado():
    disparos = []
    cliente = ClienteFalso(ultima_atividade=0, pausado_ate=3000)
    assert not watchdog(cliente, 2000, disparos).verificar()


def test_tempo_parado_conta_a_partir_do_fim_da_pausa():
    cliente = ClienteFalso(ultima_atividade=0, pausado_ate=3000)
    assert watchdog(cliente, 3500, []).parado_ha() == 500
    assert watchdog(cliente, 3700, []).verificar() is True


def test_thread_do_watchdog_dispara_e_para():
    disparos = []
    w = Watchdog(ClienteFalso(ultima_atividade=-1000), 1, disparos.append, intervalo=0.01, relogio=time.monotonic)
    w.iniciar()
    limite = time.monotonic() + 2
    while not disparos and time.monotonic() < limite:
        time.sleep(0.01)
    w.parar()
    assert len(disparos) == 1


def test_cliente_registra_pausas_longas():
    mensagens = []
    c = GitHubClient("t", dormir=lambda s: None, agora=lambda: 100.0, registrar=mensagens.append)
    c._esperar_reset({"X-RateLimit-Reset": "160"})
    c._pausar(1.0)
    assert mensagens == ["  pausa de 61 s: cota esgotada"]


def test_cliente_marca_atividade_e_pausas():
    esperas = []
    c = GitHubClient("t", dormir=esperas.append, agora=lambda: 100.0)
    antes = c.ultima_atividade
    c._esperar_reset({"X-RateLimit-Reset": "160"})
    assert esperas == [61.0]
    assert c.pausado_ate >= antes + 61.0
