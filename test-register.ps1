$headers = @{"Content-Type" = "application/json"}
$body = '{"email":"student@test.com","password":"Test123","name":"Test Student","role":"student"}'
Invoke-RestMethod -Uri "http://localhost:8000/api/auth/register" -Method POST -Headers $headers -Body $body