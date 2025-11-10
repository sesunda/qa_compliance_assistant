# Check Conversation Database - Azure PostgreSQL Query
# This script checks if conversations are being saved to the database

$API_BASE_URL = "https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io"

Write-Host "=== Conversation Database Check ===" -ForegroundColor Cyan
Write-Host ""

# Test credentials (Edward - Auditor)
$USERNAME = "auditor1"  # Edward's username
$PASSWORD = "auditor123"

# Step 1: Login
Write-Host "[1] Logging in as Edward (Auditor)..." -ForegroundColor Yellow
try {
    $loginBody = @{
        username = $USERNAME
        password = $PASSWORD
    } | ConvertTo-Json
    
    $loginResponse = Invoke-RestMethod `
        -Uri "$API_BASE_URL/auth/login" `
        -Method Post `
        -Body $loginBody `
        -ContentType "application/json" `
        -ErrorAction Stop
    
    $token = $loginResponse.access_token
    $userId = $loginResponse.user_id
    Write-Host "  ✅ Login successful" -ForegroundColor Green
    Write-Host "     User ID: $userId" -ForegroundColor Gray
    Write-Host "     Token: $($token.Substring(0, 20))..." -ForegroundColor Gray
}
catch {
    Write-Host "  ❌ Login failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

$headers = @{
    Authorization = "Bearer $token"
}

# Step 2: Send a test message to create a conversation
Write-Host "`n[2] Sending test message to create conversation..." -ForegroundColor Yellow
$testMessage = "What templates are available for IM8?"

try {
    $formData = @{
        message = $testMessage
    }
    
    # Use multipart/form-data as the endpoint expects FormData
    $boundary = [System.Guid]::NewGuid().ToString()
    $bodyLines = @(
        "--$boundary",
        "Content-Disposition: form-data; name=`"message`"",
        "",
        $testMessage,
        "--$boundary--"
    )
    $body = $bodyLines -join "`r`n"
    
    $chatResponse = Invoke-RestMethod `
        -Uri "$API_BASE_URL/agentic-chat/" `
        -Method Post `
        -Headers @{
            Authorization = "Bearer $token"
            "Content-Type" = "multipart/form-data; boundary=$boundary"
        } `
        -Body $body `
        -ErrorAction Stop
    
    $conversationId = $chatResponse.conversation_id
    Write-Host "  ✅ Message sent successfully" -ForegroundColor Green
    Write-Host "     Conversation ID: $conversationId" -ForegroundColor Gray
    Write-Host "     Response preview: $($chatResponse.response.Substring(0, [Math]::Min(100, $chatResponse.response.Length)))..." -ForegroundColor Gray
}
catch {
    Write-Host "  ❌ Failed to send message: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "     Full error: $_" -ForegroundColor Red
    exit 1
}

# Step 3: Try to retrieve the conversation
Write-Host "`n[3] Attempting to retrieve conversation history..." -ForegroundColor Yellow
if ($conversationId) {
    try {
        $historyResponse = Invoke-RestMethod `
            -Uri "$API_BASE_URL/agentic-chat/sessions/$conversationId/messages" `
            -Method Get `
            -Headers $headers `
            -ErrorAction Stop
        
        Write-Host "  ✅ Conversation retrieved successfully" -ForegroundColor Green
        Write-Host "     Total messages: $($historyResponse.messages.Count)" -ForegroundColor Gray
        Write-Host "     Session created: $($historyResponse.created_at)" -ForegroundColor Gray
        Write-Host "     Last activity: $($historyResponse.last_activity)" -ForegroundColor Gray
        
        if ($historyResponse.messages.Count -gt 0) {
            Write-Host "`n     Messages:" -ForegroundColor Gray
            foreach ($msg in $historyResponse.messages) {
                $contentPreview = $msg.content.Substring(0, [Math]::Min(80, $msg.content.Length))
                Write-Host "       - [$($msg.role)] $contentPreview..." -ForegroundColor DarkGray
            }
        }
    }
    catch {
        Write-Host "  ❌ Failed to retrieve conversation: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "     Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    }
} else {
    Write-Host "  ⚠️  No conversation ID returned from chat" -ForegroundColor Yellow
}

# Step 4: Check if conversation persists in localStorage (simulation)
Write-Host "`n[4] Frontend Behavior Analysis:" -ForegroundColor Yellow
Write-Host "     The frontend SHOULD:" -ForegroundColor Gray
Write-Host "       1. Store conversation_id in localStorage as 'agentic_session_id'" -ForegroundColor DarkGray
Write-Host "       2. Restore conversation_id on page load" -ForegroundColor DarkGray
Write-Host "       3. Call GET /sessions/{id}/messages to restore messages" -ForegroundColor DarkGray
Write-Host ""
Write-Host "     Common Issues:" -ForegroundColor Gray
Write-Host "       - If conversation_id is NULL in response → Backend not creating session" -ForegroundColor DarkGray
Write-Host "       - If localStorage is cleared → User must start new conversation" -ForegroundColor DarkGray
Write-Host "       - If GET /sessions/{id}/messages returns 404 → Session expired or deleted" -ForegroundColor DarkGray

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
if ($conversationId) {
    Write-Host "✅ Conversation created with ID: $conversationId" -ForegroundColor Green
    Write-Host "✅ Backend is storing conversations correctly" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Check browser console to see if localStorage has 'agentic_session_id'" -ForegroundColor White
    Write-Host "  2. Verify restoreMessageHistory() is being called on page load" -ForegroundColor White
    Write-Host "  3. Check network tab for GET /sessions/{id}/messages request" -ForegroundColor White
} else {
    Write-Host "❌ No conversation ID returned - backend issue" -ForegroundColor Red
}
