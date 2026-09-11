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

_Pendente — issue #60. Precisa ser feito por uma pessoa do grupo, sem cronômetro de trial e sem assistente de IA, resolvendo cada kata pra confirmar que é viável dentro dos 35 minutos. Este piloto não entra no dataset final._
