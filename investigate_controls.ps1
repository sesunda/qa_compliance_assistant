# Investigation Script for Controls Issue
$apiUrl = "https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io"

# Edward's token (Auditor)
$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlZHdhcmQiLCJleHAiOjE3MzY1OTM5Mzd9.HIQ9qZEBjlJ6SqnvlGJ66KYzLZSbKLJUW44wWbzkM3c"

$headers = @{
    Authorization = "Bearer $token"
}

Write-Host "=== 1. CHECK PROJECTS ===" -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "$apiUrl/projects/" -Headers $headers -UseBasicParsing
    $projects = $response.Content | ConvertFrom-Json
    
    Write-Host "`nProjects:" -ForegroundColor Yellow
    foreach ($project in $projects) {
        Write-Host "  ID: $($project.id) | Name: $($project.name) | Agency: $($project.agency_id)" -ForegroundColor White
    }
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== 2. CHECK ALL CONTROLS ===" -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "$apiUrl/controls/" -Headers $headers -UseBasicParsing
    $controls = $response.Content | ConvertFrom-Json
    
    Write-Host "`nTotal Controls: $($controls.Count)" -ForegroundColor Yellow
    
    # Group by project
    $byProject = $controls | Group-Object -Property project_id
    foreach ($group in $byProject) {
        $projectId = $group.Name
        $count = $group.Count
        Write-Host "`nProject ID $projectId has $count controls:" -ForegroundColor Green
        
        # Group by domain
        $byDomain = $group.Group | Group-Object -Property { 
            if ($_.control_type -match '^(IM8-\d{2})') { $matches[1] } else { 'Unknown' }
        }
        
        foreach ($domain in $byDomain | Sort-Object Name) {
            Write-Host "  $($domain.Name): $($domain.Count) controls" -ForegroundColor White
        }
    }
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== 3. CHECK CONTROLS FOR PROJECT 7 (Health Science Digital Platform) ===" -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "$apiUrl/controls/?project_id=7" -Headers $headers -UseBasicParsing
    $controls = $response.Content | ConvertFrom-Json
    
    Write-Host "`nControls for Project 7: $($controls.Count)" -ForegroundColor Yellow
    
    if ($controls.Count -gt 0) {
        foreach ($control in $controls | Select-Object -First 5) {
            Write-Host "`n  Control ID: $($control.id)" -ForegroundColor Cyan
            Write-Host "  Name: $($control.name)" -ForegroundColor White
            Write-Host "  Type: $($control.control_type)" -ForegroundColor White
            Write-Host "  Status: $($control.status)" -ForegroundColor White
        }
        
        if ($controls.Count -gt 5) {
            Write-Host "`n  ... and $($controls.Count - 5) more controls" -ForegroundColor Gray
        }
    } else {
        Write-Host "  NO CONTROLS FOUND for project 7" -ForegroundColor Red
    }
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== 4. CHECK RECENT AGENT TASKS ===" -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "$apiUrl/agent-tasks/" -Headers $headers -UseBasicParsing
    $tasks = $response.Content | ConvertFrom-Json
    
    Write-Host "`nRecent Tasks (last 10):" -ForegroundColor Yellow
    foreach ($task in ($tasks | Select-Object -First 10 | Sort-Object -Property id -Descending)) {
        Write-Host "`n  Task ID: $($task.id) | Type: $($task.task_type) | Status: $($task.status)" -ForegroundColor Cyan
        Write-Host "  Title: $($task.title)" -ForegroundColor White
        if ($task.result) {
            $result = $task.result | ConvertTo-Json -Compress
            Write-Host "  Result: $($result.Substring(0, [Math]::Min(150, $result.Length)))..." -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== 5. CHECK USER ROLES ===" -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "$apiUrl/auth/users" -Headers $headers -UseBasicParsing
    $users = $response.Content | ConvertFrom-Json
    
    Write-Host "`nUser Roles:" -ForegroundColor Yellow
    foreach ($user in $users) {
        Write-Host "  $($user.username) ($($user.full_name)): Role = $($user.role.name)" -ForegroundColor White
    }
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
