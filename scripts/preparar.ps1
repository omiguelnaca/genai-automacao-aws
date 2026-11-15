param([switch]$SemDocker)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot/..
function Run { param([scriptblock]$Command) & $Command; if ($LASTEXITCODE -ne 0) { throw 'Comando falhou.' } }
if (-not $SemDocker) {
    Run { docker compose up -d }
    Run { docker compose exec -T ollama ollama pull llama3.2 }
    Run { docker compose exec -T ollama ollama pull qwen2.5:3b }
}
Run { aws configure set aws_access_key_id test --profile floci }
Run { aws configure set aws_secret_access_key test --profile floci }
Run { aws configure set region us-east-1 --profile floci }
Run { aws configure set endpoint_url http://localhost:4566 --profile floci }
$env:AWS_PROFILE = 'floci'
Run { python -m venv .venv }
Run { ./.venv/Scripts/python.exe -m pip install -r requirements.txt }
Run { ./.venv/Scripts/cfn-lint.exe iac/vpc.yaml }
Run { ./.venv/Scripts/python.exe scripts/provisionar.py }
