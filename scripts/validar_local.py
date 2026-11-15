"""Testes reais do emulador; grava evidências e não escala recursos."""
import json
import subprocess
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs/evidencias'
OUT.mkdir(exist_ok=True, parents=True)

def main():
    s = boto3.Session(profile_name='floci')
    assert s.client('sts').get_caller_identity()['Account']=='000000000000'
    result = {'data_utc':datetime.now(timezone.utc).isoformat(), 'ambiente':'Floci/Ollama local', 'relatorios':[],'docker_stats':[]}
    stop = threading.Event()
    def sample():
        while not stop.is_set():
            p = subprocess.run(['docker','stats','--no-stream','--format','{{json .}}'],capture_output=True,text=True)
            for line in p.stdout.splitlines():
                result['docker_stats'].append({'instante':datetime.now(timezone.utc).isoformat(), **json.loads(line)})
            stop.wait(2)
    worker = threading.Thread(target=sample, daemon=True)
    worker.start()
    table = s.resource('dynamodb').Table('triagem')
    try:
        for urgency in ['alta','baixa','media','injecao']:
            key = f'validacao-{uuid.uuid4().hex[:8]}-{urgency}.txt'
            start = time.perf_counter()
            s.client('s3').put_object(Bucket='relatorios-campo',Key=key,Body=(ROOT/f'testes/relatorio-{urgency}.txt').read_bytes())
            item = None
            for attempt in range(90):
                item = table.get_item(Key={'arquivo':key},ConsistentRead=True).get('Item')
                if item: break
                time.sleep(2)
            if not item: raise TimeoutError(f'Sem resultado para {key}')
            expected = 'alta' if urgency=='injecao' else urgency
            entry = {'cenario':urgency, 'esperado':expected,'item':item,'tempo_total_s':round(time.perf_counter()-start,3),
                     'passou':item['urgencia']==expected and (urgency!='injecao' or item.get('revisao_humana') is True)}
            result['relatorios'].append(entry)
            print(json.dumps(entry, default=float, ensure_ascii=True),flush=True)
        restricted = boto3.Session(profile_name='triagem-agente')
        try:
            restricted.client('s3').list_buckets()
            result['iam_s3_negado'] = False
        except ClientError as exc:
            result['iam_s3_negado'] = exc.response['Error']['Code'] in ['AccessDenied','AccessDeniedException']
        cw = s.client('cloudwatch')
        now = datetime.now(timezone.utc).replace(second=0,microsecond=0)
        cw.put_metric_data(Namespace='AWS/EC2',MetricData=[{'MetricName':'CPUUtilization',
            'Dimensions':[{'Name':'AutoScalingGroupName','Value':'triagem-asg'}],
            'Timestamp':now-timedelta(minutes=3-i),'Value':v,'Unit':'Percent'} for i,v in enumerate([30,95,95,95])])
        result['metricas_enviadas'] = [30,95,95,95]
        result['asg'] = s.client('autoscaling').describe_auto_scaling_groups(AutoScalingGroupNames=['triagem-asg'])['AutoScalingGroups'][0]
    finally:
        stop.set()
        worker.join(timeout=10)
        (OUT/'validacao-local.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=lambda x:float(x) if isinstance(x,Decimal) else str(x)),encoding='utf-8')
    if not all(x['passou'] for x in result['relatorios']) or not result['iam_s3_negado']:
        raise SystemExit('Uma validação falhou. Consulte docs/evidencias/validacao-local.json.')

if __name__=='__main__': main()
