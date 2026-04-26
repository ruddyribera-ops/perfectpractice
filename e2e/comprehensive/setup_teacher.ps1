$ErrorActionPreference = 'Stop'
$api = "https://lucid-serenity-production.up.railway.app"
$headers = @{ "Content-Type" = "application/json" }

function Register($email, $name, $role, $password = "test123", $grade) {
    $body = @{ email = $email; name = $name; password = $password; role = $role }
    if ($grade) { $body.grade = $grade }
    $body = $body | ConvertTo-Json
    $resp = Invoke-WebRequest -Uri "$api/api/auth/register" -Method Post -Headers $headers -Body $body -UseBasicParsing -TimeoutSec 30
    if ($resp.StatusCode -notmatch "^(200|201)$") { throw "Register failed for $email : $($resp.StatusCode) $($resp.Content)" }
    return ($resp.Content | ConvertFrom-Json)
}

function Login($email, $password = "test123") {
    $body = @{ email = $email; password = $password } | ConvertTo-Json
    $resp = Invoke-WebRequest -Uri "$api/api/auth/login" -Method Post -Headers $headers -Body $body -UseBasicParsing -TimeoutSec 30
    if ($resp.StatusCode -notmatch "^(200|201)$") { throw "Login failed for $email : $($resp.StatusCode)" }
    return ($resp.Content | ConvertFrom-Json)
}

Write-Host "=== PHASE 1.1: Create Teacher + Class ===" -ForegroundColor Cyan

# Register teacher
try {
    $t = Register "profesor_e2e@test.com" "Profesor E2E" "teacher"
    Write-Host "[OK] Teacher registered: profesor_e2e@test.com"
} catch {
    Write-Host "[WARN] Teacher may already exist: $_" -ForegroundColor Yellow
    $t = Login "profesor_e2e@test.com"
    Write-Host "[OK] Teacher logged in"
}
$teacherToken = $t.access_token
$teacherHeaders = @{ Authorization = "Bearer $teacherToken"; "Content-Type" = "application/json" }

# Create class
$classBody = @{ name = "3ro Primaria A"; subject = "Matemáticas" } | ConvertTo-Json
$classResp = Invoke-WebRequest -Uri "$api/api/teachers/classes" -Method Post -Headers $teacherHeaders -Body $classBody -UseBasicParsing -TimeoutSec 30
if ($classResp.StatusCode -notmatch "^(200|201)$") { throw "Create class failed: $($classResp.StatusCode) $($classResp.Content)" }
$classData = $classResp.Content | ConvertFrom-Json
$classId = $classData.id
$inviteCode = $classData.invite_code
Write-Host "[OK] Class created: ID=$classId, invite=$inviteCode"

# Verify class
$verify = Invoke-WebRequest -Uri "$api/api/teachers/classes" -Headers $teacherHeaders -UseBasicParsing -TimeoutSec 15
$classes = ($verify.Content | ConvertFrom-Json)
$found = $classes | Where-Object { $_.id -eq $classId }
Write-Host "[OK] Class verified: $($found.name) (subject: $($found.subject))"

# Save for next phase
@{
    teacherToken = $teacherToken
    teacherHeaders = $teacherHeaders.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" } -join ","
    classId = $classId
    inviteCode = $inviteCode
} | ConvertTo-Json | Out-File -FilePath "C:/Users/Windows/math-platform/e2e/comprehensive/.setup_teacher.json" -Encoding UTF8

Write-Host "`n=== PHASE 1.1 COMPLETE ===" -ForegroundColor Green