# Etapa 5 - Escalabilidade e alertas

## Objetivo

Especificar uma automação local para acompanhar a fila de relatórios agrícolas, alertar sobre aumento de demanda e propor ajustes de capacidade.

## Componentes e fluxo

- Um Auto Scaling Group chamado `triagem-asg`, com capacidade mínima 1, desejada 1 e máxima 4 instâncias.
- Uma métrica simulada do CloudWatch representa o tamanho da fila. Um alarme é acionado quando a métrica ultrapassa o limite configurado.
- Ao alarmar, o CloudWatch publica uma notificação em um tópico SNS. O tópico entrega o alerta a uma fila SQS.
- Um agente Python consulta as métricas, descreve o ASG, lista suas atividades recentes e propõe uma ação de escala com justificativa.

## Aprovação humana

O agente apenas recomenda a ação. Executar qualquer alteração de capacidade exige confirmação humana explícita; sem aprovação, nenhuma ação de escala é realizada.

## Requisitos do ambiente

Usar o perfil e as configurações locais do Floci. Não incluir credenciais nem `endpoint_url` fixos no código. A emulação do Floci pode ter limitações; implementar e testar os componentes localmente, sem pressupor comportamento idêntico ao da AWS real.

## Critérios de evidência

Registrar evidências locais de:

1. Criação do ASG, configuração de métrica e alarme, tópico SNS e fila SQS.
2. Envio de uma métrica simulada de tamanho da fila acima do limite.
3. Acionamento do alarme e recebimento da mensagem de alerta na fila SQS.
4. Execução do agente, consulta dos dados e simulação de uma decisão, mostrando que a escala só ocorre após aprovação humana explícita.
