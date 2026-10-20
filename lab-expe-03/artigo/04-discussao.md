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

Cinco refutadas, duas confirmadas. As duas que se confirmaram são as menos informativas: a H02 porque sua segunda metade estava dada na dica do enunciado, e a H04 porque o limiar de 24 h era frouxo. As cinco que caíram são as que carregam o conteúdo deste artigo — e a H05, em particular, caiu de um jeito que obrigou a reinterpretar a própria métrica (seção 3.13).

## 4.1 O que confirmou a expectativa

**A entrega é bem mais lenta do que o discurso sobre CI/CD sugere.** A mediana de frequência fica em 0,35 release por semana nos 900 repositórios, ou aproximadamente uma release a cada vinte dias. Projetos open-source populares com GitHub Actions configurado não entregam continuamente; entregam em ciclos. A faixa Elite do DORA, que exige entrega diária ou mais, é ocupada por uma minoria pequena.

**As distribuições são fortemente assimétricas à direita.** Era a expectativa, e os dados a confirmam com folga: nenhuma das cinco métricas passa em teste de normalidade, e a média do lead time chega a ser quase seis vezes a mediana. A exigência do enunciado de reportar mediana e IQR deixou de ser convenção e passou a ser um resultado demonstrado (seção 3.12).

**Os dois proxies de CFR discordam.** A taxa de falha medida por CI (5,3%) e a medida por release corretiva (25,0%) diferem por um fator de quase cinco. Elas não medem a mesma coisa — falha de pipeline não é falha em produção — e a divergência confirma que a escolha de proxy domina o resultado da RQ03.

## 4.2 O que surpreendeu

### A classificação DORA discrimina muito pouco

A expectativa era que as faixas Elite/High/Medium/Low separassem repositórios em dimensões reconhecíveis. Elas não separam. Contra popularidade (ε² = 0,008) e número de contribuidores (ε² = 0,022), a classificação não tem poder discriminante algum, e nenhuma das duas sobrevive à correção de Holm.

O que as faixas separam bem são **variantes alternativas das próprias métricas que as definem** — o CFR (b) alcança ε² = 0,379, perto do controle tautológico de 0,403. Isso é validade convergente, não discriminância. A leitura honesta é que a classificação DORA, nesta amostra, é em grande medida uma relabelagem de variáveis contínuas, e não um agrupamento com significado externo.

Esse achado conversa com a superdispersão encontrada na contagem de releases (índice 493×): a população é tão heterogênea em ritmo de entrega que quatro faixas fixas não capturam a estrutura real.

### DORA e fluxo por PR são constructos distintos

Esta foi a maior surpresa. A expectativa implícita em boa parte da literatura é que medidas de desempenho de entrega convirjam — que um time "rápido" apareça rápido em qualquer lente. Não é o que acontece.

O par mais direto, lead time medido por release contra lead time medido por PR, compartilha **10% da variância** (ρ = 0,319, n = 574). E o CFR por release contra a taxa de aceitação de PR não tem associação alguma (ρ = 0,044, p = 0,288 após Holm, n = 597), apesar de ambos pretenderem falar sobre qualidade.

A consequência é direta e incômoda: **o DORA não é *a* medida de desempenho de engenharia, é *uma* medida**, e uma lente igualmente legítima — a do fluxo de trabalho por pull request, nos padrões CHAOSS e SPACE — ordena os mesmos 900 repositórios de maneira substancialmente diferente. Um repositório bem classificado pela cadência de release pode ser lento na revisão de código, e vice-versa.

### A recuperação não tem taxa constante

A métrica de tempo de recuperação do DORA é reportada como mediana, o que implicitamente trata todos os episódios de falha como equivalentes. O ajuste de uma Weibull aos episódios mostra que não são: o parâmetro de forma tem mediana 0,557, com β < 1 em 90,3% dos repositórios.

Isso significa **taxa de recuperação decrescente** — quanto mais tempo um episódio de falha já dura, menor a probabilidade de ele terminar no instante seguinte. Falhas curtas se resolvem rápido; o episódio que se arrasta tende a se arrastar muito mais. Duas populações com o mesmo MTTR mediano podem ter dinâmicas opostas, e a mediana não distingue.

### A regra "n ≥ 30" não vale aqui

Com a população tendo assimetria 8,26, a distribuição amostral da média ainda tem assimetria 1,53 em n = 30, e só se aproxima da normal perto de n = 300. A consequência prática recai sobre a RQ06: os testes por subgrupo — quartis de estrelas, linguagens com poucos repositórios — operam exatamente na faixa onde a aproximação não vale, o que reforça o uso de testes não paramétricos e a obrigação de reportar tamanho de efeito junto do p-valor.

## 4.3 O que o tamanho da amostra mudou, e o que não mudou

Triplicar a amostra de 300 para 900 **não alterou nenhuma conclusão qualitativa** das RQ01 a RQ05 nem da RQ07. Todas as medianas de 600 e de 900 caíram dentro do intervalo de confiança de 300, e os intervalos estreitaram de 21% a 51%.

A exceção é a RQ06: com 600 repositórios, a linguagem passa a apresentar efeito significativo que em 300 estava abaixo do limiar de detecção. Isso não é a métrica mudando de comportamento, é o teste ganhando poder — e é a razão de reportar sempre o `n` e o tamanho de efeito ao lado do p-valor.

Houve, porém, um resultado na direção oposta. A cobertura da API de Deployments **varia de forma detectável entre as três amostras independentes** (31,3%, 41,7% e 43,3%; qui-quadrado p = 0,0048, tendência de Cochran-Armitage p = 0,0026), e nem o perfil dos repositórios nem a linguagem explicam a diferença. O mesmo desenho amostral que confirma a robustez das métricas DORA detecta a fragilidade de uma medida auxiliar — e esse contraste é o que dá credibilidade ao primeiro resultado.

## 4.4 O que o estudo não consegue responder

Duas perguntas ficam estruturalmente fora de alcance, e por uma única causa: **todo o processo de entrega é medido por proxies do próprio GitHub**, sem nenhum desfecho externo de qualidade.

**Previsibilidade.** Não é possível verificar se as métricas preveem algum resultado que interesse — incidente em produção, satisfação de usuário, custo de manutenção —, porque nenhum desses desfechos está disponível.

**Poder discriminante contra qualidade.** Pelo mesmo motivo, o máximo que se consegue avaliar é se as faixas separam repositórios em atributos observáveis, e não se separam alta de baixa qualidade. O resultado negativo da seção 3.12 deve ser lido com essa ressalva: ele mostra que as faixas não separam popularidade nem tamanho de equipe, o que é informativo, mas não equivale a dizer que não separam qualidade.

Fechar essas lacunas exigiria dados de fora do GitHub — relatórios de incidente, pesquisas com mantenedores, dados de uso — e é a direção natural para uma extensão do estudo.
