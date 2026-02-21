FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -e ".[all]"

EXPOSE 8080

ENV AGENT_CONFIG=agents/example_coder.yaml
ENV PORT=8080

CMD ["python", "-m", "agent_framework.cli", "deploy", "local", \
     "/app/agents/example_coder.yaml", "--port", "8080"]
