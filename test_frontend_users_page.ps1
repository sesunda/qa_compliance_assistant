# Frontend Users Page Simulation Test - PowerShell Version
# Tests if each role can access the Users page after the role fix

$API_BASE_URL = "https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io"

$TEST_SCENARIOS = @(
    @{
        RoleName = "Admin (HSA)"
        Username = "hsa_admin"
        Password = "admin123"
        ShouldSeeUsers = $true
    },
    @{
        RoleName = "Analyst (Alice Tan)"
        Username = "hsa_analyst"
        Password = "analyst123"
        ShouldSeeUsers = $true
    },
    @{
        RoleName = "QA Reviewer"
        Username = "hsa_qa"
        Password = "qa123"
        ShouldSeeUsers = $false
    },
    @{
        RoleName = "Auditor"
        Username = "auditor1"
        Password = "auditor123"
        ShouldSeeUsers = $true
    }
)

function Test-UserPageFlow {
    param (
        [hashtable]$Scenario
    )
    
    Write-Host "`n$('='*80)" -ForegroundColor Cyan
    Write-Host "Testing: $($Scenario.RoleName) ($($Scenario.Username))" -ForegroundColor Cyan
    Write-Host "$('='*80)" -ForegroundColor Cyan
    
    # Step 1: Login
    Write-Host "`n[1] Login..." -ForegroundColor Yellow
    try {
        $loginBody = @{
            username = $Scenario.Username
            password = $Scenario.Password
        } | ConvertTo-Json
        
        $loginResponse = Invoke-RestMethod `
            -Uri "$API_BASE_URL/auth/login" `
            -Method Post `
            -Body $loginBody `
            -ContentType "application/json" `
            -ErrorAction Stop
        
        $token = $loginResponse.access_token
        Write-Host "  [OK] Login successful" -ForegroundColor Green
        Write-Host "    Token: $($token.Substring(0, 20))..." -ForegroundColor Gray
    }
    catch {
        Write-Host "  [FAIL] Login FAILED: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    
    $headers = @{
        Authorization = "Bearer $token"
    }
    
    # Step 2: Get current user
    Write-Host "`n[2] Fetching current user info (/auth/me)..." -ForegroundColor Yellow
    try {
        $meResponse = Invoke-RestMethod `
            -Uri "$API_BASE_URL/auth/me" `
            -Method Get `
            -Headers $headers `
            -ErrorAction Stop
        
        Write-Host "  [OK] User info retrieved" -ForegroundColor Green
        Write-Host "    Username: $($meResponse.username)" -ForegroundColor Gray
        Write-Host "    Email: $($meResponse.email)" -ForegroundColor Gray
        Write-Host "    Role (DB): $($meResponse.role.name)" -ForegroundColor Gray
    }
    catch {
        Write-Host "  [FAIL] Get /auth/me FAILED: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    
    # Step 3: Fetch users list
    Write-Host "`n[3] Fetching users list (/auth/users)..." -ForegroundColor Yellow
    if ($Scenario.ShouldSeeUsers) {
        Write-Host "    Expected: Should load" -ForegroundColor Gray
    } else {
        Write-Host "    Expected: Should be forbidden" -ForegroundColor Gray
    }
    
    try {
        $usersResponse = Invoke-RestMethod `
            -Uri "$API_BASE_URL/auth/users" `
            -Method Get `
            -Headers $headers `
            -ErrorAction Stop
        
        if ($Scenario.ShouldSeeUsers) {
            Write-Host "  [OK] Users list loaded successfully" -ForegroundColor Green
            Write-Host "    Total users: $($usersResponse.Count)" -ForegroundColor Gray
            if ($usersResponse.Count -gt 0) {
                Write-Host "    First user: $($usersResponse[0].username) ($($usersResponse[0].email))" -ForegroundColor Gray
            }
            return $true
        } else {
            Write-Host "  [FAIL] FAILED: Should be forbidden, but got 200!" -ForegroundColor Red
            return $false
        }
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        
        if ($Scenario.ShouldSeeUsers) {
            Write-Host "  [FAIL] FAILED: Expected 200, got $statusCode" -ForegroundColor Red
            Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
            return $false
        } else {
            if ($statusCode -eq 403) {
                Write-Host "  [OK] Correctly blocked (403 Forbidden)" -ForegroundColor Green
                return $true
            } else {
                Write-Host "  [WARN] Unexpected status: $statusCode" -ForegroundColor Yellow
                return $false
            }
        }
    }
}

# Main execution
Write-Host "$('='*80)" -ForegroundColor Cyan
Write-Host "FRONTEND USERS PAGE SIMULATION TEST" -ForegroundColor Cyan
Write-Host "$('='*80)" -ForegroundColor Cyan
Write-Host "`nAPI: $API_BASE_URL" -ForegroundColor White
Write-Host "Testing $($TEST_SCENARIOS.Count) user roles`n" -ForegroundColor White

$results = @()
foreach ($scenario in $TEST_SCENARIOS) {
    $success = Test-UserPageFlow -Scenario $scenario
    $results += @{
        Role = $scenario.RoleName
        Success = $success
    }
}

# Summary
Write-Host "`n$('='*80)" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "$('='*80)`n" -ForegroundColor Cyan

foreach ($result in $results) {
    $icon = if ($result.Success) { "[PASS]" } else { "[FAIL]" }
    $color = if ($result.Success) { "Green" } else { "Red" }
    Write-Host "  $icon $($result.Role)" -ForegroundColor $color
}

$passed = ($results | Where-Object { $_.Success }).Count
$total = $results.Count
$percentage = [math]::Round(($passed / $total) * 100, 0)

Write-Host "`n$('='*80)" -ForegroundColor Cyan
Write-Host "Result: $passed/$total tests passed ($percentage%)" -ForegroundColor $(if ($passed -eq $total) { "Green" } else { "Yellow" })
Write-Host "$('='*80)`n" -ForegroundColor Cyan

if ($passed -eq $total) {
    Write-Host "[SUCCESS] All tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "[FAIL] Some tests failed" -ForegroundColor Red
    exit 1
}
