# 4. Discussão

Esta seção confronta as hipóteses informais da seção 1.4 com o que os dados mostraram, e discute o que surpreendeu. As hipóteses foram reconstruídas depois da coleta, não pré-registradas; a seção 1.5 explica o registro e a seção 5.4 trata disso como ameaça à validade de conclusão.

## 4.0 Placar das hipóteses

| # | Hipótese (seção 1.4) | Resultado | Veredito |
| :--- | :--- | :--- | :--- |
| **H01** | ≥ 1 release/semana | mediana 0,35 release/semana, ≈ 1 a cada 20 dias | **Refutada** |
| **H02** | Lead time em dias; (a) > (b) | mediana (a) 13,2 d e (b) 8,8 d | **Confirmada** |
| **H03** | CFR < 15% nas duas variantes e convergentes | (a) 5,3%; (b) 25,0% — divergem por ≈ 5× | **Refutada** |
| **H04** | Recuperação < 24 h | mediana 2,8 h | **Confirmada** |
| **H05** | Correlação frequência × CFR nula ou negativa | ρ = +0,18 em (a) e +0,60 em (b) | **Refutada** |
| **H06** | Fatores do repositório com efeito ao menos pequeno | ε² = 0,008 (estrelas) e 0,022 (contribuidores), nenhum sobrevive a Holm | **Refutada** |
| **H07** | < 20% mudam de faixa entre definições | 27,7% a 36,0% mudam | **Refutada** |

Cinco refutadas, duas confirmadas. As duas que se confirmaram são as menos informativas: a H02 porque sua segunda metade estava dada na dica do enunciado, e a H04 porque o limiar de 24 h era frouxo. As cinco que caíram são as que carregam o conteúdo deste artigo — e a H05, em particular, caiu de um jeito que obrigou a reinterpretar a própria métrica (seção 3.7.3).

## 4.1 O que confirmou a expectativa

**A entrega é mais lenta do que o discurso sobre CI/CD sugere.** Mediana de 0,35 release por semana — uma a cada vinte dias. Projetos open-source populares com Actions configurado não entregam continuamente; entregam em ciclos, e a faixa Elite é ocupada por uma minoria.

**As distribuições são fortemente assimétricas.** Nenhuma das cinco métricas passa em teste de normalidade e a média do lead time chega a quase seis vezes a mediana. A exigência de reportar mediana e IQR deixou de ser convenção e virou resultado demonstrado.

## 4.2 O que surpreendeu

**A heurística de falha reprovou na validação humana.** Nenhuma das quatro versões alcança o F1 mínimo de 0,70; a que gerou o dataset fica em 0,478, com precisão de 36,5%. A expectativa era que errasse alguma coisa, não que errasse dois terços das vezes em que acusa. Mais revelador é o κ de 0,504 entre os avaliadores e a prevalência de "sim" variando de 16,7% a 37,3%: **o problema não é só a regra automática ser ruim, é o conceito ser ambíguo para humanos também.** Uma heurística não pode ser mais precisa que a definição que tenta capturar. Isso recontextualiza a RQ03 — a divergência entre o CFR (a) e o (b) não é um caso de dois proxies válidos medindo coisas diferentes, mas de um proxy razoável contra um que não sobrevive à validação.

**A classificação DORA discrimina muito pouco.** As faixas não separam popularidade (ε² = 0,008) nem contribuidores (ε² = 0,022). O que separam bem são as próprias variáveis que as definem, perto do controle tautológico. Nesta amostra, a classificação é em grande medida uma relabelagem de variáveis contínuas, e o índice contínuo mostra que o corte em faixas descarta mais de um terço da informação.

**DORA e fluxo por PR são constructos distintos.** O par mais direto compartilha 10% da variância, e CFR (b) contra aceitação de PR não tem associação alguma (ρ = 0,044). A consequência é incômoda: **o DORA é *uma* medida de desempenho de engenharia, não *a* medida**, e uma lente igualmente legítima ordena os mesmos repositórios de forma substancialmente diferente.

**A recuperação não tem taxa constante.** O ajuste de Weibull dá β mediano de 0,557, com β < 1 em 87,8% dos repositórios: quanto mais tempo um episódio dura, menor a chance de terminar no instante seguinte. Duas populações com o mesmo MTTR mediano podem ter dinâmicas opostas, e a mediana não distingue.

## 4.3 O que o estudo não consegue responder

Duas perguntas ficam fora de alcance pela mesma causa: **todo o processo é medido por proxies do próprio GitHub**, sem desfecho externo de qualidade. Não há como avaliar **previsibilidade** — se as métricas preveem incidente em produção, satisfação de usuário ou custo de manutenção — nem **poder discriminante contra qualidade**: o resultado negativo da seção 3.7 mostra que as faixas não separam popularidade nem tamanho de equipe, o que é informativo, mas não equivale a dizer que não separam qualidade.
