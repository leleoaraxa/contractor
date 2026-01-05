$ErrorActionPreference = "Stop"

function Test-AuthDisabled([string]$value) {
  if (-not $value) { return $false }
  $normalized = $value.Trim().ToLower()
  return @("1", "true", "yes", "y", "on").Contains($normalized)
}

function Get-ApiKey() {
  param([string]$candidate)
  if (-not $candidate) { return "" }
  $parts = $candidate -split ","
  foreach ($p in $parts) {
    $trimmed = $p.Trim()
    if ($trimmed) { return $trimmed }
  }
  return ""
}

$authDisabled = Test-AuthDisabled $Env:CONTRACTOR_AUTH_DISABLED
$apiKey = Get-ApiKey $Env:CONTRACTOR_API_KEY
if (-not $apiKey) {
  $apiKey = Get-ApiKey $Env:CONTRACTOR_API_KEYS
}

$headers = @{}
if (-not $authDisabled) {
  if (-not $apiKey) {
    throw "Set CONTRACTOR_API_KEYS (comma-separated) or CONTRACTOR_API_KEY when auth is enabled."
  }
  $headers["X-API-Key"] = $apiKey
}

Write-Host "Healthz runtime (host)..."
Invoke-RestMethod http://localhost:8000/api/v1/runtime/healthz -Headers $headers | Out-Null

Write-Host "Healthz control (host)..."
Invoke-RestMethod http://localhost:8001/api/v1/control/healthz -Headers $headers | Out-Null

Write-Host "Control reachable from runtime (container)..."
docker compose exec runtime python -c "import urllib.request; print(urllib.request.urlopen('http://control:8001/api/v1/control/healthz').read().decode())" | Out-Null

Write-Host "Validate bundle..."
Invoke-RestMethod http://localhost:8001/api/v1/control/tenants/demo/bundles/202601050001/validate -Headers $headers | Out-Null

Write-Host "Set current alias..."
Invoke-RestMethod -Method Post -ContentType "application/json" `
  -Uri http://localhost:8001/api/v1/control/tenants/demo/aliases/current `
  -Headers $headers `
  -Body '{"bundle_id":"202601050001"}' | Out-Null

Write-Host "Ask (alias current)..."
Invoke-RestMethod -Method Post -ContentType "application/json" `
  -Uri http://localhost:8000/api/v1/runtime/ask `
  -Headers $headers `
  -Body '{"tenant_id":"demo","question":"smoke test docker"}' | Out-Null

Write-Host "OK"
