# Carrega variáveis do .env se existir
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

function release {
    # Read current version from pyproject.toml
    $content = Get-Content "pyproject.toml"
    $versionLine = $content | Where-Object { $_ -match '^version = "(.+)"$' }
    $currentVersion = $matches[1]
    
    # Parse version parts
    $versionParts = $currentVersion.Split('.')
    $major = [int]$versionParts[0]
    $minor = [int]$versionParts[1]
    $patch = [int]$versionParts[2]
    
    # Increment patch version
    $patch++
    $newVersion = "$major.$minor.$patch"
    
    # Update pyproject.toml
    $newContent = $content -replace '^version = ".+"$', "version = `"$newVersion`""
    $newContent | Set-Content "pyproject.toml"
    
    Write-Host "Version bumped from $currentVersion to $newVersion"
    
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    uv build
    uv publish --token $env:UV_PUBLISH_TOKEN

    # Dispara webhook do Portainer para atualizar o deploy
    $webhookUrl = "https://portainer.uniube.br/api/webhooks/ccfe08c6-517a-4d98-b21c-5380846893de"
    if ($LASTEXITCODE -eq 0) {
        try {
            Write-Host "Triggering Portainer webhook..." -ForegroundColor Cyan
            $response = Invoke-WebRequest -Method Post -Uri $webhookUrl -UseBasicParsing -TimeoutSec 30
            $statusCode = $response.StatusCode
            $statusDesc = $response.StatusDescription
            Write-Host "Webhook response: $statusCode $statusDesc" -ForegroundColor Green
        }
        catch {
            Write-Warning "Falha ao acionar o webhook do Portainer: $($_.Exception.Message)"
        }
    }
    else {
        Write-Warning "Publicação falhou (código $LASTEXITCODE). Ignorando chamada ao webhook do Portainer."
    }
}

# Executa a função release automaticamente
if ($args.Count -gt 0) {
    & $args[0]
} else {
    release
}