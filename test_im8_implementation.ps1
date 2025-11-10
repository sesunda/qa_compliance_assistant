# IM8 Assessment Document Testing Script
# Run this after deploying the IM8 implementation

Write-Host "=== IM8 Implementation Testing ===" -ForegroundColor Cyan
Write-Host ""

# Configuration
$API_BASE_URL = "http://localhost:8000"
$AUDITOR_EMAIL = "auditor@example.com"
$ANALYST_EMAIL = "analyst@example.com"
$PASSWORD = "password"  # Change to actual password

# Test 1: Check if openpyxl is installed
Write-Host "Test 1: Checking dependencies..." -ForegroundColor Yellow
docker exec qa_compliance_assistant-api-1 python -c "import openpyxl; print(f'openpyxl version: {openpyxl.__version__}')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ openpyxl is installed" -ForegroundColor Green
} else {
    Write-Host "❌ openpyxl not found. Installing..." -ForegroundColor Red
    docker exec qa_compliance_assistant-api-1 pip install openpyxl
}
Write-Host ""

# Test 2: Verify new services are importable
Write-Host "Test 2: Checking IM8 services..." -ForegroundColor Yellow
$checkServices = @"
from api.src.services.excel_processor import get_excel_processor
from api.src.services.im8_validator import get_im8_validator
print('✅ ExcelProcessor: OK')
print('✅ IM8Validator: OK')
"@
docker exec qa_compliance_assistant-api-1 python -c "$checkServices" 2>&1
Write-Host ""

# Test 3: Check API health
Write-Host "Test 3: Checking API health..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_BASE_URL/health" -Method Get
    Write-Host "✅ API is healthy: $($response.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ API health check failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 4: Login as analyst
Write-Host "Test 4: Logging in as analyst..." -ForegroundColor Yellow
$loginBody = @{
    username = $ANALYST_EMAIL
    password = $PASSWORD
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "$API_BASE_URL/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
    $analystToken = $loginResponse.access_token
    Write-Host "✅ Analyst login successful" -ForegroundColor Green
} catch {
    Write-Host "❌ Analyst login failed: $_" -ForegroundColor Red
    $analystToken = $null
}
Write-Host ""

# Test 5: Login as auditor
Write-Host "Test 5: Logging in as auditor..." -ForegroundColor Yellow
$loginBody = @{
    username = $AUDITOR_EMAIL
    password = $PASSWORD
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "$API_BASE_URL/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
    $auditorToken = $loginResponse.access_token
    Write-Host "✅ Auditor login successful" -ForegroundColor Green
} catch {
    Write-Host "❌ Auditor login failed: $_" -ForegroundColor Red
    $auditorToken = $null
}
Write-Host ""

# Test 6: Test agentic chat with analyst (IM8 guidance)
Write-Host "Test 6: Testing agentic chat (analyst role-specific prompt)..." -ForegroundColor Yellow
if ($analystToken) {
    $chatBody = @{
        message = "How do I complete the IM8 assessment?"
    } | ConvertTo-Json

    try {
        $headers = @{
            Authorization = "Bearer $analystToken"
        }
        $chatResponse = Invoke-RestMethod -Uri "$API_BASE_URL/agentic/chat" -Method Post -Body $chatBody -ContentType "application/json" -Headers $headers
        Write-Host "✅ Chat response received" -ForegroundColor Green
        Write-Host "Response preview: $($chatResponse.answer.Substring(0, [Math]::Min(200, $chatResponse.answer.Length)))..." -ForegroundColor Gray
        
        # Check if response contains IM8-specific guidance
        if ($chatResponse.answer -match "IM8|Domain|embed.*PDF|template") {
            Write-Host "✅ Response contains IM8-specific guidance" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Response may not contain IM8-specific guidance" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ Chat test failed: $_" -ForegroundColor Red
    }
} else {
    Write-Host "⚠️ Skipping chat test (no analyst token)" -ForegroundColor Yellow
}
Write-Host ""

# Test 7: Test agentic chat with auditor
Write-Host "Test 7: Testing agentic chat (auditor role-specific prompt)..." -ForegroundColor Yellow
if ($auditorToken) {
    $chatBody = @{
        message = "How do I share the IM8 template with my analyst?"
    } | ConvertTo-Json

    try {
        $headers = @{
            Authorization = "Bearer $auditorToken"
        }
        $chatResponse = Invoke-RestMethod -Uri "$API_BASE_URL/agentic/chat" -Method Post -Body $chatBody -ContentType "application/json" -Headers $headers
        Write-Host "✅ Chat response received" -ForegroundColor Green
        Write-Host "Response preview: $($chatResponse.answer.Substring(0, [Math]::Min(200, $chatResponse.answer.Length)))..." -ForegroundColor Gray
        
        # Check if response contains template sharing guidance
        if ($chatResponse.answer -match "template|/templates/IM8") {
            Write-Host "✅ Response contains template sharing guidance" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Response may not contain template guidance" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ Chat test failed: $_" -ForegroundColor Red
    }
} else {
    Write-Host "⚠️ Skipping chat test (no auditor token)" -ForegroundColor Yellow
}
Write-Host ""

# Test 8: Check if templates directory exists
Write-Host "Test 8: Checking templates directory..." -ForegroundColor Yellow
if (Test-Path "templates") {
    $csvFiles = Get-ChildItem "templates" -Filter "im8_*.csv"
    Write-Host "✅ Templates directory exists" -ForegroundColor Green
    Write-Host "   Found $($csvFiles.Count) IM8 CSV template files" -ForegroundColor Gray
    
    # Check for README
    if (Test-Path "templates/IM8_EXCEL_TEMPLATES_README.md") {
        Write-Host "✅ IM8 template documentation exists" -ForegroundColor Green
    } else {
        Write-Host "⚠️ IM8 template documentation not found" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Templates directory not found" -ForegroundColor Red
}
Write-Host ""

# Summary
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "✅ = Pass, ❌ = Fail, ⚠️ = Warning" -ForegroundColor Gray
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Create actual Excel templates from CSV files in templates/" -ForegroundColor White
Write-Host "2. Upload a test IM8 document via API with evidence_type='im8_assessment_document'" -ForegroundColor White
Write-Host "3. Check that validation runs and document is auto-submitted to 'under_review'" -ForegroundColor White
Write-Host "4. Test auditor approval/rejection workflow" -ForegroundColor White
Write-Host ""
Write-Host "For detailed testing guide, see: IM8_IMPLEMENTATION_COMPLETE.md" -ForegroundColor Cyan
