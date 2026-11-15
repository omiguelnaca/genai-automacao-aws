# Evidências e origem

`historico/` contém cópias sem alteração das capturas fornecidas pelo autor, referentes à execução original. `validacao-local.json` contém resultados coletados novamente pela revisão em 15/11/2026: objetos com nomes únicos, registros DynamoDB, latência, tokens, amostras de Docker e IAM. Esses dois conjuntos não devem ser confundidos.

- `mcp-local.png` e `mcp-remoto.png`: descoberta de ferramentas dos servidores.
- `com-mcp.png` e `sem-mcp.png`: respostas históricas; comparar conteúdo e uso de fontes, sem inventar tempo de resposta ou avaliação quantitativa.
- `iam-leitura-escrita.png`: leitura permitida e tentativa de escrita negada.
- `iac-deploy.png` e `iac-recursos.png`: lint/deploy e recursos da stack original.
- `agente-sem-aprovacao.png` e `agente-aprovado.png`: mecanismo anterior, baseado em flag; não comprovam o novo ciclo de ferramentas.
- `git-publicacao.png`: publicação do commit original. Não comprova publicação das correções desta revisão.
- `agente-execucao.txt`: execução atual. Qualquer resposta `n` fornecida por automação é teste de recusa, não aprovação humana.

Os identificadores presentes são da conta local `000000000000`. Não incluir arquivos de credenciais na entrega.
