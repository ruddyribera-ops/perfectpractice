# Create teacher account
$headers = @{"Content-Type" = "application/json"}
$body = '{"email":"teacher@test.com","password":"Test123","name":"Test Teacher","role":"teacher"}'
$result = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/register" -Method POST -Headers $headers -Body $body
Write-Host "=== TEACHER REGISTERED ==="
$result | ConvertTo-Json -Depth 5

# Create student account
$body2 = '{"email":"student2@test.com","password":"Test123","name":"Student Two","role":"student"}'
$result2 = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/register" -Method POST -Headers $headers -Body $body2
Write-Host "`n=== STUDENT REGISTERED ==="
$result2 | ConvertTo-Json -Depth 5

$teacherToken = $result.access_token
$studentToken = $result2.access_token

# Teacher creates a class
$authHeaders = @{"Authorization" = "Bearer $teacherToken"}
$classBody = '{"name":"Matemáticas 1A","subject":"Matemáticas"}'
$class = Invoke-RestMethod -Uri "http://localhost:8000/api/classes" -Method POST -Headers $authHeaders -Body $classBody
Write-Host "`n=== CLASS CREATED ==="
$class | ConvertTo-Json -Depth 5
$inviteCode = $class.invite_code

# Student joins class
$studentAuth = @{"Authorization" = "Bearer $studentToken"}
$join = Invoke-RestMethod -Uri "http://localhost:8000/api/classes/join/$inviteCode" -Method POST -Headers $studentAuth
Write-Host "`n=== STUDENT JOINED CLASS ==="
$join | ConvertTo-Json -Depth 5

# Get topics
Write-Host "`n=== TOPICS ==="
Invoke-RestMethod -Uri "http://localhost:8000/api/topics" -Method GET | ConvertTo-Json -Depth 5