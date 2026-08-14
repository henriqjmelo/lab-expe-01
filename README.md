# Laboratório 01 — Características de Repositórios Populares + Setup do Kanban

> **Disciplina:** Laboratório de Experimentação de Software  
> **Curso:** Engenharia de Software (6º Período — Noite)  
> **Professor:** Danilo Maia  

---

## 👥 Integrantes do Grupo

* **[Henrique Jardim Melo]**
* **[Gabriel Afonso]** - GitHub: `@[usuario_b]`
* **[Camila Melo]** - GitHub: `@[usuario_c]`

---

## 📌 Links Importantes

* **Repositório:** `https://github.com/henriqmelo/lab-expe-01`
* **GitHub Projects (v2):** `https://github.com/users/henriqmelo/projects/1](https://github.com/users/henriqjmelo/projects/1/views/1`

---

## 🎯 Objetivo do Laboratório

Este laboratório visa analisar as características dos 1.000 repositórios mais populares do GitHub por meio de mineração de dados utilizando a API GraphQL oficial, além de instituir e documentar a metodologia de gestão do projeto via quadro Kanban durante o semestre.

---

## 📊 Questões de Pesquisa (RQs) e Divisão de Trabalho

A extração e validação das métricas foi dividida entre os integrantes do trio da seguinte forma:

| Questão de Pesquisa | Métrica | Responsável |
| :--- | :--- | :--- |
| **RQ 01** — Sistemas populares são maduros/antigos? | Idade do repositório (calculado a partir de `createdAt`) | Integrante A |
| **RQ 02** — Sistemas populares recebem muita contribuição externa? | Total de Pull Requests aceitos (`MERGED`) | Integrante A |
| **RQ 03** — Sistemas populares lançam releases com frequência? | Total de releases publicadas (`releases`) | Integrante B |
| **RQ 04** — Sistemas populares são atualizados com frequência? | Tempo até a última atualização (`pushedAt`) | Integrante B |
| **RQ 05** — Sistemas populares são escritos nas linguagens mais populares? | Linguagem primária (`primaryLanguage`) | Integrante C |
| **RQ 06** — Sistemas populares possuem um alto percentual de issues fechadas? | Razão entre issues fechadas (`closed`) e total de issues | Integrante C |
| **Bônus (RQ 07)** — Cruzamento das RQs 02, 03 e 04 agrupados por linguagem | Média/Mediana por linguagem | Integrante C |

### 📚 Fonte de Referência para Linguagens (RQ 05)
Para definir as "linguagens mais populares", o grupo utiliza como fonte oficial de referência o **[GitHub Octoverse](https://octoverse.github.com/)** / **[TIOBE Index](https://www.tiobe.com/tiobe-index/)**. Essa mesma fonte será mantida ao longo de todo o estudo.

---

## 🛠️ Configuração do Processo (GitHub Projects v2)

### 1. Estrutura do Board
O fluxo de trabalho do grupo segue o padrão Kanban estruturado nas seguintes colunas:
$$\text{Backlog} \longrightarrow \text{To Do} \longrightarrow \text{Doing} \longrightarrow \text{In Review} \longrightarrow \text{Done}$$

### 2. Política de Limite de WIP (Work in Progress)
* **Limite configurado na coluna `Doing`:** **2 tarefas simultâneas**.
* **Justificativa do Limite:** Sendo um grupo composto por 3 integrantes focando em entregas individuais por Sprint, definir o limite em 2 cartões força o foco na conclusão e revisão (*Review*) das tarefas ativas antes que novas sejam iniciadas. Isso previne gargalos de desenvolvimento, impede o acúmulo de tarefas incompletas e minimiza o tempo de ciclo (*cycle time*).

### 3. Regras de Desenvolvimento
1. **Rastreabilidade de Tasks:** Nenhuma tarefa é mantida como *Draft Issue*. Todas são convertidas em Issues reais do repositório e vinculadas ao Project.
2. **Atribuição:** Todas as Issues possuem um responsável direto (*Assignee*).
3. **Vínculo Commit ↔ Issue:** Todos os commits do projeto contêm a referência ao número da Issue correspondente na mensagem (ex.: `#12 implementa consulta GraphQL`), garantindo histórico auditável e vinculação automática no board.

---

## 🚀 Como Executar o Script

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/henriqmelo/lab-expe-01.git](https://github.com/henriqmelo/lab-expe-01.git)
   cd lab-expe-01
