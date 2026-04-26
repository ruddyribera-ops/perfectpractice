$api = "https://lucid-serenity-production.up.railway.app"
$headers = @{ "Content-Type" = "application/json" }

# Try student_01 linking with the parent_01 code directly
$login = Invoke-WebRequest -Uri "$api/api/auth/login" -Method Post -Headers $headers -Body (@{email="student_01@test.com";password="test123"}|ConvertTo-Json) -UseBasicParsing -TimeoutSec 15
$studentToken = ($login.Content | ConvertFrom-Json).access_token
$stHeaders = @{ Authorization = "Bearer $studentToken"; "Content-Type" = "application/json" }

# Get a fresh code from parent
$login = Invoke-WebRequest -Uri "$api/api/auth/login" -Method Post -Headers $headers -Body (@{email="parent_01@test.com";password="test123"}|ConvertTo-Json) -UseBasicParsing -TimeoutSec 15
$parentToken = ($login.Content | ConvertFrom-Json).access_token
$pHeaders = @{ Authorization = "Bearer $parentToken"; "Content-Type" = "application/json" }
$codeResp = Invoke-WebRequest -Uri "$api/api/parents/generate-code" -Method Post -Headers $pHeaders -UseBasicParsing -TimeoutSec 15
$linkCode = ($codeResp.Content | ConvertFrom-Json).link_code
Write-Host "Code: $linkCode"

# Try student linking - use -ErrorAction Continue to capture status
$body = @{ link_code = $linkCode } | ConvertTo-Json
try {
    $r = Invoke-WebRequest -Uri "$api/api/me/link-parent" -Method Post -Headers $stHeaders -Body $body -UseBasicParsing -TimeoutSec 15 -ErrorAction Continue
    Write-Host "Status: $($r.StatusCode)"
    Write-Host "Content: $($r.Content)"
} catch {
    $status = [int]$_.Exception.Response.StatusCode
    $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
    $reader.BaseStream.Position = 0
    $body_err = $reader.ReadToEnd()
    $reader.Close()
    Write-Host "Status: $status"
    Write-Host "Error body: $body_err"
}