# Deployment

The framework supports three deployment targets:

| Target | Command | Best for |
|--------|---------|----------|
| **Local HTTP server** | `agent deploy local` | Development, local API testing |
| **Docker container** | `agent deploy docker` | Portable, self-hosted production |
| **Azure Container Apps** | `agent deploy azure` | Cloud, enterprise, scalable |

---

## Local HTTP Server

Runs the agent as a lightweight HTTP server on your machine.

```bash
agent deploy local agents/my-agent.yaml --port 8080
```

Output:
```
Agent 'my-agent' listening on http://0.0.0.0:8080
  POST /run    {"message": "..."}
  GET  /health
Press Ctrl+C to stop.
```

### API Endpoints

**`POST /run`** — Send a message to the agent

```bash
curl -X POST http://localhost:8080/run \
     -H "Content-Type: application/json" \
     -d '{"message": "What is Python asyncio?"}'
```

Response:
```json
{
  "response": "Python asyncio is a library for writing concurrent code..."
}
```

**`GET /health`** — Check if the agent is running

```bash
curl http://localhost:8080/health
```

Response:
```json
{"status": "ok", "agent": "my-agent"}
```

### Options

```bash
agent deploy local agents/my-agent.yaml --port 9000   # custom port
```

---

## Docker Container

Builds a Docker image and runs the agent in a container. Ideal for deploying to any server.

### Prerequisites

- [Docker](https://www.docker.com/get-started) installed and running

### Deploy

```bash
agent deploy docker agents/my-agent.yaml
```

What this does:
1. Generates a `Dockerfile` in the current directory
2. Generates a `docker-compose.yml`
3. Runs `docker build` to build the image
4. Runs `docker run` to start the container

### Options

```bash
# Custom image name
agent deploy docker agents/my-agent.yaml --image my-company/my-agent

# Custom port
agent deploy docker agents/my-agent.yaml --port 9000
```

### Environment Variables in Docker

Create a `.env` file in your project root:

```bash
# .env
OPENAI_API_KEY=sk-...
AZURE_AI_PROJECT_CONNECTION_STRING=...
```

The deployer picks this up automatically with `--env-file .env`.

### Generated Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e ".[all]"
EXPOSE 8080
CMD ["python", "-m", "agent_framework.cli", "deploy", "local", \
     "/app/agents/my-agent.yaml", "--port", "8080"]
```

### Generated docker-compose.yml

```yaml
version: "3.9"
services:
  my-agent:
    build: .
    image: my-agent
    ports:
      - "8080:8080"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AZURE_AI_PROJECT_CONNECTION_STRING=${AZURE_AI_PROJECT_CONNECTION_STRING}
    restart: unless-stopped
```

Start with compose:
```bash
docker-compose up
```

---

## Azure Container Apps

Deploys the agent to Azure as a scalable, fully managed Container App.

### Prerequisites

1. [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) installed
2. Logged into Azure: `az login`
3. Docker available (for local build) or Azure CLI for ACR Tasks

### Deploy

```bash
export AZURE_RESOURCE_GROUP=my-resource-group
export AZURE_SUBSCRIPTION_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

agent deploy azure agents/my-agent.yaml \
  --resource-group my-resource-group \
  --location eastus
```

What this does:
1. Creates the Azure resource group (if it doesn't exist)
2. Creates an Azure Container Registry (ACR)
3. Builds the Docker image using ACR Tasks (no local Docker needed)
4. Creates an Azure Container Apps environment
5. Deploys the agent as a Container App with external HTTP ingress
6. Prints the public endpoint URL

Output:
```
Ensuring resource group 'my-resource-group'...
Creating Azure Container Registry 'myagentacr'...
Building image via ACR Tasks...
Creating Container Apps environment 'my-agent-env'...
Deploying Container App 'my-agent'...

Agent deployed! Endpoint: https://my-agent.eastus.azurecontainerapps.io/run
```

### Options

```bash
agent deploy azure agents/my-agent.yaml \
  --resource-group my-rg \
  --location westeurope \
  --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

| Option | Env Var | Description |
|--------|---------|-------------|
| `--resource-group` | `AZURE_RESOURCE_GROUP` | Azure resource group |
| `--location` | — | Azure region (default: `eastus`) |
| `--subscription` | `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |

### Storing Secrets in Azure Key Vault

For production, store your API keys in Azure Key Vault instead of environment variables:

```bash
# Create Key Vault
az keyvault create --name my-agent-kv --resource-group my-rg

# Store the OpenAI key
az keyvault secret set \
  --vault-name my-agent-kv \
  --name OPENAI-API-KEY \
  --value "sk-..."

# Grant your Container App access
az keyvault set-policy \
  --name my-agent-kv \
  --object-id <container-app-identity> \
  --secret-permissions get
```

---

## Which Target to Choose?

```
Are you developing / testing locally?
  └── YES → agent deploy local   (fastest, no containers needed)

Do you want a portable, self-hosted container?
  └── YES → agent deploy docker  (works on any server with Docker)

Do you need cloud hosting, auto-scaling, or enterprise features?
  └── YES → agent deploy azure   (fully managed, scalable)
```

---

## Next Steps

- [Setup Guide](./01-setup.md) — back to installation
- [Creating Agents](./03-creating-agents.md) — define agents to deploy
- [Multi-Agent Pipelines](./05-pipelines.md) — deploy pipelines
