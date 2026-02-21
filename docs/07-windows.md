# Windows Setup Guide

**Yes — the framework runs on Windows.** The core Python code uses `pathlib` throughout
and has no Unix-only dependencies. This guide covers the Windows-specific steps.

---

## Prerequisites

| Requirement | Download |
|-------------|----------|
| Python 3.10+ | [python.org/downloads](https://www.python.org/downloads/) |
| Git (optional) | [git-scm.com](https://git-scm.com/download/win) |
| Docker Desktop (for `agent deploy docker`) | [docker.com/get-started](https://www.docker.com/get-started/) |
| Azure CLI (for `agent deploy azure`) | [learn.microsoft.com/cli/azure/install](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows) |

> **Tip:** Use **Windows Terminal** with PowerShell or Command Prompt for the best experience.

---

## Step 1 — Install Python

Download Python 3.10+ from [python.org](https://www.python.org/downloads/).

During installation, check **"Add Python to PATH"**.

Verify:
```powershell
python --version
pip --version
```

---

## Step 2 — Install the Framework

Open **PowerShell** or **Command Prompt** and navigate to the project folder:

```powershell
cd C:\path\to\ms-ai-agent-framework
pip install -e ".[all]"
```

---

## Step 3 — Set API Keys

The syntax differs between shells on Windows:

### PowerShell (recommended)

```powershell
$env:OPENAI_API_KEY = "sk-..."
```

To make it permanent (survives reboots):
```powershell
[System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-...", "User")
```

### Command Prompt (cmd.exe)

```cmd
set OPENAI_API_KEY=sk-...
```

To make it permanent:
```cmd
setx OPENAI_API_KEY "sk-..."
```

### .env file (easiest — works on all platforms)

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-...
AZURE_AI_PROJECT_CONNECTION_STRING=...
```

Then load it before running agents:

```powershell
# PowerShell — load .env file
Get-Content .env | ForEach-Object {
    if ($_ -match "^([^#][^=]*)=(.*)$") {
        [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim())
    }
}
```

Or install `python-dotenv` and load it in code:
```bash
pip install python-dotenv
```

---

## Step 4 — Verify Installation

```powershell
agent --version
agent list agents/
```

---

## Step 5 — Run an Agent

```powershell
# One-shot
agent run agents/example_research.yaml "What is Semantic Kernel?"

# Interactive terminal chat
agent chat agents/docs_reader.yaml

# Browser UI
agent ui agents/docs_reader.yaml
```

---

## Platform Differences Summary

| Feature | macOS / Linux | Windows |
|---------|--------------|---------|
| Set env var (temporary) | `export KEY=value` | `$env:KEY = "value"` (PS) or `set KEY=value` (cmd) |
| Set env var (permanent) | `~/.zshrc` or `~/.bashrc` | System Properties → Environment Variables |
| Temp directory | `/tmp/` | `%TEMP%` or use relative path `.agent_code` |
| Docker | Docker Desktop or CLI | Docker Desktop |
| Azure CLI | brew / apt | winget or MSI installer |
| Python command | `python3` or `python` | `python` |
| Path separator | `/` | `\` (Python handles this automatically via `pathlib`) |

---

## Known Limitations on Windows

### AutoGen code execution
AutoGen can execute Python code in a sandbox. On Windows, set `use_docker: false`
and use a relative path for `work_dir` (already done in the example config):

```yaml
# agents/example_coder.yaml
extra:
  code_execution_config:
    work_dir: .agent_code    # relative path — works on Windows and Unix
    use_docker: false
```

### Docker deployment
`agent deploy docker` requires Docker Desktop for Windows.
Make sure Docker Desktop is running before using this command.

### Azure deployment
`agent deploy azure` calls the `az` CLI. Install it from:
```powershell
winget install Microsoft.AzureCLI
```
Then log in:
```powershell
az login
```

---

## Recommended: Use WSL2 (Windows Subsystem for Linux)

If you prefer a Linux environment on Windows, WSL2 is the easiest option:

```powershell
# Install WSL2 (run in PowerShell as Administrator)
wsl --install

# Then inside WSL terminal, follow the standard Linux setup:
pip install -e ".[all]"
export OPENAI_API_KEY=sk-...
agent chat agents/docs_reader.yaml
```

WSL2 gives you full Linux compatibility including Docker integration.
See [learn.microsoft.com/windows/wsl](https://learn.microsoft.com/en-us/windows/wsl/install).

---

## Next Steps

- [Setup Guide](./01-setup.md) — general installation (macOS / Linux)
- [Running Agents](./02-running-agents.md) — run, chat, and UI
- [Creating Agents](./03-creating-agents.md) — define your own agents
