# Test Agentic Chat Deployment
# Quick diagnostic script to verify Azure OpenAI integration

$API_URL = "https://ca-api-qca-dev.azurecontainerapps.io"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing Agentic Chat Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if API is responding
Write-Host "Step 1: Testing API health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$API_URL/" -Method Get
    Write-Host "✓ API is online" -ForegroundColor Green
} catch {
    Write-Host "✗ API is not responding" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Gray
    exit 1
}

Write-Host ""

# Step 2: Check agentic chat capabilities (no auth required)
Write-Host "Step 2: Testing agentic chat capabilities endpoint..." -ForegroundColor Yellow
try {
    $capabilities = Invoke-RestMethod -Uri "$API_URL/agentic-chat/capabilities" -Method Get
    Write-Host "✓ Agentic chat endpoint is accessible" -ForegroundColor Green
    Write-Host "  Status: $($capabilities.status)" -ForegroundColor Gray
    Write-Host "  Provider: $($capabilities.provider)" -ForegroundColor Gray
    Write-Host "  Capabilities count: $($capabilities.capabilities.Count)" -ForegroundColor Gray
    
    if ($capabilities.status -eq "unavailable") {
        Write-Host "" 
        Write-Host "⚠️  AI service is UNAVAILABLE" -ForegroundColor Yellow
        Write-Host "  This means Azure OpenAI environment variables are not properly set" -ForegroundColor Gray
        Write-Host "  Expected variables:" -ForegroundColor Gray
        Write-Host "    - AZURE_OPENAI_ENDPOINT" -ForegroundColor Gray
        Write-Host "    - AZURE_OPENAI_API_KEY" -ForegroundColor Gray
        Write-Host "    - AZURE_OPENAI_MODEL" -ForegroundColor Gray
    }
    else {
        Write-Host "" 
        Write-Host "✓ AI service is ACTIVE and ready!" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Agentic chat endpoint failed" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Gray
    Write-Host "  Response: $($_.ErrorDetails.Message)" -ForegroundColor Gray
}

Write-Host ""

# Step 3: Login and get token (adjust credentials if needed)
Write-Host "Step 3: Testing authentication..." -ForegroundColor Yellow
$loginBody = @{
    username = "alice.tan@superadmin.gov.sg"
    password = "SecurePass123!"
} | ConvertTo-Json

try {
    $authResponse = Invoke-RestMethod -Uri "$API_URL/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
    $token = $authResponse.access_token
    Write-Host "✓ Authentication successful" -ForegroundColor Green
    Write-Host "  User: $($authResponse.user.username)" -ForegroundColor Gray
    Write-Host "  Role: $($authResponse.user.role)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Authentication failed" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Gray
    Write-Host "  Make sure alice.tan@superadmin.gov.sg user exists" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Step 4: Test chat message (requires auth)
Write-Host "Step 4: Testing chat message with auth..." -ForegroundColor Yellow
$chatBody = @{
    message = "Upload 5 IM8 controls for Access Control domain"
} | ConvertTo-Json

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

try {
    $chatResponse = Invoke-RestMethod -Uri "$API_URL/agentic-chat/" -Method Post -Body $chatBody -Headers $headers
    Write-Host "✓ Chat message processed successfully" -ForegroundColor Green
    Write-Host "  Task created: $($chatResponse.task_created)" -ForegroundColor Gray
    
    if ($chatResponse.task_created) {
        Write-Host "  Task ID: $($chatResponse.task_id)" -ForegroundColor Gray
        Write-Host "  Task type: $($chatResponse.task_type)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "✓ AGENTIC CHAT IS FULLY OPERATIONAL!" -ForegroundColor Green
        Write-Host "  Go to Agent Tasks page to see task #$($chatResponse.task_id)" -ForegroundColor Cyan
    } else {
        Write-Host "  Response: $($chatResponse.response)" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ Chat message failed" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Gray
    Write-Host "  Response: $($_.ErrorDetails.Message)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Diagnostic Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
