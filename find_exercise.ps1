$api = "http://localhost:8000"
$body = @{ email = "student@test.com"; password = "test123" } | ConvertTo-Json
$loginResp = Invoke-WebRequest -Uri "$api/api/auth/login" -Method Post -ContentType "application/json" -Body $body -UseBasicParsing
$token = ($loginResp.Content | ConvertFrom-Json).access_token
$headers = @{ Authorization = "Bearer $token" }

# Get first topic
$topics = Invoke-WebRequest -Uri "$api/api/topics" -Headers $headers -UseBasicParsing | ConvertFrom-Json
Write-Host "Topics: $($topics.Count)"

# Get first topic's units
if ($topics.Count -gt 0) {
    $slug = $topics[0].slug
    $units = Invoke-WebRequest -Uri "$api/api/topics/$slug/units" -Headers $headers -UseBasicParsing | ConvertFrom-Json
    Write-Host "Units in topic 0: $($units.Count)"

    # Get first unit's lessons
    if ($units.Count -gt 0) {
        $unitSlug = $units[0].slug
        $lessons = Invoke-WebRequest -Uri "$api/api/units/$unitSlug/lessons" -Headers $headers -UseBasicParsing | ConvertFrom-Json
        Write-Host "Lessons in unit 0: $($lessons.Count)"

        # Get first lesson's exercises
        if ($lessons.Count -gt 0) {
            $lessonId = $lessons[0].id
            $exercises = Invoke-WebRequest -Uri "$api/api/lessons/$lessonId/exercises" -Headers $headers -UseBasicParsing | ConvertFrom-Json
            Write-Host "Exercises in lesson $($lessonId): $($exercises.Count)"

            if ($exercises.Count -gt 0) {
                $exId = $exercises[0].id
                Write-Host "Trying exercise ID: $exId"

                $attemptBody = @{ exercise_id = $exId; answer = "42"; attempt_type = "free_response" } | ConvertTo-Json
                $attemptResp = Invoke-WebRequest -Uri "$api/api/exercises/$exId/attempt" -Method Post -Headers $headers -Body $attemptBody -ContentType "application/json" -UseBasicParsing
                Write-Host "Status: $($attemptResp.StatusCode)"
                Write-Host "Content: $($attemptResp.Content)"
            }
        }
    }
}