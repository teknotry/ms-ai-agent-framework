"""
Local deployment — run the agent as a lightweight HTTP server using the stdlib.

Exposes:
  POST /run    body: {"message": "..."} → {"response": "..."}
  GET  /health → {"status": "ok", "agent": "<name>"}
"""

from __future__ import annotations

import asyncio
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from agent_framework.observability.logger import get_logger

logger = get_logger(__name__)


class LocalDeployer:
    def __init__(self, config_path: str, port: int = 8080) -> None:
        self.config_path = config_path
        self.port = port

    def deploy(self) -> None:
        from agent_framework.config.loader import load_agent_config
        from agent_framework.backends.factory import create_agent
        from agent_framework.core.tool_registry import ToolRegistry

        cfg = load_agent_config(self.config_path)
        registry = ToolRegistry.from_agent_config(cfg)
        agent = create_agent(cfg, registry)

        logger.info("local_deploy_start", agent=agent.name, port=self.port)

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):  # silence default access log
                pass

            def do_GET(self):
                if self.path == "/health":
                    self._json(200, {"status": "ok", "agent": agent.name})
                else:
                    self._json(404, {"error": "not found"})

            def do_POST(self):
                if self.path != "/run":
                    self._json(404, {"error": "not found"})
                    return
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length))
                message = body.get("message", "")
                response = asyncio.run(agent.run(message))
                self._json(200, {"response": response})

            def _json(self, code: int, payload: dict) -> None:
                data = json.dumps(payload).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        server = HTTPServer(("0.0.0.0", self.port), Handler)
        print(f"Agent '{agent.name}' listening on http://0.0.0.0:{self.port}")
        print("  POST /run    {\"message\": \"...\"}")
        print("  GET  /health")
        print("Press Ctrl+C to stop.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
