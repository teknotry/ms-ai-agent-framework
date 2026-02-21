"""
Docker deployment — generate a Dockerfile and run the agent in a container.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from agent_framework.observability.logger import get_logger

logger = get_logger(__name__)

_DOCKERFILE_TEMPLATE = """\
FROM python:3.11-slim

WORKDIR /app

# Copy framework and project files
COPY . .

# Install framework with all extras
RUN pip install --no-cache-dir -e ".[all]"

# Expose the agent HTTP port
EXPOSE {port}

ENV AGENT_CONFIG={config_filename}
ENV PORT={port}

CMD ["python", "-m", "agent_framework.cli", "deploy", "local", "$AGENT_CONFIG", "--port", "$PORT"]
"""

_COMPOSE_TEMPLATE = """\
version: "3.9"
services:
  {service_name}:
    build: .
    image: {image_name}
    ports:
      - "{port}:{port}"
    environment:
      - OPENAI_API_KEY=${{OPENAI_API_KEY}}
      - AZURE_AI_PROJECT_CONNECTION_STRING=${{AZURE_AI_PROJECT_CONNECTION_STRING}}
    restart: unless-stopped
"""


class DockerDeployer:
    def __init__(self, config_path: str, image_name: str | None = None, port: int = 8080) -> None:
        self.config_path = Path(config_path)
        self.port = port

        from agent_framework.config.loader import load_agent_config
        self._cfg = load_agent_config(config_path)
        self.image_name = image_name or self._cfg.name.lower().replace(" ", "-")

    def deploy(self) -> None:
        self._write_dockerfile()
        self._write_compose()
        self._build()
        self._run()

    def _write_dockerfile(self) -> None:
        dockerfile = Path("Dockerfile")
        content = _DOCKERFILE_TEMPLATE.format(
            port=self.port,
            config_filename=str(self.config_path),
        )
        dockerfile.write_text(content)
        logger.info("dockerfile_written", path=str(dockerfile))

    def _write_compose(self) -> None:
        compose = Path("docker-compose.yml")
        content = _COMPOSE_TEMPLATE.format(
            service_name=self.image_name,
            image_name=self.image_name,
            port=self.port,
        )
        compose.write_text(content)
        logger.info("compose_written", path=str(compose))

    def _build(self) -> None:
        print(f"Building Docker image '{self.image_name}'...")
        result = subprocess.run(
            ["docker", "build", "-t", self.image_name, "."],
            capture_output=False,
        )
        if result.returncode != 0:
            print("Docker build failed.", file=sys.stderr)
            sys.exit(result.returncode)

    def _run(self) -> None:
        print(f"Starting container '{self.image_name}' on port {self.port}...")
        subprocess.run(
            [
                "docker", "run", "--rm",
                "-p", f"{self.port}:{self.port}",
                "--env-file", ".env",
                self.image_name,
            ]
        )
