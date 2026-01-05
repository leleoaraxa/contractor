$ErrorActionPreference = "Stop"

Write-Host "Healthz runtime..."
Invoke-RestMethod http://localhost:8000/api/v1/runtime/healthz | Out-Null
Write-Host "Healthz control..."
Invoke-RestMethod http://localhost:8001/api/v1/control/healthz | Out-Null

Write-Host "Validate bundle..."
Invoke-RestMethod http://localhost:8001/api/v1/control/tenants/demo/bundles/202601050001/validate | Out-Null

Write-Host "Set current alias..."
Invoke-RestMethod -Method Post -ContentType "application/json" `
  -Uri http://localhost:8001/api/v1/control/tenants/demo/aliases/current `
  -Body '{"bundle_id":"202601050001"}' | Out-Null

Write-Host "Ask (alias current)..."
Invoke-RestMethod -Method Post -ContentType "application/json" `
  -Uri http://localhost:8000/api/v1/runtime/ask `
  -Body '{"tenant_id":"demo","question":"smoke test"}' | Out-Null

Write-Host "OK"
