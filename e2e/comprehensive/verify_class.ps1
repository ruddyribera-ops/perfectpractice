$api = "https://lucid-serenity-production.up.railway.app"
$loginResp = Invoke-WebRequest -Uri "$api/api/auth/login" -Method Post -ContentType "application/json" -Body (@{email="profesor_e2e@test.com";password="test123"}|ConvertTo-Json) -UseBasicParsing -TimeoutSec 15
$token = ($loginResp.Content | ConvertFrom-Json).access_token
$h = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }

$resp = Invoke-WebRequest -Uri "$api/api/classes" -Method Get -Headers $h -UseBasicParsing -TimeoutSec 15
$classes = ($resp.Content | ConvertFrom-Json)
$classes | ForEach-Object {
    Write-Host "Class: $($_.name) | students: $($_.student_count) | invite: $($_.invite_code)"
}