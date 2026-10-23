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

Cinco refutadas, duas confirmadas. As duas que se confirmaram são as menos informativas: a H02 porque sua segunda metade estava dada na dica do enunciado, e a H04 porque o limiar de 24 h era frouxo. As cinco que caíram são as que carregam o conteúdo deste artigo — e a H05, em particular, caiu de um jeito que obrigou a reinterpretar a própria métrica (seção 3.10.3).

## 4.1 O que confirmou a expectativa

**A entrega é bem mais lenta do que o discurso sobre CI/CD sugere.** A mediana de frequência fica em 0,35 release por semana nos 900 repositórios, ou aproximadamente uma release a cada vinte dias. Projetos open-source populares com GitHub Actions configurado não entregam continuamente; entregam em ciclos. A faixa Elite do DORA, que exige entrega diária ou mais, é ocupada por uma minoria pequena.

**As distribuições são fortemente assimétricas à direita.** Era a expectativa, e os dados a confirmam com folga: nenhuma das cinco métricas passa em teste de normalidade, e a média do lead time chega a ser quase seis vezes a mediana. A exigência do enunciado de reportar mediana e IQR deixou de ser convenção e passou a ser um resultado demonstrado (seção 3.10.5).

**Os dois proxies de CFR discordam.** A taxa de falha medida por CI (5,3%) e a medida por release corretiva (25,0%) diferem por um fator de quase cinco. Elas não medem a mesma coisa — falha de pipeline não é falha em produção — e a divergência confirma que a escolha de proxy domina o resultado da RQ03.

## 4.2 O que surpreendeu

### A classificação DORA discrimina muito pouco

A expectativa era que as faixas Elite/High/Medium/Low separassem repositórios em dimensões reconhecíveis. Elas não separam. Contra popularidade (ε² = 0,008) e número de contribuidores (ε² = 0,022), a classificação não tem poder discriminante algum, e nenhuma das duas sobrevive à correção de Holm.

O que as faixas separam bem são **variantes alternativas das próprias métricas que as definem** — o CFR (b) alcança ε² = 0,379, perto do controle tautológico de 0,403. Isso é validade convergente, não discriminância. A leitura honesta é que a classificação DORA, nesta amostra, é em grande medida uma relabelagem de variáveis contínuas, e não um agrupamento com significado externo.

Esse achado conversa com a superdispersão encontrada na contagem de releases (índice 493×): a população é tão heterogênea em ritmo de entrega que quatro faixas fixas não capturam a estrutura real.

### A heurística de falha reprovou na validação humana

O resultado mais duro do trabalho veio da amostra-ouro. Três pessoas rotularam 300 releases de forma independente, e **nenhuma das quatro versões da heurística de release corretiva alcança o F1 mínimo de 0,70** exigido pelo enunciado. A melhor fica em 0,498; a que gerou o dataset, em 0,478, com precisão de 36,5%.

A expectativa era que a heurística errasse alguma coisa. Não era que errasse dois terços das vezes em que acusa.

Mais revelador ainda é o κ de Fleiss de 0,504 entre os avaliadores humanos, e a prevalência de "sim" variando de 16,7% a 37,3% entre eles. **O problema não é só que a regra automática é ruim: é que o conceito é ambíguo para humanos também.** Uma heurística não pode ser mais precisa que a definição que tenta capturar.

Isso recontextualiza a RQ03 inteira. A divergência entre o CFR (a) e o CFR (b) não é um caso de dois proxies válidos que medem coisas diferentes — é um proxy razoavelmente bem definido (falha de CI) contra um proxy que não sobrevive à validação.

### DORA e fluxo por PR são constructos distintos

A expectativa implícita em boa parte da literatura é que medidas de desempenho convirjam — que um time "rápido" apareça rápido em qualquer lente. Não acontece. O par mais direto, lead time por release contra lead time por PR, compartilha **10% da variância** (ρ = 0,319, n = 574), e o CFR por release contra a taxa de aceitação de PR não tem associação alguma (ρ = 0,044, p = 0,288 após Holm).

A consequência é incômoda: **o DORA não é *a* medida de desempenho de engenharia, é *uma* medida.** Uma lente igualmente legítima — o fluxo por pull request, nos padrões CHAOSS e SPACE — ordena os mesmos repositórios de maneira substancialmente diferente.

### A recuperação não tem taxa constante

A métrica de recuperação é reportada como mediana, o que trata todos os episódios como equivalentes. O ajuste de Weibull mostra que não são: forma mediana β = 0,557, com β < 1 em **87,8%** dos repositórios. Isso é **taxa de recuperação decrescente** — quanto mais tempo um episódio dura, menor a chance de terminar no instante seguinte. Falhas curtas se resolvem rápido; o episódio que se arrasta tende a se arrastar muito mais. Duas populações com o mesmo MTTR mediano podem ter dinâmicas opostas, e a mediana não distingue.

### A regra "n ≥ 30" não vale aqui

Com assimetria populacional de 8,26, a distribuição amostral da média ainda tem assimetria 1,53 em n = 30, e só se aproxima da normal perto de n = 300. A consequência recai sobre a RQ06: os testes por subgrupo operam exatamente onde a aproximação não vale, o que reforça os testes não paramétricos e o relato obrigatório de tamanho de efeito.

## 4.3 O que o tamanho da amostra mudou

Triplicar de 300 para 900 **não alterou nenhuma conclusão qualitativa** das RQ01–RQ05 nem da RQ07: todas as medianas caíram dentro do IC de 300 e os intervalos estreitaram de 21% a 51%. A exceção é a RQ06, onde a linguagem passa a ter efeito significativo — ganho de poder, não mudança de fenômeno.

Houve um resultado na direção oposta: a cobertura da API de Deployments **varia de forma detectável entre as três amostras** (31,3%, 41,7%, 43,3%; p = 0,0048), sem que perfil ou linguagem expliquem. O mesmo desenho que confirma a robustez das métricas DORA detecta a fragilidade de uma medida auxiliar — e é esse contraste que dá credibilidade ao primeiro resultado.

## 4.4 O que o estudo não consegue responder

Duas perguntas ficam estruturalmente fora de alcance pela mesma causa: **todo o processo é medido por proxies do próprio GitHub**, sem desfecho externo de qualidade.

**Previsibilidade.** Não há como verificar se as métricas preveem algo que interesse — incidente em produção, satisfação de usuário, custo de manutenção — porque nenhum desses desfechos existe nos dados.

**Poder discriminante contra qualidade.** Pelo mesmo motivo, só se avalia se as faixas separam atributos observáveis, não se separam alta de baixa qualidade. O resultado negativo da seção 3.10.4 mostra que elas não separam popularidade nem tamanho de equipe — o que é informativo, mas não equivale a dizer que não separam qualidade.
