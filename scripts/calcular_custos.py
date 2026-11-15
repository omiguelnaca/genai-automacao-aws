"""Projeção explícita; não é cotação nem fatura AWS."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT/'docs/evidencias/validacao-local.json').read_text(encoding='utf-8'))
rows = [r['item'] for r in data['relatorios'] if r['cenario']!='injecao']
tokens_in = sum(r['tokens_in'] for r in rows)/len(rows)
tokens_out = sum(r['tokens_out'] for r in rows)/len(rows)
volume = 500*30
inference = (tokens_in*.62+tokens_out*1.85)/1_000_000
result = {'premissas':{'relatorios_mes':volume,'tokens_entrada_media':tokens_in,
    'tokens_saida_media':tokens_out,'modelo_preco':'DeepSeek v3.2 Standard, us-east-1',
    'entrada_usd_milhao':.62,'saida_usd_milhao':1.85,'lambda_memoria_gb':.125,
    'lambda_ia_segundos_hipotese':3,'lambda_regras_segundos_hipotese':.1,
    'gpu_usd_hora_referencia_historica':.526,'gpu_horas_mes':720},
    'inferencia_por_relatorio_usd':inference,'inferencia_mes_usd':inference*volume,
    'lambda_ia_mes_usd':volume*.125*3*.0000166667+volume*.2/1e6,
    'lambda_regras_mes_usd':volume*.125*.1*.0000166667+volume*.2/1e6,
    'gpu_mes_usd':.526*720,'equilibrio_gpu_relatorios_mes':.526*720/inference,
    'exclui':['S3','DynamoDB','logs','metricas','alarmes','SNS','SQS','EC2 de laboratorio','rede','impostos']}
(ROOT/'docs/evidencias/custos.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(result,indent=2,ensure_ascii=True))
