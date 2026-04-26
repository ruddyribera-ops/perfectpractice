$api = "https://lucid-serenity-production.up.railway.app"
$body = @{ email = "profesor_e2e@test.com"; password = "test123" } | ConvertTo-Json
$login = Invoke-WebRequest -Uri "$api/api/auth/login" -Method Post -ContentType "application/json" -Body $body -UseBasicParsing -TimeoutSec 15
$token = ($login.Content | ConvertFrom-Json).access_token
$h = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }
# Try /api/classes with explicit body
$jsonBody = '{"name":"3ro Primaria A","subject":"Matematicas"}'
try {
    $classResp = Invoke-WebRequest -Uri "$api/api/classes" -Method Post -Headers $h -Body $jsonBody -UseBasicParsing -TimeoutSec 15
    Write-Host "Status: $($classResp.StatusCode)"
    Write-Host "Content: $($classResp.Content)"
} catch {
    Write-Host "ERROR: $($_.Exception.Message)"
    # Try GET to see what routes exist
    $getResp = Invoke-WebRequest -Uri "$api/api/classes" -Method Get -Headers $h -UseBasicParsing -TimeoutSec 15
    Write-Host "GET /api/classes: $($getResp.StatusCode) - $($getResp.Content)"
}