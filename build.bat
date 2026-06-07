@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat || exit /b 1

echo Building MarkdownToPDF...
python build.py
if errorlevel 1 (
    echo Build script failed with error code %errorlevel%.
    pause
    exit /b %errorlevel%
)

echo Cleaning up build artifacts...
if exist "build" rmdir /s /q "build"
if exist "MarkdownToPDF.spec" del /q "MarkdownToPDF.spec"
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

if exist "dist\MarkdownToPDF.exe" (
    move /y "dist\MarkdownToPDF.exe" "MarkdownToPDF.exe"
) else if exist "dist\MarkdownToPDF\MarkdownToPDF.exe" (
    move /y "dist\MarkdownToPDF\MarkdownToPDF.exe" "MarkdownToPDF.exe"
) else (
    echo Build failed: exe not found in dist\.
    pause
    exit /b 1
)

if exist "dist" rmdir /s /q "dist"

echo Done! File: MarkdownToPDF.exe
pause

