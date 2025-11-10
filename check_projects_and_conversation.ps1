# Check Projects and Recent Conversation
$apiUrl = "https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io"
$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlZHdhcmQiLCJleHAiOjE3MzY1OTM5Mzd9.HIQ9qZEBjlJ6SqnvlGJ66KYzLZSbKLJUW44wWbzkM3c"

Write-Host "=== Checking Existing Projects ===" -ForegroundColor Cyan

try {
    $headers = @{
        Authorization = "Bearer $token"
    }
    $response = Invoke-WebRequest -Uri "$apiUrl/projects/" -Headers $headers -UseBasicParsing
    $projects = $response.Content | ConvertFrom-Json
    
    Write-Host "`nExisting Projects:" -ForegroundColor Yellow
    foreach ($project in $projects) {
        Write-Host "  ID: $($project.id) | Name: $($project.name) | Type: $($project.project_type)" -ForegroundColor White
    }
    
    Write-Host "`nTotal Projects: $($projects.Count)" -ForegroundColor Green
    
} catch {
    Write-Host "Error fetching projects: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Checking Conversation Sessions ===" -ForegroundColor Cyan

try {
    $response = Invoke-WebRequest -Uri "$apiUrl/conversations/?active_only=true&limit=5" -Headers $headers -UseBasicParsing
    $sessions = $response.Content | ConvertFrom-Json
    
    Write-Host "`nRecent Conversation Sessions:" -ForegroundColor Yellow
    foreach ($session in $sessions) {
        Write-Host "  Session: $($session.session_id)" -ForegroundColor White
        Write-Host "    Title: $($session.title)" -ForegroundColor Gray
        Write-Host "    Messages: $($session.message_count)" -ForegroundColor Gray
        Write-Host "    Last Activity: $($session.last_activity)" -ForegroundColor Gray
        Write-Host ""
    }
    
    # Get details of most recent conversation
    if ($sessions.Count -gt 0) {
        $latestSession = $sessions[0].session_id
        Write-Host "=== Latest Conversation Details ===" -ForegroundColor Cyan
        Write-Host "Session ID: $latestSession" -ForegroundColor Yellow
        
        $response = Invoke-WebRequest -Uri "$apiUrl/conversations/$latestSession" -Headers $headers -UseBasicParsing
        $details = $response.Content | ConvertFrom-Json
        
        Write-Host "`nConversation Messages:" -ForegroundColor Yellow
        foreach ($msg in $details.messages) {
            $role = $msg.role.ToUpper()
            $color = if ($role -eq "USER") { "Cyan" } elseif ($role -eq "ASSISTANT") { "Green" } else { "Gray" }
            Write-Host "`n[$role]:" -ForegroundColor $color
            Write-Host "$($msg.content)" -ForegroundColor White
            
            if ($msg.tool_calls) {
                Write-Host "  Tool Calls:" -ForegroundColor Magenta
                $msg.tool_calls | ConvertTo-Json -Depth 5 | Write-Host -ForegroundColor DarkGray
            }
        }
    }
    
} catch {
    Write-Host "Error fetching conversations: $($_.Exception.Message)" -ForegroundColor Red
}
