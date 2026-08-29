<#
    Budowanie pakietu MSIX dla Microsoft Store.

    Uruchomienie:
        powershell -ExecutionPolicy Bypass -File msix\build_msix.ps1
        powershell -ExecutionPolicy Bypass -File msix\build_msix.ps1 -Sign -PfxPath cert.pfx -PfxPassword haslo

    Wynik:
        dist\LyricsManagerPro-1.0.0.0.msix

    Do wyslania do Partner Center pakiet NIE musi byc podpisany - Microsoft
    podpisuje go sam. Podpis jest potrzebny tylko do instalacji lokalnej,
    zeby sprawdzic pakiet przed wyslaniem.
#>

param(
    [switch]$Sign,
    [string]$PfxPath = "",
    [string]$PfxPassword = "",
    [string]$Version = "1.0.0.0"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# --- narzedzia z Windows SDK ---------------------------------------------

function Find-SdkTool([string]$name) {
    $bases = @("${env:ProgramFiles(x86)}\Windows Kits\10\bin", "$env:ProgramFiles\Windows Kits\10\bin")
    foreach ($base in $bases) {
        if (-not (Test-Path $base)) { continue }
        $versions = Get-ChildItem $base -Directory -ErrorAction SilentlyContinue |
                    Where-Object { $_.Name -match '^10\.' } |
                    Sort-Object { [version]($_.Name) } -Descending
        foreach ($v in $versions) {
            $candidate = Join-Path $v.FullName "x64\$name"
            if (Test-Path $candidate) { return $candidate }
        }
    }
    return $null
}

$makeappx = Find-SdkTool "makeappx.exe"
$makepri  = Find-SdkTool "makepri.exe"
if (-not $makeappx) { throw "Nie znaleziono makeappx.exe. Zainstaluj Windows SDK." }
Write-Host "makeappx: $makeappx" -ForegroundColor Cyan

# --- 1. aplikacja ---------------------------------------------------------

$appDir = Join-Path $root "dist\LyricsManagerPro-msix"
if (-not (Test-Path (Join-Path $appDir "LyricsManagerPro.exe"))) {
    Write-Host "Buduje aplikacje (wariant katalogowy)..." -ForegroundColor Cyan
    python -m PyInstaller --noconfirm --clean LyricsManagerPro-msix.spec
    if ($LASTEXITCODE -ne 0) { throw "Budowanie aplikacji nie powiodlo sie" }
}

# --- 2. grafiki -----------------------------------------------------------

Write-Host "Generuje grafiki Store..." -ForegroundColor Cyan
python tools\make_icon.py | Out-Null
python tools\make_store_assets.py | Out-Null

# --- 3. uklad pakietu -----------------------------------------------------

$layout = Join-Path $root "build\msix-layout"
if (Test-Path $layout) { Remove-Item $layout -Recurse -Force }
New-Item -ItemType Directory -Force $layout | Out-Null

Copy-Item "$appDir\*" $layout -Recurse -Force
Copy-Item (Join-Path $root "msix\Assets") $layout -Recurse -Force
Copy-Item (Join-Path $root "msix\AppxManifest.xml") $layout -Force

# wersja w manifescie musi sie zgadzac z ta w nazwie pliku
$manifestPath = Join-Path $layout "AppxManifest.xml"
$xml = [xml](Get-Content $manifestPath)
$xml.Package.Identity.Version = $Version
$xml.Save($manifestPath)

Write-Host "Uklad: $layout ($([math]::Round((Get-ChildItem $layout -Recurse -File | Measure-Object Length -Sum).Sum/1MB,1)) MB)" -ForegroundColor Cyan

# --- 4. resources.pri -----------------------------------------------------
# Bez tego Windows nie wybierze wariantow grafik (scale-200, targetsize-*).

if ($makepri) {
    $priConfig = Join-Path $root "build\priconfig.xml"
    & $makepri createconfig /cf $priConfig /dq "pl-PL_en-US" /o | Out-Null
    Push-Location $layout
    & $makepri new /pr $layout /cf $priConfig /of (Join-Path $layout "resources.pri") /o | Out-Null
    Pop-Location
    if (Test-Path (Join-Path $layout "resources.pri")) {
        Write-Host "resources.pri wygenerowany" -ForegroundColor Cyan
    }
} else {
    Write-Warning "Brak makepri.exe - pakiet powstanie bez resources.pri"
}

# --- 5. pakowanie ---------------------------------------------------------

$out = Join-Path $root "dist\LyricsManagerPro-$Version.msix"
if (Test-Path $out) { Remove-Item $out -Force }
& $makeappx pack /d $layout /p $out /o
if ($LASTEXITCODE -ne 0) { throw "makeappx pack nie powiodl sie (kod $LASTEXITCODE)" }

# --- 6. podpis (opcjonalny, tylko do testow lokalnych) --------------------

if ($Sign) {
    $signtool = Find-SdkTool "signtool.exe"
    if (-not $signtool) { throw "Nie znaleziono signtool.exe" }
    if (-not (Test-Path $PfxPath)) { throw "Nie znaleziono certyfikatu: $PfxPath" }
    $args = @("sign", "/fd", "SHA256", "/a", "/f", $PfxPath)
    if ($PfxPassword) { $args += @("/p", $PfxPassword) }
    $args += $out
    & $signtool @args
    if ($LASTEXITCODE -ne 0) { throw "Podpisywanie nie powiodlo sie" }
    Write-Host "Pakiet podpisany" -ForegroundColor Green
}

$size = [math]::Round((Get-Item $out).Length / 1MB, 1)
Write-Host "`nGotowe: $out ($size MB)" -ForegroundColor Green
if (-not $Sign) {
    Write-Host "Pakiet jest niepodpisany - tak wlasnie wysyla sie go do Partner Center." -ForegroundColor Yellow
}
