param([int]$wait=5)
$base = "http://localhost:3000"
$api = "http://localhost:8000"

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

$script:failed = $false

# 1. Health check all 4 services
Test "POSTGRES pg_isready" {
    $r = docker exec math-platform-postgres-1 pg_isready -U postgres 2>&1
    if ($r -match "accepting connections") { "postgres: accepting connections" } else { throw "Got $r" }
}

Test "REDIS ping" {
    $r = docker exec math-platform-redis-1 redis-cli ping 2>&1
    if ($r -eq "PONG") { "redis: PONG" } else { throw "Got $r" }
}

Test "BACKEND /api/health" {
    $r = Invoke-WebRequest -Uri "$api/api/health" -UseBasicParsing
    if ($r.StatusCode -ne 200) { throw "Got $($r.StatusCode)" }
    $r.Content
}

Test "FRONTEND / (loads)" {
    $r = Invoke-WebRequest -Uri "$base" -UseBasicParsing
    if ($r.StatusCode -ne 200) { throw "Got $($r.StatusCode)" }
    "frontend: $($r.StatusCode)"
}

# 2. Login as student@test.com - get JWT
$loginResp = $null
Test "LOGIN student@test.com" {
    $body = @{ email = "student@test.com"; password = "test123" } | ConvertTo-Json
    $loginResp = Invoke-WebRequest -Uri "$api/api/auth/login" -Method Post -ContentType "application/json" -Body $body -UseBasicParsing
    if ($loginResp.StatusCode -ne 200) { throw "Got $($loginResp.StatusCode)" }
    $data = $loginResp.Content | ConvertFrom-Json
    if (-not $data.access_token) { throw "No access_token in response" }
    $script:token = $data.access_token
    "JWT received: $($token.Substring(0, [Math]::Min(20, $token.Length)))..."
}

# 3. Fetch /api/topics authenticated
Test "GET /api/topics (auth)" {
    $headers = @{ Authorization = "Bearer $token" }
    $r = Invoke-WebRequest -Uri "$api/api/topics" -Headers $headers -UseBasicParsing
    if ($r.StatusCode -ne 200) { throw "Got $($r.StatusCode)" }
    $data = $r.Content | ConvertFrom-Json
    if ($data.Count -eq 0) { throw "Empty topics array" }
    "topics count: $($data.Count)"
}

# 4. Submit exercise attempt (students router mounted at /api/me)
Test "POST /api/me/exercises/535/attempt" {
    $headers = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }
    $body = @{ exercise_id = 535; answer = "3"; attempt_type = "free_response" } | ConvertTo-Json
    $r = Invoke-WebRequest -Uri "$api/api/me/exercises/535/attempt" -Method Post -Headers $headers -Body $body -UseBasicParsing
    if ($r.StatusCode -notmatch "^(200|201)$") { throw "Got $($r.StatusCode): $($r.Content)" }
    $r.Content
}

# 5. Fetch /api/me/achievements
Test "GET /api/me/achievements" {
    $headers = @{ Authorization = "Bearer $token" }
    $r = Invoke-WebRequest -Uri "$api/api/me/achievements" -Headers $headers -UseBasicParsing
    if ($r.StatusCode -ne 200) { throw "Got $($r.StatusCode)" }
    $data = $r.Content | ConvertFrom-Json
    "achievements returned: $($data.Count) items"
}

Write-Host "`n================" -ForegroundColor $(if ($failed) { "Red" } else { "Green" })
if ($failed) {
    Write-Host "SOME TESTS FAILED" -ForegroundColor Red
    exit 1
} else {
    Write-Host "ALL TESTS PASSED" -ForegroundColor Green
    exit 0
}