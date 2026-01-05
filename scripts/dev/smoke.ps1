$ErrorActionPreference = "Stop"

$authDisabled = $Env:CONTRACTOR_AUTH_DISABLED
$apiKey = $Env:CONTRACTOR_API_KEY
if (-not $apiKey -or $apiKey -eq "") {
  $apiKey = ($Env:CONTRACTOR_API_KEYS -split ",")[0]
}
$headers = @{}
if ($authDisabled -ne "1") {
  if (-not $apiKey -or $apiKey -eq "") {
    throw "Set CONTRACTOR_API_KEYS (comma-separated) or CONTRACTOR_API_KEY when auth is enabled."
  }
  $headers["X-API-Key"] = $apiKey
}

Write-Host "Healthz runtime..."
Invoke-RestMethod http://localhost:8000/api/v1/runtime/healthz -Headers $headers | Out-Null
Write-Host "Healthz control..."
Invoke-RestMethod http://localhost:8001/api/v1/control/healthz -Headers $headers | Out-Null

Write-Host "Validate bundle..."
Invoke-RestMethod http://localhost:8001/api/v1/control/tenants/demo/bundles/202601050001/validate -Headers $headers | Out-Null

Write-Host "Set current alias..."
Invoke-RestMethod -Method Post -ContentType "application/json" `
  -Uri http://localhost:8001/api/v1/control/tenants/demo/aliases/current `
  -Headers $headers `
  -Body '{"bundle_id":"202601050001"}' | Out-Null

Write-Host "Confirm aliases..."
Invoke-RestMethod http://localhost:8001/api/v1/control/tenants/demo/aliases -Headers $headers | Out-Null

Write-Host "Confirm resolve current..."
Invoke-RestMethod http://localhost:8001/api/v1/control/tenants/demo/resolve/current -Headers $headers | Out-Null

Write-Host "Ask (alias current)..."
Invoke-RestMethod -Method Post -ContentType "application/json" `
  -Uri http://localhost:8000/api/v1/runtime/ask `
  -Headers $headers `
  -Body '{"tenant_id":"demo","question":"smoke test"}' | Out-Null

Write-Host "OK"
