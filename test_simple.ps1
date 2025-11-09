# Simple Test - Agentic Chat
$API_URL = "https://ca-api-qca-dev.azurecontainerapps.io"

Write-Host "Testing Agentic Chat..." -ForegroundColor Cyan

# Test 1: Capabilities
Write-Host "`n1. Testing /agentic-chat/capabilities..." -ForegroundColor Yellow
try {
    $caps = Invoke-RestMethod -Uri "$API_URL/agentic-chat/capabilities"
    Write-Host "   Status: $($caps.status)" -ForegroundColor Green
    Write-Host "   Provider: $($caps.provider)" -ForegroundColor Green
    
    if ($caps.status -eq "unavailable") {
        Write-Host "   WARNING: AI service unavailable - check environment variables" -ForegroundColor Red
    }
}
catch {
    Write-Host "   ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Login
Write-Host "`n2. Testing authentication..." -ForegroundColor Yellow
$loginBody = '{"username":"alice.tan@superadmin.gov.sg","password":"SecurePass123!"}'
try {
    $auth = Invoke-RestMethod -Uri "$API_URL/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
    $token = $auth.access_token
    Write-Host "   Logged in as: $($auth.user.username)" -ForegroundColor Green
}
catch {
    Write-Host "   ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit
}

# Test 3: Send chat message
Write-Host "`n3. Sending test message..." -ForegroundColor Yellow
$chatBody = '{"message":"Upload 5 IM8 controls for Access Control domain"}'
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

try {
    $chat = Invoke-RestMethod -Uri "$API_URL/agentic-chat/" -Method Post -Body $chatBody -Headers $headers
    Write-Host "   Task created: $($chat.task_created)" -ForegroundColor Green
    if ($chat.task_created) {
        Write-Host "   Task ID: $($chat.task_id)" -ForegroundColor Green
        Write-Host "   Task type: $($chat.task_type)" -ForegroundColor Green
    }
    Write-Host "`n   Response: $($chat.response)" -ForegroundColor Cyan
}
catch {
    Write-Host "   ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nTest complete!" -ForegroundColor Cyan
