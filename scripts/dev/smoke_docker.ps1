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
    [string]$Body = $null,
    [hashtable]$ExtraHeaders = $null
  )

  try {
    $mergedHeaders = @{}
    $headers.Keys | ForEach-Object { $mergedHeaders[$_] = $headers[$_] }
    if ($ExtraHeaders) {
      $ExtraHeaders.Keys | ForEach-Object { $mergedHeaders[$_] = $ExtraHeaders[$_] }
    }
    if ($Body) {
      $response = Invoke-WebRequest -Method $Method -Uri $Uri -Headers $mergedHeaders `
        -ContentType "application/json" -Body $Body -UseBasicParsing
    } else {
      $response = Invoke-WebRequest -Method $Method -Uri $Uri -Headers $mergedHeaders -UseBasicParsing
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

function Write-ResponseBody {
  param([string]$Label, [string]$Content)
  $display = if ($Content) { $Content } else { "<empty>" }
  Write-Host "$Label $display"
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
Write-Host "Healthz control (host)..."
if (-not (Test-Healthz $controlHealthz)) {
  Write-Host "Suba: docker compose up -d redis control"
  Write-Host "Health check failed: $controlHealthz"
  exit 1
}

$runtimeHealthz = "$runtimeBase/api/v1/runtime/healthz"
Write-Host "Healthz runtime (host)..."
if (-not (Test-Healthz $runtimeHealthz)) {
  Write-Host "Suba: docker compose up -d redis runtime"
  Write-Host "Health check failed: $runtimeHealthz"
  exit 1
}

Write-Host "Control reachable from runtime (container)..."
docker compose exec runtime python -c "import urllib.request; print(urllib.request.urlopen('http://control:8001/api/v1/control/healthz').read().decode())" | Out-Null

Write-Host "Validate bundle..."
$resp = Invoke-JsonRequest -Method Get `
  -Uri "$controlBase/api/v1/control/tenants/demo/bundles/202601050001/validate"
if ($resp.StatusCode -ne 200) { throw "Unexpected status $($resp.StatusCode): $($resp.Content)" }

Write-Host "Set current alias..."
$resp = Invoke-JsonRequest -Method Post `
  -Uri "$controlBase/api/v1/control/tenants/demo/aliases/current" `
  -Body '{"bundle_id":"202601050001"}'
if ($resp.StatusCode -ne 200) { throw "Unexpected status $($resp.StatusCode): $($resp.Content)" }

Write-Host "Ask (alias current)..."
$resp = Invoke-JsonRequest -Method Post `
  -Uri "$runtimeBase/api/v1/runtime/ask" `
  -Body '{"tenant_id":"demo","question":"smoke test docker"}'
if ($resp.StatusCode -ne 200) {
  Write-ResponseBody "Body:" $resp.Content
  throw "Unexpected status $($resp.StatusCode): $($resp.Content)"
}

Write-Host "OK"
