# Etapa 1 - Fundamentos de GenAI aplicada à nuvem

## 1. Servidor MCP local e remoto

Um servidor MCP local, usando `stdio`, é iniciado pelo próprio cliente de IA como um processo no computador. A comunicação acontece pela entrada e saída padrão do processo, sendo adequado para ferramentas instaladas localmente, como o servidor de documentação da AWS executado por `uvx`.

Um servidor MCP remoto fica hospedado em um endereço de rede e é acessado por HTTP. Ele pode atender diversos clientes e não precisa ser iniciado na máquina do usuário. Um exemplo é o AWS Knowledge MCP Server, hospedado pela AWS.

No repositório `awslabs/mcp`, os servidores open source são voltados ao transporte `stdio`. Já o protocolo MCP também define o transporte Streamable HTTP para comunicação remota.

## 2. Glossário

| Termo | Definição | Exemplo ligado à AWS |
|---|---|---|
| LLM | Modelo de linguagem treinado para compreender e gerar texto. | O `llama3.2` responde às solicitações enviadas ao Bedrock Runtime simulado. |
| Modelo de fundação | Modelo pré-treinado que pode ser adaptado a várias tarefas. | Na AWS real, o Bedrock disponibiliza modelos de fundação por API. |
| Prompt | Instrução enviada ao modelo para orientar sua resposta. | O pedido “Em uma frase: o que é IaaS?” foi enviado ao Bedrock Runtime. |
| Contexto | Informações enviadas junto do prompt para orientar a resposta. | Um relatório de inspeção armazenado no S3 pode servir de contexto para uma Lambda. |
| Janela de contexto | Limite de informações que o modelo consegue analisar em uma interação. | Relatórios muito longos podem exigir resumo ou divisão antes do envio ao Bedrock. |
| RAG | Técnica em que o modelo consulta documentos antes de responder. | Um agente pode buscar manuais no S3 antes de orientar uma manutenção. |
| MCP | Protocolo que conecta assistentes de IA a ferramentas e fontes de dados. | O servidor AWS Documentation MCP permite consultar documentação oficial. |
| Ferramenta | Função que o modelo pode solicitar para obter dados ou executar ações. | Um agente pode chamar uma função para consultar métricas do CloudWatch. |
| Agente | Sistema que usa IA para escolher ferramentas e organizar ações. | Um agente pode analisar CPU alta e recomendar ajuste no Auto Scaling. |
| Token | Unidade de texto processada pelo modelo e usada para medir consumo. | No Bedrock real, tokens de entrada e saída influenciam o custo da chamada. |

## 3. Classificação dos serviços

| Serviço | Classificação | Justificativa |
|---|---|---|
| Amazon Bedrock | PaaS | A AWS gerencia a infraestrutura e disponibiliza modelos de IA por API; a aplicação apenas consome o serviço. |
| Amazon Bedrock AgentCore | PaaS | A plataforma gerencia a execução, identidade, observabilidade e governança de agentes. |
| Kiro | SaaS | É um ambiente/assistente de desenvolvimento pronto para uso, consumido pelo usuário sem administrar sua infraestrutura. |

## 4. Serviços no ambiente Floci

| Serviço ou componente | Situação no Floci | Observação |
|---|---|---|
| Bedrock Runtime | Parcial | O Floci repassa chamadas `Converse` ao Ollama local. A qualidade depende do modelo local e algumas funções não possuem equivalência completa com a AWS. |
| Bedrock AgentCore | Parcial | Permite exercitar o plano de controle e registrar recursos, mas não executa um agente gerenciado como na AWS real. |
| Kiro | Não emulado | É uma ferramenta de desenvolvimento/assistente, não um serviço AWS executado pelo Floci. |
| Agent Toolkit for AWS | Não emulado | É um conjunto de ferramentas para interagir com contas AWS; pode ser usado separadamente, mas não é emulado pelo Floci. |
| Servidores awslabs/mcp | Não emulados | São programas locais que conectam clientes de IA à documentação ou APIs. Podem ser usados junto ao Floci quando configurados para o endpoint local. |
| Floci + Ollama | Ambiente de estudo | Não representam um serviço AWS único: simulam APIs AWS e fornecem um modelo local para os testes. |

O Floci consegue imitar a interface e parte do comportamento da API do Bedrock, como receber uma chamada `Converse` e retornar uma resposta. Porém, ele não reproduz a qualidade, tamanho, treinamento, segurança e infraestrutura dos grandes modelos hospedados pela AWS. No ambiente local, a resposta depende do `llama3.2`, que é um modelo menor e executado no computador do aluno.

## 5. Pergunta de checagem

Se um modelo responder com o nome de um serviço AWS inexistente, a técnica mais adequada para reduzir esse problema é RAG. Ela permite recuperar documentação oficial atualizada antes de gerar a resposta, diminuindo a dependência do conhecimento interno do modelo e reduzindo alucinações.

## 6. Referências consultadas

- Model Context Protocol - especificação de transportes.
- AWS Labs MCP Servers.
- Documentação do Floci.