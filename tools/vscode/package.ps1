param(
  [string]$OutDir = "dist",
  [string]$OutFile = ""
)

$ErrorActionPreference = "Stop"

$pkg = Get-Content -Raw -Path "package.json" | ConvertFrom-Json

if (-not $OutFile) {
  $OutFile = Join-Path $OutDir ("{0}-{1}.vsix" -f $pkg.name, $pkg.version)
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

Write-Host "Packaging VS Code extension (.vsix)..." -ForegroundColor Cyan
npx @vscode/vsce package -o $OutFile

Write-Host ("Done. Wrote {0}" -f $OutFile) -ForegroundColor Green
