$api = "https://lucid-serenity-production.up.railway.app"
$headers = @{ "Content-Type" = "application/json" }

# Login as student_01
$login = Invoke-WebRequest -Uri "$api/api/auth/login" -Method Post -Headers $headers -Body (@{email="student_01@test.com";password="test123"}|ConvertTo-Json) -UseBasicParsing -TimeoutSec 15
$studentToken = ($login.Content | ConvertFrom-Json).access_token

# Login as parent_01
$login = Invoke-WebRequest -Uri "$api/api/auth/login" -Method Post -Headers $headers -Body (@{email="parent_01@test.com";password="test123"}|ConvertTo-Json) -UseBasicParsing -TimeoutSec 15
$parentToken = ($login.Content | ConvertFrom-Json).access_token
$p1Headers = @{ Authorization = "Bearer $parentToken"; "Content-Type" = "application/json" }

# Generate parent code
$codeResp = Invoke-WebRequest -Uri "$api/api/parents/generate-code" -Method Post -Headers $p1Headers -UseBasicParsing -TimeoutSec 15
Write-Host "Generate code status: $($codeResp.StatusCode)"
Write-Host "Generate code response: $($codeResp.Content)"
$linkCode = ($codeResp.Content | ConvertFrom-Json).link_code

# Student links
$stHeaders = @{ Authorization = "Bearer $studentToken"; "Content-Type" = "application/json" }
$body = @{ link_code = $linkCode } | ConvertTo-Json
$linkResp = Invoke-WebRequest -Uri "$api/api/me/link-parent" -Method Post -Headers $stHeaders -Body $body -UseBasicParsing -TimeoutSec 15
Write-Host "Link status: $($linkResp.StatusCode)"
Write-Host "Link response: $($linkResp.Content)"