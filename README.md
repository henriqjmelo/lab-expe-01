# Laboratório 01 — Características de Repositórios Populares + Setup do Kanban

> **Disciplina:** Laboratório de Experimentação de Software  
> **Curso:** Engenharia de Software (6º Período — Noite)  
> **Professor:** Danilo Maia  

---

## 👥 Integrantes do Grupo

* **Henrique Jardim Melo**
* **Gabriel Afonso** 

---

## 📌 Links Importantes

* **Repositório:** `https://github.com/henriqjmelo/lab-expe-01`
* **GitHub Projects (v2):** `https://github.com/users/henriqjmelo/projects/1`

---

## 🎯 Objetivo do Laboratório

Este laboratório visa analisar as características dos 1.000 repositórios mais populares do GitHub por meio de mineração de dados utilizando a API GraphQL oficial, além de instituir e documentar a metodologia de gestão do projeto via quadro Kanban durante o semestre.

---

## 📊 Questões de Pesquisa (RQs) e Divisão de Trabalho

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

### 📚 Fonte de Referência para Linguagens (RQ 05)
Para definir as "linguagens mais populares", o grupo utiliza como fonte oficial de referência o **[GitHub Octoverse](https://octoverse.github.com/)** / **[TIOBE Index](https://www.tiobe.com/tiobe-index/)**. Essa mesma fonte será mantida ao longo de todo o estudo.

---

## 🛠️ Configuração do Processo (GitHub Projects v2)

### 1. Estrutura do Board
O fluxo de trabalho do grupo segue o padrão Kanban estruturado nas seguintes colunas:
$$\text{Backlog} \longrightarrow \text{To Do} \longrightarrow \text{Doing} \longrightarrow \text{In Review} \longrightarrow \text{Done}$$

### 2. Política de Limite de WIP (Work in Progress)
* **Limite configurado na coluna `Doing`:** **2 tarefas simultâneas**.
* **Justificativa do Limite:** Sendo uma dupla focando em entregas individuais por Sprint, definir o limite em 2 cartões (um por integrante) força o foco na conclusão e revisão (*Review*) das tarefas ativas antes que novas sejam iniciadas. Isso previne gargalos de desenvolvimento, impede o acúmulo de tarefas incompletas e minimiza o tempo de ciclo (*cycle time*).

### 3. Regras de Desenvolvimento
1. **Rastreabilidade de Tasks:** Nenhuma tarefa é mantida como *Draft Issue*. Todas são convertidas em Issues reais do repositório e vinculadas ao Project.
2. **Atribuição:** Todas as Issues possuem um responsável direto (*Assignee*).
3. **Vínculo Commit ↔ Issue:** Todos os commits do projeto contêm a referência ao número da Issue correspondente na mensagem (ex.: `#12 implementa consulta GraphQL`), garantindo histórico auditável e vinculação automática no board.

---

## 🚀 Como Executar o Script

### Estrutura do Projeto
```
lab-expe-01/
├── .env.example      # modelo do arquivo de variáveis de ambiente
├── .gitignore
├── requirements.txt
├── main.py            # script de teste de conexão
├── data/               # saída dos .csv (ignorado pelo git)
└── src/
    ├── config.py       # carrega o token do .env
    └── github_client.py # cliente HTTP genérico para a API GraphQL
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
