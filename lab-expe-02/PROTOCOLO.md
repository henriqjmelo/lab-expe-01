# Protocolo Operacional do Trial — Lab02 (S02)

> Referência: Issue #84.
>
> O [DESENHO.md](DESENHO.md) define hipóteses, variáveis e contrabalanceamento.
> O [README.md](README.md) define o ambiente, as versões fixadas, a ferramenta de IA
> e o passo a passo de execução de um trial.
> **Este documento define as condições de conduta** que precisam valer igualmente para
> os 18 trials — o que cada tratamento permite, o isolamento entre integrantes, a
> contagem de prompts e o registro de desvios.
>
> **Regra de ouro:** se as condições variarem entre integrantes, a comparação pareada
> perde o sentido. Todo desvio é **registrado** (seção 6), nunca escondido nem descartado.

---

## 1. Aceite dos três

O DoD da issue #84 exige que os três leiam e aceitem este protocolo **antes do próprio
primeiro trial**. Registre o aceite comentando na issue #84.

- [ ] Guilherme Costa — li e aceito
- [ ] Gabriel Afonso — li e aceito
- [ ] Henrique Jardim Melo — li e aceito

> Os seis trials do Gabriel (#72 a #77) foram executados **antes** deste protocolo
> existir. Ele deve confirmar na issue #84 se as condições das seções 2 a 4 foram
> atendidas. O que não tiver sido vira linha na tabela da seção 6 — nenhum trial dele
> é refeito nem removido do dataset.

---

## 2. O que cada tratamento permite

A ferramenta e o modelo do tratamento `com-ia` estão fixados na seção
"Ferramenta de IA usada nos trials" do [README.md](README.md) (issue #63): **Claude
Sonnet 5 via Claude Code**, iguais para os três. Trocar de ferramenta ou de modelo no
meio da coleta invalida a comparação e não é permitido.

### Tratamento `com-ia`

| Permitido | Não permitido |
| :--- | :--- |
| Pedir implementação, correção ou explicação ao assistente | Colar o conteúdo de `test_kN.py` no assistente |
| Colar a saída de falha do pytest (mensagem de erro) | Usar outra ferramenta ou outro modelo |
| Aceitar, editar ou rejeitar qualquer sugestão | — |
| Consultar documentação e buscar na web | Buscar solução pronta equivalente à kata |

Colar a suíte transforma a tarefa em "satisfazer asserções conhecidas", que não é a
mesma tarefa do `sem-ia`. O tempo gasto revisando sugestão conta no time-to-green.

### Tratamento `sem-ia`

| Permitido | Não permitido |
| :--- | :--- |
| Autocomplete do editor baseado em tipos e símbolos (LSP/Pylance) | Autocomplete por IA: Copilot, Codeium, Cursor Tab, Claude Code |
| Documentação oficial da linguagem e da stdlib | Qualquer consulta a assistente de IA, em qualquer aba ou terminal |
| Busca na web por conceito ou erro | Buscar solução pronta equivalente à kata |

Desativar a extensão **antes** de iniciar o cronômetro — fechar a janela do assistente
não basta. O contraste do experimento é IA vs. desenvolvimento manual com os recursos
habituais, não IA vs. memória pura; por isso documentação e busca continuam liberadas
nos dois tratamentos.

---

## 3. Regra de isolamento

Vazamento de solução entre trials é a principal ameaça interna listada no DESENHO.md.

1. **Não olhar a solução de outro integrante** para uma kata antes de ter executado o
   **seu próprio** trial daquela kata. Vale para código commitado, print, tela
   compartilhada e conversa sobre a abordagem.
2. Não abrir pastas `trials/<outro>__*` no editor durante a S02.
3. Não discutir estratégia de kata enquanto a S02 estiver aberta. Dúvida de enunciado
   (ambiguidade real) vai como comentário na issue da kata, respondida sem revelar
   abordagem de implementação.
4. Entre os trials de **um mesmo integrante**, o efeito de aprendizado é esperado e está
   controlado pelo contrabalanceamento (DESENHO.md, seção 4) — não é violação, desde que
   a ordem planejada seja respeitada.

---

## 4. Checklist de execução

Idêntico para os 18 trials. O passo a passo dos comandos está no README; aqui estão as
condições que precisam valer em volta deles.

### 4.1 Antes de iniciar o cronômetro

- [ ] `source .venv/bin/activate` com as versões fixadas no README (pytest 9.1.1).
- [ ] Kata, tratamento e **ordem** conferidos na tabela de contrabalanceamento
      (DESENHO.md, seção 4) — a ordem é argumento obrigatório do timer e é variável
      de controle, não se improvisa.
- [ ] Se `sem-ia`: extensões de IA desativadas e verificadas.
- [ ] Se `com-ia`: assistente aberto e **contador de prompts zerado** (seção 5).
- [ ] Nenhuma pasta de trial de outro integrante aberta.
- [ ] Notificações silenciadas; sem compromisso nos próximos 40 minutos.
- [ ] Enunciado da kata lido (`katas/kN/README.md`). A leitura não é cronometrada; a
      implementação é. Ler depois de iniciar o timer infla o seu tempo em relação aos
      trials já coletados.

### 4.2 Durante o trial

- [ ] Trabalhar **somente** em `trials/<integrante>__<kata>__<tratamento>/solucao.py`.
- [ ] **Não alterar `test_kN.py`.** A suíte foi congelada na issue #59 e é o denominador
      da RQ2. Alterá-la invalida o trial.
- [ ] **Sem pausa.** O cronômetro é contínuo. Interrupção inevitável encerra o trial e
      vira desvio registrado — não se "pausa e retoma".
- [ ] Rodar a suíte quantas vezes quiser com `t` (ou Enter) no terminal do timer.

### 4.3 Encerrar

O trial termina de uma destas formas, e **nenhuma descarta o registro**:

| Situação | Como | Registro |
| :--- | :--- | :--- |
| Todos os testes passaram | `t` — o timer fecha sozinho no verde | tempo real, `censurado=0` |
| 2100 s sem verde | o timer fecha sozinho | `tempo_s=2100`, `censurado=1` |
| Interrupção antes do time-box | `x` | `tempo_s=2100`, `censurado=1` |

> O `x` já foi um problema: até a correção em `src/timer.py`, ele gravava `tempo_s=2100`
> e `censurado=1` mesmo quando a verificação final passava em todos os testes, jogando
> fora o time-to-green real. Foi o que aconteceu nos trials #73, #75 e #76, corrigidos
> na mão depois. Hoje o `x` respeita o resultado da verificação final: se ela está verde,
> grava o tempo real e `censurado=0`. Ainda assim, confira a linha gravada em
> `data/trials_raw.csv` contra o `trial_log.txt` antes de fechar o cartão.

### 4.4 Depois do trial

- [ ] Conferir a linha gravada em `data/trials_raw.csv` contra o `trial_log.txt`.
- [ ] No `com-ia`, anotar `n_prompts` no `trial.json` da pasta do trial (seção 5).
- [ ] Commitar a pasta do trial referenciando a issue (ex.: `#66 registra trial K1 com-ia`).
- [ ] Preencher o registro obrigatório no corpo da issue e os campos do Project.
- [ ] Mover o cartão para **Done no mesmo dia do trial**.

---

## 5. Contagem de prompts

Métrica exploratória da RQ1, só no tratamento `com-ia`. O timer não coleta isso: anote
o total no `trial.json` da pasta do trial, na chave `n_prompts`, e
`python src/consolida.py` leva o valor para `data/trials.csv`.

Conta como **1 prompt** cada mensagem que você envia ao assistente: o pedido inicial,
cada follow-up ou correção, cada pedido de refatoração ou explicação. **Não** contam
respostas do assistente nem aceitar/rejeitar sugestão inline.

Nos trials `sem-ia` o campo fica **vazio**, nunca `0` — ausência de tratamento não é
contagem zero. `n_prompts` preenchido num trial `sem-ia` é tratado como erro pela
consolidação, porque indica uso de assistente onde não podia haver.

---

## 6. Registro de desvios

Nenhum trial é removido do dataset por falha, desistência ou violação: o desvio é
**anotado** e entra na análise como limitação. Registre na issue do trial e aqui.

| Data | Issue | Integrante | Kata | Desvio | Efeito na análise |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-09-17 | #73, #75, #76 | Gabriel | K2, K4, K5 | `x` gravou `tempo_s=2100` / `censurado=1` sobre um resultado verde; corrigido na mão a partir do `trial_log.txt` (`correcao_manual` no `trial.json`) | Tempos reais preservados; a correção manual precisa constar na metodologia do relatório |
| 2026-09-17 | #72 | Gabriel | K1 | Verificação final do `x` devolveu `0/0`: `testes_total=0` no registro, apagando o denominador da RQ2 (`trial_log.txt` mostra `0/9` no run anterior) | Linha bloqueada pela consolidação até o total ser restaurado para 9 |

Casos que **devem** ser registrados: uso acidental de IA no `sem-ia`; alteração de teste;
interrupção durante o trial; leitura prévia de solução de terceiro; execução fora da
ordem planejada; falha de ferramenta; correção manual de linha do `trials_raw.csv`.

---

## 7. Fora de escopo durante a S02

- Alterar enunciado de kata (`katas/kN/README.md`) ou suíte (`test_kN.py`).
- Alterar a tabela de contrabalanceamento ou as versões fixadas no README.
- Refazer um trial já executado (`--refazer` é só para teste da ferramenta).
- Rodar as métricas estáticas da RQ3 (issue #86) — acontecem **depois** dos 18 trials,
  em pipeline único para todos.

---

## 8. Pareamento da análise inferencial (S03, issues #90, #91, #92, #93)

**Proposta de Gabriel, pendente de aceite de Henrique e Guilherme.** Se ninguém
discordar, esta é a regra usada por todos os scripts de teste da S03.

O DESENHO.md fala em comparação pareada dentro de cada participante e afirma que a
mesma kata aparece uma vez em cada tratamento para cada participante. Isso não
bate com o próprio desenho: cada participante faz 6 trials, um por kata, cada um
em um único tratamento (tabela de contrabalanceamento e `PLANO` em `consolida.py`).
Não existe par "mesmo participante, mesma kata, com e sem IA".

O par que o dataset permite é por kata: para cada kata, a mediana dos trials com-IA
e a mediana dos trials sem-IA. São 6 pares (K1 a K6), cada kata com 3 trials (1 e 2,
em ordem que varia). Consequências:

- o teste é o Wilcoxon de postos sinalizados sobre 6 diferenças; o menor p possível
  é 0,015625 (unilateral) e 0,03125 (bilateral). Dois empates ou uma diferença nula
  já reduzem o poder de forma visível;
- o participante deixa de ser bloco do teste e vira variável de controle, descrita
  nas tabelas por trial;
- o tempo censurado entra com 2100 s e o número de pares com censura é reportado
  ao lado do p-valor;
- o relatório deve dizer que a formulação "dentro de cada participante" do
  DESENHO.md não foi executada, e por quê.

Implementação: `src/inferencia.py`. Testada só com entradas sintéticas em
`tests_analise/test_inferencia.py`; o script se recusa a testar quando faltam pares.
