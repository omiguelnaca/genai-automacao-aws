# Etapa 6 - Análise do projeto

## Custos

No Floci/Ollama, as chamadas de inferência de teste são processadas localmente, mas consomem CPU, memória e energia da máquina. Em AWS real, Lambda, S3, DynamoDB sob demanda, Bedrock, CloudWatch, SNS e SQS podem gerar custos conforme o uso. Um ASG também pode manter instâncias ativas; o mínimo configurado deve ser considerado antes de qualquer implantação.

Limitar tokens e o tamanho dos dados enviados ao modelo reduz tempo de processamento e custo de inferência. A Lambda define um limite de saída; os alarmes e logs devem ser suficientes para diagnóstico, evitando retenção excessiva, chamadas repetidas e alarmes ruidosos.

## Segurança

As permissões devem seguir menor privilégio. A política `leitura-relatorios.json` restringe `s3:ListBucket` ao bucket `relatorios` e `s3:GetObject` aos objetos desse bucket. Separadamente, a role `triagem-lambda` confia somente no serviço Lambda e restringe a leitura aos objetos de `relatorios-campo`, a gravação à tabela `triagem`, a invocação ao modelo definido e a escrita aos logs necessários. Não são necessárias permissões administrativas nem credenciais embutidas no código; o acesso local usa o perfil configurado para Floci.

## LGPD e dados

Os relatórios usados nos testes devem permanecer sem dados pessoais. Antes de processar dados reais, é necessário avaliar a finalidade, minimizar os campos enviados ao modelo e remover ou mascarar identificadores que não sejam necessários. Também devem ser definidos prazos de retenção para objetos, itens da tabela e logs, com acesso restrito e auditável.

## Sustentabilidade

O modelo local Ollama permite testar prompts sem depender de chamadas de inferência na nuvem, embora ainda use recursos do computador. Evitar invocações desnecessárias, controlar tokens e desligar serviços ociosos reduz consumo. Após a avaliação, encerrar os contêineres com `docker compose down`.

## Riscos e limitações

Floci é um emulador: não reproduz integralmente o comportamento, a disponibilidade, as permissões e os custos da AWS real. Resultados locais de Bedrock Runtime/Ollama, CloudWatch, SNS, SQS e Auto Scaling precisam ser revalidados antes de qualquer uso real. O modelo pode produzir respostas inválidas; por isso, a Lambda usa fallback e o agente exige aprovação humana para escalar.

## Encerramento

Manter a stack `lab-ia` enquanto a Etapa 4 ainda depender dela durante os testes. Somente depois da avaliação, encerrar o Docker Compose e excluir a stack de laboratório, confirmando antes que nenhuma demonstração ou validação ainda dependa desses recursos.
