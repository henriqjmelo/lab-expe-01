# Assistentes de IA vs. codificação manual: um experimento controlado

**Laboratório 02 — Laboratório de Experimentação de Software**  
**Curso:** Engenharia de Software, 6º período, noite  
**Professor:** Danilo Maia

## Integrantes

- Henrique Jardim Melo
- Gabriel Afonso Infante Vieira
- Guilherme Costa

**Repositório:** https://github.com/henriqjmelo/lab-expe-01  
**GitHub Projects:** https://github.com/users/henriqjmelo/projects/1

> **Correção desta versão.** Os seis trials do Henrique estavam registrados nas pastas individuais, em `trial.json` e `trial_log.txt`, mas não haviam sido copiados para `data/trials_raw.csv`. As seis linhas foram recuperadas diretamente desses registros, sem estimativa ou imputação. O CSV agora contém 18/18 trials planejados.

---

## 1. Introdução

Assistentes de IA generativa são usados cada vez mais no desenvolvimento de software, mas relatos pessoais não permitem separar o efeito da ferramenta de fatores como habilidade, dificuldade da tarefa e ordem de execução. Este laboratório avalia, em condições controladas, se o uso de um assistente altera o tempo de resolução, a qualidade funcional e a estrutura do código produzido em seis katas autorais de Python.

### Questões de pesquisa

- **RQ1:** o uso de assistente de IA reduz o tempo necessário para resolver uma tarefa de programação?
- **RQ2:** o uso de assistente de IA reduz a quantidade de defeitos, operacionalizada pela taxa de testes de aceitação aprovados?
- **RQ3:** o uso de assistente de IA altera a complexidade ciclomática, a duplicação ou o tamanho do código produzido?

### Hipóteses

| Questão | Hipótese nula (H0) | Hipótese alternativa (H1) |
|---|---|---|
| RQ1 | O tempo com IA é igual ou maior que o tempo sem IA. | O tempo com IA é menor. |
| RQ2 | A taxa de testes aprovados com IA é igual ou menor que sem IA. | A taxa com IA é maior. |
| RQ3 | A complexidade e a duplicação com IA são iguais ou maiores que sem IA. | A complexidade e a duplicação com IA são menores. |

O nível de significância planejado foi **α = 0,05**.

---

## 2. Metodologia

### 2.1 Desenho experimental

O plano especificou um desenho crossover com três participantes, seis katas por participante e três trials em cada tratamento. A ordem planejada foi contrabalanceada entre os integrantes. Cada trial tinha um **time-box de 35 minutos (2.100 s)**; trials que não chegassem ao verde seriam registrados como censurados em 2.100 s, sem descarte.

A coleta completa contém 18 trials:

| Participante | Com IA | Sem IA | Total |
|---|---:|---:|---:|
| Gabriel | 3 | 3 | 6 |
| Guilherme | 3 | 3 | 6 |
| Henrique | 3 | 3 | 6 |
| **Total** | **9** | **9** | **18** |

Como cada participante realizou cada kata uma única vez, uma mesma pessoa não possui a mesma kata nos dois tratamentos. Assim, o teste inferencial foi feito **por kata**, formando seis pares entre os trials com IA e sem IA. O participante é descrito como variável de controle, mas não funciona como bloco within-subject no teste por kata. Essa diferença entre o desenho pretendido e os registros reais permanece como limitação metodológica.

### 2.2 Objetos experimentais

Foram usadas seis katas autorais, com suítes de aceitação congeladas antes da coleta:

| Kata | Tema | Testes |
|---|---|---:|
| K1 | Turno de atendimento: distribuição round-robin com capacidade | 9 |
| K2 | Verificador de senha corporativa | 9 |
| K3 | Consolidador de notas fiscais | 8 |
| K4 | Detector de rajada de login com janela deslizante | 9 |
| K5 | Compactador de texto por repetição | 9 |
| K6 | Divisor de times por afinidade | 9 |
| **Total** |  | **53** |

As katas foram escritas para o laboratório e não copiadas de plataformas conhecidas. Um piloto anterior indicou que todas eram resolvíveis dentro do time-box, embora K4 e K5 fossem mais exigentes que K3.

### 2.3 Tratamentos

- **Com IA:** uso do Claude Sonnet 5 (`claude-sonnet-5`) por meio do Claude Code na IDE. Foram permitidos pedidos de implementação, correção e explicação; o participante executava a suíte e decidia o que aceitar.
- **Sem IA:** implementação manual, com documentação oficial e busca por conceitos permitidas, mas sem consulta a assistentes ou autocompletes baseados em IA.

### 2.4 Instrumentação e métricas

O `src/timer.py` registrou o tempo até a primeira execução verde da suíte ou o limite de 2.100 s. A taxa de sucesso foi calculada como:

\[
\text{taxa de sucesso} = \frac{\text{testes aprovados ao final}}{\text{testes da suíte congelada}}
\]

Para a RQ3, o pipeline utilizou `radon cc` para complexidade ciclomática média, `radon raw` para LOC/SLOC, `radon mi` para manutenibilidade e `jscpd 5.2.0` para duplicação, com `--min-lines 5 --min-tokens 50`.

Os dados brutos estão em `data/trials_raw.csv`; os resultados consolidados estão em `data/analise_parcial_trials.csv`, `data/analise_parcial_tratamentos.csv`, `data/metricas.csv`, `data/inferencia_pares.csv` e `data/inferencia_testes.csv`.

### 2.5 Análise estatística

Foram priorizadas medianas e IQR por causa do tamanho reduzido e da censura. Para a comparação por kata, foi usado o teste de Wilcoxon de postos sinalizados, unilateral na direção das hipóteses para RQ1/RQ2/RQ3. O teste não foi executado quando o número de diferenças não nulas não permitia atingir α = 0,05; nesses casos, foi informado o menor p-valor possível para a amostra observada.

---

## 3. Resultados

### 3.1 Visão geral dos 18 trials

| Tratamento | n | Verdes | Censurados | Mediana do tempo (s) | IQR do tempo (s) | Mediana da taxa | IQR da taxa |
|---|---:|---:|---:|---:|---:|---:|---:|
| Com IA | 9 | 9 | 0 | 87,0 | 59–96 | 100% | 100%–100% |
| Sem IA | 9 | 7 | 2 | 710,0 | 453–1.060 | 100% | 100%–100% |

Na condição com IA, os tempos variaram de 26 a 241 segundos. Na condição sem IA, variaram de 217 a 2.100 segundos; os dois valores de 2.100 s são censurados e não representam necessariamente conclusão após exatamente 35 minutos.

### 3.2 RQ1 — Tempo de resolução

Para cada kata, foi calculada a mediana dos trials disponíveis em cada tratamento:

| Kata | Com IA (s) | Sem IA (s) | Diferença com − sem (s) |
|---|---:|---:|---:|
| K1 | 241 | 1.580 | −1.339 |
| K2 | 79 | 314 | −235 |
| K3 | 33 | 1.405 | −1.372 |
| K4 | 105 | 453 | −348 |
| K5 | 26 | 568,5 | −542,5 |
| K6 | 77,5 | 541 | −463,5 |

**Wilcoxon unilateral:** W = 0; p = **0,01562**; correlação rank-biserial = **−1,0**; seis diferenças não nulas; dois pares contêm trials censurados.

**Resposta à RQ1:** os dados apresentam evidência estatística, no pareamento por kata adotado, de menor tempo com IA. A mediana geral foi 87 s com IA contra 710 s sem IA. O resultado é forte dentro desta amostra, mas não deve ser generalizado sem considerar os desvios de protocolo descritos na Seção 4.

### 3.3 RQ2 — Defeitos e taxa de sucesso

Todos os nove trials com IA terminaram com 100% dos testes aprovados. Nos nove trials sem IA, sete terminaram verdes; um terminou com 7/8 e outro com 0/9. Como a mediana dos dois grupos é 100%, a mediana não captura a diferença nas caudas.

| Tratamento | Trials verdes | Taxa mínima | Mediana | Taxa máxima |
|---|---:|---:|---:|---:|
| Com IA | 9/9 | 100% | 100% | 100% |
| Sem IA | 7/9 | 0% | 100% | 100% |

No pareamento por kata, apenas duas diferenças foram não nulas: K1 e K3 favoreceram IA; os outros quatro pares empataram. Com duas diferenças não nulas, o menor p unilateral possível é 0,25. Portanto, **não foi aplicado um teste inferencial com α = 0,05**.

**Resposta à RQ2:** descritivamente, a condição com IA teve menos falhas e nenhum trial incompleto; porém, os dados não permitem afirmar diferença estatisticamente significativa. A mediana permanece em 100% nos dois grupos por causa dos empates.

### 3.4 RQ3 — Estrutura do código

O trial K1 de Gabriel sem IA foi identificado como sem implementação e foi excluído apenas da análise estática, conforme o protocolo. Assim, a RQ3 usa nove soluções com IA e oito soluções sem IA.

| Métrica | Com IA (n=9), mediana [IQR] | Sem IA (n=8), mediana [IQR] |
|---|---:|---:|
| Complexidade média | 7,0 [6,0–7,0] | 7,75 [5,75–10,5] |
| LOC | 22 [20–23] | 33 [19,25–40,25] |
| SLOC | 17 [15–18] | 24 [14,75–27] |
| Índice de manutenibilidade | 63,038 [58,274–66,357] | 58,822 [50,920–66,236] |
| Linhas duplicadas | 0% [0–0] | 0% [0–0] |

No pareamento por kata, foram usados seis pares. Para a complexidade, W = 3,0; p = **0,07812**; rank-biserial = **−0,7143**. Para duplicação, todos os valores foram zero, portanto não houve diferenças não nulas. Para MI, o teste bilateral resultou em p = 0,3125; LOC e SLOC foram tratados como controles exploratórios, com p = 0,09375 e p = 0,0625, respectivamente.

**Resposta à RQ3:** a complexidade mediana foi numericamente menor com IA, mas o resultado não atingiu α = 0,05. A duplicação foi 0% em todos os códigos medidos. O código com IA também apresentou menor LOC/SLOC na descrição, mas tamanho isolado não equivale a melhor manutenibilidade.

---

## 4. Discussão e ameaças à validade

### 4.1 Interpretação conjunta

Com os seis trials do Henrique recuperados, o padrão descritivo se mantém e fica mais robusto: todos os nove trials com IA ficaram verdes em até 241 s, enquanto dois trials sem IA foram censurados e os demais demoraram de 217 a 1.060 s. Para qualidade funcional, a direção favorece IA, mas muitos empates em 100% reduzem o poder do teste. Para estrutura, a complexidade apresenta tendência descritiva menor com IA, porém p = 0,07812 não permite rejeitar H0 no nível de 5%; a duplicação não diferenciou os tratamentos.

A conclusão responsável é: **nesta coleta, a IA reduziu o tempo de resolução no pareamento por kata; não foi possível demonstrar diferença estatística em qualidade funcional ou estrutura do código.**

### 4.2 Desvios e limitações observados

1. **Pareamento diferente do planejado:** cada participante executou cada kata uma única vez, em apenas um tratamento. A inferência foi feita por kata, não por participante.
2. **Ordem de Gabriel fora do contrabalanceamento:** seus trials sem IA ocorreram antes dos com IA, confundindo tratamento com aprendizagem, cansaço e posição.
3. **Contaminação do assistente:** nos trials de Gabriel com IA, o mesmo assistente havia sido usado anteriormente para elaborar katas, testes e soluções de referência. Isso pode ter favorecido artificialmente o tratamento com IA.
4. **Correções manuais de tempo:** registros de K2, K4 e K5 de Gabriel foram corrigidos a partir dos logs porque o comando `x` havia gravado 2.100 s sobre resultados verdes. K1 também teve restauração do denominador de testes.
5. **Execução direta pelo assistente:** em alguns trials com IA, o Claude Code escreveu diretamente em `solucao.py` e, em K4/K6, executou a suíte antes da verificação registrada pelo cronômetro.
6. **Prompts não registrados:** `n_prompts` não está disponível nos trials de Gabriel.
7. **Ambiente divergente:** foi registrada a utilização de Python 3.13.0 e Node 24.13.0 em parte da coleta, enquanto o README fixa outras versões.
8. **Amostra pequena:** seis pares por kata limitam a precisão e a generalização dos resultados.

A recuperação do Henrique foi feita de forma rastreável: cada linha adicionada ao CSV corresponde aos campos de `trial.json`, e os tempos/testes também aparecem nos três runs de cada `trial_log.txt`. O CSV original foi preservado como `data/trials_raw.before_henrique_recovery.csv`.

---

## 5. Conclusão

- **RQ1:** há evidência de redução do tempo com IA no pareamento por kata (medianas gerais 87 s vs. 710 s; Wilcoxon unilateral p = 0,01562). H0 é rejeitada para esta amostra e operacionalização.
- **RQ2:** a taxa de sucesso foi descritivamente melhor com IA (9/9 trials verdes contra 7/9), mas o número de diferenças não nulas foi insuficiente para teste significativo; H0 não é rejeitada.
- **RQ3:** a complexidade foi menor com IA em termos descritivos, mas sem significância a 5% (p = 0,07812); duplicação foi 0% em ambos os tratamentos; LOC/SLOC e MI não devem ser interpretados isoladamente como qualidade.

O experimento agora está completo em cobertura (**18/18 trials**) após a recuperação dos registros existentes do Henrique. Ainda assim, as ameaças metodológicas devem ser apresentadas junto com os resultados, especialmente o pareamento por kata e a contaminação do assistente na preparação das katas.

---

## 6. Reprodução

A partir de `lab-expe-02/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm ci
python src/consolida.py --parcial
python src/metricas.py --todos
python src/analise_parcial.py
python src/inferencia.py
python -m pytest -q tests_analise
```

Os gráficos ficam em `graficos/` e as tabelas analíticas em `data/`. A análise final foi executada após a recuperação e os testes automatizados resultaram em **9 passed**.

---

## 7. Referências internas do projeto

- `DESENHO.md` — hipóteses, variáveis, katas e ameaças à validade.
- `PROTOCOLO.md` — regras dos tratamentos, isolamento, time-box e registro de desvios.
- `src/timer.py` — coleta de tempo e testes.
- `src/metricas.py` — Radon e jscpd.
- `src/analise_parcial.py` — consolidação descritiva e gráficos.
- `src/inferencia.py` — pareamento por kata e Wilcoxon.
