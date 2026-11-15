# Revisão crítica da infraestrutura e da entrega

Revisão realizada em 15/11/2026 sobre o commit original `4a64aa6`. Os achados abaixo são desta revisão; não são apresentados como três erros encontrados na geração original.

| Achado verificável | Consequência | Correção |
|---|---|---|
| EC2 sem UserData de instalação de servidor | Abrir a porta 80 não cria uma aplicação HTTP | UserData instala e inicia httpd; AMI real deve ser Amazon Linux 2023 compatível com dnf |
| README pressupunha Lambda, ASG, notificações e perfis previamente criados | Clone novo não reproduzia a demonstração | scripts/preparar.ps1 e scripts/provisionar.py automatizam recursos auxiliares |
| Dois JSONs SQS continham objeto PowerShell com PSPath em vez de Policy string | AWS CLI rejeitava os parâmetros | JSON nativo e política serializada como string; provisionador usa boto3 |
| Agente executava consultas em ordem fixa e sem identidade restrita própria | Não demonstrava ciclo de escolha de ferramentas nem isolamento IAM | toolConfig/toolUse/toolResult, identidade triagem-agente e política limitada ao ASG |
| Repetição da atualização de UserData falhou com EC2 running no Floci | UPDATE_ROLLBACK_COMPLETE | Parar, aguardar, atualizar e reiniciar a EC2 simulada |

O `cfn-lint iac/vpc.yaml` passou na revisão. A atualização da stack local terminou em UPDATE_COMPLETE. As capturas históricas de criação estão em [evidências](evidencias/historico/iac-recursos.png). O AMI fictício do script serve exclusivamente ao emulador; não é uma imagem AWS implantável.

O template declara a infraestrutura básica. Os recursos de aplicação e operação são provisionados por Python, e não são indevidamente apresentados como recursos controlados pela stack. Essa separação exige executar o provisionador para reproduzir a solução completa.

Não foi comprovado nesta revisão que o UserData roda como numa EC2 real. Validar HTTP e AMI na AWS seria um teste separado, com custos e autorização próprios. A instância e os dados de laboratório foram preservados para a apresentação.

## Persistência

A revisão encontrou perda de recursos/credenciais após recriar o contêiner. Um volume montado, sozinho, não garante que todos os serviços o usem. O Compose corrigido define explicitamente FLOCI_STORAGE_MODE=persistent e FLOCI_STORAGE_PERSISTENT_PATH=/app/data. O provisionador também detecta perfil restrito cuja chave local deixou de existir. Preserve a pasta data e execute novamente o provisionador após qualquer reinicialização que perca recursos; não trate o armazenamento do emulador como garantia de durabilidade da AWS.
