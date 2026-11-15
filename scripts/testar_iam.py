"""Teste reproduzível de leitura permitida e escrita negada no Floci."""
import json
from pathlib import Path
import uuid
import boto3
from botocore.exceptions import ClientError

ROOT = Path(__file__).resolve().parents[1]
s = boto3.Session(profile_name='floci')
assert s.client('sts').get_caller_identity()['Account']=='000000000000'
iam,s3 = s.client('iam'),s.client('s3')
try: s3.create_bucket(Bucket='relatorios')
except ClientError as e:
    if e.response['Error']['Code'] not in ['BucketAlreadyExists','BucketAlreadyOwnedByYou']: raise
user = 'leitor-teste-'+uuid.uuid4().hex[:8]
name = user+'.txt'
s3.put_object(Bucket='relatorios',Key=name,Body=b'Relatorio de teste sem dados pessoais.')
iam.create_user(UserName=user)
key = None
result = {}
try:
    iam.put_user_policy(UserName=user,PolicyName='Leitura',PolicyDocument=(ROOT/'policies/leitura-relatorios.json').read_text())
    key = iam.create_access_key(UserName=user)['AccessKey']
    restricted = boto3.client('s3',region_name='us-east-1',endpoint_url=s3.meta.endpoint_url,
        aws_access_key_id=key['AccessKeyId'],aws_secret_access_key=key['SecretAccessKey'])
    body = restricted.get_object(Bucket='relatorios',Key=name)['Body']
    try: result['get_permitido'] = bool(body.read())
    finally: body.close()
    try:
        restricted.put_object(Bucket='relatorios',Key=name+'-negado',Body=b'Teste')
        result['put_negado'] = False
    except ClientError as e: result['put_negado'] = e.response['Error']['Code']=='AccessDenied'
finally:
    if key: iam.delete_access_key(UserName=user,AccessKeyId=key['AccessKeyId'])
    iam.delete_user_policy(UserName=user,PolicyName='Leitura')
    iam.delete_user(UserName=user)
    s3.delete_object(Bucket='relatorios',Key=name)
    s3.delete_object(Bucket='relatorios',Key=name+'-negado')
(ROOT/'docs/evidencias/iam.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(result)
assert result and all(result.values())
