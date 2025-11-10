# Test script for project creation via AI chat
$API_URL = "https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io"

Write-Host "=== Testing Project Creation Bug Fix ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Login
Write-Host "Step 1: Logging in as edward (auditor)..." -ForegroundColor Yellow
$loginBody = @{
    username = "edward"
    password = "pass123"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "$API_URL/auth/login" -Method Post -ContentType "application/json" -Body $loginBody
    $token = $loginResponse.access_token
    Write-Host "Login successful!" -ForegroundColor Green
    Write-Host "Token obtained" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "Login failed" -ForegroundColor Red
    exit 1
}

# Step 2: Test project creation via chat
Write-Host "Step 2: Testing project creation via AI chat..." -ForegroundColor Yellow
$headers = @{
    "Authorization" = "Bearer $token"
}

# Create multipart form data
$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"
$bodyLines = (
    "--$boundary",
    "Content-Disposition: form-data; name=`"message`"$LF",
    "Create a new project called Test Project for Q1 2025 compliance assessment",
    "--$boundary--$LF"
) -join $LF

try {
    $chatResponse = Invoke-RestMethod -Uri "$API_URL/agentic-chat/" -Method Post -Headers $headers -ContentType "multipart/form-data; boundary=$boundary" -Body $bodyLines
    
    Write-Host "Chat request successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "AI Response:" -ForegroundColor Cyan
    Write-Host $chatResponse.response
    Write-Host ""
    
    if ($chatResponse.task_id) {
        Write-Host "Task Created:" -ForegroundColor Green
        Write-Host "  Task ID: $($chatResponse.task_id)" -ForegroundColor Gray
        Write-Host "  Task Type: $($chatResponse.task_type)" -ForegroundColor Gray
        Write-Host ""
        
        if ($chatResponse.response -like "*project_type*invalid*") {
            Write-Host "BUG STILL EXISTS" -ForegroundColor Red
        } else {
            Write-Host "No project_type error - bug fixed!" -ForegroundColor Green
        }
    } else {
        Write-Host "No task created" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Chat request failed" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Test Complete ===" -ForegroundColor Cyan
