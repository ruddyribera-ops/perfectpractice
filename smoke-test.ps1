$base = 'http://localhost:8000/api'
$ts = [int](Get-Date -UFormat %s)
$fail = 0; $pass = 0
$script:headers = @{}
$script:token = ''
$script:ptoken = ''
$script:ttoken = ''

function check($method, $path, $expected, $body=$null) {
    $url = "$base$path"
    try {
        if ($method -eq 'GET') { $r = Invoke-WebRequest -Uri $url -Method GET -Headers $script:headers -TimeoutSec 5 }
        elseif ($method -eq 'POST') { $r = Invoke-WebRequest -Uri $url -Method POST -Headers $script:headers -ContentType 'application/json' -Body ($body|ConvertTo-Json) -TimeoutSec 5 }
        elseif ($method -eq 'PUT') { $r = Invoke-WebRequest -Uri $url -Method PUT -Headers $script:headers -ContentType 'application/json' -Body ($body|ConvertTo-Json) -TimeoutSec 5 }
        $code = $r.StatusCode
    } catch {
        $code = [int]$_.Exception.Response.StatusCode
    }
    if ($code -eq $expected) { $script:pass++; Write-Host "PASS $method $path -> $code" }
    else { $script:fail++; Write-Host "FAIL $method $path -> got $code want $expected" }
}

# Health
check GET '/health' 200

# Register users
check POST '/auth/register' 200 (@{email="teacher_$ts@test.com";password='Test1234!';full_name='T';role='teacher'})
check POST '/auth/register' 200 (@{email="student_$ts@test.com";password='Test1234!';full_name='S';role='student'})
check POST '/auth/register' 200 (@{email="parent_$ts@test.com";password='Test1234!';full_name='P';role='parent'})

# Login student
$r = Invoke-WebRequest -Uri "$base/auth/login" -Method POST -ContentType 'application/json' -Body (ConvertTo-Json @{email="student_$ts@test.com";password='Test1234!'}) -TimeoutSec 5
$script:token = ($r.Content|ConvertFrom-Json).access_token
$script:headers = @{'Authorization'="Bearer $script:token"}
if ($script:token) { $script:pass++; Write-Host "PASS Login student" } else { $script:fail++; Write-Host "FAIL Login student" }

# Login parent
$r2 = Invoke-WebRequest -Uri "$base/auth/login" -Method POST -ContentType 'application/json' -Body (ConvertTo-Json @{email="parent_$ts@test.com";password='Test1234!'}) -TimeoutSec 5
$script:ptoken = ($r2.Content|ConvertFrom-Json).access_token

# Login teacher
$r3 = Invoke-WebRequest -Uri "$base/auth/login" -Method POST -ContentType 'application/json' -Body (ConvertTo-Json @{email="teacher_$ts@test.com";password='Test1234!'}) -TimeoutSec 5
$script:ttoken = ($r3.Content|ConvertFrom-Json).access_token

# Core endpoints
check GET '/topics/' 200
check GET '/units/' 200
check GET '/exercises/' 200
check GET '/exercises/1' 200
check GET '/assignments/' 200
check GET '/assignments/1' 200

# Student attempts + assignments
check POST '/students/attempts' 200 (@{exercise_id=1;answer='42';time_spent=10})
check GET '/students/me/assignments' 200
check GET '/students/me/assignments/1' 200
check GET '/students/me/history' 200
check GET '/students/me/classes' 200

# Notifications
check GET '/notifications/' 200
check PUT '/notifications/1/read' 200

# Parent portal
$pheaders = @{'Authorization'="Bearer $script:ptoken"}
check GET '/parents/me' 200 $pheaders
check POST '/parents/generate-code' 200 $pheaders

# Teacher
$theaders = @{'Authorization'="Bearer $script:ttoken"}
check GET '/teachers/classes' 200 $theaders

# Leaderboard
check GET '/leaderboard/' 200

Write-Host ""
Write-Host "=== RESULTS: $pass PASS, $fail FAIL ==="
