[net.ServicePointManager]::SecurityProtocol = 'Tls12'
$ErrorActionPreference = "Stop"

$InstallDir = "C:\Tools\cloudflared"
if (!(Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

$arch = [Environment]::Is64BitOperatingSystem ? 'windows-amd64' : 'windows-386'
$url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-$arch.exe"
$cloudflaredExe = Join-Path $InstallDir "cloudflared.exe"

Write-Host "Downloading cloudflared $arch..."
Invoke-WebRequest -Uri $url -OutFile $cloudflaredExe -UseBasicParsing

Write-Host "cloudflared installed at $cloudflaredExe"
& $cloudflaredExe --version
