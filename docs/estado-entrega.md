# Estado da entrega — revisão de 15/11/2026

## Corrigido e verificado

- Diário antes vazio reconstruído a partir das evidências, com origem e limitações explícitas.
- Configuração MCP para VS Code incluída.
- JSONs SQS corrigidos, sem metadados PowerShell.
- Provisionamento reproduzível da aplicação, perfis locais e recursos auxiliares.
- UserData HTTP acrescentado, lint aprovado e stack local atualizada.
- Quatro cenários reais S3/Lambda/Ollama/DynamoDB aprovados, incluindo injeção.
- Testes IAM de leitura/escrita e identidade restrita do agente.
- Agente com tool use, limite de rodadas, validação externa ao LLM, aprovação concreta e auditoria.
- CPU simulada, alarme e mensagem SNS/SQS comprovados por JSON.
- Medições de tokens, latência e Docker; cálculos de custo com hipóteses/fontes identificadas.
- README, revisão IaC e roteiro de apresentação atualizados; capturas históricas anexadas.

## O que não deve ser apresentado como concluído

- A aprovação humana da nova versão foi registrada em evidencias/aprovacao-humana-atual.png; a apresentação ainda precisa ser realizada pelo autor.
- A comparação histórica foi complementada por experimento controlado via MCP; isso não equivale a repetir o teste dentro do Copilot do autor.
- O orçamento é cálculo reproduzível, não um link salvo/exportado da AWS Pricing Calculator. A tarifa GPU usada é referência histórica, não cotação atual confirmada.
- Não houve deploy AWS real, medição de energia ou demonstração de CloudTrail real. A compatibilidade IAM do Floci tem exceções de PutLogEvents e SetDesiredCapacity com recurso *; a restrição de ASG é aplicada no código.
- As alterações desta revisão não foram publicadas automaticamente no GitHub.

Essas ressalvas evitam transformar requisitos não medidos em resultados inventados. Modelos adicionais e variante de saúde são extensões opcionais, não executadas.



