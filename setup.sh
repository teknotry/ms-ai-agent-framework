#!/usr/bin/env bash
# =============================================================================
# setup.sh — One-shot setup for ms-ai-agent-framework (macOS / Linux)
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
# =============================================================================

set -e  # exit on any error

VENV_DIR=".venv"

echo ""
echo "========================================"
echo "  ms-ai-agent-framework setup"
echo "========================================"
echo ""

# ── 1. Check Python version ──────────────────────────────────────────────────
PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
    echo "ERROR: Python not found. Install Python 3.10+ from https://python.org"
    exit 1
fi

VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
MAJOR=$($PYTHON -c "import sys; print(sys.version_info.major)")
MINOR=$($PYTHON -c "import sys; print(sys.version_info.minor)")

if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]; }; then
    echo "ERROR: Python 3.10+ required. Found: $VERSION"
    exit 1
fi

echo "✓ Python $VERSION found"

# ── 2. Create virtual environment ────────────────────────────────────────────
if [ -d "$VENV_DIR" ]; then
    echo "✓ Virtual environment already exists at $VENV_DIR"
else
    echo "→ Creating virtual environment at $VENV_DIR ..."
    $PYTHON -m venv "$VENV_DIR"
    echo "✓ Virtual environment created"
fi

# ── 3. Activate and install ───────────────────────────────────────────────────
echo "→ Installing dependencies ..."
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -e ".[all,dev]" -q
echo "✓ Dependencies installed"

# ── 4. Create .env from example if not present ───────────────────────────────
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ Created .env from .env.example — add your API keys"
else
    echo "✓ .env already exists"
fi

# ── 5. Done ───────────────────────────────────────────────────────────────────
echo ""
echo "========================================"
echo "  Setup complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "  1. Activate the virtual environment:"
echo "       source .venv/bin/activate"
echo ""
echo "  2. Add your API key to .env:"
echo "       OPENAI_API_KEY=sk-..."
echo ""
echo "  3. Load the .env file:"
echo "       export \$(cat .env | grep -v '#' | xargs)"
echo ""
echo "  4. Verify the install:"
echo "       agent --version"
echo "       agent list agents/"
echo ""
echo "  5. Start chatting:"
echo "       agent chat agents/docs_reader.yaml"
echo ""
