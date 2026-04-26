$ErrorActionPreference = 'Stop'
$api = "https://lucid-serenity-production.up.railway.app"
$headers = @{ "Content-Type" = "application/json" }

# Login as teacher
$login = Invoke-WebRequest -Uri "$api/api/auth/login" -Method Post -Headers $headers -Body (@{email="profesor_e2e@test.com";password="test123"}|ConvertTo-Json) -UseBasicParsing -TimeoutSec 15
$teacherToken = ($login.Content | ConvertFrom-Json).access_token
$tHeaders = @{ Authorization = "Bearer $teacherToken"; "Content-Type" = "application/json" }

# Get class ID
$classesResp = Invoke-WebRequest -Uri "$api/api/classes" -Method Get -Headers $tHeaders -UseBasicParsing -TimeoutSec 15
$classId = (($classesResp.Content | ConvertFrom-Json) | Where-Object { $_.name -eq "3ro Primaria A" }).id
Write-Host "Class ID: $classId"

# Get topic picker to find exercises
$topicsResp = Invoke-WebRequest -Uri "$api/api/topics/picker/full" -Method Get -Headers $tHeaders -UseBasicParsing -TimeoutSec 15
$topics = $topicsResp.Content | ConvertFrom-Json
Write-Host "Found $($topics.Count) topics"

# Get first topic's first unit's first 3 exercises
$topic = $topics[0]
$unit = $topic.units[0]
$exercises = $unit.exercises
Write-Host "Topic: $($topic.title), Unit: $($unit.title), Exercises: $($exercises.Count)"
$exIds = @($exercises[0].id, $exercises[1].id, $exercises[2].id)
Write-Host "Exercise IDs for assignment 1: $($exIds -join ', ')"

# Create assignment 1
$assign1Body = @{
    title = "Tarea Números 1 - Suma y Resta"
    description = "Ejercicios de práctica para números hasta 20"
    exercise_ids = $exIds
    due_date = "2026-05-01T23:59:00Z"
} | ConvertTo-Json
$assign1 = Invoke-WebRequest -Uri "$api/api/classes/$classId/assignments" -Method Post -Headers $tHeaders -Body $assign1Body -UseBasicParsing -TimeoutSec 15
if ($assign1.StatusCode -notmatch "^(200|201)$") { throw "Assignment 1 failed: $($assign1.StatusCode) $($assign1.Content)" }
Write-Host "[OK] Assignment 1 created: $((($assign1.Content | ConvertFrom-Json).title))" -ForegroundColor Green

# Get 3 more exercises from unit 2 (if exists) or different unit
if ($topic.units.Count -gt 1) {
    $unit2 = $topic.units[1]
} else {
    $unit2 = $topic.units[0]
}
$ex2Ids = @($unit2.exercises[0].id, $unit2.exercises[1].id)
Write-Host "Exercise IDs for assignment 2: $($ex2Ids -join ', ')"

$assign2Body = @{
    title = "Tarea Números 2 - Formas Geométricas"
    description = "Ejercicios de formas y medición"
    exercise_ids = $ex2Ids
    due_date = "2026-05-05T23:59:00Z"
} | ConvertTo-Json
$assign2 = Invoke-WebRequest -Uri "$api/api/classes/$classId/assignments" -Method Post -Headers $tHeaders -Body $assign2Body -UseBasicParsing -TimeoutSec 15
if ($assign2.StatusCode -notmatch "^(200|201)$") { throw "Assignment 2 failed: $($assign2.StatusCode) $($assign2.Content)" }
Write-Host "[OK] Assignment 2 created: $((($assign2.Content | ConvertFrom-Json).title))" -ForegroundColor Green

# Verify
$verify = Invoke-WebRequest -Uri "$api/api/classes/$classId/assignments" -Method Get -Headers $tHeaders -UseBasicParsing -TimeoutSec 15
$assigns = $verify.Content | ConvertFrom-Json
Write-Host "`n[VERIFY] Total assignments for class: $($assigns.Count)"
$assigns | ForEach-Object { Write-Host "  - $($_.title) (ID: $($_.id))" }

# Save class ID and assignment IDs
@{
    classId = $classId
    assignmentIds = $assigns | ForEach-Object { $_.id }
} | ConvertTo-Json | Out-File -FilePath "C:/Users/Windows/math-platform/e2e/comprehensive/.setup_data.json" -Encoding UTF8

Write-Host "`n=== PHASE 1.4 COMPLETE ===" -ForegroundColor Green