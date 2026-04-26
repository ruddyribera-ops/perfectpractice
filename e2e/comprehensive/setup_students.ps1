$ErrorActionPreference = 'Stop'
$api = "https://lucid-serenity-production.up.railway.app"
$headers = @{ "Content-Type" = "application/json" }
$inviteCode = "OrPI6HlLNEI"

# Re-login as teacher to get token
$teacherLogin = Invoke-WebRequest -Uri "$api/api/auth/login" -Method Post -Headers $headers -Body (@{ email = "profesor_e2e@test.com"; password = "test123" } | ConvertTo-Json) -UseBasicParsing -TimeoutSec 15
$teacherToken = ($teacherLogin.Content | ConvertFrom-Json).access_token

function Register($email, $name, $role, $password = "test123", $grade) {
    $body = @{ email = $email; name = $name; password = $password; role = $role }
    if ($grade) { $body.grade = $grade }
    $body = $body | ConvertTo-Json
    $resp = Invoke-WebRequest -Uri "$api/api/auth/register" -Method Post -Headers $headers -Body $body -UseBasicParsing -TimeoutSec 30
    $status = $resp.StatusCode
    if ($status -notmatch "^(200|201)$") {
        if ($resp.Content -match "already registered") {
            return @{ already = $true }
        }
        throw "Register failed for $email : $status $($resp.Content)"
    }
    return @{ already = $false; data = ($resp.Content | ConvertFrom-Json) }
}

function Login($email, $password = "test123") {
    $body = @{ email = $email; password = $password } | ConvertTo-Json
    $resp = Invoke-WebRequest -Uri "$api/api/auth/login" -Method Post -Headers $headers -Body $body -UseBasicParsing -TimeoutSec 30
    if ($resp.StatusCode -notmatch "^(200|201)$") { throw "Login failed for $email : $($resp.StatusCode)" }
    return ($resp.Content | ConvertFrom-Json)
}

function JoinClass($token, $code) {
    $h = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }
    $resp = Invoke-WebRequest -Uri "$api/api/classes/join/$code" -Method Post -Headers $h -UseBasicParsing -TimeoutSec 15
    return $resp.StatusCode
}

Write-Host "=== PHASE 1.2: Create 21 Students + Enroll ===" -ForegroundColor Cyan

$results = @()
for ($i = 1; $i -le 21; $i++) {
    $num = $i.ToString("00")
    $email = "student_$($num)@test.com"
    $name = "Estudiante $num"
    $grade = 3

    $reg = Register $email $name "student" "test123" $grade
    if ($reg.already) {
        Write-Host "[SKIP] $email already exists" -ForegroundColor DarkGray
    } else {
        Write-Host "[OK]   Registered: $email" -ForegroundColor Green
    }

    # Login
    $login = Login $email
    $token = $login.access_token

    # Join class
    $status = JoinClass $token $inviteCode
    if ($status -match "^(200|201)$") {
        Write-Host "[OK]   Enrolled: $email" -ForegroundColor Green
    } elseif ($status -eq 400 -and $login.Content -match "Already enrolled") {
        Write-Host "[OK]   Already enrolled: $email" -ForegroundColor DarkGray
    } else {
        Write-Host "[WARN] Enroll status $status for $email" -ForegroundColor Yellow
    }

    $results += @{ email = $email; token = $token }
}

# Save tokens for later use
$results | ConvertTo-Json | Out-File -FilePath "C:/Users/Windows/math-platform/e2e/comprehensive/.student_tokens.json" -Encoding UTF8

# Verify with teacher
$h = @{ Authorization = "Bearer $teacherToken"; "Content-Type" = "application/json" }
$classResp = Invoke-WebRequest -Uri "$api/api/teachers/classes" -Method Get -Headers $h -UseBasicParsing -TimeoutSec 15
$classes = ($classResp.Content | ConvertFrom-Json)
$class1 = $classes | Where-Object { $_.name -eq "3ro Primaria A" }
Write-Host "`n[VERIFY] Class '3ro Primaria A' has $($class1.student_count) students enrolled" -ForegroundColor Cyan

Write-Host "`n=== PHASE 1.2 COMPLETE ===" -ForegroundColor Green