# Clear conversation history from Azure PostgreSQL database
# This resets all agentic chat conversations for fresh testing

$ResourceGroup = "rg-qca-dev"
$PostgresServer = "psql-qca-dev-2f37g0"
$DatabaseName = "qa_compliance"
$AdminUser = "postgres"

Write-Host "🗑️  Clearing Conversation History..." -ForegroundColor Yellow
Write-Host ""

# Prompt for password
$Password = Read-Host -AsSecureString "Enter PostgreSQL admin password"
$PlainPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Password))

# Execute SQL to clear conversations
$SqlCommand = @"
DELETE FROM conversation_sessions;
SELECT 'Cleared ' || COUNT(*) || ' conversations' AS result FROM conversation_sessions;
"@

Write-Host "Executing SQL..." -ForegroundColor Cyan

# Use psql command through Azure
$env:PGPASSWORD = $PlainPassword
$ServerFQDN = "$PostgresServer.postgres.database.azure.com"

psql -h $ServerFQDN -U $AdminUser -d $DatabaseName -c "$SqlCommand"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Conversation history cleared successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 Next steps:" -ForegroundColor Yellow
    Write-Host "   1. Refresh the frontend (Ctrl+F5)" -ForegroundColor Gray
    Write-Host "   2. Start a new conversation" -ForegroundColor Gray
    Write-Host "   3. All timestamps will now show Singapore time (SGT)" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "❌ Failed to clear conversations" -ForegroundColor Red
    Write-Host "   Try running the SQL manually:" -ForegroundColor Gray
    Write-Host "   DELETE FROM conversation_sessions;" -ForegroundColor Cyan
}
