# Deployment Guide

## HTTP Deployment

**Default**: khivemcp uses stdio for local MCP clients (Claude Desktop, etc.).
**Production**: Use HTTP for remote access and microservices.

```bash
khivemcp config.json --transport http --host 0.0.0.0 --port 8000
```

**Health checks**:

- `/health` - Liveness probe (always returns 200 if running)
- `/ready` - Readiness probe (checks dependencies, returns 503 if not ready)

## Docker

**Dockerfile**:

```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Install dependencies
RUN pip install uv
COPY pyproject.toml ./
RUN uv pip install --system khivemcp

# Copy service code
COPY config/ ./config/
COPY services/ ./services/

ENV PYTHONPATH=/app/services
EXPOSE 8000

CMD ["khivemcp", "config/service.json", "--transport", "http", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and run**:

```bash
docker build -t my-service .
docker run -p 8000:8000 --env-file .env my-service
```

## Docker Compose

**docker-compose.yml**:

```yaml
version: "3.8"
services:
  my-service:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./config:/app/config:ro
    restart: unless-stopped
```

Run: `docker-compose up -d`

## Production Essentials

**1. Secrets management**:

```python
api_key = os.getenv("API_KEY")  # Never hardcode or put in config
```

**2. Health checks**:

```python
async def readiness(self) -> ReadinessStatus:
    # Verify dependencies are available
    await self.db.ping()
    return ReadinessStatus(name="my_service", status="ready")
```

**3. Resource limits** (Docker Compose):

```yaml
deploy:
  resources:
    limits:
      cpus: "2"
      memory: 1G
```

**4. Structured logging**:

```bash
khivemcp config.json --log-level INFO --transport http
```

---

That's the essentials. For Kubernetes, monitoring, advanced deployments, see the
examples directory.
