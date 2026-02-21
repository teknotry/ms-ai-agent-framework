"""
CLI entry point — the `agent` command.

Commands:
  agent init                              Scaffold a new project
  agent create <name> --backend <b>       Create an agent config template
  agent run <config> "<message>"          Run a single agent
  agent chat <config>                     Interactive terminal chat loop
  agent ui <config>                       Launch Gradio browser chat UI
  agent pipeline run <config> "<task>"    Run a multi-agent pipeline
  agent deploy local <config>             Run agent as local HTTP server
  agent deploy docker <config>            Build & run Docker container
  agent deploy azure <config>             Deploy to Azure Container Apps
  agent list [dir]                        List all agent configs
  agent logs <agent-name>                 (placeholder) Stream agent logs
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import click

from agent_framework.observability.logger import get_logger, setup_telemetry

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(package_name="ms-ai-agent-framework")
def cli():
    """ms-ai-agent-framework — build and deploy AI agents with Microsoft tools."""
    setup_telemetry()


# ---------------------------------------------------------------------------
# agent init
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("project_dir", default=".", type=click.Path())
def init(project_dir: str):
    """Scaffold a new agent project in PROJECT_DIR."""
    base = Path(project_dir)
    dirs = [base / "agents", base / "tools", base / "tests"]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        click.echo(f"  created {d}")

    _write_if_missing(
        base / "tools" / "example_tool.py",
        '''\
"""Example tool — replace with your own."""

from agent_framework.core.tool_registry import register_tool


@register_tool
def greet(name: str) -> str:
    """Return a greeting for *name*."""
    return f"Hello, {name}!"
''',
    )

    _write_if_missing(
        base / "agents" / "example_agent.yaml",
        '''\
name: example-agent
backend: autogen          # autogen | semantic_kernel | azure
instructions: "You are a helpful assistant."
llm:
  model: gpt-4o
  api_key_env: OPENAI_API_KEY
tools:
  - name: greet
    module: tools.example_tool
    function: greet
    description: Greet a person by name
max_turns: 5
''',
    )

    _write_if_missing(base / ".env.example", "OPENAI_API_KEY=sk-...\n")
    click.secho(f"\nProject scaffolded in '{project_dir}'. Edit agents/example_agent.yaml to get started.", fg="green")


# ---------------------------------------------------------------------------
# agent create
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("name")
@click.option("--backend", default="autogen", type=click.Choice(["autogen", "semantic_kernel", "azure"]))
@click.option("--out-dir", default="agents", type=click.Path())
def create(name: str, backend: str, out_dir: str):
    """Create a new agent config template for NAME."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"{name}.yaml"
    if dest.exists():
        click.secho(f"'{dest}' already exists. Aborting.", fg="red")
        sys.exit(1)

    azure_extras = (
        "\nazure_builtin_tools:\n  - code_interpreter\n  - file_search\n"
        if backend == "azure"
        else ""
    )
    dest.write_text(
        f'''\
name: {name}
backend: {backend}
instructions: "You are a helpful assistant named {name}."
llm:
  model: gpt-4o
  api_key_env: OPENAI_API_KEY
tools: []
max_turns: 10{azure_extras}
'''
    )
    click.secho(f"Created {dest}", fg="green")


# ---------------------------------------------------------------------------
# agent run
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("config", type=click.Path(exists=True))
@click.argument("message")
def run(config: str, message: str):
    """Run a single agent defined in CONFIG with MESSAGE."""
    from agent_framework.config.loader import load_agent_config
    from agent_framework.backends.factory import create_agent
    from agent_framework.core.tool_registry import ToolRegistry

    agent_config = load_agent_config(config)
    registry = ToolRegistry.from_agent_config(agent_config)
    agent = create_agent(agent_config, registry)

    click.echo(f"Running agent '{agent.name}' [{agent_config.backend}]...")
    result = asyncio.run(agent.run(message))
    click.echo("\n--- Response ---")
    click.echo(result)


# ---------------------------------------------------------------------------
# agent pipeline (sub-group)
# ---------------------------------------------------------------------------

@cli.group()
def pipeline():
    """Multi-agent pipeline commands."""


@pipeline.command("run")
@click.argument("pipeline_config", type=click.Path(exists=True))
@click.argument("task")
@click.option(
    "--agents-dir",
    default="agents",
    type=click.Path(),
    help="Directory containing agent YAML configs referenced by the pipeline.",
)
def pipeline_run(pipeline_config: str, task: str, agents_dir: str):
    """Run a multi-agent pipeline defined in PIPELINE_CONFIG with TASK."""
    from agent_framework.config.loader import load_agent_config, load_pipeline_config
    from agent_framework.backends.factory import create_agent
    from agent_framework.core.tool_registry import ToolRegistry
    from agent_framework.core.pipeline import Pipeline

    pipe_cfg = load_pipeline_config(pipeline_config)
    agents_path = Path(agents_dir)

    agents = {}
    for agent_name in pipe_cfg.agents:
        cfg_file = agents_path / f"{agent_name}.yaml"
        if not cfg_file.exists():
            click.secho(f"Agent config not found: {cfg_file}", fg="red")
            sys.exit(1)
        agent_cfg = load_agent_config(cfg_file)
        registry = ToolRegistry.from_agent_config(agent_cfg)
        agents[agent_name] = create_agent(agent_cfg, registry)

    pipe = Pipeline(pipe_cfg, agents)
    click.echo(f"Running pipeline '{pipe.name}' [{pipe_cfg.strategy}]...")
    result = asyncio.run(pipe.run(task))
    click.echo("\n--- Pipeline Result ---")
    click.echo(result)


# ---------------------------------------------------------------------------
# agent deploy (sub-group)
# ---------------------------------------------------------------------------

@cli.group()
def deploy():
    """Deployment commands."""


@deploy.command("local")
@click.argument("config", type=click.Path(exists=True))
@click.option("--port", default=8080, show_default=True)
def deploy_local(config: str, port: int):
    """Run agent as a local HTTP server on PORT."""
    from agent_framework.deploy.local import LocalDeployer
    deployer = LocalDeployer(config_path=config, port=port)
    deployer.deploy()


@deploy.command("docker")
@click.argument("config", type=click.Path(exists=True))
@click.option("--image", default=None, help="Docker image name (defaults to agent name)")
@click.option("--port", default=8080, show_default=True)
def deploy_docker(config: str, image: str | None, port: int):
    """Build and run agent in a Docker container."""
    from agent_framework.deploy.docker import DockerDeployer
    deployer = DockerDeployer(config_path=config, image_name=image, port=port)
    deployer.deploy()


@deploy.command("azure")
@click.argument("config", type=click.Path(exists=True))
@click.option("--resource-group", envvar="AZURE_RESOURCE_GROUP", required=True)
@click.option("--location", default="eastus", show_default=True)
@click.option("--subscription", envvar="AZURE_SUBSCRIPTION_ID", default=None)
def deploy_azure(config: str, resource_group: str, location: str, subscription: str | None):
    """Deploy agent to Azure Container Apps."""
    from agent_framework.deploy.azure import AzureDeployer
    deployer = AzureDeployer(
        config_path=config,
        resource_group=resource_group,
        location=location,
        subscription_id=subscription,
    )
    deployer.deploy()


# ---------------------------------------------------------------------------
# agent list
# ---------------------------------------------------------------------------

@cli.command("list")
@click.argument("agents_dir", default="agents", type=click.Path())
def list_agents(agents_dir: str):
    """List all agent configs in AGENTS_DIR."""
    from agent_framework.config.loader import load_agent_config

    path = Path(agents_dir)
    if not path.exists():
        click.secho(f"Directory not found: {path}", fg="red")
        sys.exit(1)

    files = sorted(path.glob("*.yaml")) + sorted(path.glob("*.yml")) + sorted(path.glob("*.json"))
    if not files:
        click.echo("No agent configs found.")
        return

    click.secho(f"{'NAME':<25} {'BACKEND':<18} {'MODEL':<15} FILE", bold=True)
    click.echo("-" * 80)
    for f in files:
        try:
            cfg = load_agent_config(f)
            click.echo(f"{cfg.name:<25} {cfg.backend:<18} {cfg.llm.model:<15} {f}")
        except Exception:
            pass  # skip pipeline configs and malformed files silently


# ---------------------------------------------------------------------------
# agent chat  — interactive terminal loop
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("config", type=click.Path(exists=True))
@click.option("--no-color", is_flag=True, default=False, help="Disable coloured output")
def chat(config: str, no_color: bool):
    """Start an interactive terminal chat session with the agent in CONFIG."""
    from agent_framework.config.loader import load_agent_config
    from agent_framework.backends.factory import create_agent
    from agent_framework.core.tool_registry import ToolRegistry

    agent_config = load_agent_config(config)
    registry = ToolRegistry.from_agent_config(agent_config)
    agent = create_agent(agent_config, registry)

    def out(text, **kwargs):
        if no_color:
            click.echo(text)
        else:
            click.secho(text, **kwargs)

    out(f"\nChatting with '{agent.name}' [{agent_config.backend}]", fg="cyan", bold=True)
    out("Type 'exit' or 'quit' to stop. Type 'reset' to clear conversation history.\n", fg="yellow")

    while True:
        try:
            user_input = click.prompt(click.style("You", fg="green", bold=True) if not no_color else "You")
        except (KeyboardInterrupt, EOFError):
            out("\nGoodbye!", fg="yellow")
            break

        user_input = user_input.strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            out("Goodbye!", fg="yellow")
            break
        if user_input.lower() == "reset":
            asyncio.run(agent.reset())
            out("[Conversation history cleared]", fg="yellow")
            continue

        try:
            response = asyncio.run(agent.run(user_input))
            out(f"\nAgent: ", fg="blue", bold=True, nl=False)
            click.echo(response)
            click.echo()
        except Exception as exc:
            out(f"[Error] {exc}", fg="red")


# ---------------------------------------------------------------------------
# agent ui  — Gradio browser chat UI
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("config", type=click.Path(exists=True))
@click.option("--port", default=7860, show_default=True)
@click.option("--share", is_flag=True, default=False, help="Create a public Gradio share link")
def ui(config: str, port: int, share: bool):
    """Launch a Gradio browser chat UI for the agent in CONFIG."""
    try:
        import gradio as gr
    except ImportError:
        click.secho(
            "Gradio is not installed. Install it with:\n  pip install gradio",
            fg="red",
        )
        sys.exit(1)

    from agent_framework.config.loader import load_agent_config
    from agent_framework.backends.factory import create_agent
    from agent_framework.core.tool_registry import ToolRegistry

    agent_config = load_agent_config(config)
    registry = ToolRegistry.from_agent_config(agent_config)
    agent = create_agent(agent_config, registry)

    async def respond(message: str, history: list) -> str:
        return await agent.run(message)

    def reset_agent():
        asyncio.run(agent.reset())
        return [], ""

    with gr.Blocks(title=f"cre-agent: {agent.name}", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            f"## {agent.name}\n"
            f"**Backend:** `{agent_config.backend}` &nbsp;|&nbsp; "
            f"**Model:** `{agent_config.llm.model}`\n\n"
            f"_{agent_config.instructions.strip().splitlines()[0]}_"
        )

        chatbot = gr.Chatbot(
            label="Conversation",
            height=500,
            show_copy_button=True,
            type="messages",
        )
        with gr.Row():
            msg_box = gr.Textbox(
                placeholder="Type your message and press Enter...",
                label="",
                scale=9,
                autofocus=True,
            )
            send_btn = gr.Button("Send", variant="primary", scale=1)

        with gr.Row():
            reset_btn = gr.Button("Reset conversation", variant="secondary")
            gr.Markdown(
                "_Tip: ask the agent to crawl docs, write code, or answer questions._",
                elem_classes="tip",
            )

        def user_submit(message, history):
            if not message.strip():
                return history, ""
            history = history or []
            history.append({"role": "user", "content": message})
            return history, ""

        def bot_reply(history):
            if not history:
                return history
            last_user = history[-1]["content"]
            try:
                response = asyncio.run(agent.run(last_user))
            except Exception as exc:
                response = f"[Error] {exc}"
            history.append({"role": "assistant", "content": response})
            return history

        msg_box.submit(user_submit, [msg_box, chatbot], [chatbot, msg_box]).then(
            bot_reply, chatbot, chatbot
        )
        send_btn.click(user_submit, [msg_box, chatbot], [chatbot, msg_box]).then(
            bot_reply, chatbot, chatbot
        )
        reset_btn.click(reset_agent, outputs=[chatbot, msg_box])

    click.secho(f"\nLaunching UI for '{agent.name}' on http://localhost:{port}", fg="cyan", bold=True)
    demo.launch(server_port=port, share=share, inbrowser=True)


# ---------------------------------------------------------------------------
# agent logs
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("agent_name")
def logs(agent_name: str):
    """Stream logs for AGENT_NAME (placeholder — configure OTEL_EXPORTER_OTLP_ENDPOINT)."""
    click.echo(f"Streaming logs for '{agent_name}'...")
    click.secho(
        "Tip: Set OTEL_EXPORTER_OTLP_ENDPOINT to ship traces to Jaeger, Azure Monitor, or Grafana.",
        fg="yellow",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content)
        click.echo(f"  created {path}")


if __name__ == "__main__":
    cli()
