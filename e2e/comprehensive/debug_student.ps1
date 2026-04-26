$api = "https://lucid-serenity-production.up.railway.app"
$headers = @{ "Content-Type" = "application/json" }
$login = Invoke-WebRequest -Uri "$api/api/auth/login" -Method Post -Headers $headers -Body (@{email="student_01@test.com";password="test123"}|ConvertTo-Json) -UseBasicParsing -TimeoutSec 15
$token = ($login.Content | ConvertFrom-Json).access_token
$h = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }

# Test various endpoints to find the issue
$tests = @(
  @{ name = "progress"; url = "$api/api/me/progress"; method = "GET" },
  @{ name = "achievements"; url = "$api/api/me/achievements"; method = "GET" },
  @{ name = "classes"; url = "$api/api/me/classes"; method = "GET" },
  @{ name = "stats"; url = "$api/api/me/stats/me"; method = "GET" }
)

foreach ($t in $tests) {
  try {
    if ($t.method -eq "GET") {
      $r = Invoke-WebRequest -Uri $t.url -Method Get -Headers $h -UseBasicParsing -TimeoutSec 15
    } else {
      $r = Invoke-WebRequest -Uri $t.url -Method Post -Headers $h -UseBasicParsing -TimeoutSec 15
    }
    Write-Host "$($t.name): $($r.StatusCode)" -ForegroundColor Green
  } catch {
    Write-Host "$($t.name): ERROR - $($_.Exception.Message.Split("`n")[0])" -ForegroundColor Red
  }
}

# Try linking with a direct test
$linkCode = "TEST01"
$linkBody = @{ link_code = $linkCode } | ConvertTo-Json
try {
    $r = Invoke-WebRequest -Uri "$api/api/me/link-parent" -Method Post -Headers $h -Body $linkBody -UseBasicParsing -TimeoutSec 15
    Write-Host "link-parent (test code): $($r.StatusCode) - $($r.Content)"
} catch {
    Write-Host "link-parent (test code): ERROR - $($_.Exception.Message.Split("`n")[0])" -ForegroundColor Red
}

# Check debug endpoint
try {
    $r = Invoke-WebRequest -Uri "$api/debug/login-test" -UseBasicParsing -TimeoutSec 15
    Write-Host "`nDebug info:"
    Write-Host $r.Content
} catch {
    Write-Host "debug: $($_.Exception.Message)"
}