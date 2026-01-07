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
$controlBase = if ($Env:CONTROL_BASE_URL) { $Env:CONTROL_BASE_URL } else { "http://localhost:8001" }
$runtimeBase = if ($Env:RUNTIME_BASE_URL) { $Env:RUNTIME_BASE_URL } else { "http://localhost:8000" }

function Normalize-Base([string]$base, [string]$suffix) {
  $trimmed = $base.TrimEnd("/")
  if ($trimmed.EndsWith($suffix)) {
    $trimmed = $trimmed.Substring(0, $trimmed.Length - $suffix.Length).TrimEnd("/")
  }
  return $trimmed
}

$controlBase = Normalize-Base $controlBase "/api/v1/control"
$runtimeBase = Normalize-Base $runtimeBase "/api/v1/runtime"
$headers = @{}
if (-not $authDisabled) {
  if (-not $apiKey) {
    throw "Set CONTRACTOR_API_KEYS (comma-separated) or CONTRACTOR_API_KEY when auth is enabled."
  }
  $headers["X-API-Key"] = $apiKey
}

function Invoke-JsonRequest {
  param(
    [string]$Method,
    [string]$Uri,
    [string]$Body = $null
  )

  try {
    if ($Body) {
      $response = Invoke-WebRequest -Method $Method -Uri $Uri -Headers $headers `
        -ContentType "application/json" -Body $Body
    } else {
      $response = Invoke-WebRequest -Method $Method -Uri $Uri -Headers $headers
    }
    return [pscustomobject]@{ StatusCode = $response.StatusCode; Content = $response.Content }
  } catch {
    $resp = $_.Exception.Response
    $status = if ($resp) { [int]$resp.StatusCode } else { 0 }
    $content = ""
    if ($resp -and $resp.GetResponseStream()) {
      $reader = New-Object System.IO.StreamReader($resp.GetResponseStream())
      $content = $reader.ReadToEnd()
    }
    return [pscustomobject]@{ StatusCode = $status; Content = $content }
  }
}

python scripts/quality/smoke_quality_gate.py `
  --tenant-id demo `
  --control-base $controlBase `
  --runtime-base $runtimeBase

Write-Host "Promotion PASS (bundle 202601050001)..."
$resp = Invoke-JsonRequest -Method Post -Uri "$controlBase/api/v1/control/tenants/demo/aliases/candidate" `
  -Body '{"bundle_id":"202601050001"}'
if ($resp.StatusCode -ne 200) { throw "Unexpected status $($resp.StatusCode): $($resp.Content)" }
$candidate = ($resp.Content | ConvertFrom-Json).candidate
if ($candidate -ne "202601050001") { throw "Unexpected candidate: $($resp.Content)" }

$resp = Invoke-JsonRequest -Method Post -Uri "$controlBase/api/v1/control/tenants/demo/aliases/current" `
  -Body '{"bundle_id":"202601050001"}'
if ($resp.StatusCode -ne 200) { throw "Unexpected status $($resp.StatusCode): $($resp.Content)" }
$current = ($resp.Content | ConvertFrom-Json).current
if ($current -ne "202601050001") { throw "Unexpected current: $($resp.Content)" }
Write-Host "Promotion PASS OK"

Write-Host "Promotion FAIL (template safety, bundle 202601050002)..."
$resp = Invoke-JsonRequest -Method Post -Uri "$controlBase/api/v1/control/tenants/demo/aliases/candidate" `
  -Body '{"bundle_id":"202601050002"}'
if ($resp.StatusCode -ne 400) { throw "Unexpected status $($resp.StatusCode): $($resp.Content)" }
$detail = ($resp.Content | ConvertFrom-Json).detail
if ($detail.gate -ne "template_safety") { throw "Unexpected gate: $($resp.Content)" }
Write-Host "Template safety gate OK"

Write-Host "Rate limit enforcement (bundle 202601050003)..."
$askPayload = '{"tenant_id":"demo","question":"smoke test","bundle_id":"202601050003","release_alias":"current"}'
$resp = Invoke-JsonRequest -Method Post -Uri "$runtimeBase/api/v1/runtime/ask" -Body $askPayload
if ($resp.StatusCode -ne 200) { throw "Unexpected status $($resp.StatusCode): $($resp.Content)" }
$resp = Invoke-JsonRequest -Method Post -Uri "$runtimeBase/api/v1/runtime/ask" -Body $askPayload
if ($resp.StatusCode -ne 429) { throw "Unexpected status $($resp.StatusCode): $($resp.Content)" }
$detail = ($resp.Content | ConvertFrom-Json).detail
if ($detail.error -ne "rate_limit_exceeded") { throw "Unexpected detail: $($resp.Content)" }
Write-Host "Rate limit OK"

Write-Host "OK"
