$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:DJANGO_READ_DOT_ENV_FILE = 'True'
docker compose -f compose.database.yml up -d --wait
if ($LASTEXITCODE -ne 0) { throw 'No se pudo iniciar PostgreSQL. Verifica Docker Desktop.' }
& "$PSScriptRoot\.venv\Scripts\python.exe" manage.py migrate --noinput
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron aplicar las migraciones.' }
& "$PSScriptRoot\.venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000
