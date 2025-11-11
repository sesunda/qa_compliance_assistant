# Check Alice's Role from API
$apiUrl = "https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io"

# Login as Alice
$loginBody = @{
    username = "alice"
    password = "alice123"
} | ConvertTo-Json

try {
    Write-Host "=== Logging in as Alice ===" -ForegroundColor Cyan
    $loginResponse = Invoke-RestMethod -Uri "$apiUrl/auth/login" -Method POST -Body $loginBody -ContentType "application/json"
    $token = $loginResponse.access_token
    
    Write-Host "Login successful!" -ForegroundColor Green
    Write-Host "Token: $($token.Substring(0, 20))..." -ForegroundColor Gray
    
    # Get current user info
    Write-Host "`n=== Getting Alice's User Info ===" -ForegroundColor Cyan
    $headers = @{
        Authorization = "Bearer $token"
    }
    
    $userInfo = Invoke-RestMethod -Uri "$apiUrl/auth/me" -Method GET -Headers $headers
    
    Write-Host "`nUser Details:" -ForegroundColor Yellow
    Write-Host "  Username: $($userInfo.username)" -ForegroundColor White
    Write-Host "  Full Name: $($userInfo.full_name)" -ForegroundColor White
    Write-Host "  Email: $($userInfo.email)" -ForegroundColor White
    Write-Host "  Agency ID: $($userInfo.agency_id)" -ForegroundColor White
    Write-Host "  Role ID: $($userInfo.role_id)" -ForegroundColor White
    
    if ($userInfo.role) {
        Write-Host "`nRole Details:" -ForegroundColor Yellow
        Write-Host "  Role Name: '$($userInfo.role.name)'" -ForegroundColor White
        Write-Host "  Role Description: $($userInfo.role.description)" -ForegroundColor White
    } else {
        Write-Host "`nERROR: No role information!" -ForegroundColor Red
    }
    
    Write-Host "`n=== Full User Object ===" -ForegroundColor Cyan
    $userInfo | ConvertTo-Json -Depth 5
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}
