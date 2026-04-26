$api = "https://lucid-serenity-production.up.railway.app"
$body = @{ email = "student@test.com"; password = "test123" } | ConvertTo-Json
$resp = Invoke-WebRequest -Uri "$api/api/auth/login" -Method Post -ContentType "application/json" -Body $body -UseBasicParsing -TimeoutSec 15
$token = ($resp.Content | ConvertFrom-Json).access_token
$headers = @{ Authorization = "Bearer $token" }

$endpoints = @(
  "/api/me/stats",
  "/api/me/progress",
  "/api/me/notifications",
  "/api/me/assignments",
  "/api/me/history",
  "/api/students/dashboard",
  "/api/me/dashboard"
)

foreach ($ep in $endpoints) {
  try {
    $r = Invoke-WebRequest -Uri "$api$ep" -Headers $headers -UseBasicParsing -TimeoutSec 10
    $snippet = $r.Content.Substring(0, [Math]::Min(100, $r.Content.Length))
    Write-Host "$ep -> $($r.StatusCode) : $snippet"
  } catch {
    $msg = $_.Exception.Message
    if ($msg -match "404") { Write-Host "$ep -> 404 Not Found" }
    elseif ($msg -match "401") { Write-Host "$ep -> 401 Unauthorized" }
    else { Write-Host "$ep -> ERROR: $msg" }
  }
}