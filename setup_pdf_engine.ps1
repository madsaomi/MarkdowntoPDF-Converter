<#
.SYNOPSIS
    Диагностика и установка PDF-движка WeasyPrint для MarkdownToPDF Converter Pro.

.DESCRIPTION
    Цепочка проверок:
      1. Портативный weasyprint.exe в weasyprint-windows/dist/ (приоритет, обязателен для сборки .exe).
      2. pip-пакет weasyprint (fallback для разработки; требует GTK3 на Windows).
    Скрипт ничего не удаляет и не изменяет систему без явного подтверждения.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File setup_pdf_engine.ps1
#>

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$exe  = Join-Path $root "weasyprint-windows\dist\weasyprint.exe"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " PDF-движок WeasyPrint — диагностика" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# --- 1. Портативный exe ---
Write-Host "`n[1] Портативный движок: $exe"
if (Test-Path $exe) {
    Write-Host "    [OK] Найден — приоритетный движок активен." -ForegroundColor Green
} else {
    Write-Host "    [--] Не найден." -ForegroundColor Yellow
    Write-Host "    Для дистрибутивов и сборки .exe положи сюда портативный weasyprint.exe:"
    Write-Host "        $exe"
}

# --- 2. pip-пакет ---
Write-Host "`n[2] pip-пакет weasyprint (fallback для разработки):"
$hasPip = python -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('weasyprint') else 1)" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "    [OK] Пакет установлен." -ForegroundColor Green
    $importOk = python -c "import weasyprint" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    [OK] Импорт работает (GTK3 доступен) — PDF-рендер функционален." -ForegroundColor Green
    } else {
        Write-Host "    [WARN] Пакет установлен, но import weasyprint падает — вероятно, нет GTK3." -ForegroundColor Yellow
        Write-Host "    Решение (Windows):"
        Write-Host "      winget install MSYS2.MSYS2"
        Write-Host "      msys2 -c 'pacman -S --noconfirm mingw-w64-x86_64-gtk3'"
        Write-Host "      затем добавь C:\msys64\mingw64\bin в PATH"
        Write-Host "      Подробнее: https://doc.courtbouillon.org/weasyprint/stable/first_install.html"
    }
} else {
    Write-Host "    [--] Не установлен." -ForegroundColor Yellow
    $answer = Read-Host "    Установить pip install weasyprint? [y/N]"
    if ($answer -match "^[yY]") {
        pip install weasyprint
        Write-Host "    Готово. Если рендер всё ещё не работает — нужен GTK3 (см. выше)." -ForegroundColor Green
    } else {
        Write-Host "    Пропущено. PDF-экспорт будет недоступен до установки движка." -ForegroundColor Yellow
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host " Итог: exe = $(if (Test-Path $exe) {'OK'} else {'нет'}), см. шаги выше." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
