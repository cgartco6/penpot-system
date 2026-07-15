# ============================================================
# Penpot System - Windows 10 Pro Fully Automated Setup
# ============================================================
# Run as Administrator
# ============================================================

Write-Host "===== Penpot System: Windows Auto-Installer =====" -ForegroundColor Cyan

# ---- Check Admin ----
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "ERROR: Please run PowerShell as Administrator." -ForegroundColor Red
    exit 1
}

# ---- Install via winget ----
function Install-WingetPackage {
    param($PackageId)
    Write-Host "Installing $PackageId via winget..." -ForegroundColor Yellow
    & winget install --silent --accept-package-agreements $PackageId
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Winget failed. Trying chocolatey..." -ForegroundColor Yellow
        & choco install $PackageId -y
    }
}

# ---- Enable WSL2 & Hyper-V ----
Write-Host "Enabling Windows features (WSL2 / Hyper-V)..." -ForegroundColor Yellow
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All -NoRestart
Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -NoRestart
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -NoRestart
wsl --set-default-version 2

# ---- Install Git ----
if (-NOT (Get-Command git -ErrorAction SilentlyContinue)) { Install-WingetPackage "Git.Git" }
else { Write-Host "Git already installed." -ForegroundColor Green }

# ---- Install Docker Desktop ----
if (-NOT (Get-Command docker -ErrorAction SilentlyContinue)) {
    Install-WingetPackage "Docker.DockerDesktop"
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -WindowStyle Hidden
    Start-Sleep -Seconds 30
} else { Write-Host "Docker already installed." -ForegroundColor Green }

# ---- Wait for Docker ----
$dockerReady = $false
for ($i=0; $i -lt 10; $i++) {
    $test = docker info 2>$null
    if ($LASTEXITCODE -eq 0) { $dockerReady = $true; break }
    Write-Host "Waiting for Docker daemon... ($i/10)" -ForegroundColor Cyan
    Start-Sleep -Seconds 5
}
if (-NOT $dockerReady) { Write-Host "Docker failed to start. Please restart manually." -ForegroundColor Red; exit 1 }

# ---- Clone/Update Repo ----
if (-NOT (Test-Path "..\..\docker-compose.yml")) {
    Write-Host "Cloning repository..." -ForegroundColor Yellow
    git clone https://github.com/your-repo/penpot-system.git ..\..\
    Set-Location ..\..\
} else {
    Write-Host "Repository exists. Pulling latest..." -ForegroundColor Yellow
    git pull
}

# ---- Port Conflict Resolver ----
function Test-Port {
    param($Port)
    try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('127.0.0.1', $Port); $tcp.Close(); return $true } catch { return $false }
}
function Get-Free-Port {
    param($StartPort)
    while (Test-Port $StartPort) { $StartPort++ }
    return $StartPort
}

if (-NOT (Test-Path ".env")) { Copy-Item ".env.example" ".env" }

$envContent = Get-Content ".env"
$newEnv = @()
$defaultPorts = @{
    NGINX_PORT=8080; PENPOT_PORT=9001; STRAPI_PORT=1337
    SALEOR_API_PORT=8000; SALEOR_DASHBOARD_PORT=9000
    APPSMITH_PORT=8081; PAYMENT_PORT=8001
}
$assignedPorts = @{}
foreach ($line in $envContent) {
    if ($line -match '^([A-Z_]+)=(\d+)$') {
        $key = $matches[1]
        $val = [int]$matches[2]
        if ($defaultPorts.ContainsKey($key)) {
            if (Test-Port $val) {
                $newPort = Get-Free-Port -StartPort ($val + 1)
                Write-Host "Port $val ($key) in use. Reassigning to $newPort" -ForegroundColor Yellow
                $line = "$key=$newPort"
                $assignedPorts[$key] = $newPort
            } else {
                $assignedPorts[$key] = $val
            }
        }
    }
    $newEnv += $line
}
Set-Content -Path ".env" -Value ($newEnv -join "`n")
Write-Host ".env updated with free ports." -ForegroundColor Green

# ---- Pull & Start ----
Write-Host "Pulling Docker images..." -ForegroundColor Yellow
docker-compose pull
docker-compose up -d

# ---- Print Access ----
$nginxPort = $assignedPorts['NGINX_PORT']
Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "✅ Penpot System is RUNNING!" -ForegroundColor Green
Write-Host "Access via: http://localhost:$nginxPort"
Write-Host "  Design Studio: /design/"
Write-Host "  CMS (Strapi): /cms/admin"
Write-Host "  Web Store: /store/"
Write-Host "  App Builder: /apps/"
Write-Host "  Payment API: /api/docs"
Write-Host "=========================================" -ForegroundColor Cyan
