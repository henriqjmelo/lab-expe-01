# 5. Ameaças à validade

As ameaças seguem a taxonomia de Cook & Campbell adotada por Wohlin et al. em engenharia de software. Cada uma é apoiada nos resultados da validação manual (seção 2) e das análises de sensibilidade e validade (seções 3.8 e 3.12), e é classificada entre **mitigada**, **parcialmente mitigada** e **aberta**.

## 5.1 Validade de construto

*Medimos o que achamos que medimos?*

### Release não é deploy — **aberta, por construção**

O GitHub não registra deploy em produção. A frequência de entrega é medida por releases publicadas, e o lead time pelo intervalo entre commit e release. Um projeto que publica release sem implantar, ou que implanta continuamente sem publicar release, é medido errado por este estudo.

A tentativa de medir deploy diretamente, pela API de Deployments, esbarrou em **cobertura de 38,8% nos 900 repositórios** — e numa cobertura que varia entre amostras de forma detectável (seção 3.12). Por isso ela entra como subamostra de validação, não como medida principal. A ameaça permanece aberta e é a limitação mais importante do trabalho.

### Falha de CI não é falha em produção — **parcialmente mitigada**

O CFR (a) mede falha de pipeline. A diferença em relação ao CFR (b), que mede release seguida de corretiva, é de quase cinco vezes (5,3% contra 25,0%), o que mostra que os dois proxies não são intercambiáveis. A mitigação adotada foi reportar as duas variantes lado a lado em todas as análises, em vez de escolher uma.

### O CFR (b) pode estar acoplado à cadência de publicação — **aberta**

A correlação entre frequência de deploy e CFR (b) é positiva e forte (ρ = 0,562). O CFR (b) conta releases seguidas de uma corretiva em até 7 dias, e quem publica com mais frequência tem naturalmente mais chance de ter *alguma* release nessa janela. **Parte da associação pode estar embutida na definição da métrica.**

A verificação é possível e não foi feita: bastaria comparar o CFR (b) observado com o esperado sob publicação aleatória na mesma cadência. Fica registrado como limitação conhecida.

### Mono-método — **parcialmente mitigada**

Todas as métricas vêm da mesma fonte, a API do GitHub. A mitigação foi medir os mesmos constructos por caminhos independentes: releases e CI (DORA clássico) contra pull requests e issues (CHAOSS, Flow, SPACE). O resultado foi revelador — **nenhum par de medidas do mesmo constructo alcança ρ = 0,7** (seção 3.12), o que indica que a operacionalização escolhida determina boa parte do resultado.

### Ausência de desfecho externo — **aberta**

Não há nenhuma medida de qualidade independente do pipeline: nem incidente em produção, nem satisfação de usuário, nem custo de manutenção. Isso impede avaliar a **previsibilidade** das métricas e limita a avaliação do **poder discriminante** a atributos observáveis, não a qualidade de fato.

## 5.2 Validade interna

*Há fatores não controlados que explicam os resultados?*

### Tamanho e popularidade como variável de confusão — **mitigada**

Repositórios grandes têm mais releases, mais runs, mais contribuidores e mais issues ao mesmo tempo, o que é o padrão que El Emam et al. (2001) encontraram ao controlar o tamanho da classe nas métricas CK.

A ameaça foi **testada por dois caminhos independentes** (seção 3.12): estratificação em quartis e correlação parcial de Spearman. O ρ agregado de 0,562 cai no máximo 0,059 na parcial, e os doze estratos mantêm o mesmo sinal, variando entre 0,381 e 0,698. **Verificação feita, confusão não encontrada.**

Reforça o resultado o fato de as faixas DORA não separarem estrelas (ε² = 0,008) nem contribuidores (ε² = 0,022).

### Repositórios antigos acumulam mais releases — **parcialmente mitigada**

A idade é o único atributo independente que as faixas DORA separam (ε² = 0,109, p = 1,2 × 10⁻⁶), ainda que com efeito pequeno. Como as métricas são normalizadas pela janela de 12 meses, o efeito de acumulação histórica é limitado, mas repositórios mais maduros podem ter processos mais estabelecidos. A idade entra como fator na RQ06 e o efeito é reportado.

### Heterogeneidade da população — **documentada, não mitigável**

A contagem de releases tem índice de dispersão de **493×** em relação ao que a Poisson exigiria (seção 3.12). A população não é homogênea em ritmo de entrega, e nenhum agrupamento em quatro faixas fixas captura essa estrutura. Isso não é um defeito do estudo, mas precisa ser considerado ao interpretar qualquer média ou classificação.

## 5.3 Validade externa

*Os resultados valem para além da amostra?*

### Amostra de repositórios populares — **aberta, por desenho**

O critério de inclusão exige no mínimo 1.000 estrelas, 5 releases publicadas e 50 workflow runs válidos na janela. Isso seleciona projetos open-source maduros e visíveis. **Nada aqui se generaliza para projetos corporativos, projetos pequenos ou projetos sem CI/CD estabelecido**, e as conclusões devem ser lidas restritas a esse contexto.

### Sobrevivência do funil — **documentada**

Dos 8.457 candidatos da busca, apenas uma fração chega à amostra: o filtro de releases é o mais severo, eliminando a maioria. O funil completo é reportado por amostra (seções 3.9 e 2), e a caracterização dos descartados está na seção de viés de seleção.

### Estabilidade entre amostras independentes — **mitigada para as métricas DORA**

Três amostras com sementes distintas e **nenhum repositório em comum** produzem estimativas que se sobrepõem em todas as seis métricas, com os intervalos estreitando de 21% a 51% ao triplicar o n (seção 3.9). É evidência de que os resultados não dependem do sorteio.

A mitigação **não se estende** à cobertura da API de Deployments, que varia entre as amostras de forma estatisticamente detectável e sem causa identificada (seção 3.12).

### Janela de observação única — **aberta**

Os dados cobrem 12 meses (01/10/2025 a 30/09/2026). A RQ08 não encontrou tendência sistemática dentro da janela, mas nada garante que outro período produziria os mesmos valores absolutos.

## 5.4 Validade de conclusão

*A análise estatística é adequada?*

### Hipóteses reconstruídas, não pré-registradas — **aberta**

As hipóteses informais da seção 1.4 foram escritas em 20/10/2026, depois de a coleta terminar e os resultados estarem disponíveis ao grupo (seção 1.5). Isso abre espaço para HARKing — formular a hipótese já sabendo o resultado — e para viés de confirmação na escolha de quais análises reportar.

Três coisas limitam o dano, nenhuma o elimina. Primeiro, cada hipótese declara a origem da expectativa, e todas vêm do programa DORA, do texto do enunciado ou de raciocínio anterior à coleta; nenhuma foi derivada dos dados. Segundo, cinco das sete foram refutadas (seção 4.0), o que é o oposto do padrão que HARKing produz. Terceiro, as decisões analíticas que poderiam ter sido ajustadas ao resultado têm justificativa verificável sem olhar os dados — a escolha da série mensal em vez da trimestral na RQ08 (seção 3.11), por exemplo, decorre de um fato aritmético sobre o teste de Mann-Kendall (com n = 4, o menor p bilateral possível é ≈ 0,089, qualquer que seja a série), e não de preferência por um resultado.

Ainda assim, a ameaça permanece aberta: não há como provar, depois do fato, que a expectativa era essa. Uma replicação deste desenho deve registrar as hipóteses antes da coleta.

### Múltiplas comparações — **mitigada**

Todas as famílias de testes são corrigidas por **Holm**, e a RQ08, com centenas de testes simultâneos, usa FDR. O efeito da correção é visível e foi reportado: na RQ08, apenas 1 dos 600 repositórios mantém tendência significativa após o FDR.

### Pressupostos de normalidade — **mitigada**

Nenhuma das cinco métricas passa em teste de normalidade (p entre 10⁻¹⁴ e 10⁻³³). Por isso **todos os testes são não paramétricos** — Spearman, Mann-Whitney, Kruskal-Wallis — e as estimativas centrais são medianas com IQR, nunca média e desvio.

### Poder estatístico em subgrupos — **parcialmente mitigada**

A demonstração do Teorema Central do Limite (seção 3.12) mostra que, nesta população, a distribuição amostral só se aproxima da normal perto de n = 300. Os testes por subgrupo da RQ06 operam com n muito menor. A mitigação é dupla: testes não paramétricos, que não dependem da aproximação, e **relato obrigatório do tamanho de efeito** (ε² e delta de Cliff) junto do p-valor.

O caso da linguagem na RQ06 ilustra o ponto: o efeito só passa a ser significativo com 600 repositórios, o que é ganho de poder e não mudança de fenômeno.

### Dados censurados — **mitigada**

Episódios de falha que não terminam dentro da janela e releases publicadas nos últimos 7 dias ficam fora dos denominadores, e a proporção censurada é reportada por repositório em vez de ser descartada em silêncio.

### Truncamento da paginação — **documentada**

A coleta GraphQL tem limite por repositório. O truncamento atinge cerca de 3% dos PRs e 8% a 10% dos deployments, e é marcado por repositório, de modo que as medidas afetadas são lidas como limite inferior.
