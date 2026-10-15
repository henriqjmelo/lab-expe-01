from __future__ import annotations

from metricas.cfr import Deploy
from metricas.corretiva import (
    VERSOES,
    construir_corretiva_combinada,
    construir_corretiva_mensagens,
    construir_corretiva_nome_da_tag,
    construir_corretiva_patch_e_poucos_commits,
)

ANTERIOR = Deploy("v1.2.0", "2026-05-10T00:00:00Z")
ATUAL = Deploy("v1.2.1", "2026-05-12T00:00:00Z")


def test_mensagens_com_fix_marca_corretiva():
    heuristica = construir_corretiva_mensagens()({"v1.2.1": ["fix: corrige crash no boot"]})

    assert heuristica(ATUAL, ANTERIOR) is True


def test_mensagens_so_com_feat_nao_marca_corretiva():
    heuristica = construir_corretiva_mensagens()({"v1.2.1": ["feat: adiciona exportacao em PDF"]})

    assert heuristica(ATUAL, ANTERIOR) is False


def test_mensagens_mistura_abaixo_do_limiar_nao_marca():
    mensagens = ["feat: a", "feat: b", "feat: c", "fix: d"]
    heuristica = construir_corretiva_mensagens(limiar_prop=0.5)({"v1.2.1": mensagens})

    assert heuristica(ATUAL, ANTERIOR) is False


def test_mensagens_sem_anterior_nunca_marca():
    heuristica = construir_corretiva_mensagens()({"v1.2.1": ["fix: corrige crash"]})

    assert heuristica(ATUAL, None) is False


def test_mensagens_release_sem_commit_registrado_nao_marca():
    heuristica = construir_corretiva_mensagens()({})

    assert heuristica(ATUAL, ANTERIOR) is False


def test_patch_e_poucos_commits_marca_quando_os_dois_batem():
    heuristica = construir_corretiva_patch_e_poucos_commits(limite_commits=3)({"v1.2.1": ["fix: a", "fix: b"]})

    assert heuristica(ATUAL, ANTERIOR) is True


def test_patch_e_poucos_commits_nao_marca_com_muitos_commits():
    muitos = [f"fix: {i}" for i in range(10)]
    heuristica = construir_corretiva_patch_e_poucos_commits(limite_commits=3)({"v1.2.1": muitos})

    assert heuristica(ATUAL, ANTERIOR) is False


def test_patch_e_poucos_commits_exige_semver_patch():
    # minor subiu, nao e patch: mesmo com poucos commits nao marca
    minor = Deploy("v1.3.0", "2026-05-12T00:00:00Z")
    heuristica = construir_corretiva_patch_e_poucos_commits()({"v1.3.0": ["fix: a"]})

    assert heuristica(minor, ANTERIOR) is False


def test_nome_da_tag_com_hotfix_marca():
    heuristica = construir_corretiva_nome_da_tag()({})
    tag = Deploy("v1.2.1-hotfix", "2026-05-12T00:00:00Z")

    assert heuristica(tag, ANTERIOR) is True


def test_nome_da_tag_sem_palavra_chave_nao_marca():
    heuristica = construir_corretiva_nome_da_tag()({})

    assert heuristica(ATUAL, ANTERIOR) is False


def test_combinada_marca_por_semver_mesmo_sem_sinal_de_mensagem():
    heuristica = construir_corretiva_combinada()({"v1.2.1": ["feat: algo"]})

    assert heuristica(ATUAL, ANTERIOR) is True  # patch do semver ja basta


def test_combinada_marca_por_mensagem_quando_nao_e_semver_patch():
    minor = Deploy("v1.3.0", "2026-05-12T00:00:00Z")
    heuristica = construir_corretiva_combinada()({"v1.3.0": ["fix: corrige regressao"]})

    assert heuristica(minor, ANTERIOR) is True


def test_combinada_nao_marca_quando_nenhum_sinal_bate():
    minor = Deploy("v1.3.0", "2026-05-12T00:00:00Z")
    heuristica = construir_corretiva_combinada()({"v1.3.0": ["feat: nova tela"]})

    assert heuristica(minor, ANTERIOR) is False


def test_tag_fora_do_semver_nao_quebra_nenhuma_versao():
    fora_do_padrao = Deploy("release-experimental", "2026-05-12T00:00:00Z")
    for construtor in VERSOES.values():
        heuristica = construtor({"release-experimental": ["fix: algo"]})
        heuristica(fora_do_padrao, ANTERIOR)  # so nao pode levantar excecao


def test_primeira_release_nunca_marca_em_nenhuma_versao():
    for construtor in VERSOES.values():
        heuristica = construtor({"v1.2.0": ["fix: algo"]})
        assert heuristica(ANTERIOR, None) is False


def test_versoes_tem_as_quatro_chaves_esperadas():
    assert set(VERSOES) == {"v0_semver_patch", "v1_mensagens", "v2_patch_poucos_commits", "v3_combinada"}
