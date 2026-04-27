#Requires -Version 5.1
<#
.SYNOPSIS
  PersonaCore 2 — Windows setup script
.DESCRIPTION
  Installs dependencies, checks Ollama, checks FFmpeg, optionally installs diffusers.
#>

$ErrorActionPreference = "Stop"

$VIOLET = [System.ConsoleColor]::Magenta
$CYAN   = [System.ConsoleColor]::Cyan
$GREEN  = [System.ConsoleColor]::Green
$YELLOW = [System.ConsoleColor]::Yellow
$RED    = [System.ConsoleColor]::Red
$WHITE  = [System.ConsoleColor]::White

function Write-Header($msg) {
    Write-Host "`n══ $msg ══" -ForegroundColor $CYAN
}
function Write-Info($msg)    { Write-Host "[INFO] $msg" -ForegroundColor $CYAN }
function Write-OK($msg)      { Write-Host "[OK]   $msg" -ForegroundColor $GREEN }
function Write-Warn($msg)    { Write-Host "[WARN] $msg" -ForegroundColor $YELLOW }
function Write-Err($msg)     { Write-Host "[ERR]  $msg" -ForegroundColor $RED }

Write-Host @"
  ____                              ____               ___
 |  _ \ ___ _ __ ___  ___  _ __  / ___|___  _ __ ___|__ \
 | |_) / _ \ '__/ __|/ _ \| '_ \| |   / _ \| '__/ _ \ / /
 |  __/  __/ |  \__ \ (_) | | | | |__| (_) | | |  __// /
 |_|   \___|_|  |___/\___/|_| |_|\____\___/|_|  \___|/_/

 AI Video Generation Suite — Windows Setup
"@ -ForegroundColor $VIOLET

# ── Python ───────────────────────────────────────────────────────────────────
Write-Header "Python"
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $python) {
    Write-Err "Python not found. Install Python 3.11+ from https://python.org"
    exit 1
}

$pyVer = & $python.Name -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$major, $minor = $pyVer.Split('.')
if ([int]$major -lt 3 -or ([int]$major -eq 3 -and [int]$minor -lt 11)) {
    Write-Err "Python 3.11+ required, found $pyVer"
    exit 1
}
Write-OK "Python $pyVer"

# ── Virtual environment ───────────────────────────────────────────────────────
Write-Header "Virtual Environment"
if (-not (Test-Path ".venv")) {
    Write-Info "Creating .venv..."
    & $python.Name -m venv .venv
}

$activate = ".\.venv\Scripts\Activate.ps1"
if (-not (Test-Path $activate)) {
    Write-Err "Could not find .venv activation script"
    exit 1
}
. $activate
Write-OK "Activated .venv"

# ── Core packages ─────────────────────────────────────────────────────────────
Write-Header "Core Dependencies"
Write-Info "Upgrading pip..."
python -m pip install --quiet --upgrade pip setuptools wheel

Write-Info "Installing PersonaCore 2 and dependencies..."
python -m pip install --quiet -e "." 2>&1 | Select-Object -Last 5
Write-OK "Core packages installed"

# ── FFmpeg ────────────────────────────────────────────────────────────────────
Write-Header "FFmpeg"
$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($ffmpeg) {
    $ffVer = (& ffmpeg -version 2>&1 | Select-Object -First 1) -replace "ffmpeg version ", ""
    Write-OK "FFmpeg found: $ffVer"
} else {
    Write-Warn "FFmpeg not found — video export will use OpenCV fallback"
    Write-Info "Install FFmpeg via winget:  winget install --id Gyan.FFmpeg"
    Write-Info "Or download from: https://ffmpeg.org/download.html"
}

# ── Ollama ────────────────────────────────────────────────────────────────────
Write-Header "Ollama"
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollama) {
    Write-OK "Ollama found"
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:11434/" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        Write-OK "Ollama is running at http://localhost:11434"
        $models = & ollama list 2>&1
        Write-Info "Models: $($models | Select-Object -Skip 1 | Select-Object -First 5)"
    } catch {
        Write-Warn "Ollama installed but not running. Start it: ollama serve"
    }
} else {
    Write-Warn "Ollama not found"
    Write-Info "Download Ollama: https://ollama.ai/download"
}

# ── GPU ────────────────────────────────────────────────────────────────────────
Write-Header "GPU"
$nvSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($nvSmi) {
    $gpu = & nvidia-smi --query-gpu=name --format=csv,noheader 2>$null | Select-Object -First 1
    Write-OK "NVIDIA GPU: $gpu"
} else {
    Write-Warn "No NVIDIA GPU detected — will use CPU (slower)"
}

# ── Optional diffusers ────────────────────────────────────────────────────────
Write-Header "Optional: Diffusers"
$installDiff = Read-Host "Install PyTorch + diffusers for Zeroscope/AnimateDiff? [y/N]"
if ($installDiff -match "^[Yy]$") {
    Write-Info "Installing diffusers extras (may take several minutes)..."
    python -m pip install --quiet -e ".[diffusers]" 2>&1 | Select-Object -Last 10
    Write-OK "Diffusers extras installed"
} else {
    Write-Info "Skipping — Demo backend will be available"
}

# ── Default model ─────────────────────────────────────────────────────────────
Write-Header "Ollama Model"
if ($ollama) {
    try {
        Invoke-WebRequest -Uri "http://localhost:11434/" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop | Out-Null
        $modelLines = (& ollama list 2>&1) | Select-Object -Skip 1
        if (-not $modelLines -or $modelLines -match "^\s*$") {
            $pullModel = Read-Host "No models found. Pull llama3.2? [y/N]"
            if ($pullModel -match "^[Yy]$") {
                Write-Info "Pulling llama3.2 (this downloads ~2GB)..."
                & ollama pull llama3.2
                Write-OK "llama3.2 pulled"
            }
        } else {
            Write-OK "Models available:"
            $modelLines | Select-Object -First 5 | ForEach-Object { Write-Info "  • $_" }
        }
    } catch {
        Write-Warn "Ollama not running — skipping model setup"
    }
}

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host "`n" -NoNewline
Write-OK "Setup complete!"
Write-Host ""
Write-Host "  Run PersonaCore 2:" -ForegroundColor $CYAN
Write-Host "    .\.venv\Scripts\Activate.ps1; python main.py" -ForegroundColor $WHITE
Write-Host ""
