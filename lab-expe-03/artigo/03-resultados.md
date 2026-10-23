# 3. Resultados

Todas as métricas são resumidas por **mediana e IQR** (1º–3º quartil), como pede o enunciado e como a seção 3.7.5 demonstra ser necessário. Os resultados aparecem no escopo pedido (300 repositórios da amostra 1) e na amostra estendida, para mostrar que não dependem do sorteio.

O CFR (b) usa a heurística v0 de release corretiva, **reprovada na validação contra o gabarito humano** (F1 = 0,478, precisão 36,5%; seção 2.7). Foi mantida por ser a melhor disponível sem recoletar, e todo resultado marcado **[NÃO VALIDADO]** deve ser lido com essa ressalva.

**Tabela 3 — Resumo das métricas.** Mediana [IQR].

| Métrica | n (300 / 900) | 300 | 900 |
| :--- | :--- | :--- | :--- |
| Frequência de deploy (releases/semana) | 300 / 900 | 0,35 [0,19 – 0,81] | 0,35 [0,19 – 0,84] |
| Lead time (a), por release (dias) | 293 / 873 | 13,2 [3,1 – 37,3] | 12,0 [3,0 – 37,4] |
| Lead time (b), por commit (dias) | 293 / 873 | 8,8 [2,8 – 29,4] | 9,0 [2,5 – 28,1] |
| CFR (a), proxy de CI | 300 / 900 | 5,6% [2,2% – 11,2%] | 5,3% [2,2% – 11,2%] |
| CFR (b), proxy de entrega [NÃO VALIDADO] | 300 / 900 | 25,0% [5,2% – 56,5%] | 25,0% [6,2% – 50,3%] |
| Tempo de recuperação (horas) | 278 / 834 | 2,8 [0,9 – 11,9] | 3,1 [0,9 – 17,3] |

Ficam sem lead time os repositórios com mais de 300 releases na janela, cujo cálculo foi omitido para preservar a cota da API (7 na A1, 27 no total). Ficam sem tempo de recuperação os que não tiveram nenhum episódio de falha fechado (22 na A1, 66 no total).

**Leitura geral:** ao triplicar a amostra, **todas as medianas ficam praticamente no mesmo lugar**, dentro do intervalo de confiança do escopo de 300. O detalhe está na seção 3.7.1. As figuras se regeneram com `python -m analise`.

---

## 3.1 RQ 01 a RQ 04 — as quatro métricas

Os valores centrais estão na Tabela 3. Em síntese:

**Frequência (RQ01).** Mediana de 0,35 release por semana, cerca de uma a cada 20 dias. Quase metade dos repositórios é **Medium** (entre uma por mês e uma por semana) e um terço é **Low**. Só 2% alcançam Elite. Projetos que entregam continuamente sem publicar releases ficam subestimados por construção, e os que não chegam a 5 releases já caíram no funil.

**Lead time (RQ02).** Medianas de 13,2 dias pela variante (a) e 8,8 pela (b). Em **65% dos repositórios a (b) é menor**. A razão é estrutural: a (a) mede desde o commit *mais antigo* de cada release, e um único commit esquecido puxa a release inteira para cima; a (b) usa a mediana de todos os commits, e a maioria entra perto da publicação. Quando cada release tem poucos commits, as duas convergem.

**Change failure rate (RQ03).** Os dois proxies contam histórias opostas. Pela falha de CI, **84% dos repositórios são Elite** (mediana 5,6%). Pela release corretiva em até 7 dias, só **37%** (mediana 25,0%), e 23% têm CFR (b) igual a zero. O CFR (a) mede falha de *pipeline* — teste instável entra como falha; o CFR (b) depende da heurística corretiva, reprovada na seção 2.7.

**Recuperação (RQ04).** Mediana de 2,8 horas. Recuperam-se em menos de 1 hora 27% dos repositórios, em menos de 1 dia 83%, em menos de 1 semana 97%. Os episódios censurados são 0,7% de 20.077.

![Change failure rate pelos dois proxies](../analise/saida/600/figuras/fig04_rq03_cfr.png)

**Como ler.** Curva acumulada: para cada valor de CFR no eixo horizontal, a altura é a proporção de repositórios com CFR até ali. Quanto mais cedo a curva sobe, menor a taxa de falha. As verticais são as fronteiras DORA (15%, 30%, 45%). As duas curvas separadas são o resultado: o proxy escolhido domina a resposta da RQ03.

## 3.2 Classificação DORA (combinação de referência)

![Perfil DORA por métrica](../analise/saida/600/figuras/fig06_perfil_dora.png)

**Como ler.** Cada barra soma 100% dos repositórios, divididos pela categoria DORA daquela métrica; o tom mais escuro é Elite. "Geral" é a classificação final do enunciado: mediana dos pontos das quatro métricas, arredondada para baixo.

| Classificação geral | Elite | High | Medium | Low |
| :--- | ---: | ---: | ---: | ---: |
| 300 repositórios | 8% | 35% | 50% | 7% |
| 600 repositórios | 7% | 36% | 48% | 9% |

Metade é Medium e um terço é High. Cada métrica puxa para um lado: o CFR (a), quase todo em Elite, puxa para cima; a frequência, com ~80% entre Medium e Low, puxa para baixo; o lead time se espalha pelas quatro.

## 3.3 RQ 05 — Velocidade × estabilidade

![Frequência de deploy contra taxa de falha](../analise/saida/600/figuras/fig07_rq05_velocidade_estabilidade.png)

**Como ler.** Cada ponto é um repositório: frequência de deploy no eixo horizontal (escala log), CFR no vertical. O ρ de Spearman vai de −1 a 1; perto de zero indica ausência de relação monotônica.

| Correlação com a frequência | 300 | 600 |
| :--- | :--- | :--- |
| CFR (a), proxy de CI | ρ = 0,18 (p = 0,002) | ρ = 0,12 (p = 0,004) |
| CFR (b), proxy de entrega [NÃO VALIDADO] | ρ = 0,60 (p < 0,001) | ρ = 0,56 (p < 0,001) |

Pelo CI a correlação é significativa mas **fraca**, e diminui com a amostra maior: publicar mais não se associa a quebrar mais o pipeline, o que é coerente com a tese do DORA. Pela entrega é **forte** — mas a seção 3.7 mostra que isso é artefato da definição, não achado. Em nenhum dos casos correlação implica causalidade.

## 3.4 RQ 06 — Características associadas ao desempenho

![Tamanho de efeito por fator e métrica](../analise/saida/600/figuras/fig08_rq06_fatores.png)

**Como ler.** Cada célula cruza uma característica do repositório com uma métrica. O valor é o tamanho de efeito ε² = H/(n−1) do Kruskal-Wallis: quanto da variação da métrica aquela característica explica (< 0,01 desprezível, < 0,06 pequeno, < 0,14 médio, ≥ 0,14 grande). Em negrito, os que sobrevivem à correção de Holm sobre os 24 testes.

**A idade é o fator de maior efeito** (ε² = 0,21–0,25 no lead time, efeito grande): repositórios de até 2 anos têm lead time mediano de 2,0 dias contra 28,5 nos mais antigos, e publicam quase três vezes mais (0,67 contra 0,23 release/semana). Equipes maiores têm lead time maior (ε² 0,08–0,14). O **CFR (a) não se associa a nenhum fator**.

**A linguagem só fica significativa com 600 repositórios** — com 300 não sobrevivia a Holm. Lead time mediano: TypeScript 7,1 dias, JavaScript 8,9, Python 11,5, Rust 14,1, Go 16,7, Java 22,9, C 35,3, C++ 60,6. É um exemplo didático de **poder estatístico**: o efeito existia, mas 300 repositórios divididos em seis grupos não bastavam para detectá-lo após a correção.

**Controlando os fatores entre si**, a leitura muda. Idade, contribuidores e estrelas são correlacionados (ρ de 0,07 a 0,59; VIF entre 1,2 e 1,9, abaixo do corte de 5). Na correlação parcial de Spearman, a **idade resiste** (ρ parcial 0,34 no lead time, −0,39 na frequência, −0,34 no CFR (b), todas p < 0,001) e é o maior coeficiente padronizado da regressão log-log (0,52; IC 95% [0,38; 0,65]). Já **contribuidores perde** a associação com o lead time (ρ parcial 0,10, p = 0,17). **Estrelas** não tem associação parcial com nenhuma métrica. Parte do efeito de "equipes maiores" é, portanto, efeito da idade.

## 3.5 RQ 07 — Sensibilidade à definição operacional

Três combinações de definições operacionais: **C1** (release, lead time a, CFR a), **C2** (release + pré-release, b, b) e **C3** (tag, b, a).

| Par | Mudam de categoria (300 → 600) | κ ponderado (300 → 600) |
| :--- | :--- | :--- |
| C1 × C2 | 36% → 35% | 0,42 → 0,46 |
| C1 × C3 | 28% → 28% | 0,63 → 0,64 |
| C2 × C3 | 33% → 34% | 0,54 → 0,53 |

**Entre 28% e 36% dos repositórios mudam de categoria só por trocar a definição**, e a proporção não varia de 300 para 600 — não é ruído amostral. Em C2, cerca de 23% descem e 13% sobem, porque o CFR (b) é mais severo; em C3, 23% sobem e 5% descem, porque tags são mais frequentes que releases. A classificação DORA de um repositório **não é robusta à definição operacional**, o que exige cautela ao comparar estudos que usam proxies diferentes.

## 3.6 RQ 08 (bônus) — Evolução temporal

O enunciado sugere séries trimestrais com Mann-Kendall, mas com 4 pontos esse teste nunca alcança p < 0,05 — o menor p bilateral possível com n = 4 é 0,089, qualquer que seja a série. A análise usa a **série mensal** (12 pontos), com Mann-Kendall por repositório e métrica e correção de Benjamini-Hochberg sobre os 250 a 600 testes de cada métrica.

| Métrica | p bruto < 0,05 | Significativo após FDR | Dados insuficientes |
| :--- | :---: | :---: | :---: |
| Frequência | 16,8% | 0% | 0% |
| Lead time (a) | 16,7% | 0% | 50,2% |
| CFR (a) | 13,2% | 0,17% (1 repo) | 19,2% |
| Recuperação | 16,5% | 0% | 59,7% |

O teste bruto "encontra" tendência em 13% a 17% dos repositórios, acima dos 5% esperados por acaso. **Após o FDR, só 1 dos 600 sobrevive.** É o retrato de por que a correção de múltiplos testes importa: a aparência de um em cada seis repositórios mudando vira quase inteiramente ruído quando se testa centenas ao mesmo tempo. Não há melhora nem piora sistemática ao longo do ano; a conclusão defensável é metodológica.

## 3.7 Análises complementares (além do escopo pedido)

O estudo foi estendido a 900 repositórios em três amostras independentes, com análises de validade que o enunciado não pede. Seguem só as conclusões; o material completo está em `analise/saida/` e em `docs/base-teorica.md`.

**Reprodutibilidade.** A1 e A2 são estatisticamente indistinguíveis nas seis métricas (todos |δ| < 0,07, nenhum p significativo). De 300 a 900, todas as medianas caem dentro do IC de 300 e os intervalos estreitam de 21% a 51%.

**O CFR (b) mede cadência, não falha.** Quem publica mais tem mais oportunidade de ter uma release seguida por outra em 7 dias. Condicionando pela oportunidade, **a correlação com a frequência cai de 0,604 para −0,039** (p = 0,52). Confusão por tamanho foi testada e descartada (o ρ cai no máximo 0,059). É a mesma conclusão que a precisão de 36,5% da heurística já indicava, por via independente.

**As faixas quase não discriminam.** ε² de 0,008 (estrelas) e 0,022 (contribuidores), nenhum sobrevivendo a Holm; o que elas separam bem são as variáveis que as definem (CFR (b), ε² = 0,379, perto do controle tautológico de 0,403). Um índice contínuo por posto percentílico mostra que **as faixas retêm 63,2% da variância**, com 8,2% dos pares entre faixas invertidos.

**Por que mediana e IQR.** Nenhuma métrica passa em teste de normalidade e a média chega a 5,7× a mediana. A contagem de releases tem dispersão 493× a da Poisson. A recuperação segue Weibull com β mediano 0,557 e β < 1 em 87,8% dos repositórios — **taxa decrescente**, o que invalida o modelo exponencial. O Teorema do Limite Central só se aproxima perto de n = 300 nesta população.

**O DORA é uma lente entre outras.** Contra medidas de fluxo por pull request (CHAOSS, SPACE), nenhum par chega a ρ = 0,7, e **CFR (b) × aceitação de PR fica em 0,044** (não significativo). Trocando o proxy de falha, o mesmo conjunto aparece como 99% Elite (reverts), 84% (CI) ou 38% (release corretiva).

**Uma medida que não se reproduz.** A cobertura da API de Deployments varia entre as três amostras (31,3%, 41,7%, 43,3%; p = 0,0048) sem causa identificada — evidência negativa de confiabilidade, e contraste que dá credibilidade à positiva acima.
