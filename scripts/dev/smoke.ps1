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

function Normalize-Base([string]$base, [string[]]$suffixes) {
  $trimmed = $base.TrimEnd("/")
  foreach ($suffix in $suffixes) {
    if ($trimmed.EndsWith($suffix)) {
      $trimmed = $trimmed.Substring(0, $trimmed.Length - $suffix.Length).TrimEnd("/")
      break
    }
  }
  return $trimmed
}

$controlBase = Normalize-Base $controlBase @("/api/v1/control/healthz", "/api/v1/control")
$runtimeBase = Normalize-Base $runtimeBase @("/api/v1/runtime/healthz", "/api/v1/runtime")
$headers = @{}
if (-not $authDisabled) {
  if (-not $apiKey) {
    $apiKey = "dev-key"
    Write-Warning "CONTRACTOR_API_KEY(S) not set; using fallback dev-key."
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
        -ContentType "application/json" -Body $Body -UseBasicParsing
    } else {
      $response = Invoke-WebRequest -Method $Method -Uri $Uri -Headers $headers -UseBasicParsing
    }
    return [pscustomobject]@{ StatusCode = $response.StatusCode; Content = $response.Content }
  } catch {
    $resp = $_.Exception.Response
    $status = if ($resp) { [int]$resp.StatusCode } else { 0 }
    $content = ""
    if ($resp) {
      try {
        $stream = $resp.GetResponseStream()
        if ($stream) {
          $reader = New-Object System.IO.StreamReader($stream)
          $content = $reader.ReadToEnd()
        }
      } catch {
      }
    }
    if (-not $content -and $_.ErrorDetails -and $_.ErrorDetails.Message) {
      $content = $_.ErrorDetails.Message
    }
    return [pscustomobject]@{ StatusCode = $status; Content = $content }
  }
}

function Test-Healthz {
  param([string]$Uri)
  try {
    Invoke-WebRequest -Method Get -Uri $Uri -Headers $headers -UseBasicParsing | Out-Null
    return $true
  } catch {
    return $false
  }
}

$controlHealthz = "$controlBase/api/v1/control/healthz"
if (-not (Test-Healthz $controlHealthz)) {
  Write-Host "Suba: docker compose up -d redis control"
  Write-Host "Health check failed: $controlHealthz"
  exit 1
}
$runtimeHealthz = "$runtimeBase/api/v1/runtime/healthz"
if (-not (Test-Healthz $runtimeHealthz)) {
  Write-Host "Suba: docker compose up -d redis runtime"
  Write-Host "Health check failed: $runtimeHealthz"
  exit 1
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
$parsed = $null
try {
  $parsed = $resp.Content | ConvertFrom-Json
} catch {
  Write-Warning "Failed to parse JSON response: $($resp.Content)"
}
$detail = if ($parsed) { $parsed.detail } else { $null }
$detailObj = $null
if ($detail -is [string]) {
  try {
    $detailObj = $detail | ConvertFrom-Json
  } catch {
    $detailObj = $null
  }
} elseif ($detail) {
  $detailObj = $detail
}
if (-not $detailObj -or $detailObj.gate -ne "template_safety") {
  throw "Unexpected gate: $($resp.Content)"
}
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
