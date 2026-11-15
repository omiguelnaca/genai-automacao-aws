# Etapa 5 — Agente e alertas

Objetivo: diagnosticar CPU alta e propor aumento controlado de capacidade, usando APIs AWS locais e decisão de ferramentas pelo modelo.

1. ASG triagem-asg com limites 1 a 4. A capacidade existente é preservada ao repetir o provisionamento.
2. Métrica CPUUtilization no namespace AWS/EC2 e dimensão AutoScalingGroupName=triagem-asg. Valores simulados; não são telemetria real da aplicação.
3. Alarme cpu-triagem-alta: média em períodos de 60 s, três de três acima de 80%, ausência não violando; ação SNS para SQS alertas-triagem.
4. Agente chama converse com toolConfig. O modelo seleciona ler_metricas, descrever_asg, listar_atividades e ajustar_capacidade; resultados retornam por toolResult. Limite de seis rodadas e oito ferramentas por resposta.
5. Ajuste só fica autorizado após os resultados das três leituras em rodada anterior. Verificação determinística exige três pontos recentes e consecutivos, alvo atual+1, limite do grupo, justificativa e confirmação s/N da ação concreta. Condições são consultadas novamente após aprovação.
6. Uma escrita por execução. Negativa, dados ausentes/antigos, pico isolado ou falha na auditoria impedem a alteração.
7. Identidade IAM exclusiva triagem-agente. Escrita de capacidade restrita ao ARN obtido do ASG. Logs registram solicitação, resultado, aprovação e escrita. Credenciais ficam no perfil local.
8. A entrada do agente é manual. SNS/SQS demonstra a entrega do alerta; não existe um processo consumindo a fila e iniciando automaticamente o agente.

Amostras publicadas no mesmo minuto são agregadas: aguarde uma janela nova antes de comparar pico com carga sustentada. Um pico isolado é testado de forma determinística no teste unitário, sem interferência de pontos antigos.
