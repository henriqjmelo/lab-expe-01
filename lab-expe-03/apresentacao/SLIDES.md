---
marp: true
theme: default
paginate: true
header: 'Laboratório de Experimentação de Software · Lab03'
---

<!-- _paginate: false -->
<!-- _header: '' -->

# Mineração de métricas DORA em repositórios open-source

### E o que acontece quando a gente testa se elas medem o que dizem medir

**Guilherme Costa · Henrique Jardim Melo · Gabriel Afonso**
Engenharia de Software, 6º período

---

## O problema

As métricas DORA foram definidas para **equipes que controlam o próprio pipeline** e sabem, por definição interna, o que é um "deploy" e o que é uma "falha em produção".

Repositórios open-source no GitHub **não oferecem nenhuma das duas coisas**.

O que existe são rastros: releases, workflow runs, commits, tags.

> Medir DORA aqui não é aplicar uma definição. É **escolher proxies** — e assumir o custo dessa escolha.

---

## O que fizemos além do pedido

| Escopo do enunciado | O que entregamos |
| :--- | :--- |
| 300 repositórios | **900**, em 3 amostras independentes |
| Calcular as 4 métricas | Calcular **e validar** segundo a IEEE 1061 |
| Validar a heurística | Validar — **e reprovar** |
| RQ01–RQ08 | + análise de distribuições, índice contínuo, lente alternativa |

---

## Desenho

- **Janela:** 12 meses
- **Inclusão:** ≥ 5 releases e ≥ 50 workflow runs válidos
- **Amostras:** 3 × 300, sementes 42 / 2026 / 2027, **zero sobreposição**
- **Proxies:**
  - deploy → release publicada
  - falha → (a) falha de CI · (b) release corretiva em ≤ 7 dias
  - recuperação → 1ª falha após sucesso → próximo sucesso

Pipeline próprio, sem bibliotecas de acesso à API. Dados versionados: quem replicar **não precisa recoletar**.

---

## RQ01–RQ04 — os números (n = 900)

| Métrica | Mediana | IQR |
| :--- | ---: | :--- |
| Frequência de deploy | **0,35 release/semana** | 0,19 – 0,84 |
| Lead time (a), por release | **12,0 dias** | 3,0 – 37,4 |
| Lead time (b), por commit | **9,0 dias** | 2,5 – 28,1 |
| CFR (a), falha de CI | **5,3%** | 2,2 – 11,2% |
| CFR (b), release corretiva | **25,0%** | 6,2 – 50,3% |
| Recuperação | **3,1 h** | 0,9 – 17,3 |

Uma release a cada ~20 dias. **Não é entrega contínua** — é entrega em ciclos.

---

## RQ05 — velocidade × estabilidade

O DORA afirma que **não** há trade-off.

Encontramos correlação **positiva**: ρ = 0,60 entre frequência e CFR (b).

Parecia contradizer a tese.

**Não contradiz. É artefato da definição.** → próximo slide

---

## RQ06 e RQ07

**RQ06 — o que explica desempenho?** Quase nada do que se esperava.

- Estrelas: ε² = 0,008 · Contribuidores: ε² = 0,022
- Nenhum sobrevive à correção de Holm
- Só idade mostra efeito (ε² = 0,109)

**RQ07 — a classificação é estável?** Não.

- **27,7% a 36,0%** dos repositórios mudam de faixa ao trocar a definição operacional

---

## A validação manual: o resultado mais duro

3 pessoas × 60 repositórios × 300 releases, rotulados **independentemente**. 1.080 julgamentos.

**Nenhuma das 4 versões da heurística atinge o F1 mínimo de 0,70.**

| Versão | Precisão | Recall | F1 |
| :--- | ---: | ---: | ---: |
| v0 — *a que gerou o dataset* | **36,5%** | 69,2% | 0,478 |
| v1 mensagens | 94,4% | 21,8% | 0,354 |
| v2 patch + poucos commits | 59,5% | 28,2% | 0,383 |
| v3 combinada | 37,7% | 73,1% | **0,498** |

De cada 3 releases que a v0 marca como corretivas, **2 não são**.

---

## E o problema é mais fundo

κ de Fleiss entre os três avaliadores humanos:

| Dimensão | κ | Interpretação |
| :--- | ---: | :--- |
| Tipo do projeto | 0,872 | quase perfeita |
| Releases são entrega real | 0,157 | leve* |
| **Release é corretiva** | **0,504** | **moderada** |

\* paradoxo do kappa: 90% de concordância bruta, mas 95,6% dos rótulos são "sim"

Prevalência de "sim" em `corretiva`: **16,7% a 37,3%** entre avaliadores.

> Não é só que a regra automática é ruim. **O conceito é ambíguo para humanos também.**

---

## O CFR (b) mede cadência, não falha

Quem publica mais releases tem **mais oportunidade** de ter uma release seguida por outra em ≤ 7 dias.

| Correlação com frequência de deploy | ρ |
| :--- | ---: |
| Oportunidade de observação | **0,784** |
| CFR (b) bruto | 0,604 |
| **CFR (b) condicionado pela oportunidade** | **−0,039** (p = 0,52) |

A correlação da RQ05 **desaparece**.

Testamos também confusão por tamanho: o ρ cai no máximo 0,059. Não é porte do projeto — é a definição da métrica.

---

## As faixas DORA quase não discriminam

O que as faixas separam bem são **as variáveis que as definem**:

| Atributo | ε² |
| :--- | ---: |
| Estrelas | 0,008 |
| Contribuidores | 0,022 |
| CFR (b) — *componente da própria faixa* | 0,379 |
| Frequência de deploy — *controle tautológico* | 0,403 |

Isso é validade convergente, **não poder discriminante**.

**Proposta:** índice contínuo por posto percentílico. As faixas retêm só **63,2%** da variância, e **8,2%** dos pares entre faixas aparecem invertidos.

---

## DORA não é *a* medida — é *uma* medida

Mesmos repositórios, lente de fluxo por pull request (CHAOSS / SPACE):

| Par | ρ | Variância compartilhada |
| :--- | ---: | ---: |
| Lead time: release × PR | 0,319 | 10% |
| Ritmo: releases × PRs/semana | 0,460 | 21% |
| **CFR (b) × aceitação de PR** | **0,044** | **0,2%** (n.s.) |

Nenhum par chega a ρ = 0,7.

Trocando o proxy de falha, o mesmo conjunto é **99% Elite** (reverts), **84% Elite** (CI) ou **38% Elite** (release corretiva).

---

## Reprodutibilidade: 300 → 600 → 900

3 amostras independentes, sementes distintas, zero sobreposição.

- **A1 × A2 são estatisticamente indistinguíveis**: nenhum p significativo, todos \|δ\| < 0,07
- Todas as medianas de 600 e 900 caem **dentro do IC de 300**
- Os intervalos estreitam de **21% a 51%**

**Evidência negativa também conta:** a cobertura da API de Deployments varia entre amostras (31,3% / 41,7% / 43,3%, p = 0,0048) sem causa identificada.

---

## Hipóteses: 5 das 7 refutadas

| | Esperávamos | Encontramos | |
| :-- | :-- | :-- | :-- |
| H01 | ≥ 1 release/semana | 0,35 | ❌ |
| H02 | dias, e (a) > (b) | 13,2 e 8,8 d | ✅ |
| H03 | CFR < 15%, convergentes | 5,3% × 25,0% | ❌ |
| H04 | recuperação < 24 h | 2,8 h | ✅ |
| H05 | correlação nula/negativa | +0,60 | ❌ |
| H06 | fatores com efeito | ε² ≈ 0,01 | ❌ |
| H07 | < 20% mudam de faixa | 27,7–36,0% | ❌ |

As hipóteses foram **reconstruídas após a coleta**, não pré-registradas — declarado na §1.5 e tratado como ameaça aberta.

---

## Ameaças principais

| Ameaça | Status |
| :--- | :--- |
| Release não é deploy | **aberta, por construção** |
| CFR (b) acoplado à cadência | **medida e quantificada** |
| Confusão por tamanho | **testada, não encontrada** |
| Estabilidade entre amostras | **mitigada** |
| Hipóteses pós-coleta | **aberta** |

---

## Conclusões

1. **Os números DORA são fáceis. A validade é que é difícil.**
2. O **CFR (b) não sobrevive à validação** — F1 = 0,478, precisão 36,5% — e boa parte do que ele mede é ritmo de publicação.
3. As **faixas DORA não discriminam** nada além do que as define. Um índice contínuo preserva 36,8% de informação que elas jogam fora.
4. O **DORA é uma lente entre outras**, e lentes legítimas ordenam os mesmos repositórios de forma diferente.
5. Com 900 repositórios em 3 amostras, **os resultados descritivos se reproduzem** — mas reprodutibilidade não é validade.

---

<!-- _paginate: false -->

## Obrigado

**Dados, código e artigo:** `github.com/henriqjmelo/lab-expe-01`

Dataset de 900 repositórios, eventos brutos, 1.080 rótulos humanos e pipeline reprodutível com um comando.
