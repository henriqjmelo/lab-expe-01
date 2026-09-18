# Laboratório 02 — Assistentes de IA vs. Codificação Manual

> **Disciplina:** Laboratório de Experimentação de Software
> **Curso:** Engenharia de Software (6º Período — Noite)
> **Professor:** Danilo Maia
> **Pontuação:** 20 pontos

---

## Integrantes do Grupo

* Henrique Jardim Melo
* Gabriel Afonso
* Guilherme Costa

---

## Links Importantes

* Repositório: `https://github.com/henriqjmelo/lab-expe-01`
* GitHub Projects (v2): `https://github.com/users/henriqjmelo/projects/1`
* Relatório final: `<preencher>`

---

## Contexto

Ferramentas de IA generativa (GitHub Copilot, ChatGPT, Claude, Gemini, etc.) tornaram-se onipresentes no desenvolvimento de software, mas ainda há pouca evidência controlada e reproduzível sobre seu real impacto em produtividade e qualidade — a maior parte do que se ouve é relato anedótico.

Neste laboratório, o objetivo é realizar um **experimento controlado** para avaliar quantitativamente os efeitos do uso de um assistente de IA na resolução de tarefas de programação.

---

## Questões de Pesquisa

| RQ | Pergunta |
| :--- | :--- |
| **RQ1** | O uso de assistente de IA reduz o tempo necessário para resolver uma tarefa de programação? |
| **RQ2** | O uso de assistente de IA reduz a quantidade de defeitos (testes que falham) no código produzido? |
| **RQ3** | O uso de assistente de IA altera a complexidade ciclomática ou a duplicação do código produzido? (métricas via CK — apenas Java — e/ou PMD; usar ferramenta equivalente, como Radon, se a linguagem escolhida não for Java) |

---

## GQM (Goal-Question-Metric)

### Goal

> Analisar o uso de assistentes de IA generativa na resolução de tarefas de programação, com o propósito de comparar seu efeito frente à codificação manual, com respeito a tempo de resolução, qualidade funcional (defeitos) e qualidade estrutural do código produzido, do ponto de vista do grupo pesquisador, no contexto de katas de dificuldade equivalente resolvidos por estudantes de graduação sob condições controladas (crossover within-subject, time-boxed).

As RQ1–RQ3 acima são as *Questions* do GQM. Cabe ao grupo escolher, entre as métricas candidatas abaixo, quais usar para responder cada RQ — a escolha e a justificativa devem constar no **Desenho do Experimento (Passo 1)** e no **Relatório Final**.

### RQ1 — Tempo (métricas candidatas)

* **Tempo até passar em todos os testes de aceitação ("time-to-green")** — métrica primária recomendada.
* Trial que atinge o time-box (35 min) sem sucesso deve ser registrado como **censurado em 35 min**, não descartado — descartar distorce a comparação a favor do tratamento com mais falhas.
* Métrica agregada recomendada: **mediana** por tratamento (não a média), dado o N pequeno (4–6 trials/integrante) e a sensibilidade da média a outliers.
* *Opcional/exploratória:* nº de prompts/interações com o assistente de IA — não obrigatória, mas útil para discussão qualitativa.

### RQ2 — Defeitos (métricas candidatas)

* **Taxa de sucesso:** % de testes de aceitação passando ao final do time-box — mais robusta que a contagem bruta, pois normaliza katas com números diferentes de testes.
* **Nº absoluto de testes falhando** ao final do tempo — métrica complementar, mais simples de reportar.
* *Opcional:* densidade de defeitos (testes falhando / KLOC), para comparar katas de tamanhos bem diferentes.

### RQ3 — Estrutura do código (métricas candidatas)

* **Complexidade ciclomática média (McCabe)** por método/função — via CK (Java, métrica WMC/complexity) ou Radon `cc` (Python).
* **Duplicação de código:** % de linhas duplicadas via PMD CPD (Java) ou ferramenta equivalente (ex.: `jscpd` para Python/JS, se Radon não cobrir duplicação).
* **LOC (linhas de código) como métrica de controle** — obrigatória sempre que reportar complexidade/duplicação: código gerado por IA pode ser mais verboso, e complexidade/duplicação sem normalizar por LOC pode enganar.
* *Opcional (aprofundamento):* Índice de Manutenibilidade (Maintainability Index, disponível no Radon `mi`) — métrica composta (complexidade + LOC + volume de Halstead), mais robusta que olhar cada métrica isoladamente.

### Robustez estatística

Dado o tamanho amostral reduzido, preferir **mediana e IQR** (intervalo interquartil) a média e desvio-padrão nas tabelas e gráficos descritivos, e manter o **teste de Wilcoxon** (não paramétrico) na análise inferencial do Passo 4 — consistente com o desenho *within-subject*.

---

## Etapas Esperadas por Sprint

### Passo 1 — Desenho do Experimento

Definir, no mínimo:

* **(A)** Hipóteses nula e alternativa;
* **(B)** Variáveis dependentes (tempo, nº de testes passando, métricas estáticas);
* **(C)** Variável independente (uso ou não do assistente de IA);
* **(D)** Tratamentos;
* **(E)** Objetos experimentais (conjunto de exercícios/katas de dificuldade equivalente);
* **(F)** Tipo de projeto experimental (recomenda-se *crossover/within-subject*, contrabalanceado, para controlar variação individual de habilidade);
* **(G)** Quantidade de medições;
* **(H)** Ameaças à validade: efeito de aprendizado entre katas, familiaridade prévia com a ferramenta de IA, vazamento de solução já vista e **memorização** — se as katas forem muito conhecidas (ex.: exercícios clássicos do LeetCode/HackerRank), o assistente de IA pode reproduzir uma solução já vista em seu treinamento em vez de efetivamente "ajudar"; para reduzir esse risco, preferir katas autorais do grupo/professor ou exercícios pouco indexados.

### Passo 2 — Preparação do Experimento

* Escolher **4 ou 6 katas/exercícios** de dificuldade comparável — número par, para permitir a divisão exata pela metade entre trials com e sem assistente de IA (ex.: HackerRank, LeetCode, Codewars, ou exercícios próprios — preferir exercícios pouco indexados para reduzir o risco de memorização).
* Todos os katas precisam de **testes automatizados de aceitação**.
* Preparar o ambiente: linguagem, IDE, assistente de IA, cronômetro/registro de tempo e scripts de coleta das métricas estáticas.
* O grupo deve usar o **mesmo assistente de IA em todos os trials**, para que o tratamento seja comparável dentro do próprio experimento (ex.: GitHub Copilot gratuito via GitHub Student Developer Pack, ou a versão gratuita de um chatbot como ChatGPT/Claude/Gemini).
* Fixar também a **linguagem de programação** das katas de acordo com a ferramenta de métricas estáticas escolhida (CK exige Java; para outras linguagens, usar equivalente, como Radon para Python).

### Passo 3 — Execução do Experimento

* Cada integrante resolve **metade dos katas com assistente de IA habilitado e a outra metade sem**, em ordem **contrabalanceada** entre os integrantes.
* **Time-box fixo: 35 minutos por trial.** O grupo pode reduzir esse limite e justificar no relatório, mas **não pode aumentá-lo**, para manter a comparabilidade entre grupos da turma.
* Ao final do tempo, o trial é encerrado independentemente do resultado.
* Registrar: tempo até passar nos testes de aceitação (ou até o fim do time-box), nº de testes passando ao final do tempo, e executar CK/PMD (ou equivalente) sobre o código final de cada trial.

### Passo 4 — Análise de Resultados

Revisar os dados coletados, identificar outliers e aplicar os testes estatísticos adequados (ex.: **teste de Wilcoxon para amostras pareadas**, dado o desenho *within-subject*).

### Passo 5 — Relatório Final

Documento contendo:

1. Introdução com as hipóteses;
2. Metodologia detalhada o suficiente para permitir reprodução/replicação (ambiente, katas usados, assistente de IA e versão);
3. Resultados por RQ com as respostas estatísticas obtidas;
4. Discussão final;
5. Link do repositório/GitHub Projects do grupo.

### Passo 6 — Dashboard de Visualização

Importar os dados do experimento e gerar gráficos (Pandas + Matplotlib/Seaborn) comparando tempo, taxa de sucesso e métricas estáticas entre os tratamentos.

---

## Processo de Desenvolvimento

### Contribuição individual por sprint

Em **toda sprint (S01, S02 e S03)**, cada integrante do trio deve ser **Assignee de ao menos uma Issue com artefato de código commitado** (script, notebook, gráfico ou trial de kata) — não apenas nas Issues de execução de katas da S02. A ausência de commits atribuíveis a um integrante em uma sprint **zera a parcela individual** daquele integrante na sprint.

### Sugestão de divisão de papéis por sprint (não obrigatória)

O trio é livre para se organizar de outra forma, desde que a regra acima seja respeitada.

* **S01:** um integrante escreve o script de cronometragem/coleta de tempo; outro prepara o ambiente e o script de execução das métricas estáticas (CK/PMD ou Radon); o terceiro pesquisa e valida os katas (dificuldade comparável, baixa indexação) e redige hipóteses e ameaças à validade — os três revisam o desenho em conjunto.
* **S02:** já naturalmente dividida por design — cada integrante resolve, individualmente, todos os katas (metade com IA, metade sem), em ordem contrabalanceada.
* **S03:** um integrante conduz os testes estatísticos (Wilcoxon) para RQ1/RQ2; outro conduz a análise da RQ3 (métricas estáticas); o terceiro monta o dashboard (Pandas/Matplotlib/Seaborn) consolidando os resultados dos três.

---

## Entregáveis e Pontuação

| Sprint | Entregável | Pontos |
| :--- | :--- | :---: |
| **Lab02S01** | Desenho do experimento + preparação (Passos 1–2: katas escolhidos, ambiente, scripts de medição de tempo e métricas). Cartões do desenho e da preparação devem estar no Kanban do grupo. | 5 |
| **Lab02S02** | Execução do experimento + coleta de dados (Passo 3). | 5 |
| **Lab02S03** | Análise de resultados (Passo 4, cobrindo RQ1, RQ2 e RQ3) + Dashboard de Visualização (Passo 6). | 5 |
| **Relatório Final** | Elaboração do documento final (Passo 5). | 5 |
| | **Total** | **20** |

**Prazo final:** conforme cronograma da disciplina.

---

## Regras de Avaliação do GitHub Projects

* Desconto de **até 10% da nota da sprint** por qualidade insuficiente do uso do GitHub Projects (WIP não respeitado, Issues sem Assignee, cartões desatualizados, ausência de evolução semanal).
* **Todos os trials** devem ser registrados no GitHub Projects do grupo como **Issues individuais** (uma por kata/tratamento), atribuídas ao integrante responsável (campo *Assignee*), mantendo a rastreabilidade entre o experimento e o board.
* A correção é feita a partir do GitHub Projects: **commits sem referência ao número da Issue correspondente não serão considerados.**

---

## Execução do Experimento (este repositório)

Esta seção é do grupo, não do enunciado: documenta o ambiente e o passo a passo
necessários para reproduzir o experimento a partir do zero.

### Ferramenta de IA usada nos trials

Os trials `com-IA` devem usar **o mesmo assistente, na mesma versão/modelo,
por todos os três integrantes** — é a operacionalização da variável independente
(seção 1 do [DESENHO.md](DESENHO.md)) e entra na metodologia do relatório final.

| Item | Valor |
| :--- | :--- |
| Assistente | Claude (Anthropic) |
| Versão / modelo | Claude Sonnet 5 (`claude-sonnet-5`) |
| Modo de acesso | Claude Code (extensão na IDE) |
| Regras de uso no trial | Uso livre dentro da IDE: pedir sugestões, implementações completas, correções e explicações de erro. O participante roda a suíte e decide o que aceitar — não precisa aceitar sugestão sem entender. Fora do trial `com-ia`, nenhuma IA pode ser consultada. |

> Definido a partir da decisão do Gabriel nesta issue. Como a regra vale para
> os três integrantes (mesma ferramenta e versão em todos os trials `com-IA`),
> confirmar com Henrique e Guilherme antes dos trials deles.

### Estrutura de pastas

```
lab-expe-02/
├── katas/kN/         # especificação, esqueleto e suíte congelada de cada kata
├── src/              # instrumentação: timer.py e metricas.py
├── data/             # CSVs brutos e consolidados
├── graficos/         # figuras geradas na S03
├── trials/           # uma pasta por trial executado (cópia isolada da kata)
├── prints/           # evidências do board
└── DESENHO.md        # desenho do experimento
```

As katas em `katas/` são **somente leitura durante a S02**: cada trial trabalha
numa cópia dentro de `trials/`, o que atende à mitigação de vazamento de solução
da seção 5 do DESENHO.md. As suítes `test_kN.py` foram congeladas na issue #59 e
não podem ser alteradas durante a execução.

### Instalação

Python 3.12 e Node 20+ são pré-requisitos.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r lab-expe-02/requirements.txt
cd lab-expe-02 && npm install      # instala o jscpd localmente
```

O `npm install` instala o jscpd em `lab-expe-02/node_modules` — não é preciso
instalação global. Os scripts o localizam via `npx`.

### Versões fixadas

Fixar versões é a mitigação da ameaça de **efeito de medição** (seção 5 do
DESENHO.md). Os números abaixo são os usados na coleta; ao replicar, use os
mesmos ou registre a divergência no relatório.

| Ferramenta | Versão | Uso |
| :--- | :--- | :--- |
| Python | 3.12.13 | linguagem das katas |
| pytest | 9.1.1 | suítes de aceitação (RQ1, RQ2) |
| radon | 6.0.1 | complexidade, LOC e MI (RQ3) |
| Node.js | 26.0.0 | runtime do jscpd |
| jscpd | 5.2.0 | duplicação de linhas (RQ3) |
| pandas / scipy | 3.0.5 / 1.18.1 | análise estatística (S03) |
| matplotlib / seaborn | 3.11.1 / 0.13.2 | dashboard (S03) |

Comandos fixados do jscpd: `--min-lines 5 --min-tokens 50` (definidos em
`PARAMS_JSCPD`, em `src/metricas.py`). Mudar esses valores invalida a comparação
entre trials já coletados.

### Passo a passo de um trial

A ordem de cada participante está congelada na tabela de contrabalanceamento
(seção 4 do DESENHO.md) e **não deve ser improvisada** — a posição do trial é
uma variável de controle.

1. Confira sua linha na tabela de contrabalanceamento e identifique a kata, o
   tratamento e a ordem do trial.
2. Leia a especificação em `katas/kN/README.md` — **antes** de iniciar o
   cronômetro. A leitura não é cronometrada; a implementação é.
3. Feche o assistente de IA se o trial for `sem-IA`.
4. Inicie o trial:

   ```bash
   python src/timer.py --integrante guilherme --kata k1 --tratamento com-ia --ordem 1
   ```

   O script cria `trials/guilherme__k1__com-ia/` com uma cópia limpa da kata e
   começa a contar.
5. Implemente em `trials/guilherme__k1__com-ia/solucao.py`. No terminal do timer:

   | Comando | Efeito |
   | :--- | :--- |
   | `t` ou Enter | roda a suíte e mostra quantos testes passam |
   | `s` | mostra o tempo restante |
   | `x` | encerra antes do time-box (registrado como censurado) |

6. O trial termina sozinho de uma destas formas, e **nenhuma descarta o registro**:
   - **verde** — todos os testes passam; grava o tempo real com `censurado = 0`;
   - **time-box** — 2100 s sem verde; roda a suíte uma última vez para preservar
     o parcial, grava `tempo_s = 2100` e `censurado = 1`.
7. A linha é acrescentada a `data/trials_raw.csv`. A pasta do trial guarda ainda
   `trial.json` (metadados) e `trial_log.txt` (cada execução da suíte, para auditoria).
8. Commite a pasta do trial referenciando a issue correspondente.

Qualquer desvio de protocolo (uso acidental de IA em trial `sem-IA`, falha de
ferramenta, interrupção) deve ser **registrado na issue do trial**, nunca
removido silenciosamente do dataset.

### Coleta das métricas estáticas

Depois dos trials, sobre o código final de cada um:

```bash
python src/metricas.py --todos                       # todos os trials
python src/metricas.py --trial trials/guilherme__k1__com-ia
```

Gera `data/metricas.csv` com chave `(integrante, kata, tratamento)` e as colunas
`complexidade_media`, `n_blocos`, `loc`, `sloc`, `mi`, `duplicacao_pct`.

Notas de interpretação:

- `complexidade_media` é a média por função/método; entradas de classe são
  ignoradas para não contar os métodos duas vezes.
- `loc` é **variável de controle** e não deve ser lida isoladamente como
  qualidade (seção 2 do DESENHO.md).
- `mi` é o aprofundamento opcional previsto no enunciado.

### Dados gerados

| Arquivo | Origem | Conteúdo |
| :--- | :--- | :--- |
| `data/trials_raw.csv` | `src/timer.py` | uma linha por trial: tempo, testes e censura |
| `data/metricas.csv` | `src/metricas.py` | métricas estáticas por trial |
