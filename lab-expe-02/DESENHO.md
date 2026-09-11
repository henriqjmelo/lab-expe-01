# Desenho do Experimento — Lab02

> Documento em construção. Seções 1, 2, 3 e 5 são conteúdo das issues #55-57
> (Henrique) e ainda não foram escritas. Seção 6 depende do piloto de
> calibração (#60), que precisa ser feito por uma pessoa, sem IA, dentro do
> time-box — ainda pendente.

## 1. Hipóteses (H0 / H1)

O experimento compara dois tratamentos: desenvolvimento **com-IA**, no qual o participante pode consultar o assistente de IA definido pelo grupo, e desenvolvimento **sem-IA**, no qual o participante não pode consultar esse assistente. As hipóteses são direcionais e serão avaliadas por comparações pareadas dentro de cada participante, com nível de significância planejado de $\alpha = 0,05$.

### RQ1 — O uso de IA reduz o tempo de desenvolvimento?

- **H0:** o uso de IA não reduz o time-to-green; a mediana pareada do tempo com-IA é igual ou maior que a mediana sem-IA.
- **H1:** o uso de IA reduz o time-to-green; a mediana pareada do tempo com-IA é menor que a mediana sem-IA.

### RQ2 — O uso de IA melhora a qualidade funcional da solução?

- **H0:** o uso de IA não aumenta o percentual de testes de aceitação aprovados; a mediana pareada com-IA é igual ou menor que a mediana sem-IA.
- **H1:** o uso de IA aumenta o percentual de testes de aceitação aprovados; a mediana pareada com-IA é maior que a mediana sem-IA.

### RQ3 — O uso de IA altera a estrutura e a manutenibilidade do código?

- **H0:** o uso de IA não reduz a complexidade ciclomatica média nem o percentual de linhas duplicadas; as medianas pareadas com-IA são iguais ou maiores que as sem-IA.
- **H1:** o uso de IA reduz a complexidade ciclomatica média e o percentual de linhas duplicadas, sem interpretar LOC isoladamente como qualidade.

As hipóteses são formuladas como diferenças de tratamento, e não como afirmações causais universais. O teste estatístico, o tamanho da amostra e as limitações do estudo serão registrados antes da análise final.

## 2. Variáveis dependentes e independente

### Variável independente

O fator experimental é o **uso do assistente de IA**, com dois níveis:

1. `com-IA`: o participante pode usar o assistente durante o trial;
2. `sem-IA`: o participante resolve a kata sem consultar o assistente.

### Variáveis dependentes

| RQ | Variável | Operacionalização | Justificativa GQM |
| :--- | :--- | :--- | :--- |
| RQ1 | Time-to-green | Segundos entre o início do trial e a execução dos testes de aceitação com resultado aprovado; trial que estoura o limite recebe 2100 s e é marcado como censurado | Mede diretamente a eficiência de entrega e é mais informativo que contar linhas ou commits |
| RQ2 | Percentual de testes aprovados | Testes de aceitação aprovados dividido pelo total de testes da kata | Permite comparar katas com números de testes diferentes e representa a qualidade funcional observável |
| RQ3 | Complexidade ciclomatica média | Média da complexidade por função ou método da solução | Observa a dificuldade estrutural de manutenção; é preferível a LOC como indicador de complexidade |
| RQ3 | Percentual de linhas duplicadas | Percentual de linhas identificadas como duplicadas pela ferramenta definida no protocolo | Captura repetição estrutural que pode dificultar manutenção e evolução |
| Controle | LOC | Linhas de código da solução | Controla o tamanho da implementação, mas não será interpretada isoladamente como qualidade |

Também serão registrados como variáveis de controle o participante, a kata, a ordem do trial, o tratamento, o tempo bruto, o status de censura e a quantidade total de testes. O dataset manterá os valores brutos por trial; nenhum trial será descartado por falha ou por exceder o time-box.

## 3. Tratamentos, projeto experimental e quantidade de medições

O experimento usa um desenho **crossover within-subject**: cada um dos três participantes executa as seis katas nos dois tratamentos, com-IA e sem-IA. Assim, cada participante funciona como seu próprio controle, reduzindo o efeito de diferenças individuais de experiência, velocidade e estilo de programação.

O desenho tem três fatores observados: participante, kata e tratamento. O tratamento é o fator de interesse; participante e kata são controlados pela repetição cruzada. Cada participante executa três katas com IA e três sem IA, totalizando seis trials por participante e **18 trials no experimento**, sendo nove por tratamento.

O time-box de cada trial é de **35 minutos (2100 segundos)**. O relógio começa quando o participante inicia a implementação e termina na primeira execução dos testes de aceitação totalmente aprovados. Se o time-box for atingido antes disso, o trial não é descartado: o tempo é registrado como **2100 segundos, com indicador de censura**, e o percentual de testes aprovados observado naquele momento é preservado. A análise de tempo deverá tratar esses valores como censurados, e não como se fossem tempos exatos de conclusão.

## 4. Contrabalanceamento e ordem de execução

A ordem foi contrabalanceada para distribuir tratamento, kata e posição do trial. Guilherme e Gabriel começam alternando os tratamentos; Henrique usa a ordem invertida para reduzir a associação entre posição e tratamento. A tabela fixa a ordem planejada antes da coleta:

| Ordem | Guilherme | Gabriel | Henrique |
|:-:|:--|:--|:--|
| 1 | K1 com IA | K1 sem IA | K6 com IA |
| 2 | K2 sem IA | K2 com IA | K5 sem IA |
| 3 | K3 com IA | K3 sem IA | K4 com IA |
| 4 | K4 sem IA | K4 com IA | K3 sem IA |
| 5 | K5 com IA | K5 sem IA | K2 com IA |
| 6 | K6 sem IA | K6 com IA | K1 sem IA |

O contrabalanceamento evita que todas as katas mais fáceis ou mais difíceis fiquem no mesmo tratamento e reduz o efeito de aprendizado associado à posição. A mesma kata aparece uma vez em cada tratamento para cada participante, permitindo calcular diferenças pareadas. A ordem planejada deverá ser refletida nas issues de trial da S02; qualquer desvio será registrado como protocolo e não ocultado na análise.

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
| K4 | 9 |
| K5 | 9 |
| K6 | 9 |
| **Total** | **53** |

Todas as 53 asserções foram conferidas contra uma implementação de referência (descartável, não commitada) antes de congelar as suítes: as 53 passam com a referência e falham de forma limpa (`NotImplementedError`, sem erro de import) contra o esqueleto vazio de `solucao.py`, que é o estado em que cada trial começa.

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
