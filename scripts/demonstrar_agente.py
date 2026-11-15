"""Publica CPU simulada e inicia o agente restrito. Não aprova ações automaticamente."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timedelta, timezone
import boto3

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--cenario', choices=['pico','sustentada'],default='sustentada')
parser.add_argument('--recusar',action='store_true',help='Teste automatizado: recusar qualquer proposta')
args = parser.parse_args()
s = boto3.Session(profile_name='floci')
assert s.client('sts').get_caller_identity()['Account']=='000000000000'
now = datetime.now(timezone.utc).replace(second=0,microsecond=0)
values = [30,30,95] if args.cenario=='pico' else [95,95,95]
s.client('cloudwatch').put_metric_data(Namespace='AWS/EC2',MetricData=[{
    'MetricName':'CPUUtilization','Dimensions':[{'Name':'AutoScalingGroupName','Value':'triagem-asg'}],
    'Timestamp':now-timedelta(minutes=3-i),'Value':v,'Unit':'Percent'} for i,v in enumerate(values)])
print('CPU simulada:', values, flush=True)
env = dict(os.environ, PYTHONIOENCODING='utf-8')
command = [sys.executable,str(ROOT/'agent/triagem_agente.py')]
if args.recusar:
    p = subprocess.run(command,input='n\n'*6,text=True,encoding='utf-8',capture_output=True,env=env)
    output = ROOT/'docs/evidencias/agente-execucao.txt'
    output.write_text(p.stdout+'\n'+p.stderr,encoding='utf-8')
    print(p.stdout.encode('ascii','backslashreplace').decode(),flush=True)
    if p.returncode:
        print(p.stderr)
        raise SystemExit(p.returncode)
else:
    raise SystemExit(subprocess.call(command,env=env))
cw = s.client('cloudwatch')
sqs = s.client('sqs')
queue = sqs.get_queue_url(QueueName='alertas-triagem')['QueueUrl']
evidence = {'data_utc':datetime.now(timezone.utc).isoformat(), 'cenario':args.cenario,
    'aprovacao':'recusada automaticamente para teste',
    'alarme':cw.describe_alarms(AlarmNames=['cpu-triagem-alta'])['MetricAlarms'],
    'mensagens_sqs':sqs.receive_message(QueueUrl=queue,MaxNumberOfMessages=10,WaitTimeSeconds=1,VisibilityTimeout=0).get('Messages',[]),
    'logs':s.client('logs').filter_log_events(logGroupName='/genai/agente',startTime=int((now-timedelta(minutes=1)).timestamp()*1000)).get('events',[])}
# ReceiptHandle é transitório e desnecessário para a evidência.
for message in evidence['mensagens_sqs']: message.pop('ReceiptHandle',None)
(ROOT/'docs/evidencias/monitoramento.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False,default=str),encoding='utf-8')
