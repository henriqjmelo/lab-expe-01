# Protocolo da amostra-ouro

Os três avaliadores classificam independentemente os mesmos 60 repositórios e até cinco releases por repositório, sem consultar os rótulos dos demais nem a saída das heurísticas. As categorias aceitas estão definidas em `ENUNCIADO.md` e no módulo `analise/concordancia.py`.

Depois do cálculo do kappa de Fleiss, o consenso segue estas regras:

1. Dois ou três votos iguais definem o rótulo por maioria simples.
2. Se os três rótulos forem diferentes em uma dimensão tricotômica (`tipo_projeto` ou `releases_reais`), o caso fica pendente até discussão conjunta. A decisão final e sua justificativa são registradas em `decisoes_consenso_repos.csv`, com as colunas `full_name,dimensao,rotulo,justificativa`; `dimensao` identifica a coluna decidida.
3. Todo rótulo de decisão manual deve pertencer ao conjunto de categorias permitido. Não se substitui um rótulo ausente por decisão automática.
4. Os arquivos de decisão são dados do consenso do grupo e devem ser versionados junto com os rótulos individuais.

O script `python -m analise.concordancia` valida os arquivos, calcula um kappa por dimensão e produz os consensos. Ele interrompe a execução quando algum avaliador ainda tem rótulos vazios ou inválidos; não se calcula concordância com dados incompletos. Uma decisão 1–1–1 sem registro continua marcada como pendente no CSV de consenso.