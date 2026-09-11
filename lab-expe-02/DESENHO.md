# Desenho do Experimento — Lab02

> Documento em construção. Seções 1, 2, 3 e 5 são conteúdo das issues #55-57
> (Henrique) e ainda não foram escritas. Seção 6 depende do piloto de
> calibração (#60), que precisa ser feito por uma pessoa, sem IA, dentro do
> time-box — ainda pendente.

## 1. Hipóteses (H0 / H1)

_Pendente — issue #55._

## 2. Variáveis dependentes e independente

_Pendente — issue #55._

## 3. Tratamentos, projeto experimental e quantidade de medições

_Pendente — issue #56._

## 4. Objetos experimentais — katas

Seis katas autorais, dificuldade comparável, linguagem Python. Especificação completa de cada um em `katas/kN/README.md`. Nenhum copiado de fonte conhecida (LeetCode/HackerRank/Codewars), para reduzir o risco de o assistente de IA reconhecer e reproduzir uma solução já vista em treinamento.

| Kata | Nome | Domínio |
| :--- | :--- | :--- |
| K1 | Turno de Atendimento | Alocação round-robin com capacidade |
| K2 | Verificador de Senha Corporativa | Validação de string com múltiplas regras |
| K3 | Consolidador de Notas Fiscais | Agregação com filtro e arredondamento |
| K4 | Detector de Rajada de Login | Janela deslizante sobre timestamps |
| K5 | Compactador de Texto por Repetição | Codificação/decodificação customizada |
| K6 | Divisor de Times por Afinidade | Particionamento com algoritmo determinístico |

### Suítes de teste de aceitação

Cada kata tem `test_kN.py` com testes de aceitação escritos e congelados antes dos trials (issue #59) — nenhum teste pode ser alterado durante a S02. O número de testes por kata entra no denominador da taxa de sucesso da RQ2, por isso a contagem foi mantida próxima entre os seis:

| Kata | Nº de testes |
| :--- | ---: |
| K1 | 9 |
| K2 | 9 |
| K3 | 8 |
| K4 | 8 |
| K5 | 9 |
| K6 | 9 |
| **Total** | **52** |

Todas as 52 asserções foram conferidas contra uma implementação de referência (descartável, não commitada) antes de congelar as suítes: as 52 passam com a referência e falham de forma limpa (`NotImplementedError`, sem erro de import) contra o esqueleto vazio de `solucao.py`, que é o estado em que cada trial começa.

## 5. Ameaças à validade

_Pendente — issue #57._

## 6. Calibração do piloto

Piloto feito pelo Gabriel, sem cronômetro de trial e sem assistente de IA — cada kata resolvido uma vez, pra confirmar viabilidade dentro do time-box de 35 minutos. Este piloto não entra no dataset final.

| Kata | Tempo estimado | Dificuldade percebida |
| :--- | :--- | :--- |
| K1 — Turno de Atendimento | 10-15 min | Fácil |
| K2 — Verificador de Senha Corporativa | 15-20 min | Fácil/Intermediário |
| K3 — Consolidador de Notas Fiscais | 5-10 min | Muito fácil |
| K4 — Detector de Rajada de Login | 20-25 min | Intermediário |
| K5 — Compactador de Texto por Repetição | 20-30 min | Intermediário |
| K6 — Divisor de Times por Afinidade | 5-15 min | Fácil |

**Os 6 katas foram confirmados como resolvíveis dentro do time-box**, com folga em todos os casos — o mais lento (K5) ficou em até 30 min no pior cenário estimado.

### Observação de balanceamento

Há uma diferença de 2 a 4x entre o kata mais rápido (K3, 5-10 min) e os mais lentos (K4 e K5, 20-30 min). Nenhum estoura o time-box, mas a diferença é grande o suficiente pra valer a pena conferir que o contrabalanceamento entre participantes e tratamentos (issue #56) distribui essa variação de forma equilibrada entre as condições com/sem IA — evitando concentrar os katas mais difíceis do mesmo lado da comparação.

### Anotações por kata

- **K1**: casos de borda (`ValueError`) precisam ser tratados antes da distribuição; o operador módulo (`%`) resolve o round-robin diretamente.
- **K2**: não é complexo, mas é trabalhoso — várias validações isoladas, com a ordem dos códigos de violação importando. Regex ajuda bastante na regra de repetição.
- **K3**: agregação clássica em dicionário. Único cuidado é arredondar só no final e validar valor negativo antes de somar.
- **K4**: o mais exigente em raciocínio algorítmico — agrupar eventos por usuário, ordenar por timestamp, aplicar janela deslizante.
- **K5**: duas funções (encode/decode). Descompactar é a parte mais trabalhosa, por causa de contagens com mais de um dígito.
- **K6**: `sorted()` do Python é estável — ordenar só por habilidade decrescente já mantém a ordem de empate automaticamente. Quem não souber disso pode perder tempo tentando montar uma chave de ordenação mais complexa.

### Ajuste feito a partir deste processo

O enunciado do K5 tinha um exemplo autocontraditório (uma linha incorreta seguida de uma nota tentando corrigi-la no próprio texto), encontrado durante a verificação da especificação e corrigido antes do piloto. Nenhum outro kata precisou de ajuste ou substituição.
