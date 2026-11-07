# Roteiro oral — Lab04

Respostas de cerca de 30 segundos (70 a 80 palavras faladas), cada uma apontando o ponto do dashboard. Todos devem conhecer o dashboard inteiro: o professor pode pedir qualquer pergunta a qualquer integrante.

## Gabriel — perguntas 1, 2, 3, 4 e 14

### 1. Qual é o cenário e o que H₀ e H₁ afirmam?

*Mostrar: seção 1, "A pergunta".*

"Nosso cenário pergunta se classes maiores concentram mais defeitos. H₀ diz que não existe associação entre o tamanho da classe, em linhas de código, e o número de defeitos dela: ρ igual a zero. H₁ diz que existe associação, ρ diferente de zero. Comparamos dois testes para responder isso, Pearson e Spearman, e usamos simulação para ver qual deles acerta mais."

### 2. O teste é unicaudal ou bicaudal? Por quê?

*Mostrar: seção 1, quadro "Teste bicaudal".*

"Bicaudal. A literatura prevê associação positiva, mas uma associação negativa também seria um achado relevante: indicaria que classes grandes recebem mais revisão. Se fixássemos a direção antes de olhar os dados, gastaríamos os 5% de erro numa cauda só. No bicaudal ficam 2,5% em cada ponta, e o corte da t com 28 graus de liberdade é ±2,048."

### 3. Como os dados reais foram coletados e o que mostraram sobre a distribuição?

*Mostrar: seção 2, G1 (painéis em verde).*

"Baixamos o KC1 da NASA em nível de classe, 145 classes, de uma cópia pública no GitHub; a origem acadêmica é Koru e Liu, 2005, e a ressalva está no README dos dados. A distribuição é muito assimétrica à direita: assimetria 3,4 no tamanho e 5,5 nos defeitos, mediana de 162 linhas. E 85 das 145 classes, 59%, têm zero defeito."

### 4. Como os dados reais ajudaram a escolher os parâmetros da simulação?

*Mostrar: seção 2, G1 e texto abaixo dele.*

"Como os dados são assimétricos, a situação B usa uma lognormal, não uma normal. Estimamos a média e o desvio do log do tamanho nas 145 classes: 4,68 e 1,75. Para defeitos, como zero não tem log, usamos só as 60 classes com defeito: 1,92 e 0,98. A limitação é que o simulado nunca gera zero, e o G1 mostra essa diferença."

### 14. Nos dados reais, os dois testes chegaram à mesma conclusão? O efeito tem importância prática?

*Mostrar: seção 6, tabela.*

"Sim, os dois rejeitam H₀ com p menor que 0,001. O Pearson deu 0,69 e o Spearman 0,57, ambos efeito grande. O tamanho explica cerca de metade da variação dos defeitos pelo Pearson e um terço pelo Spearman. Na prática importa: tamanho é uma métrica barata para priorizar revisão. Mas não prova causa, porque classes grandes têm mais código onde errar."

## Pontos de atenção para a pergunta de follow-up

- **Pearson maior que Spearman nos dados reais.** A explicação provável é a assimetria: poucas classes enormes com muitos defeitos puxam o Pearson. Os dois intervalos de confiança de 95% se sobrepõem ([0,59; 0,77] e [0,44; 0,68]), então a diferença entre eles não é conclusiva.
- **Empates em zero.** Os 85 zeros empatam nos postos e tornam o p-valor do Spearman aproximado, sem mudar a decisão com n = 145.
- **Os números vêm de** `src/params.py` (parâmetros e estatísticas) e `src/dados_reais.py` (seção 6). Se o dataset mudar, o dashboard recalcula e este roteiro precisa ser revisado.
