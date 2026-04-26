$api = "https://lucid-serenity-production.up.railway.app"
$frontend = "https://proactive-wisdom-production-cd0e.up.railway.app"
$failed = $false

function Test($name, $script) {
    Write-Host "`n[$name]" -ForegroundColor Cyan
    try {
        $result = & $script
        Write-Host "  PASS" -ForegroundColor Green
        $result
    } catch {
        Write-Host "  FAIL: $_" -ForegroundColor Red
        $script:failed = $true
    }
}

Test "BACKEND /api/health" {
    $r = Invoke-WebRequest -Uri "$api/api/health" -UseBasicParsing -TimeoutSec 15
    if ($r.StatusCode -ne 200) { throw "Got $($r.StatusCode)" }
    $r.Content
}

Test "LOGIN student@test.com" {
    $body = @{ email = "student@test.com"; password = "test123" } | ConvertTo-Json
    $resp = Invoke-WebRequest -Uri "$api/api/auth/login" -Method Post -ContentType "application/json" -Body $body -UseBasicParsing -TimeoutSec 15
    if ($resp.StatusCode -ne 200) { throw "Got $($resp.StatusCode)" }
    $data = $resp.Content | ConvertFrom-Json
    if (-not $data.access_token) { throw "No access_token" }
    $script:token = $data.access_token
    "JWT: $($token.Substring(0, [Math]::Min(15, $token.Length)))..."
}

Test "GET /api/topics (auth)" {
    $headers = @{ Authorization = "Bearer $token" }
    $r = Invoke-WebRequest -Uri "$api/api/topics" -Headers $headers -UseBasicParsing -TimeoutSec 15
    if ($r.StatusCode -ne 200) { throw "Got $($r.StatusCode)" }
    $data = $r.Content | ConvertFrom-Json
    "topics: $($data.Count)"
}

Test "POST /api/me/exercises/1/attempt" {
    $headers = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }
    $body = @{ exercise_id = 1; answer = "3"; attempt_type = "free_response" } | ConvertTo-Json
    $r = Invoke-WebRequest -Uri "$api/api/me/exercises/1/attempt" -Method Post -Headers $headers -Body $body -UseBasicParsing -TimeoutSec 15
    if ($r.StatusCode -notmatch "^(200|201)$") { throw "Got $($r.StatusCode): $($r.Content)" }
    $r.Content | ConvertFrom-Json | Select-Object -ExpandProperty correct
}

Test "GET /api/me/achievements" {
    $headers = @{ Authorization = "Bearer $token" }
    $r = Invoke-WebRequest -Uri "$api/api/me/achievements" -Headers $headers -UseBasicParsing -TimeoutSec 15
    if ($r.StatusCode -ne 200) { throw "Got $($r.StatusCode)" }
    $data = $r.Content | ConvertFrom-Json
    "achievements: $($data.Count)"
}

Test "FRONTEND /api/health" {
    $r = Invoke-WebRequest -Uri "$frontend/api/health" -UseBasicParsing -TimeoutSec 15
    if ($r.StatusCode -ne 200) { throw "Got $($r.StatusCode)" }
    $r.Content
}

Test "FRONTEND loads login page" {
    $r = Invoke-WebRequest -Uri "$frontend/login" -UseBasicParsing -TimeoutSec 15
    if ($r.StatusCode -ne 200) { throw "Got $($r.StatusCode)" }
    if ($r.Content -notmatch "Iniciar") { throw "No login text found" }
    "login page OK"
}

Write-Host "`n================" -ForegroundColor $(if ($failed) { "Red" } else { "Green" })
if ($failed) {
    Write-Host "SOME TESTS FAILED" -ForegroundColor Red; exit 1
} else {
    Write-Host "ALL TESTS PASSED" -ForegroundColor Green; exit 0
}