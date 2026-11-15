"""Agente com tool use, aprovação da ação concreta e auditoria obrigatória."""
import argparse
import json
import time
import uuid
from datetime import datetime, timedelta, timezone
import boto3

MODEL = 'qwen2.5:3b'
GROUP = 'triagem-asg'
LOG_GROUP = '/genai/agente'
MAX_ITERATIONS = 6


def tool(name, description, properties=None, required=None):
    return {'toolSpec': {'name': name, 'description': description, 'inputSchema': {'json': {
        'type': 'object', 'properties': properties or {}, 'required': required or [], 'additionalProperties': False}}}}


TOOLS = [
    tool('ler_metricas', 'Get CPU history and whether load is sustained. No arguments required.'),
    tool('descrever_asg', 'Get the current DesiredCapacity, MinSize and MaxSize. No arguments required.'),
    tool('listar_atividades', 'Get recent scaling activities and their causes. No arguments required.'),
    tool('ajustar_capacidade', 'Request target capacity equal to DesiredCapacity plus one. Requires human approval.',
         {'capacidade': {'type': 'integer'}, 'justificativa': {'type': 'string'}}, ['capacidade', 'justificativa']),
]


def sustained(points):
    recent = sorted(points, key=lambda p: p['Timestamp'])[-3:]
    if len(recent) != 3 or any(p['Average'] <= 80 for p in recent):
        return False
    gaps = [(recent[i+1]['Timestamp']-recent[i]['Timestamp']).total_seconds() for i in range(2)]
    age = (datetime.now(timezone.utc)-recent[-1]['Timestamp']).total_seconds()
    return all(0 < gap <= 90 for gap in gaps) and 0 <= age <= 180


class Agent:
    def __init__(self, session, confirm=input):
        identity = session.client('sts').get_caller_identity()
        if identity['Account'] != '000000000000' or not identity['Arn'].endswith(':user/triagem-agente'):
            raise RuntimeError('Use o usuário restrito triagem-agente na conta Floci 000000000000.')
        self.cw = session.client('cloudwatch')
        self.asg = session.client('autoscaling')
        self.logs = session.client('logs')
        self.bedrock = session.client('bedrock-runtime')
        self.confirm = confirm
        self.stream = str(uuid.uuid4())
        self.logs.create_log_stream(logGroupName=LOG_GROUP, logStreamName=self.stream)
        self.observed = set()
        self.written = False
        self.audit('inicio', {'identidade': identity['Arn'], 'modelo': MODEL})

    def audit(self, event, data):
        message = json.dumps({'evento': event, **data}, ensure_ascii=False, default=str)
        self.logs.put_log_events(logGroupName=LOG_GROUP, logStreamName=self.stream,
            logEvents=[{'timestamp': int(time.time()*1000), 'message': message}])
        print(message, flush=True)

    def metrics(self):
        now = datetime.now(timezone.utc)
        return self.cw.get_metric_statistics(Namespace='AWS/EC2', MetricName='CPUUtilization',
            Dimensions=[{'Name': 'AutoScalingGroupName', 'Value': GROUP}],
            StartTime=now-timedelta(minutes=10), EndTime=now, Period=60,
            Statistics=['Average'])['Datapoints']

    def group(self):
        return self.asg.describe_auto_scaling_groups(AutoScalingGroupNames=[GROUP])['AutoScalingGroups'][0]

    def execute(self, name, args):
        if not isinstance(args, dict):
            return {'erro': 'Argumentos devem ser um objeto JSON.'}
        self.audit('ferramenta_solicitada', {'nome': name, 'argumentos': args})
        if name == 'ler_metricas':
            points = self.metrics()
            self.observed.add(name)
            result = {'pontos': sorted(points, key=lambda p: p['Timestamp']), 'carga_sustentada': sustained(points)}
        elif name == 'descrever_asg':
            group = self.group()
            self.observed.add(name)
            result = {k: group[k] for k in ('AutoScalingGroupName', 'MinSize', 'MaxSize', 'DesiredCapacity')}
        elif name == 'listar_atividades':
            result = {'atividades': self.asg.describe_scaling_activities(AutoScalingGroupName=GROUP, MaxRecords=5).get('Activities', [])}
            self.observed.add(name)
        elif name == 'ajustar_capacidade':
            self.proposal_attempted = True
            result = self.adjust(args)
        else:
            result = {'erro': 'Ferramenta não permitida.'}
        self.audit('ferramenta_resultado', {'nome': name, 'resultado': result})
        return json.loads(json.dumps(result, default=str))

    def adjust(self, args):
        if not {'ler_metricas', 'descrever_asg', 'listar_atividades'} <= self.observed or self.written:
            return {'erro': 'Consulte as três ferramentas; no máximo uma alteração por execução.'}
        group = self.group()
        target = args.get('capacidade')
        if type(target) is not int or target != group['DesiredCapacity']+1 or target > group['MaxSize']:
            return {'erro': 'Somente aumento de uma unidade dentro dos limites é permitido.'}
        if not isinstance(args.get('justificativa'), str) or not args['justificativa'].strip():
            return {'erro': 'Justificativa obrigatória.'}
        if not sustained(self.metrics()):
            return {'erro': 'CPU não está acima de 80% em três períodos consecutivos recentes.'}
        request = f"Aprovar {GROUP}: {group['DesiredCapacity']} -> {target}? {args['justificativa']} [s/N] "
        approved = self.confirm(request).strip().lower() == 's'
        self.audit('aprovacao', {'grupo': GROUP, 'capacidade': target, 'aprovado': approved})
        if not approved:
            return {'status': 'negado pelo operador'}
        if self.group()['DesiredCapacity'] != group['DesiredCapacity'] or not sustained(self.metrics()):
            return {'erro': 'Condições mudaram durante a aprovação; execute um novo diagnóstico.'}
        self.audit('escrita_autorizada', {'grupo': GROUP, 'capacidade': target})
        self.asg.set_desired_capacity(AutoScalingGroupName=GROUP, DesiredCapacity=target, HonorCooldown=True)
        self.written = True
        return {'status': 'executado', 'capacidade': target}

    def run(self):
        messages = [{'role': 'user', 'content': [{'text':
            'Investigate triagem-asg using the three read tools first. Wait for their results. '
            'If carga_sustentada is true, call ajustar_capacidade with DesiredCapacity plus one. '
            'Otherwise keep capacity. Report verified facts and uncertainty in Portuguese.'}]}]
        for iteration in range(MAX_ITERATIONS):
            missing = [t for t in TOOLS[:3] if t['toolSpec']['name'] not in self.observed]
            available = missing or TOOLS
            permitted = {t['toolSpec']['name'] for t in available}
            response = self.bedrock.converse(modelId=MODEL, messages=messages,
                system=[{'text': 'You are an operations assistant. Use tools to get facts. Never invent metrics. '
                         'Call each tool at most once per turn. Respect refusal and errors. '
                         'Do not adjust capacity until the read tool results are available. '
                         'The target capacity is DesiredCapacity + 1.'}],
                toolConfig={'tools': available}, inferenceConfig={'maxTokens': 400, 'temperature': 0})
            message = response['output']['message']
            messages.append(message)
            self.audit('modelo', {'iteracao': iteration+1, 'mensagem': message})
            uses = [b['toolUse'] for b in message.get('content', []) if 'toolUse' in b]
            if not uses:
                if not {'ler_metricas','descrever_asg','listar_atividades'} <= self.observed:
                    self.audit('diagnostico_incompleto', {'iteracao': iteration+1})
                    messages.append({'role':'user','content':[{'text':'You have not collected all three required read tool results. Call the missing read tools now; do not invent data.'}]})
                    continue
                if not getattr(self, 'proposal_attempted', False) and sustained(self.metrics()):
                    group = self.group()
                    if group['DesiredCapacity'] < group['MaxSize']:
                        messages.append({'role':'user','content':[{'text':
                            f"You described a proposal but did not call the tool. Request ajustar_capacidade with capacidade={group['DesiredCapacity']+1} and justificativa. The operator will accept or reject. Do not claim execution."}]})
                        continue
                self.audit('estado_verificado', {'carga_sustentada_agora': sustained(self.metrics()),
                    'capacidade_desejada': self.group()['DesiredCapacity'], 'alteracao_executada': self.written,
                    'aviso': 'O texto do modelo é uma hipótese; prevalecem estes dados e os resultados das ferramentas.'})
                self.audit('fim', {'iteracoes': iteration+1, 'alterou': self.written})
                return
            if len(uses) > 8:
                self.audit('limite_ferramentas', {'quantidade': len(uses)})
                return
            results = []
            for use in uses:
                result = (self.execute(use['name'], use.get('input', {})) if use['name'] in permitted
                          else {'erro':'Ferramenta não disponível nesta rodada. Leia os resultados antes de propor uma ação.'})
                results.append({'toolResult': {'toolUseId': use['toolUseId'],
                    'content': [{'json': result}], 'status': 'error' if 'erro' in result else 'success'}})
            messages.append({'role': 'user', 'content': results})
        self.audit('limite_iteracoes', {'limite': MAX_ITERATIONS})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', default='triagem-agente')
    options = parser.parse_args()
    Agent(boto3.Session(profile_name=options.profile)).run()
