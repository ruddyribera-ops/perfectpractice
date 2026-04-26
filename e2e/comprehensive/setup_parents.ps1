$ErrorActionPreference = 'Stop'
$api = "https://lucid-serenity-production.up.railway.app"
$headers = @{ "Content-Type" = "application/json" }

function Register($email, $name, $role, $password = "test123") {
    $body = @{ email = $email; name = $name; password = $password; role = $role } | ConvertTo-Json
    $resp = Invoke-WebRequest -Uri "$api/api/auth/register" -Method Post -Headers $headers -Body $body -UseBasicParsing -TimeoutSec 30
    $status = $resp.StatusCode
    if ($status -notmatch "^(200|201)$") {
        if ($resp.Content -match "already registered") { return @{ already = $true } }
        throw "Register failed for $email : $status $($resp.Content)"
    }
    return @{ already = $false; data = ($resp.Content | ConvertFrom-Json) }
}

function Login($email, $password = "test123") {
    $body = @{ email = $email; password = $password } | ConvertTo-Json
    $resp = Invoke-WebRequest -Uri "$api/api/auth/login" -Method Post -Headers $headers -Body $body -UseBasicParsing -TimeoutSec 30
    return ($resp.Content | ConvertFrom-Json)
}

function GenerateParentCode($token) {
    $h = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }
    $resp = Invoke-WebRequest -Uri "$api/api/parents/generate-code" -Method Post -Headers $h -UseBasicParsing -TimeoutSec 15
    if ($resp.StatusCode -notmatch "^(200|201)$") { throw "Generate code failed: $($resp.StatusCode) $($resp.Content)" }
    return ($resp.Content | ConvertFrom-Json).link_code
}

function StudentLinkParent($token, $linkCode) {
    $h = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }
    $body = @{ link_code = $linkCode } | ConvertTo-Json
    $resp = Invoke-WebRequest -Uri "$api/api/me/link-parent" -Method Post -Headers $h -Body $body -UseBasicParsing -TimeoutSec 15
    return $resp.StatusCode
}

Write-Host "=== PHASE 1.3: Create 3 Parents + Link to Students ===" -ForegroundColor Cyan

# Create 3 parent accounts
$parents = @()
for ($i = 1; $i -le 3; $i++) {
    $email = "parent_0$($i)@test.com"
    $reg = Register $email "Parent $i" "parent"
    if ($reg.already) { Write-Host "[SKIP] $email already exists" -ForegroundColor DarkGray }
    else { Write-Host "[OK] Parent registered: $email" -ForegroundColor Green }
    $parents += $email
}

# Load student tokens
$studentTokens = Get-Content "C:/Users/Windows/math-platform/e2e/comprehensive/.student_tokens.json" | ConvertFrom-Json

# Parent 1 links to students 01-07
Write-Host "`n--- Parent 1 linking students 01-07 ---" -ForegroundColor Yellow
$p1 = Login $parents[0]
$p1Code = GenerateParentCode $p1.access_token
Write-Host "Parent 1 code: $p1Code" -ForegroundColor Cyan
for ($i = 0; $i -lt 7; $i++) {
    $st = $studentTokens[$i].token
    $status = StudentLinkParent $st $p1Code
    if ($status -match "^(200|201)$") { Write-Host "[OK] Linked student $($i+1)" -ForegroundColor Green }
    else { Write-Host "[WARN] Status $status for student $($i+1)" -ForegroundColor Yellow }
}

# Parent 2 links to students 08-14
Write-Host "`n--- Parent 2 linking students 08-14 ---" -ForegroundColor Yellow
$p2 = Login $parents[1]
$p2Code = GenerateParentCode $p2.access_token
Write-Host "Parent 2 code: $p2Code" -ForegroundColor Cyan
for ($i = 7; $i -lt 14; $i++) {
    $st = $studentTokens[$i].token
    $status = StudentLinkParent $st $p2Code
    if ($status -match "^(200|201)$") { Write-Host "[OK] Linked student $($i+1)" -ForegroundColor Green }
    else { Write-Host "[WARN] Status $status for student $($i+1)" -ForegroundColor Yellow }
}

# Parent 3 links to students 15-21
Write-Host "`n--- Parent 3 linking students 15-21 ---" -ForegroundColor Yellow
$p3 = Login $parents[2]
$p3Code = GenerateParentCode $p3.access_token
Write-Host "Parent 3 code: $p3Code" -ForegroundColor Cyan
for ($i = 14; $i -lt 21; $i++) {
    $st = $studentTokens[$i].token
    $status = StudentLinkParent $st $p3Code
    if ($status -match "^(200|201)$") { Write-Host "[OK] Linked student $($i+1)" -ForegroundColor Green }
    else { Write-Host "[WARN] Status $status for student $($i+1)" -ForegroundColor Yellow }
}

# Verify: check parent 1 dashboard
$p1 = Login $parents[0]
$p1Headers = @{ Authorization = "Bearer $($p1.access_token)"; "Content-Type" = "application/json" }
$dashResp = Invoke-WebRequest -Uri "$api/api/parents/me" -Method Get -Headers $p1Headers -UseBasicParsing -TimeoutSec 15
$dash = $dashResp.Content | ConvertFrom-Json
Write-Host "`n[VERIFY] Parent 1 sees $($dash.linked_students.Count) linked students" -ForegroundColor Cyan

Write-Host "`n=== PHASE 1.3 COMPLETE ===" -ForegroundColor Green