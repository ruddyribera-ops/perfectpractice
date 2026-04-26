$ErrorActionPreference = 'Stop'
$api = "https://lucid-serenity-production.up.railway.app"
$headers = @{ "Content-Type" = "application/json" }

Write-Host "=== PHASE 5: 21-STUDENT SIMULATION ===" -ForegroundColor Cyan

# Load student tokens
$studentTokens = Get-Content "C:/Users/Windows/math-platform/e2e/comprehensive/.student_tokens.json" | ConvertFrom-Json

# Get exercises to use for simulation
$login = Invoke-WebRequest -Uri "$api/api/auth/login" -Method Post -Headers $headers -Body (@{email="student_01@test.com";password="test123"}|ConvertTo-Json) -UseBasicParsing -TimeoutSec 15
$token = ($login.Content | ConvertFrom-Json).access_token
$tHeaders = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }
$topics = Invoke-WebRequest -Uri "$api/api/topics/picker/full" -Method Get -Headers $tHeaders -UseBasicParsing -TimeoutSec 15
$topicData = $topics.Content | ConvertFrom-Json
$exIds = @($topicData[0].units[0].exercises[0].id, $topicData[0].units[0].exercises[1].id, $topicData[0].units[0].exercises[2].id)
Write-Host "Exercises to submit: $($exIds -join ', ')"

# PHASE 5.1: All 21 students submit 3 exercise attempts each
Write-Host "`n--- 5.1: Submitting exercises for all 21 students ---" -ForegroundColor Yellow
$results = @()
$totalAttempts = 0
$totalCorrect = 0

for ($i = 0; $i -lt 21; $i++) {
    $st = $studentTokens[$i]
    $stHeaders = @{ Authorization = "Bearer $($st.token)"; "Content-Type" = "application/json" }
    $studentCorrect = 0

    foreach ($exId in $exIds) {
        $body = @{
            exercise_id = $exId
            answer = "5"
            attempt_type = "free_response"
        } | ConvertTo-Json

        try {
            $r = Invoke-WebRequest -Uri "$api/api/me/exercises/$exId/attempt" -Method Post -Headers $stHeaders -Body $body -UseBasicParsing -TimeoutSec 15
            $totalAttempts++
            if ($r.StatusCode -match "^(200|201)$") {
                $data = $r.Content | ConvertFrom-Json
                if ($data.correct) { $studentCorrect++; $totalCorrect++ }
                Write-Host "." -NoNewline
            } else {
                Write-Host "E" -NoNewline
            }
        } catch {
            Write-Host "X" -NoNewline
        }
    }

    $results += @{
        student = $st.email
        attempts = 3
        correct = $studentCorrect
    }
}

Write-Host "`n"
Write-Host "[RESULTS] Total attempts: $totalAttempts | Correct: $totalCorrect | Accuracy: $([Math]::Round($totalCorrect/$totalAttempts*100,1))%" -ForegroundColor $(if ($totalCorrect -gt 0) { "Green" } else { "Red" })

# PHASE 5.2: Verify teacher sees all activity
Write-Host "`n--- 5.2: Verifying teacher sees updated data ---" -ForegroundColor Yellow
$tLogin = Invoke-WebRequest -Uri "$api/api/auth/login" -Method Post -Headers $headers -Body (@{email="profesor_e2e@test.com";password="test123"}|ConvertTo-Json) -UseBasicParsing -TimeoutSec 15
$tToken = ($tLogin.Content | ConvertFrom-Json).access_token
$tHeaders = @{ Authorization = "Bearer $tToken"; "Content-Type" = "application/json" }

# Check class student count
$classes = Invoke-WebRequest -Uri "$api/api/classes" -Method Get -Headers $tHeaders -UseBasicParsing -TimeoutSec 15
$class = ($classes.Content | ConvertFrom-Json) | Where-Object { $_.name -eq "3ro Primaria A" }
Write-Host "[TEACHER] Class: $($class.name)" -ForegroundColor Cyan
Write-Host "[TEACHER] Students: $($class.student_count)" -ForegroundColor Cyan

# Check leaderboard
$lb = Invoke-WebRequest -Uri "$api/api/leaderboard" -Method Get -Headers $tHeaders -UseBasicParsing -TimeoutSec 15
$lbData = ($lb.Content | ConvertFrom-Json)
Write-Host "[LEADERBOARD] Entries: $($lbData.Count)" -ForegroundColor Cyan
if ($lbData.Count -gt 0) {
    Write-Host "  Top student: $($lbData[0].name) - $($lbData[0].all_time_points) XP"
}

# PHASE 5.3: Verify parent dashboards reflect activity
Write-Host "`n--- 5.3: Verifying parent dashboards ---" -ForegroundColor Yellow
$pLogin = Invoke-WebRequest -Uri "$api/api/auth/login" -Method Post -Headers $headers -Body (@{email="parent_01@test.com";password="test123"}|ConvertTo-Json) -UseBasicParsing -TimeoutSec 15
$pToken = ($pLogin.Content | ConvertFrom-Json).access_token
$pHeaders = @{ Authorization = "Bearer $pToken"; "Content-Type" = "application/json" }
$pDash = Invoke-WebRequest -Uri "$api/api/parents/me" -Method Get -Headers $pHeaders -UseBasicParsing -TimeoutSec 15
$pData = $pDash.Content | ConvertFrom-Json
Write-Host "[PARENT 1] Linked students: $($pData.linked_students.Count)" -ForegroundColor Cyan
if ($pData.linked_students.Count -gt 0) {
    $first = $pData.linked_students[0]
    Write-Host "[PARENT 1] First child: $($first.name) | XP: $($first.xp_total) | Exercises: $($first.exercises_completed)"
}

Write-Host "`n=== PHASE 5 COMPLETE ===" -ForegroundColor Green