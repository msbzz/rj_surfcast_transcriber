param(
    [Parameter(Mandatory=$true)]
    [string]$AudioPath,
    [string]$BaseUrl = "http://127.0.0.1:9001",
    [string]$Token = ""
)

if (-not (Test-Path $AudioPath)) {
    throw "Arquivo não encontrado: $AudioPath"
}

Write-Host "Testando health check..."
Invoke-RestMethod -Method Get -Uri "$BaseUrl/health" | ConvertTo-Json

$headers = @{}
if ($Token) { $headers["Authorization"] = "Bearer $Token" }

Write-Host "Enviando áudio para transcrição..."
curl.exe -X POST "$BaseUrl/v1/transcribe" `
    -H "Accept: application/json" `
    $(if ($Token) { @("-H", "Authorization: Bearer $Token") }) `
    -F "audio=@$AudioPath"
