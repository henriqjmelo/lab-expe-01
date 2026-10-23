# 6. Replicação cruzada

> **Seção pendente da entrega final.** O professor sorteia, para cada grupo, o pipeline de outro grupo da turma. Esta seção só pode ser escrita depois do sorteio e da execução.

## 6.1 O que esta seção deve conter

Conforme a seção 9 do enunciado, o grupo **replicador** deve registrar aqui:

1. **Execução do pipeline do grupo sorteado usando apenas o README**, sobre uma subamostra de 30 repositórios do dataset original, sem pedir ajuda ao grupo autor. Travar é um resultado a registrar, não um fracasso a esconder.
2. **Comparação com o CSV original:** diferença relativa por métrica e percentual de repositórios com a mesma classificação DORA. Pequenas diferenças são esperadas, porque os repositórios continuam recebendo commits e as datas de coleta diferem.
3. **Issues abertas no repositório do grupo autor**, com evidências: comando executado, mensagem de erro, valores esperados e obtidos.
4. **Resposta:** o estudo foi reproduzível? O que impediu ou dificultou?

Responsáveis: execução pelo Henrique (#143), comparação e abertura de issues pelo Gabriel (#144).

## 6.2 O lado autor: o que está pronto para quem nos replicar

Os três datasets, os eventos por repositório e as medidas auxiliares estão versionados no Git, com cada coluna descrita em `data/DICIONARIO.md`: quem replicar **não precisa gastar cota de API nem as ~15 h de coleta**. A execução é por comando único (`python -m pipeline` e `python -m analise`), com dependências fixadas.

O cache da coleta (vários GB) **não** vai para o Git, então reexecutar sobre os dados versionados é reprodutível, mas **recoletar do zero não é** — depende do estado corrente da API. É a limitação mais provável de aparecer na replicação, e está declarada. Os demais pontos frágeis conhecidos são a exigência de `GITHUB_TOKEN`, o consumo de cota numa recoleta completa, a mudança natural das métricas entre datas de coleta e a cobertura instável da API de Deployments (seção 3.7).

## 6.3 Link do repositório e do Projects

- Repositório: `https://github.com/henriqjmelo/lab-expe-01`
- GitHub Projects: https://github.com/users/henriqjmelo/projects/2
