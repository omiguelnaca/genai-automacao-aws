# Etapa 5 — Evidências

## Revisão atual

- Provisionamento local passou; template passou no cfn-lint.
- CPU simulada foi publicada. O alarme cpu-triagem-alta entrou em ALARM com motivo “Threshold Crossed: 3 datapoint(s) breaching the threshold.”
- A fila alertas-triagem recebeu mensagem SNS cujo Subject identifica cpu-triagem-alta. O arquivo também contém mensagens antigas: não confundir com o teste atual.
- Usuário restrito triagem-agente foi usado na execução do agente. Logs reais foram consultados no CloudWatch Logs.
- Artefatos: [monitoramento.json](evidencias/monitoramento.json), [execução do agente](evidencias/agente-execucao.txt), [IAM](evidencias/iam.json).
- Houve uma geração com 66 chamadas repetidas; o limite bloqueou a execução. Evidência preservada em agente-limite-ferramentas.txt. Isso demonstra um limite do modelo pequeno e a necessidade de controle fora do LLM.
- Doze testes automatizados cobrem aprovação, recusa, mudança durante confirmação, limites, pico isolado, dados antigos, falha de logs, ferramenta desconhecida, JSON inválido, injeção e retorno de toolResult. A aprovação com mock é teste de código; não é evidência de uma pessoa aprovando.

## Histórico anterior à revisão

As capturas agente-sem-aprovacao.png e agente-aprovado.png mostram a versão anterior propondo 1→2 e aplicando a alteração com uma flag. O ASG foi criado e a capacidade 2 foi confirmada. A afirmação anterior de que o ASG ainda estava pendente foi corrigida. O novo agente exige confirmação interativa da ação concreta, portanto as capturas históricas não são apresentadas como teste desse novo mecanismo.

## Limite IAM do emulador

PutLogEvents foi negado mesmo com o ARN do grupo/streams. Uma política complementar permite apenas essa ação em Resource *. A exceção é exclusiva do Floci, não concede administração e não deve ser levada à AWS. A política principal mantém o recurso exato para SetDesiredCapacity. A leitura S3 pelo agente foi negada em teste real.

## Execução atual do agente

Com qwen2.5:3b no Ollama, o modelo consultou as três ferramentas, propôs 1 → 2 por toolUse e recebeu recusa automática. A capacidade permaneceu 1. Após a recusa, o modelo afirmou incorretamente que não havia evidência de carga sustentada; o evento estado_verificado registrou carga sustentada=true e nenhuma alteração. Isso ilustra por que os resultados das ferramentas e as validações determinísticas prevalecem sobre o texto. A aprovação real do novo agente permanece para a demonstração do autor.

## Compatibilidade de escala no Floci

No teste com aprovação humana, SetDesiredCapacity retornou AccessDenied apesar da política específica do ARN. A política local adicional agente-floci-escala.json permite somente SetDesiredCapacity em qualquer ASG do emulador. Isso amplia o privilégio IAM: o limite ao grupo triagem-asg, aprovação e revalidação são controles do código, não da política adicional. Não usar essa exceção na AWS; validar uma política restrita ao ARN real. A primeira tentativa aprovada não alterou a capacidade.

## Aprovação humana da versão atual

Em 15/11/2026, o operador aprovou interativamente a proposta de 1 para 2 instâncias. A ferramenta retornou status executado e a verificação posterior registrou capacidade desejada 2 e alteracao_executada=true. A [captura fornecida pelo operador](evidencias/aprovacao-humana-atual.png) documenta a execução no Floci. Isso confirma capacidade desejada, não comprova por si só que duas instâncias estejam em serviço.
