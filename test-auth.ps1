# Test login and get token
$headers = @{"Content-Type" = "application/json"}
$body = '{"email":"student@test.com","password":"Test123"}'
$result = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method POST -Headers $headers -Body $body
$token = $result.access_token
Write-Host "Token acquired: $($token.Substring(0, [Math]::Min(30, $token.Length)))..."

# Test auth-required endpoints
$authHeaders = @{"Authorization" = "Bearer $token"}

Write-Host "`n=== MY PROGRESS ==="
try { Invoke-RestMethod -Uri "http://localhost:8000/api/me/progress" -Method GET -Headers $authHeaders } catch { Write-Host "Error: $_" }

Write-Host "`n=== LEADERBOARD ==="
try { Invoke-RestMethod -Uri "http://localhost:8000/api/leaderboard/global?limit=5" -Method GET } catch { Write-Host "Error: $_" }

Write-Host "`n=== TOPICS ==="
try { Invoke-RestMethod -Uri "http://localhost:8000/api/topics" -Method GET } catch { Write-Host "Error: $_" }

Write-Host "`n=== EXERCISES ==="
try { Invoke-RestMethod -Uri "http://localhost:8000/api/exercises/1" -Method GET } catch { Write-Host "Error: $_" }

Write-Host "`n=== LOGOUT ==="
try { Invoke-RestMethod -Uri "http://localhost:8000/api/auth/logout" -Method POST -Headers $authHeaders } catch { Write-Host "Error: $_" }