# Budowanie Lyrics Manager Pro do pliku .exe
# Uruchomienie:  powershell -ExecutionPolicy Bypass -File build.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "== Zaleznosci ==" -ForegroundColor Cyan
python -m pip install --quiet --upgrade -r requirements.txt
python -m pip install --quiet --upgrade pyinstaller pillow

Write-Host "== Ikona ==" -ForegroundColor Cyan
python tools\make_icon.py

Write-Host "== Testy ==" -ForegroundColor Cyan
python tests\test_analysis.py
if (-not $?) { throw "Testy analityczne nie przeszly" }
python tests\test_spelling.py
if (-not $?) { throw "Testy pisowni nie przeszly" }
python tests\test_shortcuts_help.py
if (-not $?) { throw "Testy skrotow i instrukcji nie przeszly" }
python tests\test_ui_smoke.py
if (-not $?) { throw "Test dymny interfejsu nie przeszedl" }

Write-Host "== Budowanie .exe ==" -ForegroundColor Cyan
python -m PyInstaller --noconfirm --clean LyricsManagerPro.spec

$exe = Join-Path $PSScriptRoot "dist\LyricsManagerPro.exe"
if (Test-Path $exe) {
    $mb = [math]::Round((Get-Item $exe).Length / 1MB, 1)
    Write-Host "`nGotowe: $exe ($mb MB)" -ForegroundColor Green
} else {
    throw "Nie powstal plik .exe"
}
