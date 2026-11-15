# GenAI na Automação de Serviços AWS

Projeto prático de automação em nuvem com IA generativa, utilizando Floci e Ollama como ambiente local simulado da AWS.

## Etapa 0 - Ambiente local

### Componentes utilizados

- Docker Desktop 29.9.3
- Python 3.14.10
- AWS CLI 2.40.3
- Floci, simulando serviços AWS localmente
- Ollama com o modelo local `llama3.2`

### Arquitetura inicial

```text
AWS CLI -> Floci (localhost:4566) -> Bedrock Runtime simulado -> Ollama (llama3.2)