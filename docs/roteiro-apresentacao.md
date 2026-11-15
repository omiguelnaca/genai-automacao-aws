# Roteiro de apresentação - até 10 minutos

## 0:00–0:50 — Problema e objetivo

Apresentar a necessidade de resumir relatórios agrícolas e indicar urgência. Explicar que o projeto demonstra essa automação em ambiente local, sem credenciais no código nem deploy em AWS real.

## 0:50–1:50 — Arquitetura e ambiente

Mostrar o fluxo S3 `relatorios-campo` → Lambda `triagem` → Bedrock Runtime no Floci, com inferência pelo Ollama → DynamoDB `triagem`. Explicar que o evento `ObjectCreated` inicia o processamento e que a função usa `TABELA=triagem`.

## 1:50–2:40 — MCP e documentação

Mostrar a configuração `.mcp.json`: `awsDocs` local via `stdio` e `awsKnowledge` via HTTP. Explicar que consultar documentação oficial ajuda a validar conceitos e propriedades, mas o MCP não é um serviço emulado pelo Floci.

## 2:40–3:40 — IAM e menor privilégio

Resumir a role `triagem-lambda`: confiança exclusiva para `lambda.amazonaws.com`, leitura S3 restrita, gravação na tabela, invocação do modelo necessário e logs. Reforçar que não há acesso administrativo nem credenciais versionadas.

## 3:40–4:35 — IaC

Apresentar `iac/vpc.yaml`: VPC com sub-redes pública e privada, rota pública, Security Group com HTTP e sem SSH, instância EC2, bucket e tabela. Esclarecer que a validação do template não equivale a deploy.

## 4:35–6:10 — Demonstração da triagem

Mostrar os relatórios `relatorio-baixa.txt`, `relatorio-media.txt` e `relatorio-alta.txt`. Apresentar a evidência de que os uploads acionaram a Lambda e os itens chegaram à DynamoDB com urgências `baixa`, `media` e `alta`. Explicar o fallback `urgencia=media` e `revisao_humana=true` para saída inválida.

## 6:10–7:15 — Alertas

Mostrar as evidências da métrica `TamanhoFilaRelatorios` com valor `25`, do alarme `fila-triagem-acima-limite` com limite `10` em estado `ALARM` e da mensagem `Threshold Crossed` recebida na SQS por meio da inscrição SNS.

## 7:15–8:10 — Agente e aprovação

Explicar que o agente consulta métrica, ASG, atividades e contagem da fila e solicita ao modelo uma decisão em JSON. Só executa escala com a decisão `escalar` e a opção explícita `--aprovar-escalonamento`. Informar que o ASG ainda está pendente de criação/validação local.

## 8:10–9:15 — Segurança, custos e LGPD

Destacar menor privilégio, ausência de credenciais no código, dados de teste sem informação pessoal, controle de retenção e limites de tokens. Comentar que recursos AWS reais podem gerar custos e que a execução local também consome recursos da máquina.

## 9:15–10:00 — Limitações e conclusão

Concluir que o Floci/Ollama facilita testes locais, mas não reproduz integralmente a AWS real. Agradecer e lembrar que Docker e a stack `lab-ia` só devem ser encerrados/removidos depois da avaliação, pois a Etapa 4 depende deles durante os testes.
