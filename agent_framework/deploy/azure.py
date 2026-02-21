"""
Azure deployment — deploy the agent as an Azure Container App.

Prerequisites:
  - az CLI logged in  (az login)
  - Docker available for building the image
  - azure-mgmt-containerinstance installed  (pip install ms-ai-agent-framework[azure])
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

from agent_framework.observability.logger import get_logger

logger = get_logger(__name__)


class AzureDeployer:
    def __init__(
        self,
        config_path: str,
        resource_group: str,
        location: str = "eastus",
        subscription_id: Optional[str] = None,
    ) -> None:
        self.config_path = config_path
        self.resource_group = resource_group
        self.location = location
        self.subscription_id = subscription_id

        from agent_framework.config.loader import load_agent_config
        self._cfg = load_agent_config(config_path)
        self.app_name = self._cfg.name.lower().replace(" ", "-").replace("_", "-")
        self.image_name = f"{self.app_name}:latest"

    def deploy(self) -> None:
        self._ensure_resource_group()
        self._build_and_push_image()
        self._deploy_container_app()

    def _run_az(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        cmd = ["az", *args]
        if self.subscription_id:
            cmd += ["--subscription", self.subscription_id]
        logger.debug("az_command", cmd=" ".join(cmd))
        result = subprocess.run(cmd, capture_output=False)
        if check and result.returncode != 0:
            print(f"az command failed: {' '.join(cmd)}", file=sys.stderr)
            sys.exit(result.returncode)
        return result

    def _ensure_resource_group(self) -> None:
        print(f"Ensuring resource group '{self.resource_group}' in '{self.location}'...")
        self._run_az(
            "group", "create",
            "--name", self.resource_group,
            "--location", self.location,
        )

    def _build_and_push_image(self) -> None:
        acr_name = f"{self.app_name.replace('-', '')}acr"
        print(f"Creating Azure Container Registry '{acr_name}'...")
        self._run_az(
            "acr", "create",
            "--resource-group", self.resource_group,
            "--name", acr_name,
            "--sku", "Basic",
            "--admin-enabled", "true",
        )

        # Build image using ACR Tasks (no local Docker required)
        print(f"Building image '{self.image_name}' via ACR Tasks...")
        self._run_az(
            "acr", "build",
            "--registry", acr_name,
            "--image", self.image_name,
            ".",
        )

        self._acr_name = acr_name
        self._full_image = f"{acr_name}.azurecr.io/{self.image_name}"

    def _deploy_container_app(self) -> None:
        env_name = f"{self.app_name}-env"

        print(f"Creating Container Apps environment '{env_name}'...")
        self._run_az(
            "containerapp", "env", "create",
            "--name", env_name,
            "--resource-group", self.resource_group,
            "--location", self.location,
        )

        print(f"Deploying Container App '{self.app_name}'...")
        self._run_az(
            "containerapp", "create",
            "--name", self.app_name,
            "--resource-group", self.resource_group,
            "--environment", env_name,
            "--image", self._full_image,
            "--registry-server", f"{self._acr_name}.azurecr.io",
            "--target-port", "8080",
            "--ingress", "external",
            "--min-replicas", "1",
            "--max-replicas", "3",
        )

        # Print the FQDN
        result = subprocess.run(
            [
                "az", "containerapp", "show",
                "--name", self.app_name,
                "--resource-group", self.resource_group,
                "--query", "properties.configuration.ingress.fqdn",
                "--output", "tsv",
            ],
            capture_output=True, text=True,
        )
        fqdn = result.stdout.strip()
        if fqdn:
            print(f"\nAgent deployed! Endpoint: https://{fqdn}/run")
        else:
            print("\nDeployment complete. Check the Azure Portal for the endpoint URL.")
