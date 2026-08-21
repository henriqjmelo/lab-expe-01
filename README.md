# Laboratório 01 — Características de Repositórios Populares + Setup do Kanban

> **Disciplina:** Laboratório de Experimentação de Software  
> **Curso:** Engenharia de Software (6º Período — Noite)  
> **Professor:** Danilo Maia  

---

## Integrantes do Grupo

* Henrique Jardim Melo
* Gabriel Afonso

---

## Links Importantes

* Repositório: `https://github.com/henriqjmelo/lab-expe-01`
* GitHub Projects (v2): `https://github.com/users/henriqjmelo/projects/1`

---

## Objetivo do Laboratório

Analisar as características dos repositórios mais populares do GitHub (por número de estrelas) usando a API GraphQL oficial, e documentar o processo de gestão do projeto via quadro Kanban ao longo do semestre.

---

## Questões de Pesquisa (RQs) e Divisão de Trabalho

A extração e validação das métricas foi dividida entre os integrantes da dupla da seguinte forma:

| Questão de Pesquisa | Métrica | Responsável |
| :--- | :--- | :--- |
| **RQ 01** — Sistemas populares são maduros/antigos? | Idade do repositório (calculado a partir de `createdAt`) | Henrique Jardim Melo |
| **RQ 02** — Sistemas populares recebem muita contribuição externa? | Total de Pull Requests aceitos (`MERGED`) | Henrique Jardim Melo |
| **RQ 03** — Sistemas populares lançam releases com frequência? | Total de releases publicadas (`releases`) | Gabriel Afonso |
| **RQ 04** — Sistemas populares são atualizados com frequência? | Tempo até a última atualização (`pushedAt`) | Gabriel Afonso |
| **RQ 05** — Sistemas populares são escritos nas linguagens mais populares? | Linguagem primária (`primaryLanguage`) | Henrique Jardim Melo |
| **RQ 06** — Sistemas populares possuem um alto percentual de issues fechadas? | Razão entre issues fechadas (`closed`) e total de issues | Henrique Jardim Melo |
| **Bônus (RQ 07)** — Cruzamento das RQs 02, 03 e 04 agrupados por linguagem | Média/Mediana por linguagem | Henrique Jardim Melo |

### Fonte de Referência para Linguagens (RQ 05)
Para definir as "linguagens mais populares", o grupo usa como referência o [GitHub Octoverse](https://octoverse.github.com/) e o [TIOBE Index](https://www.tiobe.com/tiobe-index/). A mesma fonte é mantida ao longo de todo o estudo.

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
└── src/
    ├── config.py           # carrega o token do .env
    ├── github_client.py    # cliente HTTP genérico para a API GraphQL
    ├── collect.py           # coletor unificado (todas as RQs, paginado)
    ├── export_csv.py
    ├── snapshot.py          # snapshot do Project v2 → CSV
    ├── rq/                   # implementação + amostra de cada RQ
    └── validate/             # validação de nulos/outliers no dataset completo
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
