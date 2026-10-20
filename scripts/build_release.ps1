<#
.SYNOPSIS
    Сборка релизных артефактов Markdown to PDF Converter Pro.
.DESCRIPTION
    Шаги:
      1. Проверка окружения (python, pyinstaller).
      2. Сборка .exe через build.py (PyInstaller onefile).
      3. Опционально — сборка инсталлятора через Inno Setup (iscc.exe), если найден.
    Артефакты складываются в dist/. Скрипт ничего не удаляет без явного флага -Clean.
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts/build_release.ps1
    powershell -ExecutionPolicy Bypass -File scripts/build_release.ps1 -SkipPdfEngine -Console
#>
param(
    [switch]$SkipPdfEngine,   # собрать без встроенного weasyprint.exe (PDF-экспорт в .exe не заработает)
    [switch]$Console,         # собрать с консолью (для отладки CLI)
    [switch]$Clean,           # очистить build/ и dist/ перед сборкой
    [switch]$SkipInstaller    # не собирать инсталлятор, даже если Inno Setup найден
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Write-Step($msg) { Write-Host ""; Write-Host "=== $msg ===" -ForegroundColor Cyan }

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Markdown to PDF Converter Pro — сборка релиза" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# --- 0. Версия ---
$versionLine = (Get-Content "src\__version__.py" | Select-String '__version__').Line
$version = ($versionLine -replace '.*=\s*"', '') -replace '".*', ''
Write-Host "Версия: $version"

# --- 1. Окружение ---
Write-Step "[1/4] Проверка окружения"
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[FAIL] python не найден в PATH." -ForegroundColor Red
    exit 1
}
$hasPyInstaller = python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] PyInstaller не установлен. Установи: pip install pyinstaller" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] python и PyInstaller доступны." -ForegroundColor Green

# --- 2. Очистка (опционально) ---
if ($Clean) {
    Write-Step "[2/4] Очистка build/ и dist/"
    foreach ($d in @("build", "dist")) {
        if (Test-Path $d) { Remove-Item -Recurse -Force $d; Write-Host "  удалён $d" }
    }
} else {
    Write-Step "[2/4] Очистка пропущена (используй -Clean для полной очистки)"
}

# --- 3. PyInstaller ---
Write-Step "[3/4] Сборка .exe (PyInstaller)"
$buildArgs = @()
if ($SkipPdfEngine) { $buildArgs += "--skip-pdf-engine" }
if ($Console)       { $buildArgs += "--console" }
& python build.py @buildArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] build.py завершился с ошибкой ($LASTEXITCODE)." -ForegroundColor Red
    exit 1
}
$exePath = Join-Path $root "dist\MarkdownToPDF.exe"
if (-not (Test-Path $exePath)) {
    Write-Host "[FAIL] Ожидался $exePath, но файла нет." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Собран: $exePath" -ForegroundColor Green

# --- 4. Inno Setup (опционально) ---
Write-Step "[4/4] Инсталлятор (Inno Setup)"
$iscc = $null
foreach ($candidate in @(
    "iscc",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
)) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) { $iscc = $candidate; break }
    if (Test-Path $candidate) { $iscc = $candidate; break }
}

if ($SkipInstaller) {
    Write-Host "[--] Пропущено (-SkipInstaller)." -ForegroundColor Yellow
} elseif ($iscc) {
    & $iscc "installer.iss"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] Inno Setup завершился с ошибкой ($LASTEXITCODE)." -ForegroundColor Red
        exit 1
    }
    $setupPath = Join-Path $root "dist\MarkdownToPDF_Setup.exe"
    if (Test-Path $setupPath) {
        Write-Host "[OK] Инсталлятор: $setupPath" -ForegroundColor Green
    }
} else {
    Write-Host "[--] Inno Setup (iscc.exe) не найден — инсталлятор не собран." -ForegroundColor Yellow
    Write-Host "     Установи: winget install JRSoftware.InnoSetup" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Готово. Артефакты в dist/ (версия $version)." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
