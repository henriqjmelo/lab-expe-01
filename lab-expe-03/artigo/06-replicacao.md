# 6. Replicação cruzada

> **Seção pendente da entrega final.** O professor sorteia, para cada grupo, o pipeline de outro grupo da turma. Esta seção só pode ser escrita depois do sorteio e da execução.

## 6.1 O que esta seção deve conter

Conforme a seção 9 do enunciado, o grupo **replicador** deve registrar aqui:

1. **Execução do pipeline do grupo sorteado usando apenas o README**, sobre uma subamostra de 30 repositórios do dataset original, sem pedir ajuda ao grupo autor. Travar é um resultado a registrar, não um fracasso a esconder.
2. **Comparação com o CSV original:** diferença relativa por métrica e percentual de repositórios com a mesma classificação DORA. Pequenas diferenças são esperadas, porque os repositórios continuam recebendo commits e as datas de coleta diferem.
3. **Issues abertas no repositório do grupo autor**, com evidências: comando executado, mensagem de erro, valores esperados e obtidos.
4. **Resposta:** o estudo foi reproduzível? O que impediu ou dificultou?

Responsáveis: execução pelo Henrique (#143), comparação e abertura de issues pelo Gabriel (#144).

## 6.2 O lado autor: o que já está pronto para quem for nos replicar

O grupo autor precisa responder às issues recebidas (#145). Independente do sorteio, os pontos abaixo determinam se este pipeline é replicável, e valem ser conferidos antes:

**Dados versionados, sem necessidade de recoleta.** Os três datasets, os eventos por repositório e as medidas GraphQL estão no Git. Quem replicar não precisa gastar cota de API nem as ~15 h de coleta: `data/DICIONARIO.md` documenta cada coluna de cada arquivo.

**O cache não vai para o Git.** O diretório `.cache/` tem vários GB e existe apenas na máquina de quem coletou. Isso significa que **a recoleta a partir do zero não é bit a bit reprodutível** — ela depende do estado corrente da API. Reexecutar sobre os dados versionados é; recoletar não é. É a limitação mais provável de aparecer na replicação, e está declarada.

**Comando único.** `python -m pipeline --config config.yaml` para a coleta e `python -m analise` para figuras e tabelas, com as dependências fixadas em `requirements.txt` e `requirements-analise.txt`.

**Pontos frágeis conhecidos**, que provavelmente gerarão issues:

| Ponto | Por quê |
| :--- | :--- |
| Token do GitHub | o pipeline exige `GITHUB_TOKEN` no ambiente; sem ele, falha de imediato |
| Cota de API | uma recoleta completa consome a cota de 5.000 chamadas/hora por horas seguidas |
| Datas de coleta diferentes | repositórios recebem commits novos; as métricas mudam entre execuções |
| API de Deployments | cobertura instável entre amostras (seção 3.10.8), o que pode produzir divergência legítima |

## 6.3 Link do repositório e do Projects

- Repositório: `https://github.com/henriqjmelo/lab-expe-01`
- GitHub Projects: https://github.com/users/henriqjmelo/projects/2
