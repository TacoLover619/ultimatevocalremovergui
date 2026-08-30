[CmdletBinding()]
param(
    [switch]$CleanEnvironment,
    [string]$PythonBootstrap
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = $PSScriptRoot
$VirtualEnvironment = Join-Path $ProjectRoot '.venv'
$Python = Join-Path $VirtualEnvironment 'Scripts\python.exe'
$LockFile = Join-Path $ProjectRoot 'requirements-windows.lock.txt'
$DownloadDirectory = Join-Path $ProjectRoot 'third_party\downloads'
$FfmpegArchive = Join-Path $DownloadDirectory 'ffmpeg-release-essentials.zip'
$RubberBandArchive = Join-Path $DownloadDirectory 'rubberband-windows.zip'
$BinaryDirectory = Join-Path $ProjectRoot 'third_party\bin'
$FfmpegExecutable = Join-Path $BinaryDirectory 'ffmpeg.exe'
$RubberBandExecutable = Join-Path $BinaryDirectory 'rubberband.exe'
$SndFileLibrary = Join-Path $BinaryDirectory 'sndfile.dll'

if ($CleanEnvironment -and (Test-Path -LiteralPath $VirtualEnvironment)) {
    $resolvedEnvironment = (Resolve-Path -LiteralPath $VirtualEnvironment).Path
    if (-not $resolvedEnvironment.StartsWith($ProjectRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a virtual environment outside the project: $resolvedEnvironment"
    }
    Remove-Item -LiteralPath $resolvedEnvironment -Recurse -Force
}

if (-not (Test-Path -LiteralPath $Python)) {
    if (-not $PythonBootstrap) {
        $PythonBootstrap = (Get-Command python -ErrorAction Stop).Source
    }
    & $PythonBootstrap -m venv $VirtualEnvironment
}

& $Python -m ensurepip --upgrade

New-Item -ItemType Directory -Path $DownloadDirectory -Force | Out-Null
New-Item -ItemType Directory -Path $BinaryDirectory -Force | Out-Null

if (-not (Test-Path -LiteralPath $FfmpegExecutable)) {
    & curl.exe -L --fail --retry 3 -o $FfmpegArchive 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'
    $FfmpegExtract = Join-Path $ProjectRoot 'third_party\ffmpeg'
    Expand-Archive -LiteralPath $FfmpegArchive -DestinationPath $FfmpegExtract -Force
    Copy-Item -LiteralPath (Get-ChildItem -LiteralPath $FfmpegExtract -Filter ffmpeg.exe -Recurse -File).FullName -Destination $FfmpegExecutable
}

if (-not (Test-Path -LiteralPath $RubberBandExecutable) -or -not (Test-Path -LiteralPath $SndFileLibrary)) {
    & curl.exe -L --fail --retry 3 -o $RubberBandArchive 'https://breakfastquay.com/files/releases/rubberband-3.3.0-gpl-executable-windows.zip'
    $RubberBandExtract = Join-Path $ProjectRoot 'third_party\rubberband'
    Expand-Archive -LiteralPath $RubberBandArchive -DestinationPath $RubberBandExtract -Force
    Copy-Item -LiteralPath (Get-ChildItem -LiteralPath $RubberBandExtract -Filter rubberband.exe -Recurse -File).FullName -Destination $RubberBandExecutable
    Copy-Item -LiteralPath (Get-ChildItem -LiteralPath $RubberBandExtract -Filter sndfile.dll -Recurse -File).FullName -Destination $SndFileLibrary
}

$RequiredBinaries = @($FfmpegExecutable, $RubberBandExecutable, $SndFileLibrary)
foreach ($RequiredBinary in $RequiredBinaries) {
    if (-not (Test-Path -LiteralPath $RequiredBinary -PathType Leaf)) {
        throw "Required bundled binary is missing: $RequiredBinary"
    }
}

& $Python -m pip install --upgrade pip
if (Test-Path -LiteralPath $LockFile) {
    & $Python -m pip install -r $LockFile
} else {
    & $Python -m pip install -r (Join-Path $ProjectRoot 'requirements-windows.in')
    & $Python -m pip freeze --local | Set-Content -Encoding utf8 $LockFile
}
& $Python -m PyInstaller --noconfirm --clean (Join-Path $ProjectRoot 'UVR-Windows.spec')

$InnoCompiler = @(
    (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'),
    'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
    'C:\Program Files\Inno Setup 6\ISCC.exe'
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if (-not $InnoCompiler) {
    throw 'Inno Setup 6.5 or newer is required to build the v6.0 installer. Install JRSoftware.InnoSetup with winget.'
}

& $InnoCompiler (Join-Path $ProjectRoot 'UVR-Windows.iss')
