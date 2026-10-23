# 5. Ameaças à validade

Taxonomia de Cook & Campbell, na adaptação de Wohlin et al. para engenharia de software. Cada ameaça é classificada em **mitigada**, **parcialmente mitigada** ou **aberta**, e apoiada nos resultados da validação manual (seção 2.7) e das análises de validade (seções 3.5 e 3.7).

## 5.1 Validade de construto — *medimos o que achamos que medimos?*

| Ameaça | Situação | Evidência |
| :--- | :--- | :--- |
| **Release não é deploy** | aberta, por construção | O GitHub não registra implantação. A API de Deployments cobre só 38,8% dos 900 repositórios, com cobertura que varia entre amostras (seção 3.7.8). É a limitação mais importante do trabalho. |
| **A heurística de release corretiva não é válida** | **aberta, agora quantificada** | Contra o gabarito humano, nenhuma das quatro versões atinge F1 = 0,70; a que gerou o dataset tem precisão de 36,5% (seção 2.7). |
| **O CFR (b) está acoplado à cadência** | **confirmada e medida** | A suspeita foi testada: ao condicionar pela oportunidade de observação, ρ cai de 0,604 para −0,039 (p = 0,52). O CFR (b) mede, em boa parte, ritmo de publicação (seção 3.7.3). |
| **Falha de CI não é falha em produção** | parcialmente mitigada | Os dois proxies diferem por quase cinco vezes (5,3% × 25,0%). Mitigação: reportar as duas variantes lado a lado, nunca escolher uma. |
| **Mono-método** | parcialmente mitigada | Tudo vem da API do GitHub. Mitigação: medir os mesmos constructos por PRs e issues (CHAOSS, SPACE). Nenhum par alcança ρ = 0,7 (seção 3.7.6). |
| **Ausência de desfecho externo** | aberta | Não há incidente em produção, satisfação de usuário nem custo de manutenção. Impede avaliar previsibilidade e restringe o poder discriminante a atributos observáveis, não a qualidade. |

As duas primeiras linhas mudaram de natureza neste trabalho: eram suspeitas e passaram a ser **resultados medidos**. Isso não as mitiga — ao contrário, confirma que o CFR (b) deve ser lido como indicador de cadência, não de falha.

## 5.2 Validade interna — *há fatores não controlados?*

| Ameaça | Situação | Evidência |
| :--- | :--- | :--- |
| **Tamanho e popularidade como confusão** | **mitigada** | Testada por dois caminhos: estratificação em quartis e correlação parcial de Spearman. O ρ de 0,562 cai no máximo 0,059 na parcial, e os doze estratos mantêm o sinal (0,381–0,698). As faixas também não separam estrelas (ε² = 0,008) nem contribuidores (ε² = 0,022). |
| **Repositórios antigos acumulam releases** | parcialmente mitigada | Idade é o único atributo independente que as faixas separam (ε² = 0,109). As métricas são normalizadas pela janela, o que limita a acumulação, e a idade entra como fator na RQ06. |
| **Heterogeneidade da população** | documentada, não mitigável | Índice de dispersão de 493× em relação à Poisson (seção 3.7.5). Quatro faixas fixas não capturam essa estrutura. |

## 5.3 Validade externa — *vale além da amostra?*

| Ameaça | Situação | Evidência |
| :--- | :--- | :--- |
| **Amostra de repositórios populares** | aberta, por desenho | ≥ 1.000 estrelas, ≥ 5 releases e ≥ 50 runs. **Nada aqui se generaliza para projetos corporativos, pequenos ou sem CI/CD estabelecido.** |
| **Sobrevivência do funil** | documentada | Dos 8.457 candidatos, poucos chegam à amostra; o filtro de releases é o mais severo. Funil e caracterização dos descartados em 2.6 e 3.7.1. |
| **Estabilidade entre amostras** | **mitigada para as métricas DORA** | Três amostras sem repositório em comum produzem estimativas sobrepostas nas seis métricas, com ICs estreitando 21%–51% (seção 3.7.1). |
| **…mas não para medidas auxiliares** | aberta | A cobertura da API de Deployments varia entre amostras de forma detectável (p = 0,0048) e sem causa identificada. |
| **Janela única** | aberta | 12 meses. A RQ08 não encontrou tendência interna, mas outro período pode dar outros valores absolutos. |

## 5.4 Validade de conclusão — *a estatística é adequada?*

| Ameaça | Situação | Evidência |
| :--- | :--- | :--- |
| **Hipóteses reconstruídas, não pré-registradas** | **aberta** | Ver abaixo. |
| **Múltiplas comparações** | mitigada | Holm em todas as famílias de testes; FDR na RQ08, onde apenas 1 de 600 repositórios mantém tendência após a correção. |
| **Pressupostos de normalidade** | mitigada | Nenhuma métrica passa em Shapiro-Wilk (p entre 10⁻¹⁴ e 10⁻³³). Todos os testes são não paramétricos e as estimativas são medianas com IQR. |
| **Poder em subgrupos** | parcialmente mitigada | O TLC só se aproxima perto de n = 300 nesta população (seção 3.7.5), e os subgrupos da RQ06 são menores. Mitigação: testes não paramétricos e relato obrigatório de tamanho de efeito. A linguagem na RQ06, que só fica significativa com 600, ilustra ganho de poder e não mudança de fenômeno. |
| **Dados censurados** | mitigada | Episódios sem recuperação na janela e releases dos últimos 7 dias ficam fora dos denominadores, com a proporção censurada reportada. |
| **Truncamento da paginação** | documentada | Atinge ~3% dos PRs e 8%–10% dos deployments, marcado por repositório; as medidas afetadas são lidas como limite inferior. |

**Sobre as hipóteses.** As da seção 1.4 foram escritas em 20/10/2026, com os resultados já disponíveis (seção 1.5). Isso abre espaço para HARKing e para viés na escolha do que reportar. Três coisas limitam o dano sem eliminá-lo: cada hipótese declara a origem da expectativa, e nenhuma foi derivada dos dados; cinco das sete foram refutadas, o oposto do padrão que HARKing produz; e as decisões analíticas sensíveis têm justificativa verificável sem olhar os dados — a série mensal da RQ08, por exemplo, decorre de um fato aritmético do teste de Mann-Kendall (com n = 4 o menor p bilateral possível é ≈ 0,089). Ainda assim não há como provar, depois do fato, qual era a expectativa. **Uma replicação deste desenho deve registrar as hipóteses antes da coleta.**
