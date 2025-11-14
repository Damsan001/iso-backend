# =========================
# run_static_tests.ps1
# Reemplazo completo (solo ASCII)
# =========================

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Write-Info($msg) { Write-Host ("[INFO]  {0}" -f $msg) -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host ("[OK]    {0}" -f $msg) -ForegroundColor Green }
function Write-Warn($msg) { Write-Host ("[WARN]  {0}" -f $msg) -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host ("[ERROR] {0}" -f $msg) -ForegroundColor Red }

# ----- Paths / timestamp -----
$root    = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$stamp   = (Get-Date -Format 'yyyyMMdd-HHmmss')
$reports = Join-Path $root 'reports'
New-Item -ItemType Directory -Force -Path $reports | Out-Null

$ruffFile     = Join-Path $reports ("ruff-{0}.txt" -f $stamp)
$mypyFile     = Join-Path $reports ("mypy-{0}.txt" -f $stamp)
$banditFile   = Join-Path $reports ("bandit-{0}.txt" -f $stamp)
$pipauditFile = Join-Path $reports ("pip-audit-{0}.txt" -f $stamp)
$summaryFile  = Join-Path $reports ("summary-{0}.txt" -f $stamp)
$zipFile      = Join-Path $reports ("static-analysis-{0}.zip" -f $stamp)

# ----- Ejecutar y capturar -----
function Run-And-Capture([string]$name, [ScriptBlock]$block, [string]$outFile) {
    Write-Info ("Ejecutando {0}..." -f $name)
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $exit = 0
    try {
        $output = & $block 2>&1
        $exit = $LASTEXITCODE
        if ($null -eq $exit) { $exit = 0 }
        $output | Out-File -FilePath $outFile -Encoding utf8
    } catch {
        $_ | Out-File -FilePath $outFile -Encoding utf8
        $exit = 1
    }
    $sw.Stop()
    Write-Info ("{0} exit-code {1} en {2:n1}s" -f $name, $exit, $sw.Elapsed.TotalSeconds)
    return $exit
}

# ----- Buscar Python (venv o sistema) -----
function Find-Python {
    if ($env:VIRTUAL_ENV) {
        $p = Join-Path $env:VIRTUAL_ENV 'Scripts\python.exe'
        if (Test-Path $p) { return $p }
    }
    $candidates = @(
        '.venv\Scripts\python.exe',
        'venv\Scripts\python.exe',
        'env\Scripts\python.exe'
    ) | ForEach-Object { Join-Path $root $_ }

    foreach ($c in $candidates) { if (Test-Path $c) { return $c } }

    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        try {
            $p = & py -3 -c "import sys;print(sys.executable)" 2>$null
            if ($p) { return $p.Trim() }
        } catch {}
    }
    return $null
}

$python = Find-Python
if (-not $python) {
    Write-Err 'No se encontró python ni virtualenv activo. Activa tu venv e inténtalo de nuevo.'
    exit 1
}

# Escribir versión al summary
("Python exe : {0}" -f $python) | Out-File -FilePath $summaryFile -Encoding utf8
("Python ver : " + (& $python -c "import sys;print(sys.version)") ) | Out-File -FilePath $summaryFile -Append -Encoding utf8
("Workdir    : {0}" -f $root) | Out-File -FilePath $summaryFile -Append -Encoding utf8
"" | Out-File -FilePath $summaryFile -Append -Encoding utf8

# ----- Instalar/actualizar herramientas -----
Write-Info 'Actualizando pip e instalando herramientas (ruff, mypy, bandit, pip-audit)...'
& $python -m pip install --upgrade --quiet pip 2>&1 | Out-Null
& $python -m pip install --upgrade --quiet ruff mypy bandit pip-audit 2>&1 | Out-Null
Write-Ok 'Herramientas listas.'

# ----- Detectar bandera de formato para ruff -----
$ruffHelp = & $python -m ruff --help 2>&1
$RuffFmtArg = ''
if ($ruffHelp -match '--output-format') { $RuffFmtArg = '--output-format=github' }
elseif ($ruffHelp -match '--format')    { $RuffFmtArg = '--format=github' }

# ----- Targets -----
$paths = @()
if (Test-Path (Join-Path $root 'app'))   { $paths += 'app' }
if (Test-Path (Join-Path $root 'tests')) { $paths += 'tests' }
if ($paths.Count -eq 0) { $paths = @('app') }

# ----- RUFF -----
$ruffExit = Run-And-Capture 'ruff' {
    if ($RuffFmtArg -ne '') {
        & $python -m ruff check $paths $RuffFmtArg
    } else {
        & $python -m ruff check $paths
    }
} $ruffFile

# ----- MYPY -----
$mypyExit = Run-And-Capture 'mypy' {
    & $python -m mypy $paths --ignore-missing-imports
} $mypyFile

# ----- BANDIT (via python -m para evitar PATH) -----
$banditTargets = @()
if (Test-Path (Join-Path $root 'app')) { $banditTargets += 'app' }
if ($banditTargets.Count -eq 0) { $banditTargets = @('app') }

$banditExit = Run-And-Capture 'bandit' {
    & $python -m bandit -r $banditTargets -lll
} $banditFile

# ----- PIP-AUDIT -----
$reqFile = Join-Path $root 'requirements.txt'
$pipauditExit = Run-And-Capture 'pip-audit' {
    if (Test-Path $reqFile) {
        & $python -m pip_audit -r $reqFile
    } else {
        & $python -m pip_audit
    }
} $pipauditFile

# ----- Resumen -----
@(
    '=== Static Analysis Summary ===',
    ('ruff      : exit-code {0} -> {1}' -f $ruffExit,     (Split-Path -Leaf $ruffFile)),
    ('mypy      : exit-code {0} -> {1}' -f $mypyExit,     (Split-Path -Leaf $mypyFile)),
    ('bandit    : exit-code {0} -> {1}' -f $banditExit,   (Split-Path -Leaf $banditFile)),
    ('pip-audit : exit-code {0} -> {1}' -f $pipauditExit, (Split-Path -Leaf $pipauditFile)),
    '',
    ('Archivos en: {0}' -f $reports)
) | Out-File -FilePath $summaryFile -Append -Encoding utf8

Write-Ok ("Resumen: {0}" -f $summaryFile)

# ----- ZIP -----
try {
    if (Test-Path $zipFile) { Remove-Item $zipFile -Force }
    Compress-Archive -Path (Join-Path $reports '*') -DestinationPath $zipFile -Force
    Write-Ok ("ZIP: {0}" -f $zipFile)
} catch {
    Write-Warn ("No se pudo crear el ZIP: {0}" -f $_.Exception.Message)
}

# ----- Exit coherente -----
if ($ruffExit -ne 0 -or $mypyExit -ne 0 -or $banditExit -ne 0) {
    Write-Warn 'Finalizado con findings. Revisa los .txt en "reports".'
    exit 2
} else {
    Write-Ok 'Pruebas estaticas completadas. Revisa "reports".'
    exit 0
}
