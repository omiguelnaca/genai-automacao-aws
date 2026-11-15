"""Implanta apenas no Floci; código fonte e políticas são a fonte da configuração."""
import configparser
import io
import json
import os
from pathlib import Path
import sys
import zipfile
import boto3
from botocore.exceptions import ClientError

ROOT = Path(__file__).resolve().parents[1]
ACCOUNT = '000000000000'
REGION = 'us-east-1'


def local_session():
    s = boto3.Session(profile_name='floci', region_name=REGION)
    if s.client('sts').get_caller_identity()['Account'] != ACCOUNT:
        raise RuntimeError('Recusado: conta diferente do Floci.')
    return s


def ensure(call, **kwargs):
    try:
        return call(**kwargs)
    except ClientError as exc:
        if exc.response['Error']['Code'] not in ('EntityAlreadyExists', 'ResourceAlreadyExistsException',
                                                 'BucketAlreadyOwnedByYou', 'BucketAlreadyExists',
                                                 'ResourceInUseException', 'AlreadyExists'):
            raise


def policy(statements):
    return json.dumps({'Version': '2012-10-17', 'Statement': statements})


def allow(actions, resource):
    return {'Effect': 'Allow', 'Action': actions, 'Resource': resource}


def main():
    s = local_session()
    cf, iam, logs = (s.client(x) for x in ('cloudformation', 'iam', 'logs'))
    template = (ROOT/'iac/vpc.yaml').read_text(encoding='utf-8-sig')
    params = [{'ParameterKey': 'AmiId', 'ParameterValue': 'ami-0123456789abcdef0'}]
    try:
        cf.describe_stacks(StackName='lab-ia')
        # O emulador exige a instância parada para atualizar UserData.
        instance = cf.describe_stack_resource(StackName='lab-ia', LogicalResourceId='WebInstance')['StackResourceDetail']['PhysicalResourceId']
        s.client('ec2').stop_instances(InstanceIds=[instance])
        s.client('ec2').get_waiter('instance_stopped').wait(InstanceIds=[instance], WaiterConfig={'Delay': 1, 'MaxAttempts': 60})
        try:
            cf.update_stack(StackName='lab-ia', TemplateBody=template, Parameters=params)
            cf.get_waiter('stack_update_complete').wait(StackName='lab-ia', WaiterConfig={'Delay': 2, 'MaxAttempts': 120})
        except ClientError as exc:
            if 'No updates' not in str(exc):
                raise
        finally:
            s.client('ec2').start_instances(InstanceIds=[instance])
    except ClientError as exc:
        if 'does not exist' not in str(exc):
            raise
        cf.create_stack(StackName='lab-ia', TemplateBody=template, Parameters=params)
        cf.get_waiter('stack_create_complete').wait(StackName='lab-ia', WaiterConfig={'Delay': 2, 'MaxAttempts': 120})
    def resource(name):
        return cf.describe_stack_resource(StackName='lab-ia', LogicalResourceId=name)['StackResourceDetail']['PhysicalResourceId']
    ensure(iam.create_role, RoleName='triagem-lambda', AssumeRolePolicyDocument=(ROOT/'policies/triagem-lambda-trust.json').read_text())
    iam.put_role_policy(RoleName='triagem-lambda', PolicyName='TriagemLambdaMinima',
                        PolicyDocument=(ROOT/'policies/triagem-lambda-permissions.json').read_text())
    for name in ['/aws/lambda/triagem', '/genai/agente']:
        ensure(logs.create_log_group, logGroupName=name)
        logs.put_retention_policy(logGroupName=name, retentionInDays=7)
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(ROOT/'lambda/app.py', 'app.py')
    fn = s.client('lambda')
    try:
        fn.get_function(FunctionName='triagem')
        fn.update_function_code(FunctionName='triagem', ZipFile=data.getvalue())
        fn.update_function_configuration(FunctionName='triagem', Handler='app.lambda_handler', Timeout=120,
            Role=f'arn:aws:iam::{ACCOUNT}:role/triagem-lambda', Environment={'Variables': {'TABELA': 'triagem'}})
    except ClientError as exc:
        if exc.response['Error']['Code'] != 'ResourceNotFoundException':
            raise
        fn.create_function(FunctionName='triagem', Runtime='python3.12', Handler='app.lambda_handler',
            Code={'ZipFile': data.getvalue()}, Timeout=120, Role=f'arn:aws:iam::{ACCOUNT}:role/triagem-lambda',
            Environment={'Variables': {'TABELA': 'triagem'}})
    try:
        fn.add_permission(FunctionName='triagem', StatementId='S3Relatorios', Action='lambda:InvokeFunction',
            Principal='s3.amazonaws.com', SourceArn='arn:aws:s3:::relatorios-campo', SourceAccount=ACCOUNT)
    except ClientError as exc:
        if exc.response['Error']['Code'] != 'ResourceConflictException':
            raise
    s.client('s3').put_bucket_notification_configuration(Bucket='relatorios-campo', NotificationConfiguration={
        'LambdaFunctionConfigurations': [{'LambdaFunctionArn': f'arn:aws:lambda:{REGION}:{ACCOUNT}:function:triagem',
            'Events': ['s3:ObjectCreated:*']}]})
    asg = s.client('autoscaling')
    if not asg.describe_launch_configurations(LaunchConfigurationNames=['triagem-launch-v1'])['LaunchConfigurations']:
        asg.create_launch_configuration(LaunchConfigurationName='triagem-launch-v1', ImageId='ami-0123456789abcdef0',
            InstanceType='t3.micro', SecurityGroups=[resource('WebSecurityGroup')])
    if not asg.describe_auto_scaling_groups(AutoScalingGroupNames=['triagem-asg'])['AutoScalingGroups']:
        asg.create_auto_scaling_group(AutoScalingGroupName='triagem-asg', LaunchConfigurationName='triagem-launch-v1',
            MinSize=1, MaxSize=4, DesiredCapacity=1, VPCZoneIdentifier=resource('PublicSubnet'))
    group_arn = asg.describe_auto_scaling_groups(AutoScalingGroupNames=['triagem-asg'])['AutoScalingGroups'][0]['AutoScalingGroupARN']
    sns, sqs = s.client('sns'), s.client('sqs')
    topic = sns.create_topic(Name='alertas-triagem')['TopicArn']
    queue = sqs.create_queue(QueueName='alertas-triagem')['QueueUrl']
    queue_arn = sqs.get_queue_attributes(QueueUrl=queue, AttributeNames=['QueueArn'])['Attributes']['QueueArn']
    p = json.loads((ROOT/'policies/sqs-alertas-policy.json').read_text(encoding='utf-8-sig'))
    p['Statement'][0]['Resource'] = queue_arn
    p['Statement'][0]['Condition']['ArnEquals']['aws:SourceArn'] = topic
    sqs.set_queue_attributes(QueueUrl=queue, Attributes={'Policy': json.dumps(p)})
    sns.subscribe(TopicArn=topic, Protocol='sqs', Endpoint=queue_arn)
    s.client('cloudwatch').put_metric_alarm(AlarmName='cpu-triagem-alta', Namespace='AWS/EC2', MetricName='CPUUtilization',
        Dimensions=[{'Name': 'AutoScalingGroupName', 'Value': 'triagem-asg'}], Statistic='Average', Period=60,
        EvaluationPeriods=3, DatapointsToAlarm=3, Threshold=80, ComparisonOperator='GreaterThanThreshold',
        TreatMissingData='notBreaching', AlarmActions=[topic])
    statements = [allow(['cloudwatch:GetMetricStatistics','autoscaling:DescribeAutoScalingGroups',
                         'autoscaling:DescribeScalingActivities'], '*'),
        allow('autoscaling:SetDesiredCapacity', group_arn),
        allow('bedrock:InvokeModel', f'arn:aws:bedrock:{REGION}::foundation-model/qwen2.5:3b'),
        allow(['logs:CreateLogStream','logs:PutLogEvents'], [f'arn:aws:logs:{REGION}:{ACCOUNT}:log-group:/genai/agente',
              f'arn:aws:logs:{REGION}:{ACCOUNT}:log-group:/genai/agente:*'])]
    agent_policy = policy(statements)
    (ROOT/'policies/agente-gerada.json').write_text(agent_policy, encoding='utf-8')
    ensure(iam.create_user, UserName='triagem-agente')
    iam.put_user_policy(UserName='triagem-agente', PolicyName='AgenteMinimo', PolicyDocument=agent_policy)
    # A versão local avalia PutLogEvents contra '*'. Exceção isolada, não usar na AWS.
    compatibility = policy([allow('logs:PutLogEvents', '*')])
    (ROOT/'policies/agente-floci-compat.json').write_text(compatibility, encoding='utf-8')
    iam.put_user_policy(UserName='triagem-agente', PolicyName='FlociCompatLogs', PolicyDocument=compatibility)
    # Floci avalia SetDesiredCapacity contra '*'; o código limita grupo e aprovação.
    compatibility_scale = policy([allow('autoscaling:SetDesiredCapacity', '*')])
    (ROOT/'policies/agente-floci-escala.json').write_text(compatibility_scale, encoding='utf-8')
    iam.put_user_policy(UserName='triagem-agente', PolicyName='FlociCompatEscala', PolicyDocument=compatibility_scale)
    config_path = Path(os.environ.get('AWS_CONFIG_FILE', str(Path.home()/'.aws/config')))
    credentials_path = Path(os.environ.get('AWS_SHARED_CREDENTIALS_FILE', str(Path.home()/'.aws/credentials')))
    config, credentials = configparser.RawConfigParser(), configparser.RawConfigParser()
    config.read(config_path)
    credentials.read(credentials_path)
    valid_profile = False
    if credentials.has_section('triagem-agente'):
        try:
            identity = boto3.Session(profile_name='triagem-agente').client('sts').get_caller_identity()
            valid_profile = identity['Arn'].endswith(':user/triagem-agente') and identity['Account'] == ACCOUNT
        except ClientError:
            pass
    if not valid_profile:
        # Chaves ficam apenas no arquivo local AWS, nunca no repositório ou console.
        key = iam.create_access_key(UserName='triagem-agente')['AccessKey']
        credentials['triagem-agente'] = {'aws_access_key_id': key['AccessKeyId'], 'aws_secret_access_key': key['SecretAccessKey']}
        credentials_path.parent.mkdir(parents=True, exist_ok=True)
        with credentials_path.open('w') as f:
            credentials.write(f)
    config['profile triagem-agente'] = {'region': REGION, 'endpoint_url': s.client('sts').meta.endpoint_url}
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open('w') as f:
        config.write(f)
    print('Implantação local concluída: Lambda, IAM restrito, CPU/alarme, SNS/SQS e agente.')


if __name__ == '__main__':
    main()
