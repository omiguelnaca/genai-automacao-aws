# Etapa 5 - Evidências de testes

## Auto Scaling

- A Launch Configuration `triagem-launch-v1` foi criada.
- O Auto Scaling Group `triagem-asg` foi criado com mínimo `1`, capacidade desejada inicial `1` e máximo `4`.

## Métrica, alarme e notificação

- Foi publicada a métrica `TamanhoFilaRelatorios`, no namespace `GenAIAutomacao`, com valor `25`; o limite do alarme era `10`.
- O alarme `fila-triagem-acima-limite` entrou no estado `ALARM`.
- O tópico SNS `alertas-triagem` entregou o alerta à fila SQS `alertas-triagem`. A política da fila permite `sqs:SendMessage` somente ao serviço `sns.amazonaws.com` e quando `aws:SourceArn` corresponde ao ARN desse tópico.
- A mensagem recebida na fila continha `Threshold Crossed`.

## Agente e aprovação humana

- Sem `--aprovar-escalonamento`, o agente recomendou aumentar a capacidade de `1` para `2`, mas não alterou o ASG.
- Com `--aprovar-escalonamento`, o agente efetuou a alteração; a capacidade desejada foi confirmada como `2`.
- A execução de `set_desired_capacity` depende de uma decisão `escalar` e da aprovação explícita pela opção de linha de comando.

## Ambiente

Os testes foram realizados localmente no Floci. A emulação pode diferir do comportamento da AWS real; os resultados não representam um deploy em AWS.
