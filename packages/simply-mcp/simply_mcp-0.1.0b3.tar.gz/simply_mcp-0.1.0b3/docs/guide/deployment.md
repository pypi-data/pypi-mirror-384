# Deployment Guide

Deploy Simply-MCP-PY servers to production environments.

## Deployment Options

1. **Docker Containers**
2. **Systemd Services**
3. **Cloud Platforms (AWS, GCP, Azure)**
4. **Standalone Executables**
5. **Kubernetes**

## Docker Deployment

### Dockerfile

Create a `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Install server
RUN pip install -e .

# Expose port (for HTTP transport)
EXPOSE 3000

# Run server
CMD ["simply-mcp", "run", "server.py", "--transport", "http", "--port", "3000"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  mcp-server:
    build: .
    ports:
      - "3000:3000"
    environment:
      - SIMPLY_MCP_TRANSPORT_TYPE=http
      - SIMPLY_MCP_TRANSPORT_PORT=3000
      - SIMPLY_MCP_LOGGING_LEVEL=INFO
      - SIMPLY_MCP_SECURITY_AUTH_API_KEYS=${API_KEYS}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
```

### Build and Run

```bash
# Build image
docker build -t mcp-server .

# Run container
docker run -d -p 3000:3000 --name mcp-server \
  -e SIMPLY_MCP_SECURITY_AUTH_API_KEYS="your-key" \
  mcp-server

# Using docker-compose
docker-compose up -d
```

## Systemd Service

### Service File

Create `/etc/systemd/system/mcp-server.service`:

```ini
[Unit]
Description=MCP Server
After=network.target

[Service]
Type=simple
User=mcp
Group=mcp
WorkingDirectory=/opt/mcp-server
Environment="PATH=/opt/mcp-server/venv/bin"
EnvironmentFile=/opt/mcp-server/.env
ExecStart=/opt/mcp-server/venv/bin/simply-mcp run server.py --transport http --port 3000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Installation

```bash
# Create user
sudo useradd -r -s /bin/false mcp

# Copy files
sudo mkdir -p /opt/mcp-server
sudo cp -r . /opt/mcp-server/
sudo chown -R mcp:mcp /opt/mcp-server

# Create virtual environment
cd /opt/mcp-server
sudo -u mcp python -m venv venv
sudo -u mcp venv/bin/pip install -e .

# Enable and start service
sudo systemctl enable mcp-server
sudo systemctl start mcp-server
sudo systemctl status mcp-server
```

## Cloud Platforms

### AWS (Elastic Beanstalk)

Create `.ebextensions/python.config`:

```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: wsgi.py
  aws:elasticbeanstalk:application:environment:
    SIMPLY_MCP_TRANSPORT_TYPE: "http"
    SIMPLY_MCP_LOGGING_LEVEL: "INFO"
```

Create `wsgi.py`:

```python
from simply_mcp import BuildMCPServer
from server import MyServer

application = MyServer.to_wsgi()
```

Deploy:

```bash
eb init -p python-3.10 mcp-server
eb create mcp-server-env
eb deploy
```

### GCP (Cloud Run)

Create `Dockerfile` (see Docker section above).

Deploy:

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/mcp-server

# Deploy to Cloud Run
gcloud run deploy mcp-server \
  --image gcr.io/PROJECT_ID/mcp-server \
  --platform managed \
  --port 3000 \
  --set-env-vars SIMPLY_MCP_TRANSPORT_TYPE=http
```

### Azure (App Service)

Create `startup.sh`:

```bash
#!/bin/bash
pip install -e .
simply-mcp run server.py --transport http --port 8000
```

Deploy:

```bash
az webapp up --name mcp-server \
  --runtime PYTHON:3.10 \
  --sku B1
```

## Standalone Executable

### Using PyInstaller

Bundle your server:

```bash
simply-mcp bundle server.py --output dist/
```

Or manually:

```bash
pyinstaller --onefile \
  --name mcp-server \
  --add-data "simplymcp.config.toml:." \
  server.py
```

### Distribution

```bash
# The executable is now standalone
./dist/mcp-server --transport http --port 3000
```

## Kubernetes

### Deployment YAML

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-server
  template:
    metadata:
      labels:
        app: mcp-server
    spec:
      containers:
      - name: mcp-server
        image: your-registry/mcp-server:latest
        ports:
        - containerPort: 3000
        env:
        - name: SIMPLY_MCP_TRANSPORT_TYPE
          value: "http"
        - name: SIMPLY_MCP_LOGGING_LEVEL
          value: "INFO"
        - name: SIMPLY_MCP_SECURITY_AUTH_API_KEYS
          valueFrom:
            secretKeyRef:
              name: mcp-secrets
              key: api-keys
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-server
spec:
  selector:
    app: mcp-server
  ports:
  - port: 80
    targetPort: 3000
  type: LoadBalancer
```

### Deploy

```bash
# Create secret
kubectl create secret generic mcp-secrets \
  --from-literal=api-keys="key1,key2"

# Deploy
kubectl apply -f k8s-deployment.yaml

# Check status
kubectl get pods
kubectl get svc
```

## Production Best Practices

### 1. Security

```toml
[security]
enable_auth = true
enable_rate_limiting = true

[security.auth]
type = "api_key"
api_keys = ["${API_KEY}"]  # From environment

[security.rate_limit]
requests_per_minute = 100
```

### 2. Logging

```toml
[logging]
level = "WARNING"  # or "INFO"
format = "json"    # Structured logs
output = "/var/log/mcp/server.log"
```

### 3. Monitoring

Add health check endpoint:

```python
@tool(description="Health check")
def health(self) -> dict:
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time()
    }
```

### 4. Error Handling

```python
@tool(description="Robust tool")
def robust_tool(self, param: str) -> Union[dict, str]:
    try:
        # Your logic
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return {"success": False, "error": str(e)}
```

### 5. Resource Limits

Set appropriate limits:

```yaml
# Docker Compose
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 512M
```

### 6. Graceful Shutdown

```python
import signal
import sys

def signal_handler(sig, frame):
    logger.info("Shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

## Environment-Specific Configurations

### Development

```toml
[logging]
level = "DEBUG"

[development]
watch_enabled = true
debug = true
```

### Staging

```toml
[server]
name = "staging-server"

[logging]
level = "INFO"

[security]
enable_auth = true
```

### Production

```toml
[server]
name = "prod-server"

[logging]
level = "WARNING"
format = "json"

[security]
enable_auth = true
enable_rate_limiting = true

[security.rate_limit]
requests_per_minute = 100
```

## Monitoring and Observability

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram

request_count = Counter('mcp_requests_total', 'Total requests')
request_duration = Histogram('mcp_request_duration_seconds', 'Request duration')

@tool(description="Monitored tool")
def monitored_tool(self, param: str) -> str:
    request_count.inc()
    with request_duration.time():
        return f"Result: {param}"
```

### Log Aggregation

Use structured JSON logging for easy parsing:

```python
import logging
import json

logger = logging.getLogger(__name__)

logger.info(json.dumps({
    "event": "tool_executed",
    "tool": "add",
    "params": {"a": 1, "b": 2},
    "result": 3
}))
```

## Backup and Recovery

### Data Backup

```bash
# Backup script
#!/bin/bash
BACKUP_DIR="/backups/mcp"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup data
tar -czf "$BACKUP_DIR/data_$DATE.tar.gz" /opt/mcp-server/data

# Backup config
cp /opt/mcp-server/simplymcp.config.toml "$BACKUP_DIR/config_$DATE.toml"
```

### Automated Backups

```bash
# Add to crontab
0 2 * * * /opt/mcp-server/backup.sh
```

## Troubleshooting

### Check Logs

```bash
# Systemd
sudo journalctl -u mcp-server -f

# Docker
docker logs -f mcp-server

# Kubernetes
kubectl logs -f deployment/mcp-server
```

### Common Issues

1. **Port already in use**: Change port or kill existing process
2. **Permission denied**: Check file permissions and user
3. **Module not found**: Ensure dependencies are installed
4. **Connection refused**: Check firewall rules

## Next Steps

- [Configuration Guide](configuration.md) - Configure for production
- [Testing Guide](testing.md) - Test before deployment
- [API Reference](../api/core/server.md) - Server API details
