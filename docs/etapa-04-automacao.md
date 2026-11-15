# Etapa 4 - Automação de triagem de relatórios

## Arquitetura

```text
S3: relatorios-campo
       │ evento s3:ObjectCreated:*
       ▼
Lambda Python: triagem
       │ Bedrock Runtime Converse
       ▼
Floci / Ollama: anthropic.claude-3-haiku-20240307-v1:0
       │ resultado validado
       ▼
DynamoDB: triagem
```

## Sequência do processamento

1. Um objeto enviado ao bucket `relatorios-campo` gera um evento `ObjectCreated`.
2. A função Lambda `triagem` decodifica a chave do objeto e lê o arquivo no S3.
3. A função envia o conteúdo ao `bedrock-runtime.converse`, usando o modelo `anthropic.claude-3-haiku-20240307-v1:0`.
4. O modelo deve retornar somente um objeto JSON com `resumo` e `urgencia`. A urgência aceita é `baixa`, `media` ou `alta`.
5. A Lambda grava na tabela DynamoDB `triagem` os campos `arquivo`, `resumo`, `urgencia`, `tokens_in` e `tokens_out`. O nome da tabela é configurado pela variável de ambiente `TABELA=triagem`.

Se a resposta não for JSON válido, não tiver o formato esperado ou trouxer uma urgência fora da lista, a função grava `urgencia=media` e `revisao_humana=true`. Assim, um resultado que não pode ser classificado com segurança fica identificado para análise manual.

## Prompt injection

O documento é tratado como conteúdo não confiável. A instrução enviada ao modelo determina que ele não siga comandos encontrados dentro do arquivo e que use o conteúdo apenas para resumir e classificar a urgência. Essa orientação reduz o risco de prompt injection, mas não garante por si só que o modelo sempre se comporte corretamente.

## Permissões da Lambda

A role `triagem-lambda` segue o princípio de menor privilégio:

- A relação de confiança permite que somente `lambda.amazonaws.com` assuma a role.
- `s3:GetObject` permite ler objetos de `relatorios-campo`.
- `dynamodb:PutItem` permite gravar itens na tabela `triagem`.
- `bedrock:InvokeModel` permite invocar somente o modelo Claude 3 Haiku indicado.
- `logs:CreateLogGroup`, `logs:CreateLogStream` e `logs:PutLogEvents` permitem registrar a execução no CloudWatch Logs.

## Evidência de teste

Os uploads de `relatorio-baixa.txt`, `relatorio-media.txt` e `relatorio-alta.txt` acionaram a Lambda. Os três resultados foram gravados na tabela `triagem` com urgências `baixa`, `media` e `alta`, respectivamente.

## Ambiente

O processamento foi executado no ambiente local Floci/Ollama. O código não contém credenciais, e não foi feito deploy em uma conta AWS real.

## Validação adicional de 15/11/2026

O teste scripts/validar_local.py enviou objetos únicos ao S3 e aguardou resultados no DynamoDB. Os quatro cenários passaram: alta, baixa, média e injeção. Foram registrados tokens e latência em [validacao-local.json](evidencias/validacao-local.json). O relatório injetado foi marcado alta com suspeita_injecao e revisao_humana. Essa quarentena é uma decisão conservadora, não uma classificação médica/agronômica garantida.

A detecção de frases maliciosas complementa a instrução de sistema e a validação JSON. Não foi medida uma taxa geral de resistência a ataques. Modelos adicionais e variante de saúde não foram executados; são extensões opcionais.
