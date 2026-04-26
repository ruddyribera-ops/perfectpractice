$api = "https://lucid-serenity-production.up.railway.app"
$headers = @{ "Content-Type" = "application/json" }

# Check if parent_student_links table exists by trying to access it via the parent dashboard
$login = Invoke-WebRequest -Uri "$api/api/auth/login" -Method Post -Headers $headers -Body (@{email="parent_01@test.com";password="test123"}|ConvertTo-Json) -UseBasicParsing -TimeoutSec 15
$parentToken = ($login.Content | ConvertFrom-Json).access_token
$pHeaders = @{ Authorization = "Bearer $parentToken"; "Content-Type" = "application/json" }

# Parent dashboard
$dash = Invoke-WebRequest -Uri "$api/api/parents/me" -Method Get -Headers $pHeaders -UseBasicParsing -TimeoutSec 15
Write-Host "Parent dashboard: $($dash.StatusCode)"
Write-Host $dash.Content

# Check the debug endpoint to see all tables
$debug = Invoke-WebRequest -Uri "$api/debug/login-test" -UseBasicParsing -TimeoutSec 15
Write-Host "`nDB Tables:"
Write-Host $debug.Content