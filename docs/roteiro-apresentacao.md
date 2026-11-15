# Roteiro de apresentação — 10 minutos

| Tempo | Mostrar e explicar |
|---|---|
| 0:00–0:50 | Problema: relatórios agrícolas não estruturados; resumo e urgência com revisão humana. |
| 0:50–1:40 | Diagrama no README. Floci emula APIs; Ollama executa llama3.2 na triagem e qwen2.5:3b no agente. O ID Haiku é alias local. |
| 1:40–2:30 | MCP local/remoto, capturas e diário. Explicar limites da comparação retrospectiva com/sem MCP. |
| 2:30–3:30 | Executar testar_iam.py: GetObject permitido, PutObject negado. Mostrar role mínima da Lambda e usuário do agente. |
| 3:30–4:20 | Mostrar template, lint e evidências da stack. UserData, AMI por parâmetro, HTTP sem SSH; revisão crítica de três ou mais achados. |
| 4:20–5:40 | Mostrar três relatórios e validacao-local.json com baixa/média/alta. Upload de um relatório e consulta DynamoDB se houver tempo. |
| 5:40–6:30 | Relatório com injeção: resultado alta e revisão humana. Explicar fallback e limites da regex. |
| 6:30–7:30 | CPU simulada, alarme ALARM, mensagem SNS na SQS e logs coletados. O agente é iniciado manualmente. |
| 7:30–8:30 | Mostrar toolUse/toolResult, identidade restrita e proteção de capacidade. Executar demonstrar_agente.py --recusar. Se optar por aprovação real, executar sem flag e aprovar somente a ação exibida. |
| 8:30–9:30 | Tokens médios, latência e CPU/RAM medidos; cálculo para 15 mil relatórios, regras fixas e GPU 24h. Distinguir subtotal projetado de fatura real. |
| 9:30–10:00 | Limites: erros do LLM, exceção local de logs, ausência de teste AWS real. Explicar decisão arquitetural e encerramento após avaliação. |

Pré-carregar o modelo antes da apresentação. A inferência pode levar tempo; manter os JSONs de evidência disponíveis. Não afirmar que uma chamada com recusa automática demonstra aprovação humana. As capturas antigas de aprovação referem-se à versão anterior baseada em flag.
