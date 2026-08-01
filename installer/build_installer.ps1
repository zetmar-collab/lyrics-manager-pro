# Budowanie instalatora Lyrics Manager Pro (Inno Setup)
#
# Uruchomienie:  powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1
# Wynik:         dist\LyricsManagerPro-Setup-<wersja>.exe
#
# Skrypt sam znajduje kompilator ISCC.exe - Inno Setup bywa instalowany zarowno
# w Program Files, jak i per uzytkownik w AppData, a wersja 6 i 7 moga stac obok
# siebie. Preferujemy wersje stabilna 6.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Find-InnoCompiler {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 7\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 7\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 7\ISCC.exe"
    )
    foreach ($p in $candidates) { if (Test-Path $p) { return $p } }

    $inPath = Get-Command "iscc" -ErrorAction SilentlyContinue
    if ($inPath) { return $inPath.Source }
    return $null
}

$iscc = Find-InnoCompiler
if (-not $iscc) {
    throw "Nie znaleziono kompilatora Inno Setup (ISCC.exe). Pobierz go z https://jrsoftware.org/isdl.php"
}
Write-Host "Kompilator: $iscc" -ForegroundColor Cyan

$appExe = Join-Path $root "dist\LyricsManagerPro.exe"
if (-not (Test-Path $appExe)) {
    throw "Brak dist\LyricsManagerPro.exe - zbuduj najpierw aplikacje: build.ps1"
}

foreach ($required in @("LICENSE", "README.md", "assets\app.ico", "installer\info_before.txt")) {
    if (-not (Test-Path (Join-Path $root $required))) { throw "Brak pliku: $required" }
}

& $iscc "/Qp" (Join-Path $root "installer\LyricsManagerPro.iss")
if ($LASTEXITCODE -ne 0) { throw "Kompilacja instalatora nie powiodla sie (kod $LASTEXITCODE)" }

$setup = Get-ChildItem (Join-Path $root "dist") -Filter "LyricsManagerPro-Setup-*.exe" |
         Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $setup) { throw "Instalator nie powstal" }

$mb = [math]::Round($setup.Length / 1MB, 1)
Write-Host "`nGotowe: $($setup.FullName) ($mb MB)" -ForegroundColor Green
