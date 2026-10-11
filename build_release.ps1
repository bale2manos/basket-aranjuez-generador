$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$buildDir = Join-Path $projectRoot "build\generator"
$distDir = Join-Path $projectRoot "dist\BasketAranjuezGenerador"
$releaseDir = Join-Path $projectRoot "release"
$version = "2.0.0"
$archivePath = Join-Path $releaseDir "BasketAranjuezGenerador-v$version-windows.zip"

Push-Location -LiteralPath $projectRoot
try {
    $assetJson = python -B -c "import sys,json; sys.path.insert(0,'src'); from config import default_config; from generador_horarios.resources import validate_render_assets; c=default_config(); validate_render_assets(c); print(json.dumps({'background':str(c.background_image_path),'fonts':list(dict.fromkeys(str(p) for p in [c.font_path,c.number_font_path,c.cover_title_font_path,c.cover_date_font_path])),'logos':str(c.logos_dir),'club_map':str(c.club_logo_map_path),'venue_map':str(c.venue_map_path),'excel':str(c.excel_path)}))"
    if ($LASTEXITCODE -ne 0) { throw "No se puede compilar: revisa las fuentes y la foto en config.py." }
    $assets = $assetJson | ConvertFrom-Json

    foreach ($target in @($buildDir, $distDir)) {
        $resolvedTarget = [System.IO.Path]::GetFullPath($target)
        if (-not $resolvedTarget.StartsWith($projectRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "La carpeta de compilacion queda fuera del proyecto: $resolvedTarget"
        }
        if (Test-Path -LiteralPath $resolvedTarget) { Remove-Item -LiteralPath $resolvedTarget -Recurse -Force }
    }
    New-Item -ItemType Directory -Path $buildDir, $releaseDir -Force | Out-Null
    python -m PyInstaller --noconfirm --clean --onedir --windowed `
        --name BasketAranjuezGenerador --paths (Join-Path $projectRoot "src") `
        --workpath $buildDir --specpath $buildDir --distpath (Join-Path $projectRoot "dist") `
        --exclude-module numpy --exclude-module pandas --exclude-module matplotlib --exclude-module scipy `
        (Join-Path $projectRoot "launcher.py")
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller no pudo crear el ejecutable." }

    New-Item -ItemType Directory -Path (Join-Path $distDir "fonts"), (Join-Path $distDir "logos"), (Join-Path $distDir "data"), (Join-Path $distDir "input") -Force | Out-Null
    foreach ($font in $assets.fonts) { Copy-Item -LiteralPath $font -Destination (Join-Path $distDir "fonts") }
    Get-ChildItem -LiteralPath (Join-Path $projectRoot "fonts") -File | Where-Object { $_.Extension.ToLowerInvariant() -in ".ttf", ".otf" } | Copy-Item -Destination (Join-Path $distDir "fonts") -Force
    Get-ChildItem -LiteralPath (Join-Path $projectRoot "fonts") -Filter "*-OFL.txt" -File | Copy-Item -Destination (Join-Path $distDir "fonts")
    Get-ChildItem -LiteralPath $assets.logos -File | Where-Object { $_.Extension.ToLowerInvariant() -in ".png", ".jpg", ".jpeg" } | Copy-Item -Destination (Join-Path $distDir "logos")
    Copy-Item -LiteralPath $assets.background -Destination $distDir
    Copy-Item -LiteralPath $assets.club_map, $assets.venue_map -Destination (Join-Path $distDir "data")
    '[]' | Set-Content -LiteralPath (Join-Path $distDir "data\result_overrides.json") -Encoding UTF8
    if (Test-Path -LiteralPath $assets.excel) { Copy-Item -LiteralPath $assets.excel -Destination (Join-Path $distDir "input\ejemplo.xlsx") }
    $readmePath = Join-Path $projectRoot "README_GENERADOR.md"
    if (-not (Test-Path -LiteralPath $readmePath)) { $readmePath = Join-Path $projectRoot "README.md" }
    Copy-Item -LiteralPath $readmePath -Destination (Join-Path $distDir "README.md")
    Copy-Item -LiteralPath (Join-Path $projectRoot "LICENSE") -Destination $distDir
    Compress-Archive -Path (Join-Path $distDir "*") -DestinationPath $archivePath -CompressionLevel Optimal -Force
    Write-Host "Release creada: $archivePath"
} finally {
    Pop-Location
}
