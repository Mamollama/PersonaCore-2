#!/usr/bin/env bash
# PersonaCore 2 — Linux/macOS setup script

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC}   $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERR]${NC}  $*" >&2; }
header()  { echo -e "\n${BOLD}${CYAN}══ $* ══${NC}"; }

echo -e "${BOLD}${CYAN}"
cat << 'EOF'
  ____                              ____               ___
 |  _ \ ___ _ __ ___  ___  _ __  / ___|___  _ __ ___|__ \
 | |_) / _ \ '__/ __|/ _ \| '_ \| |   / _ \| '__/ _ \ / /
 |  __/  __/ |  \__ \ (_) | | | | |__| (_) | | |  __// /
 |_|   \___|_|  |___/\___/|_| |_|\____\___/|_|  \___|/_/

 AI Video Generation Suite — Setup Script
EOF
echo -e "${NC}"

# ─── Python version ───────────────────────────────────────────────────────────
header "Python"
if ! command -v python3 &>/dev/null; then
    error "Python 3 not found. Install Python 3.11+ and try again."
    exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]; }; then
    error "Python 3.11+ required, found $PY_VER"
    exit 1
fi
success "Python $PY_VER"

# ─── Virtual environment ──────────────────────────────────────────────────────
header "Virtual Environment"
if [ ! -d ".venv" ]; then
    info "Creating .venv..."
    python3 -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate
success "Activated .venv"

# ─── Pip upgrade ─────────────────────────────────────────────────────────────
pip install --quiet --upgrade pip setuptools wheel

# ─── Core dependencies ────────────────────────────────────────────────────────
header "Core Dependencies"
info "Installing core packages..."
pip install --quiet -e ".[dev]" 2>&1 | tail -5
success "Core packages installed"

# ─── FFmpeg check ─────────────────────────────────────────────────────────────
header "FFmpeg"
if command -v ffmpeg &>/dev/null; then
    FFMPEG_VER=$(ffmpeg -version 2>&1 | head -1 | awk '{print $3}')
    success "FFmpeg $FFMPEG_VER"
else
    warn "FFmpeg not found — video export will use OpenCV fallback"
    info "Install FFmpeg:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        info "  brew install ffmpeg"
    else
        info "  sudo apt install ffmpeg   # Debian/Ubuntu"
        info "  sudo dnf install ffmpeg   # Fedora"
    fi
fi

# ─── Ollama check ─────────────────────────────────────────────────────────────
header "Ollama"
if command -v ollama &>/dev/null; then
    OLLAMA_VER=$(ollama --version 2>/dev/null || echo "unknown")
    success "Ollama $OLLAMA_VER"
    info "Checking if Ollama is running..."
    if curl -s http://localhost:11434/ &>/dev/null; then
        success "Ollama is running at http://localhost:11434"
        info "Available models:"
        ollama list 2>/dev/null | head -10 || true
    else
        warn "Ollama installed but not running. Start it with: ollama serve"
    fi
else
    warn "Ollama not found"
    info "Install Ollama: https://ollama.ai/download"
    info "  curl -fsSL https://ollama.ai/install.sh | sh"
fi

# ─── GPU check ────────────────────────────────────────────────────────────────
header "GPU"
if command -v nvidia-smi &>/dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
    success "NVIDIA GPU: $GPU_NAME"
    info "CUDA is available for accelerated generation"
elif command -v rocm-smi &>/dev/null; then
    success "AMD GPU detected (ROCm)"
else
    warn "No GPU detected — will use CPU (slower generation)"
fi

# ─── Optional diffusers ───────────────────────────────────────────────────────
header "Optional: Diffusers (Video Generation Models)"
read -rp "Install PyTorch + diffusers for Zeroscope/AnimateDiff? [y/N] " INSTALL_DIFF
if [[ "$INSTALL_DIFF" =~ ^[Yy]$ ]]; then
    info "Installing diffusers extras (this may take a while)..."
    pip install --quiet -e ".[diffusers]" 2>&1 | tail -10
    success "Diffusers extras installed"
else
    info "Skipping diffusers — Demo backend will be available"
fi

# ─── Default model ───────────────────────────────────────────────────────────
header "Ollama Default Model"
if command -v ollama &>/dev/null && curl -s http://localhost:11434/ &>/dev/null; then
    MODELS=$(ollama list 2>/dev/null | tail -n +2 | awk '{print $1}' || true)
    if [ -z "$MODELS" ]; then
        read -rp "No models found. Pull llama3.2 now? [y/N] " PULL_MODEL
        if [[ "$PULL_MODEL" =~ ^[Yy]$ ]]; then
            info "Pulling llama3.2..."
            ollama pull llama3.2
            success "llama3.2 pulled"
        fi
    else
        success "Models available:"
        echo "$MODELS" | while read -r m; do info "  • $m"; done
    fi
fi

# ─── Done ─────────────────────────────────────────────────────────────────────
echo -e "\n${GREEN}${BOLD}Setup complete!${NC}\n"
echo -e "  ${CYAN}Run PersonaCore 2:${NC}"
echo -e "    ${BOLD}source .venv/bin/activate && python main.py${NC}"
echo ""
