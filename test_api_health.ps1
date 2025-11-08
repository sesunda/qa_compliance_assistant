# Test API Health
$apiUrl = "https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io"

Write-Host "Testing API endpoints..." -ForegroundColor Cyan

# Test health endpoint
Write-Host "`n1. Testing /health endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$apiUrl/health" -Method GET -UseBasicParsing
    Write-Host "✓ Health check: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($response.Content)"
} catch {
    Write-Host "✗ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test root endpoint
Write-Host "`n2. Testing / endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$apiUrl/" -Method GET -UseBasicParsing
    Write-Host "✓ Root endpoint: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($response.Content)"
} catch {
    Write-Host "✗ Root endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test CORS preflight
Write-Host "`n3. Testing CORS preflight (OPTIONS)..." -ForegroundColor Yellow
try {
    $headers = @{
        "Origin" = "https://ca-frontend-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io"
        "Access-Control-Request-Method" = "GET"
    }
    $response = Invoke-WebRequest -Uri "$apiUrl/health" -Method OPTIONS -Headers $headers -UseBasicParsing
    Write-Host "✓ CORS preflight: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "CORS Headers:"
    $response.Headers.GetEnumerator() | Where-Object { $_.Key -like "*Access-Control*" } | ForEach-Object {
        Write-Host "  $($_.Key): $($_.Value)"
    }
} catch {
    Write-Host "✗ CORS preflight failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nDone!" -ForegroundColor Cyan
