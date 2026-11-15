# Etapa 2 — Diário de prompts e revisão crítica

Este diário foi reconstruído retrospectivamente em 15/11/2026 a partir das capturas fornecidas e do repositório. O arquivo original estava vazio. Trechos resumidos abaixo são paráfrases, não transcrições integrais nem histórico recuperado do chat.

| Objetivo/prompt registrado | Resposta/artefato observado | Erro ou limite | Correção/verificação |
|---|---|---|---|
| Explicar conceitos AWS com e sem MCP | Duas respostas nas capturas com-mcp e sem-mcp | Uma resposta sem ferramenta não prova consulta à fonte; não há benchmark de qualidade | Comparar presença de consulta e referências; conferir conceitos na documentação |
| Criar scripts/inventario.py para listar S3, DynamoDB e IAM | Script boto3 com verificação da conta local | Executar com perfil errado poderia consultar outro ambiente | Guarda da conta 000000000000 e perfil floci |
| Usar awsDocs para criar política de leitura do bucket relatorios | ListBucket no bucket e GetObject em seus objetos | O primeiro teste retornou 404 porque o bucket/objeto não existia | Recriação do recurso pelo administrador; leitura posterior passou e PutObject foi negado |
| Criar template seguindo etapa-03-especificacao, sem SSH | iac/vpc.yaml e cfn-lint | Na revisão, faltava iniciar servidor HTTP | UserData acrescido; implantação local atualizada; ver etapa-03-revisao |
| Criar Lambda que leia S3, invoque converse e grave triagem | lambda/app.py, resumo, urgência e tokens | Cenário chamado media foi classificado alta | Texto de teste foi tornado inequívoco; nova consulta mostrou media; isso não demonstra melhoria geral do modelo |
| Configurar SNS/SQS | Política da fila e inscrição | ConvertTo-Json serializou metadados PowerShell e arquivo inválido | Correção com JSON nativo e Policy string; teste via boto3 |
| Criar agente com aprovação | Agente anterior propôs escala e depois alterou capacidade com flag | Sequência fixa e JSON inválido em uma execução | Novo ciclo real tool use, limite de seis iterações, validação e confirmação da ação concreta |
| Finalizar documentação sem inventar resultados | README e análise | Diário vazio e roteiro ainda dizia que ASG estava pendente | Esta reconstrução, evidências originais separadas das novas e roteiro corrigido |

## Comparação com/sem MCP

Ver [com MCP](evidencias/historico/com-mcp.png), [sem MCP](evidencias/historico/sem-mcp.png), [servidor local](evidencias/historico/mcp-local.png) e [remoto](evidencias/historico/mcp-remoto.png). As capturas documentam as respostas e a conexão. Não bastam para garantir que modelo, contexto e parâmetros foram idênticos. Portanto a comparação histórica é qualitativa, não um experimento controlado.

Para repetir de forma controlada: abrir dois chats vazios no mesmo modelo; enviar exatamente “Compare Security Group e NACL na AWS: estado, associação, regras e exemplo”; em um desabilitar ferramentas, no outro habilitar somente awsDocs; registrar nome do modelo, prompt integral, fontes, resposta e erros factuais. Não atribuir ao MCP a correção de uma resposta sem conferir as fontes.

## Aprendizado

A IA auxiliou na escrita de código e consulta de documentação, mas não substituiu testes. Nome de arquivo não determina urgência. Lint valida estrutura, não comprova HTTP funcionando. Uma política aparentemente correta precisa ser exercitada com a identidade restrita. A revisão corrigiu problemas efetivos e registra também as limitações remanescentes.

## Experimento controlado adicional — 15/11/2026

Executado por `scripts/comparar_mcp.py`: duas chamadas independentes a llama3.2, mesmo prompt, temperature=0 e maxTokens=400. A diferença foi acrescentar ao contexto o retorno real de aws___search_documentation do AWS Knowledge MCP. Não é um teste do Copilot: é uma comparação de geração com contexto recuperado por MCP. Respostas integrais, parâmetros e retorno da ferramenta estão em [comparacao-mcp.json](evidencias/comparacao-mcp.json).

| Critério | Sem MCP | Com contexto MCP |
|---|---|---|
| Estado da conexão | Não explicou stateful/stateless | Confundiu estado com permanente/temporário |
| Associação NACL | Disse rede virtual, impreciso | Identificou sub-rede |
| Regras SG | Exemplo sugere bloqueio explícito, incorreto | Também incluiu Bloquear, incorreto |
| Fontes | Gerou URLs sem contexto de fonte | Citou uma URL realmente recuperada |
| Latência observada | 32,459 s | 28,037 s |

Conclusão: nesta amostra, MCP melhorou a rastreabilidade de fonte e a associação da NACL, mas **não garantiu correção**. Ambas as respostas precisam de revisão. SG é stateful e permite regras Allow; NACL é stateless, atua na sub-rede e admite Allow/Deny. O próprio trecho recuperado da [FAQ oficial VPC](https://aws.amazon.com/vpc/faqs/) informa essa distinção. “Permanente/temporário” não responde ao estado das conexões. Uma amostra por condição não permite concluir melhora geral nem vantagem de latência; houve outras atividades locais durante a execução.
