$envVars = @{}
Get-Content ".env" | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') { $envVars[$matches[1]] = $matches[2].Trim() }
}
$nginxPort = $envVars['NGINX_PORT'] -or "8080"
Write-Host "Starting Penpot System on http://localhost:$nginxPort" -ForegroundColor Cyan
docker-compose up -d
Write-Host "Access: http://localhost:$nginxPort" -ForegroundColor Green
