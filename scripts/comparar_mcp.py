"""Mesmo modelo/prompt/parâmetros, com e sem contexto recuperado por MCP."""
import json
from pathlib import Path
import time
from datetime import datetime, timezone
import boto3
from mcp_cliente import call

ROOT = Path(__file__).resolve().parents[1]
s = boto3.Session(profile_name='floci')
assert s.client('sts').get_caller_identity()['Account']=='000000000000'
client = s.client('bedrock-runtime')
prompt = 'Compare Security Group e NACL na AWS: estado, associação, regras e exemplo. Responda em português em até 200 palavras. Cite fontes somente se disponíveis no contexto.'
result = {'data_utc':datetime.now(timezone.utc).isoformat(),'modelo_real':'llama3.2',
          'model_id_proxy':'anthropic.claude-3-haiku-20240307-v1:0','prompt':prompt,'temperature':0,'maxTokens':400}
retrieval = call('tools/call',{'name':'aws___search_documentation','arguments':{
    'search_phrase':'VPC security groups network ACLs stateful stateless allow deny subnet network interface',
    'topics':['general'],'limit':2}})
if 'error' in retrieval or retrieval.get('result',{}).get('isError'): raise RuntimeError(retrieval)
result['mcp_resultado'] = retrieval
context = json.dumps(retrieval['result'],ensure_ascii=False)
for label,extra in [('sem_mcp',''),('com_mcp','\nDocumentação recuperada por AWS Knowledge MCP:\n'+context)]:
    start=time.perf_counter()
    response=client.converse(modelId=result['model_id_proxy'],
        system=[{'text':'Explique conceitos AWS com precisão. Não invente fontes.'+extra}],
        messages=[{'role':'user','content':[{'text':prompt}]}],
        inferenceConfig={'temperature':0,'maxTokens':400})
    result[label]={'resposta':response,'latencia_s':round(time.perf_counter()-start,3)}
    print(label, 'concluido',flush=True)
(ROOT/'docs/evidencias/comparacao-mcp.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,default=str),encoding='utf-8')
