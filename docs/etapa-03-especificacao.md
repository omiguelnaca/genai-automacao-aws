# Especificação da infraestrutura

1. Criar uma VPC com CIDR `10.0.0.0/16`.
2. Criar uma sub-rede pública `10.0.1.0/24` e uma privada `10.0.2.0/24`.
3. A sub-rede pública deve ter rota para Internet Gateway.
4. Criar Security Group permitindo somente HTTP TCP na porta 80 de `0.0.0.0/0`.
5. Não liberar SSH ou outras portas de entrada.
6. Criar uma instância EC2 `t3.micro` na sub-rede pública.
7. A AMI deve ser recebida por parâmetro, sem ID fixo no template.
8. Criar o bucket S3 `relatorios-campo` e a tabela DynamoDB `triagem`, com chave `arquivo` do tipo String.
9. Aplicar a tag `Project: GenAI-Automacao` aos recursos compatíveis.
10. Expor Outputs com VpcId, IP público, nome do bucket e ARN da tabela.