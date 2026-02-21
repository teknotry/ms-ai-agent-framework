@echo off
REM =============================================================================
REM setup.bat — One-shot setup for ms-ai-agent-framework (Windows)
REM
REM Usage:  Double-click setup.bat  OR  run from Command Prompt:
REM         setup.bat
REM =============================================================================

echo.
echo ========================================
echo   ms-ai-agent-framework setup
echo ========================================
echo.

REM ── 1. Check Python ──────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    echo Install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo Found Python %PYVER%

REM ── 2. Create virtual environment ────────────────────────────────────────────
if exist ".venv\" (
    echo Virtual environment already exists at .venv
) else (
    echo Creating virtual environment at .venv ...
    python -m venv .venv
    echo Virtual environment created.
)

REM ── 3. Install dependencies ───────────────────────────────────────────────────
echo Installing dependencies ...
.venv\Scripts\pip install --upgrade pip -q
.venv\Scripts\pip install -e ".[all,dev]"
echo Dependencies installed.

REM ── 4. Create .env from example ──────────────────────────────────────────────
if not exist ".env" (
    copy .env.example .env >nul
    echo Created .env from .env.example - add your API keys.
) else (
    echo .env already exists.
)

REM ── 5. Done ───────────────────────────────────────────────────────────────────
echo.
echo ========================================
echo   Setup complete!
echo ========================================
echo.
echo Next steps:
echo.
echo   1. Activate the virtual environment:
echo         .venv\Scripts\activate
echo.
echo   2. Add your API key to .env:
echo         OPENAI_API_KEY=sk-...
echo.
echo   3. Load the .env and verify:
echo         agent --version
echo         agent list agents/
echo.
echo   4. Start chatting:
echo         agent chat agents/docs_reader.yaml
echo.
pause
