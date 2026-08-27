# Laboratório 01 — Características de Repositórios Populares + Setup do Kanban

> **Disciplina:** Laboratório de Experimentação de Software  
> **Curso:** Engenharia de Software (6º Período — Noite)  
> **Professor:** Danilo Maia  

---

## Integrantes do Grupo

* Henrique Jardim Melo
* Gabriel Afonso
* Terceiro integrante a definir

---

## Links Importantes

* Repositório: `https://github.com/henriqjmelo/lab-expe-01`
* GitHub Projects (v2): `https://github.com/users/henriqjmelo/projects/1`
* Relatório: [RELATORIO.md](RELATORIO.md)

---

## Objetivo do Laboratório

Analisar as características dos repositórios mais populares do GitHub (por número de estrelas) usando a API GraphQL oficial, e documentar o processo de gestão do projeto via quadro Kanban ao longo do semestre.

---

## Questões de Pesquisa (RQs) e Divisão de Trabalho

As RQs são divididas em três partes, uma por integrante. A tabela mostra a divisão da análise e visualização (Lab01S03). A divisão da extração e da validação, nas sprints anteriores, está registrada no board e no histórico de commits.

| Questão de Pesquisa | Métrica | Responsável |
| :--- | :--- | :--- |
| **RQ 01** — Sistemas populares são maduros/antigos? | Idade do repositório (calculado a partir de `createdAt`) | Gabriel Afonso |
| **RQ 02** — Sistemas populares recebem muita contribuição externa? | Total de Pull Requests aceitos (`MERGED`) | Gabriel Afonso |
| **RQ 03** — Sistemas populares lançam releases com frequência? | Total de releases publicadas (`releases`) | Henrique Jardim Melo |
| **RQ 04** — Sistemas populares são atualizados com frequência? | Tempo até a última atualização (`pushedAt`) | Henrique Jardim Melo |
| **RQ 05** — Sistemas populares são escritos nas linguagens mais populares? | Linguagem primária (`primaryLanguage`) | A definir |
| **RQ 06** — Sistemas populares possuem um alto percentual de issues fechadas? | Razão entre issues fechadas (`closed`) e total de issues | A definir |
| **Bônus (RQ 07)** — Cruzamento das RQs 02, 03 e 04 agrupados por linguagem | Mediana por linguagem, com boxplot | A definir |

### Fonte de Referência para Linguagens (RQ 05)
Para definir as "linguagens mais populares", o grupo usa como referência o [GitHub Octoverse](https://octoverse.github.com/) e o [TIOBE Index](https://www.tiobe.com/tiobe-index/). A mesma fonte é mantida ao longo de todo o estudo.

Os dois rankings usados na comparação ficam fixos em `src/analysis/rq05_rq06.py`, com a data da consulta (Octoverse 2025 e TIOBE de agosto/2026), para que a análise continue reproduzível depois que os rankings mudarem. A RQ07 importa essas mesmas listas em vez de redefini-las, para que "linguagem popular" signifique a mesma coisa nas duas RQs.

### Corte mínimo de repositórios por linguagem (RQ07)
A RQ07 só compara linguagens com pelo menos **10 repositórios** no dataset. Das 43 linguagens primárias distintas, 24 aparecem em menos de 5 repositórios e 12 aparecem em um único — nesses casos a mediana descreve dois ou três projetos específicos, não a linguagem. Com o corte sobram 13 linguagens, que cobrem 819 dos 905 repositórios com linguagem informada (90,5%).

---

## Configuração do Processo (GitHub Projects v2)

### 1. Estrutura do Board
O board segue o fluxo: Backlog → To Do → Doing → In Review → Done.

### 2. Política de Limite de WIP (Work in Progress)
Limite configurado na coluna `Doing`: 2 tarefas simultâneas (uma por integrante). Com uma dupla fazendo entregas individuais por sprint, esse limite força terminar e revisar o que já está em andamento antes de começar outra coisa, em vez de acumular tarefas abertas ao mesmo tempo.

### 3. Regras de Desenvolvimento
1. Nenhuma tarefa fica como *draft issue* solta — todas viram Issues reais do repositório, vinculadas ao Project.
2. Toda Issue tem um responsável (*assignee*) definido.
3. Todo commit referencia o número da Issue correspondente na mensagem (ex.: `#12 implementa consulta GraphQL`), pra manter o vínculo automático entre commit e board.

---

## Como Executar o Script

### Estrutura do Projeto
```
lab-expe-01/
├── .env.example          # modelo do arquivo de variáveis de ambiente
├── .gitignore
├── requirements.txt
├── main.py                # teste de conexão
├── RELATORIO.md
├── data/
│   ├── repositorios.csv   # dataset coletado (versionado)
│   └── snapshot_*.csv     # snapshots do board, um por sprint
├── graficos/              # PNG gerados na análise (versionados)
└── src/
    ├── config.py           # carrega o token do .env
    ├── github_client.py    # cliente HTTP genérico para a API GraphQL
    ├── collect.py           # coletor unificado (todas as RQs, paginado)
    ├── export_csv.py
    ├── snapshot.py          # snapshot do Project v2 → CSV
    ├── rq/                   # implementação + amostra de cada RQ
    ├── validate/             # validação de nulos/outliers no dataset completo
    └── analysis/             # estatísticas e gráficos das RQs
        └── base.py            # carregamento tipado, métricas derivadas e helpers de gráfico
```

### Passo a passo

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/henriqjmelo/lab-expe-01.git
   cd lab-expe-01
   ```

2. **Crie um ambiente virtual e instale as dependências:**
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # Linux/Mac
   pip install -r requirements.txt
   ```

3. **Gere um GitHub Personal Access Token:**
   - Acesse [github.com/settings/tokens](https://github.com/settings/tokens)
   - Clique em **Generate new token** → **Fine-grained token** (recomendado) ou **Tokens (classic)**
   - Se optar por *classic*: marque o escopo `public_repo` (é suficiente para ler dados públicos via GraphQL)
   - Copie o token gerado — ele só é exibido uma vez

4. **Configure o token localmente:**
   ```bash
   cp .env.example .env
   ```
   Edite o `.env` e cole o token na variável `GITHUB_TOKEN`. Esse arquivo **nunca é commitado** (está no `.gitignore`).

5. **Teste a conexão:**
   ```bash
   python main.py
   ```
   Se tudo estiver certo, o script imprime seu login do GitHub e o rate limit disponível.

### Coleta de dados

```bash
python -m src.collect 1000     # coleta os repositórios e grava data/repositorios.csv
python -m src.snapshot         # exporta o board para data/snapshot_AAAA-MM-DD.csv
```

A coleta completa leva alguns minutos, porque pagina em blocos e respeita o limite de requisições da API.

### Validação e análise

Os scripts abaixo leem `data/repositorios.csv` e não fazem requisições à API.

```bash
python -m src.validate.rq01_rq02   # nulos e outliers de idade e PRs aceitas
python -m src.validate.rq03_rq04   # nulos e outliers de releases e atualização
python -m src.validate.rq05_rq06   # nulos, linguagens e razão de issues

python -m src.analysis.rq01_rq02   # estatísticas e gráficos de RQ01 e RQ02
python -m src.analysis.rq05_rq06   # estatísticas e gráficos de RQ05 e RQ06
python -m src.analysis.rq07        # RQ07: RQ02, RQ03 e RQ04 por linguagem
```

Os gráficos são salvos em `graficos/`.

### Sobre as dependências

A coleta usa apenas `requests` e a query GraphQL é escrita à mão, como o enunciado exige. `matplotlib` e `numpy` entram só na etapa de análise e visualização, e não consultam a API do GitHub.
