Param(
  [Parameter(Mandatory=$false)][string]$TenantId = "demo",
  [Parameter(Mandatory=$false)][string]$ControlBase = "http://localhost:8001",
  [Parameter(Mandatory=$false)][string]$RuntimeBase = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"

function Get-Json($Url) {
  return Invoke-RestMethod -Method Get -Uri $Url
}

function Post-Json($Url, $Body) {
  return Invoke-RestMethod -Method Post -Uri $Url -ContentType "application/json" -Body ($Body | ConvertTo-Json)
}

Write-Host "Resolve candidate..."
$cand = Get-Json "$ControlBase/api/v1/control/tenants/$TenantId/resolve/candidate"
$candidateBundle = $cand.bundle_id
if (-not $candidateBundle) { throw "candidate bundle not set" }

Write-Host "Read current (for rollback)..."
$cur = Get-Json "$ControlBase/api/v1/control/tenants/$TenantId/resolve/current"
$previousCurrent = $cur.bundle_id
if (-not $previousCurrent) { throw "current bundle not set" }

Write-Host "Validate candidate bundle..."
$val = Get-Json "$ControlBase/api/v1/control/tenants/$TenantId/bundles/$candidateBundle/validate"
if ($val.status -ne "pass") {
  throw ("validate failed: " + ($val.errors | ConvertTo-Json -Depth 8))
}

Write-Host "Run promotion suites against release_alias=candidate..."
# Promotion set: start with routing suites (Stage 1). Expand later.
$promotionSuites = @(
  "data/quality/suites/demo_thresholds_suite.json"
)

foreach ($suite in $promotionSuites) {
  $out = python scripts/quality/run_routing_suite.py --base-url $RuntimeBase --suite $suite | ConvertFrom-Json
  if ($out.passed -ne $out.total) {
    throw ("suite failed: " + ($out | ConvertTo-Json -Depth 8))
  }
  Write-Host ("OK " + $out.suite_id + " " + $out.passed + "/" + $out.total)
}

Write-Host "Promote: set current = candidate bundle..."
$set = Post-Json "$ControlBase/api/v1/control/tenants/$TenantId/aliases/current" @{ bundle_id = $candidateBundle }
Write-Host ("Current is now: " + $set.current)

Write-Host "Promotion complete."
Write-Host ("Rollback command (if needed): POST $ControlBase/api/v1/control/tenants/$TenantId/aliases/current { bundle_id: $previousCurrent }")
