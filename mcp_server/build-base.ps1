# Build MCP Base Image (run once or when dependencies change)
# This creates a cached base image with all dependencies installed

Write-Host "Building MCP base image with dependencies..." -ForegroundColor Cyan

# Build base image with all dependencies
az acr build `
    --registry acrqcadev2f37g0 `
    --image qca-mcp-base:latest `
    --file Dockerfile `
    .

Write-Host "`n✅ Base image built successfully!" -ForegroundColor Green
Write-Host "Future builds using Dockerfile.fast will be much faster (~30 seconds vs ~2 minutes)" -ForegroundColor Yellow
