import json, urllib.request
url='https://knowledge-mcp.global.api.aws'
def call(method, params={}):
    request=urllib.request.Request(url,data=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode(),headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream','MCP-Protocol-Version':'2025-03-26'})
    with urllib.request.urlopen(request,timeout=30) as response:
        body=response.read().decode()
    if body.startswith('event:') or body.startswith('data:'):
        body=next(line[5:].strip() for line in body.splitlines() if line.startswith('data:'))
    return json.loads(body)
if __name__=='__main__':
    print(json.dumps(call('tools/list'),ensure_ascii=True))
