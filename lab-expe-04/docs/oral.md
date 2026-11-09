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

## Guilherme — perguntas 5, 6, 7, 8 e 10

### 5. O que cada um dos dois testes compara de fato (médias, postos, proporções...)?

*Mostrar: seção 3, o parágrafo "O que cada teste compara".*

"Os dois medem associação, mas não a mesma coisa. O Pearson compara o quanto tamanho e defeitos variam juntos em valor: é associação linear sobre os números crus. O Spearman faz a mesma conta depois de trocar cada valor pelo seu posto, então mede se a ordem acompanha — associação monotônica. Na prática: para o Pearson, uma classe de 3.000 linhas vale vinte vezes uma de 150; para o Spearman ela é só a maior da fila."

### 6. No G2: o que é a distribuição da estatística sob H₀, e por que a região de rejeição fica onde fica?

*Mostrar: seção 3, G2 (a curva azul e o zoom da cauda).*

"A curva é a distribuição da estatística do teste quando H₀ é verdadeira. O Pearson converte o r num t: r vezes raiz de n menos 2, dividido por raiz de 1 menos r ao quadrado. Com n igual a 30, isso segue uma t de Student com 28 graus de liberdade. A região de rejeição fica nas duas pontas porque é lá que estão os valores de t improváveis caso não houvesse associação nenhuma: 2,5% de cada lado, além de mais ou menos 2,048."

### 7. O que significa o p-valor do exemplo mostrado no G2? E o que ele não significa?

*Mostrar: seção 3, a área amarela do G2 e a tabela logo abaixo.*

"No exemplo o Pearson deu p igual a 0,042, que é a área amarela. Significa: se H₀ fosse verdadeira, um t tão ou mais extremo quanto o nosso apareceria em 4,2% das amostras. O que ele não significa: não é a probabilidade de H₀ ser verdadeira, não é a chance de estarmos errados ao rejeitar, e não mede tamanho de efeito. Prova disso é o mesmo conjunto: o Spearman deu 0,188 e não rejeita."

### 8. No cenário de vocês, o que seria um erro tipo I e um erro tipo II? Qual seria mais grave?

*Mostrar: seção 1, a tabela "O que seria errar, aqui".*

"Erro tipo I seria concluir que classes maiores têm mais defeitos quando não têm: o time passaria a priorizar revisão e refatoração por tamanho, gastando esforço num critério que não prevê nada. Erro tipo II seria existir a associação e o teste não detectar: aí se joga fora um indicador de risco barato, porque o tamanho já está medido. Para nós o tipo I é mais grave: ele cria uma política custosa e difícil de reverter, enquanto o tipo II só mantém o time onde já está."

### 10. No G4, qual teste tem mais poder? A diferença muda conforme o tamanho do efeito?

*Mostrar: seção 5, G4.*

"Na situação A, que é a bem comportada, o Pearson tem mais poder em toda a faixa. E a diferença muda, sim. Em r igual a 0,1 os dois praticamente empatam, perto de 8%. A distância máxima aparece em r igual a 0,4: Pearson 61,3% contra 55,8% do Spearman, quase 6 pontos. Em 0,5 volta a encolher, porque as duas curvas sobem para o teto. Faz sentido: com normalidade o Pearson é o teste ótimo, e o Spearman paga um pedaço do poder por usar postos."

Na situação B, a vantagem troca: Pearson fica ligeiramente acima em r=0,1 (9,2% contra 7,8%), mas Spearman supera o Pearson de r=0,2 até r=0,5; no efeito máximo, 77,2% contra 48,5%. O G4 mostra ambas as situações, com linhas sólidas para A e tracejadas para B.

## Henrique — perguntas 9, 11, 12, 13 e 15

### 9. No G3, algum teste se afastou de 5%? Ele ficou liberal ou conservador, e por quê?

*Mostrar: seção 4, G3.*

"Com α=0,05, nenhum teste se afastou de forma relevante: as taxas de erro tipo I ficaram entre 5,07% e 5,16% nas situações normal e lognormal, dentro da margem visual de aproximadamente 0,4 ponto percentual. Portanto, ambos ficaram perto dos 5% nominais. O achado muda no α=0,01: o Pearson na situação B rejeitou 2,69% das vezes, acima do 1% esperado, sinal de que a aproximação t fica menos bem calibrada com as marginais muito assimétricas."

### 11. Que violação de pressuposto vocês simularam, e por que ela afeta mais um teste?

*Mostrar: seção 2, G1, e seção 5, G4.*

"Na situação B transformamos os valores latentes normais com exponencial, produzindo marginais lognormais assimétricas, como as do KC1. O Pearson trabalha sobre os valores brutos e é sensível à assimetria; sob essa transformação a associação linear em escala original enfraquece e seu poder cai. O Spearman usa postos e a exponencial preserva a ordem, então sua estatística e curva de poder ficam iguais às da situação A neste desenho. A limitação é que a lognormal nunca gera zero defeitos, embora 58,6% das classes reais sejam zero."

### 12. Se usássemos α=0,01 em vez de 0,05, o que mudaria no G3 e no G4?

*Mostrar: tabela de α=0,01 abaixo do G3.*

"O corte mais rigoroso reduz falso positivo, mas também reduz poder, porque exige um p-valor menor para rejeitar H₀. Na situação A, o erro tipo I fica perto de 1%: Pearson 1,05% e Spearman 1,16%. Na situação B, Spearman também fica em 1,16%, mas Pearson sobe para 2,69%, revelando pior calibração da aproximação t sob assimetria. Em r=0,5, por exemplo, o poder cai de 82,5% para 62,0% no Pearson da situação A e de 77,2% para 54,7% no Spearman."

### 13. A simulação confirmou o que o grupo esperava antes de simular?

*Mostrar: seção 1, hipótese prévia, e seção 5, G4.*

"Em grande parte, sim. Esperávamos que Pearson fosse melhor no caso normal e Spearman se beneficiasse da assimetria. Na situação A, Pearson teve mais poder em todos os efeitos positivos. Na situação B, Spearman passou a ter mais poder a partir de r=0,2; em r=0,1 o Pearson ainda ficou ligeiramente à frente. Isso é coerente com Spearman preservar os postos sob transformação monotônica, enquanto a associação linear medida pelo Pearson é reduzida na escala lognormal."

### 15. Qual teste vocês recomendam, quando mudariam a recomendação e qual é a principal limitação?

*Mostrar: seção 7, conclusão.*

"Para LOC e defeitos do KC1, que são muito assimétricos e levantam uma pergunta sobre associação monotônica, recomendamos Spearman como análise principal e Pearson como complemento para associação linear. Se os dados fossem aproximadamente normais, sem outliers influentes, e o interesse fosse especificamente linear, escolheríamos Pearson, que teve maior poder na situação A. A limitação principal é que a situação B lognormal não reproduz as classes sem defeitos, quase 59% do KC1; além disso, a simulação usa n=30 e não permite inferir causalidade."

## Pontos de atenção para a pergunta de follow-up

- **Pearson maior que Spearman nos dados reais.** A explicação provável é a assimetria: poucas classes enormes com muitos defeitos puxam o Pearson. Os dois intervalos de confiança de 95% se sobrepõem ([0,59; 0,77] e [0,44; 0,68]), então a diferença entre eles não é conclusiva.
- **Empates em zero.** Os 85 zeros empatam nos postos e tornam o p-valor do Spearman aproximado, sem mudar a decisão com n = 145.
- **Os números vêm de** `src/params.py` (parâmetros e estatísticas) e `src/dados_reais.py` (seção 6). Se o dataset mudar, o dashboard recalcula e este roteiro precisa ser revisado.
