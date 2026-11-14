# Os 3 critérios do software: OpenJDK 25

O enunciado (seção 2a) pede que o software seja **real**, **em operação** e de **alto impacto**, cada um com número e fonte. O objeto de pesquisa deste estudo é a **JVM do OpenJDK 25 em execução, com os coletores de lixo G1 e ZGC**. Não é o repositório do OpenJDK no GitHub.

**Data de acesso de todas as fontes: 13/11/2026.**

Legenda da coluna *Verificação*:
- **lido** = a página foi aberta e o número conferido nesta data;
- **imprensa** = o número vem de cobertura da imprensa sobre o relatório e **deve ser conferido no relatório original** antes de citar;
- **conferir** = não foi possível abrir a fonte (bloqueio de acesso automatizado); confirmar manualmente.

## 1. Real

| Afirmação | Evidência | URL | Verificação |
| :--- | :--- | :--- | :--- |
| O OpenJDK é o projeto de referência do Java SE, com site, builds e documentação oficiais | Site do OpenJDK e página de builds do JDK 25 | <https://jdk.java.net/25/> e <https://openjdk.org/projects/jdk/25/> | conferir (acesso automatizado retornou HTTP 403) |
| O código do OpenJDK é open source (GPLv2 com Classpath Exception) | "OpenJDK code is under GPLv2 with Classpath Exception" | <https://adoptium.net/about/> | lido |
| Existe uma distribuição binária mantida e gratuita do OpenJDK: **Eclipse Temurin**, do projeto Eclipse Adoptium | Imagem oficial `eclipse-temurin` no Docker Hub, "Maintained by: Adoptium" | <https://hub.docker.com/_/eclipse-temurin> | lido |

A imagem usada no estudo será a oficial do Eclipse Temurin JDK 25, com tag e digest fixados na issue S01-B1.

## 2. Em operação

| Afirmação | Número ou fato | URL | Verificação |
| :--- | :--- | :--- | :--- |
| O JDK 25 é a **LTS mais recente** | API da Adoptium: `available_lts_releases` = 8, 11, 17, 21, 25 e `most_recent_lts` = 25 | <https://api.adoptium.net/v3/info/available_releases> | lido |
| O JDK 25 é uma versão **mantida hoje**, com release recente | Último build Temurin 25: **`jdk-25.0.5+8`**, atualizado em **22/10/2026** | <https://api.adoptium.net/v3/assets/latest/25/hotspot?os=linux&architecture=x64&image_type=jdk> | lido |
| Existem versões **não LTS mais novas** que o JDK 25 | `most_recent_feature_release` = 27 e `tip_version` = 28 (JDK 26 e 27 já existem) | mesma API de `available_releases` | lido |
| O JDK 25 foi lançado em setembro de 2025 | Data de disponibilidade geral (GA) | <https://openjdk.org/projects/jdk/25/> | conferir |
| O ZGC está em uso em produção em escala | Netflix migrou de G1 para o ZGC geracional a partir do JDK 21 (relato do próprio Netflix, republicado em 06/03/2024) | <https://inside.java/2024/03/06/generational-zgc-netflix> | imprensa (resultados da busca; abrir o post antes de citar números) |
| Há adoção de versões recentes em produção | JetBrains, 2025: versões Java usadas regularmente: **21 = 40 %, 17 = 39 %, 8 = 31 %, 11 = 17 %, 24 = 14 %** (múltipla escolha) | <https://lp.jetbrains.com/the-state-of-java-2025> | lido |

### Por que o JDK 25 e o par G1 × ZGC

- O JDK 25 é a **LTS atual**: é a versão que organizações tendem a adotar para produção e a que vai receber atualizações por mais tempo.
- G1 é o coletor **padrão** da JVM; o ZGC é a principal alternativa de baixa pausa, e no JDK 25 só existe no modo geracional (JEP 490, a conferir em <https://openjdk.org/jeps/490>).
- Comparar os dois responde a uma decisão real de operador: manter o padrão ou trocar por uma alternativa de menor latência de cauda.

## 3. Alto impacto

Cada fonte mede uma coisa diferente. **Não somar nem comparar os percentuais entre fontes.**

| Fonte | Quem publica (e interesse comercial) | Número | O que mede | URL | Verificação |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Stack Overflow Developer Survey 2025 | Stack Overflow (comunidade de perguntas e respostas) | Java usado por **29,4 %** de todos os respondentes e **29,6 %** dos desenvolvedores profissionais (31.771 respostas na pergunta geral; 24.759 de profissionais) | desenvolvedores que usaram a linguagem no último ano | <https://survey.stackoverflow.co/2025/technology/> | lido |
| TIOBE Index, novembro de 2026 | TIOBE (empresa de qualidade de software; o índice conta resultados de buscas) | Java em **3º lugar, 8,89 %** (C++ em 4º, 8,35 %; Python em 1º, 20,86 %) | popularidade medida por buscas, não uso real | <https://www.tiobe.com/tiobe-index/> | lido |
| JetBrains State of Developer Ecosystem 2025 | JetBrains (vende IDEs, incluindo para Java) | Java como **linguagem principal de 33 %** dos respondentes; versões em uso regular: ver seção 2 | desenvolvedores que respondem à pesquisa da empresa | <https://devecosystem-2025.jetbrains.com/> e <https://lp.jetbrains.com/the-state-of-java-2025> | versões: lido; 33 %: imprensa |
| Azul State of Java 2026 | Azul (fornece JVM comercial) | **62 %** das organizações usam Java para funcionalidades de IA; **81 %** estão migrando parte do Oracle Java para distribuições OpenJDK; **97 %** tomaram ações para reduzir o custo de nuvem, e 41 % citam uma plataforma Java de alto desempenho entre as 5 principais (2.039 respondentes, coleta entre set. e nov. de 2025) | organizações **que já usam Java** (a amostra é só de usuários de Java) | press release de 10/02/2026, via <https://secure.businesswire.com/news/home/20260210972138/en/> | imprensa |
| New Relic State of the Java Ecosystem 2024 | New Relic (observabilidade; mede só clientes dela) | Java 17 em mais de **35 %** das aplicações monitoradas (era 9,1 % em 2023); Java 21 em 1,4 % nos 6 primeiros meses | aplicações Java **monitoradas pela New Relic** | <https://newrelic.com/resources/report/2024-state-of-the-java-ecosystem> | imprensa (edição mais recente que consegui localizar: 2024) |
| Docker Hub, imagem `eclipse-temurin` | Docker, Inc. (contagem de pulls) | **100M+ pulls** de uma única imagem de JDK | downloads da imagem, não instalações | <https://hub.docker.com/_/eclipse-temurin> | lido |

### Como ler esses números

- **Stack Overflow e JetBrains** medem **desenvolvedores** que respondem a uma pesquisa (viés de autosseleção).
- **TIOBE** mede **buscas**, não uso.
- **Azul e New Relic** são **fornecedores** com interesse comercial no resultado, e suas amostras já são de usuários de Java ou de clientes da empresa. Servem como indício de adoção entre quem usa Java, não como fatia do mercado.
- **Docker Hub** mede **downloads**, não instalações em produção.

Em conjunto: Java está entre as 3 linguagens mais populares em 2026 (TIOBE) e é usada por cerca de 3 em cada 10 desenvolvedores (Stack Overflow). Isso sustenta "alto impacto" por **número de usuários**, e a análise de impacto na S03 usa preços públicos de nuvem para traduzir o resultado em custo.

## 4. O que não foi encontrado

- Nenhuma fonte pública que informe a **fatia de aplicações em produção que usam G1 ou ZGC**. Qualquer percentual desse tipo seria estimativa.
- **Número de instalações ou de instâncias de JVM** em produção.
- **Volume de requisições ou de CPU-horas** gastas em JVMs (a análise de impacto trata o tamanho da frota como hipótese rotulada).
- Uma edição **2025 ou 2026** do relatório da New Relic (só foi localizada a de 2024).

## 5. Por que o objeto é a JVM em execução e não o repositório

O estudo executa o **OpenJDK 25 já compilado** (imagem oficial do Eclipse Temurin) dentro de um contêiner e mede o comportamento da JVM com dois coletores de lixo, rodando uma suíte de benchmarks. Nenhum commit, issue, pull request ou código-fonte do repositório do OpenJDK é minerado ou analisado. O repositório é só de onde a distribuição binária se origina. Isso é o que o FAQ do enunciado aceita: rodar no ambiente do grupo um software open source usado em produção.

## 6. Alvo móvel

Existem JDKs mais novos (26, 27) e haverá novas atualizações do 25. **O estudo congela o JDK 25** (LTS) com tag e digest fixados na S01-B1 e **não atualiza durante a coleta**. Se sair um `25.0.x` novo no meio, ele não entra. A ameaça é discutida em `06-ameacas-validade.md`.

## 7. Pendências de conferência

1. Abrir <https://jdk.java.net/25/> e <https://openjdk.org/projects/jdk/25/> no navegador (o acesso automatizado foi bloqueado) e confirmar a data de GA do JDK 25.
2. Conferir a JEP 490 em <https://openjdk.org/jeps/490>.
3. Abrir o relatório original da Azul e o da New Relic antes de citar os números de **imprensa**.
4. Abrir o post do Netflix antes de citar qualquer número de pausa.
5. Na entrega final, **reconferir** o último `25.0.x`, a posição no TIOBE e os números do Docker Hub, que mudam.

## 8. Pergunta que o professor pode fazer

**"Vocês estudam a JVM, não o repositório. Que evidência mostra que isso é software em operação?"**
O JDK 25 é a LTS mais recente segundo a Adoptium, com build de 22/10/2026; a imagem oficial passa de 100 milhões de pulls; há relato de operação em escala do ZGC (Netflix); e levantamentos de 2025 mostram Java 17 e 21 em uso regular por cerca de 40 % dos respondentes da JetBrains. O objeto é o software rodando, e é isso que o estudo mede.
