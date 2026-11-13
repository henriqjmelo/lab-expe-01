# Roteiro de apresentação — Lab04

Guia do grupo para a apresentação: o que foi feito, onde cada coisa está no dashboard e como
conduzir os 7 minutos. As **respostas faladas** das 15 perguntas, já escritas e cronometradas,
estão em [`oral.md`](oral.md) — este arquivo é o mapa em volta delas.

O grupo comparou Pearson e Spearman por simulação: sob H₀ os dois erram igual (≈5,1%), mas quando
os dados ficam assimétricos o Pearson cai de 82,5% para 48,5% de poder, enquanto o Spearman não se
mexe — é esse número que sustenta a recomendação final.

São 7 minutos e 15 perguntas, cinco para cada um, respondidas em cima do
[dashboard publicado](https://lab-expe-01-be7jrem4xjxjbshdmy9ocq.streamlit.app). Todo mundo precisa
conhecer o dashboard inteiro: o professor pode passar qualquer pergunta para qualquer integrante.

## O que foi feito

Comparamos dois testes de correlação por simulação, para medir qual deles erra menos no nosso cenário.

- **O cenário.** A pergunta é se classes maiores concentram mais defeitos. H₀ diz que não existe
  associação entre o tamanho da classe (LOC) e o número de defeitos; H₁ diz que existe. Pearson e
  Spearman servem os dois para responder isso.
- **Por que simular.** Com dados reais ninguém sabe a resposta certa, então não dá para dizer se o
  teste acertou. Na simulação somos nós que decidimos se existe efeito e de que tamanho, e aí dá
  para contar os acertos e os erros.
- **Como.** 10.000 conjuntos de 30 observações por ponto, com a correlação latente indo de 0 a 0,5,
  em duas situações: **A** (normal, bem comportada) e **B** (lognormal, assimétrica como os dados
  reais). Semente 42 em tudo, então roda duas vezes e dá igual.
- **A amarração com o real.** As 145 classes do KC1 (NASA) deram os parâmetros da situação B e
  levaram os dois testes no fim, para ver se a recomendação se sustenta fora da simulação.

Com a correlação latente em zero, a proporção de rejeições **é** o erro tipo I; acima de zero, **é**
o poder. Os quatro gráficos do dashboard são leituras dessas mesmas 10.000 repetições.

## Os números de cor

Se for decorar só três: **5,1%** (erro tipo I dos dois), **82,5% → 48,5%** (o tombo do Pearson na
situação B) e **r = 0,2** (onde o Spearman passa).

| Número | Valor | Onde está |
| :--- | :--- | :--- |
| Dados reais | 145 classes do KC1 (NASA), mediana de 162 LOC | seção 1 |
| Assimetria dos dados reais | 3,40 em LOC e 5,53 em defeitos | seção 1 e 2 |
| Classes sem defeito nenhum | 85 de 145 (58,6%) — a principal limitação | seção 2 e 7 |
| Tamanho de cada conjunto simulado | n = 30, logo 28 graus de liberdade, corte em ±2,048 | seção 3 |
| Exemplo do G2 | Pearson p = 0,042 rejeita; Spearman p = 0,188 não | seção 3 |
| Erro tipo I, α = 0,05 | 5,07% a 5,16% nos dois testes e nas duas situações | seção 4 (G3) |
| Erro tipo I, α = 0,01 | Pearson na B em 2,69%, contra ≈1% dos outros três | seção 4 (tabela) |
| Poder em r = 0,5, situação A | Pearson 82,5% × Spearman 77,2% | seção 5 (G4) |
| Poder em r = 0,5, situação B | Pearson 48,5% × Spearman 77,2% | seção 5 (G4) |
| Onde a vantagem troca na B | r = 0,2 | seção 5 (G4) |
| Nas 145 classes reais | Pearson r = 0,69 e Spearman ρ = 0,57, ambos p < 0,001 | seção 6 |
| Margem das 10.000 repetições | ±0,4 ponto percentual | seção 4 (barras de erro) |

**O 77,2% repetido não é erro de digitação.** O Spearman dá exatamente o mesmo resultado nas duas
situações, e isso é a prova visual da robustez dele.

## O passeio pelo dashboard

A apresentação é guiada pelas 15 perguntas, não por um tour livre — mas vale saber onde cada coisa
está, porque a resposta é sempre "mostrar e falar". São 7 minutos: conte **cerca de 25 segundos por
pergunta** e uns 20 segundos de abertura.

| Seção | O que aparece | A frase que resume | Perguntas |
| :--- | :--- | :--- | :--- |
| 1. Cenário | A pergunta, H₀ e H₁, os quatro números do KC1, a tabela de erro tipo I × II e a expectativa registrada | "Classes maiores concentram mais defeitos? Dois testes respondem isso, e nós medimos qual erra menos." | 1, 2, 8, 13 |
| 2. Os dados (G1) | Histogramas real × simulado, em escala log, lado a lado | "Os dados reais são muito assimétricos, por isso a situação B usa lognormal e não normal." | 3, 4, 11 |
| 3. Como os testes funcionam (G2) | A curva t(28) sob H₀, a região de rejeição em vermelho, a área do p-valor em amarelo e o zoom da cauda | "A região de rejeição fica nas pontas porque é lá que estão os valores improváveis se H₀ fosse verdade." | 5, 6, 7 |
| 4. Erro tipo I (G3) | Quatro barras com a linha de 5% e a tabela de α = 0,01 | "Em 5% os dois estão calibrados; em 1% o Pearson da situação B escapa." | 9, 12 |
| 5. Poder (G4) | Três curvas, a linha roxa em r = 0,2 e os textos de leitura | "Quem detecta mais depende da distribuição — e é aqui que a vantagem troca de lado." | 10, 11, 13 |
| 6. Dados reais | Tabela com r, p, IC 95%, r² e decisão das 145 classes | "Nos dados reais os dois rejeitam H₀, e o efeito é grande pelos dois critérios." | 14 |
| 7. Conclusão | Expectativa × resultado, recomendação e limitações | "Recomendamos Spearman como análise principal neste cenário, e dizemos quando mudaríamos." | 15 |

**Dica de condução.** Em toda resposta, aponte primeiro ("isto aqui no G4") e só depois fale. O
dashboard foi feito para se explicar sozinho: cada gráfico já tem o texto de leitura embaixo, então
se travar, leia a primeira frase do bloco — ela é a conclusão.

## Quem responde o quê

Cinco perguntas para cada um — o enunciado exige no mínimo quatro. As respostas faladas estão em
[`oral.md`](oral.md); a tabela abaixo é só o mapa.

| # | Pergunta | Quem | Mostrar |
| :--- | :--- | :--- | :--- |
| 1 | O cenário e o que H₀ e H₁ afirmam | Gabriel | seção 1, "A pergunta" |
| 2 | Unicaudal ou bicaudal, e por quê | Gabriel | seção 1, quadro "Teste bicaudal" |
| 3 | Como os dados reais foram coletados e o que mostraram | Gabriel | seção 2, G1 |
| 4 | Como os dados reais escolheram os parâmetros da simulação | Gabriel | seção 2, texto abaixo do G1 |
| 5 | O que cada teste compara de fato | Guilherme | seção 3, "O que cada teste compara" |
| 6 | A distribuição sob H₀ e por que a região de rejeição fica onde fica | Guilherme | seção 3, G2 e o zoom |
| 7 | O que o p-valor significa — e o que não significa | Guilherme | seção 3, a área amarela |
| 8 | Erro tipo I e tipo II no cenário, qual seria mais grave | Guilherme | seção 1, tabela "O que seria errar" |
| 9 | No G3, algum teste se afastou de 5% | Henrique | seção 4, G3 |
| 10 | No G4, qual tem mais poder, e se a diferença muda | Guilherme | seção 5, G4 |
| 11 | Que violação foi simulada e por que afeta mais um teste | Henrique | seção 2 (G1) e seção 5 (G4) |
| 12 | O que mudaria com α = 0,01 | Henrique | seção 4, tabela de α |
| 13 | A simulação confirmou o que o grupo esperava | Henrique | seção 1 (expectativa) e seção 5 |
| 14 | Nos dados reais os dois concordam; o efeito importa na prática | Gabriel | seção 6, tabela |
| 15 | Qual teste recomendam, quando mudariam, qual a limitação | Henrique | seção 7, conclusão |

As perguntas **8, 11 e 13 são as que mais se repetem entre si** — todas tocam a assimetria. Se uma
delas já foi respondida, quem pegar a seguinte pode encurtar e só complementar.

## O que pode pegar

Seis perguntas de follow-up que o resultado abre. Todas têm resposta no próprio dashboard — vale ler
antes.

**1. "Por que o Spearman aparece com uma curva só no G4?"** — a mais provável, porque a legenda chama
atenção. A situação B só aplica `exp()` aos mesmos valores latentes da A, e `exp()` não muda a
**ordem** dos valores. Como o Spearman só olha postos, ele recebe exatamente a mesma entrada nas duas
— os números são idênticos, não parecidos. Isso é a definição de robustez a transformações
monotônicas, visível no gráfico.

**2. "Nos dados reais o Pearson deu 0,69 e o Spearman 0,57. Então o Pearson não é melhor?"** — a mais
perigosa, porque parece contradizer a recomendação. Duas coisas: correlação maior não é teste melhor
(poder é sobre **detectar**, não sobre o tamanho da estimativa), e os intervalos de confiança se
sobrepõem ([0,59; 0,77] contra [0,44; 0,68]), então a diferença entre os dois não é conclusiva. Além
disso, 85 classes empatadas em zero defeito reduzem a resolução dos postos e prejudicam justamente o
Spearman.

**3. "O erro tipo I ficou igual nos dois, então a assimetria não atrapalhou nada?"** — atrapalhou, só
não aparece em α = 0,05. Em α = 0,01 o Pearson da situação B rejeita 2,69% das vezes, quase o triplo
do nominal. É exatamente o que a tabela da seção 4 mostra, e é o sinal de que a aproximação t fica
mal calibrada na cauda.

**4. "Vocês erraram a previsão?"** — em parte, e o dashboard registra isso em vez de esconder.
Acertamos na situação B, a partir de r = 0,2. Erramos na A, onde o Pearson ganhou em toda a faixa, e
também no menor efeito da B (r = 0,1), onde o Pearson ainda ficou à frente. A expectativa prévia está
escrita na seção 1, com data anterior à S02.

**5. "A lognormal nunca gera zero, mas 59% das classes reais têm zero defeito. Isso não invalida a
situação B?"** — é a limitação que nós mesmos declaramos, na seção 2 e na 7. Ela deixa a simulação um
pouco **mais fácil** que a realidade, então o tombo do Pearson no mundo real tende a ser igual ou
pior, não menor.

**6. "Por que n = 30 e 10.000 repetições?"** — n = 30 é o tamanho que o enunciado pede e é onde os
pressupostos pesam mais; com 10.000 repetições a proporção estimada tem margem de cerca de ±0,4 ponto
percentual, que é o tamanho das barras de erro do G3.

## Checklist do dia

O primeiro item é o que mais dá errado: **no plano gratuito o app hiberna depois de um tempo sem
acesso**. Quem abre o link frio vê uma tela "Zzzz — this app has gone to sleep" e precisa clicar para
acordar, o que levou cerca de um minuto no nosso teste. Se o professor abrir o link antes de vocês, é
isso que ele vê.

- [ ] Abrir o dashboard 5 minutos antes de começar, para ele acordar
- [ ] Deixar a página rolada no topo, na seção 1
- [ ] Conferir que o cabeçalho mostra os três links: Repositório, GitHub Projects e Dashboard publicado
- [ ] Deixar o repositório e o Projects abertos em outra aba, caso ele peça
- [ ] Plano B testado: `cd lab-expe-04 && streamlit run app.py` roda local sem internet
- [ ] Cada um com o `docs/oral.md` aberto no celular
- [ ] Combinar a ordem de quem fala, para não haver pausa entre as perguntas

**Orçamento de tempo.** 20 segundos de abertura + 15 perguntas × 25 segundos ≈ 6 min 35 s, dentro dos
7 minutos. Se estourar, as perguntas 11 e 13 são as que mais repetem conteúdo já dito e podem ser
encurtadas.

**Links.** [Dashboard](https://lab-expe-01-be7jrem4xjxjbshdmy9ocq.streamlit.app) ·
[Repositório](https://github.com/henriqjmelo/lab-expe-01) ·
[GitHub Projects](https://github.com/users/henriqjmelo/projects/1)
