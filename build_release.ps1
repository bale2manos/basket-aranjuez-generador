$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$dist = Join-Path $root "dist\BasketAranjuezGenerador"
$release = Join-Path $root "release"
$version = "1.0.1"
$zip = Join-Path $release "BasketAranjuezGenerador-v$version-windows.zip"

if (Test-Path (Join-Path $root "build")) { Remove-Item (Join-Path $root "build") -Recurse -Force }
if (Test-Path (Join-Path $root "dist")) { Remove-Item (Join-Path $root "dist") -Recurse -Force }
if (Test-Path $release) { Remove-Item $release -Recurse -Force }
New-Item -ItemType Directory -Path $release | Out-Null

python -m PyInstaller --noconfirm --clean --onedir --windowed `
    --name BasketAranjuezGenerador --paths $root\src $root\launcher.py

Copy-Item (Join-Path $root "fonts") $dist -Recurse
New-Item -ItemType Directory -Path (Join-Path $dist "logos") | Out-Null
Get-ChildItem (Join-Path $root "logos") -File | Where-Object { $_.Extension.ToLowerInvariant() -in ".png", ".jpg", ".jpeg" } | Copy-Item -Destination (Join-Path $dist "logos")
Copy-Item (Join-Path $root "data") $dist -Recurse
Copy-Item (Join-Path $root "input") $dist -Recurse
Copy-Item (Join-Path $root "header.png") $dist
Copy-Item (Join-Path $root "cover.png") $dist
Copy-Item (Join-Path $root "foto.png") $dist
Copy-Item (Join-Path $root "README.md") $dist
Copy-Item (Join-Path $root "LICENSE") $dist

Compress-Archive -Path (Join-Path $dist "*") -DestinationPath $zip -CompressionLevel Optimal
Write-Host "Release creada: $zip"
