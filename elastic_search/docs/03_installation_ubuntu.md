# 03 · Installation on Ubuntu

> **Goal:** Get Elasticsearch running locally on Ubuntu (or WSL2 on Windows) and verify it works with Python.

---

## What You'll Install

| Component | Version | Purpose |
|-----------|---------|---------|
| Elasticsearch | 8.x | The search engine |
| Python client | `elasticsearch==8.*` | Talk to ES from Python |
| (Optional) Kibana | 8.x | Visual UI to explore data |

---

## Option A — Docker (Recommended for Development)

The fastest way to get started. No system configuration needed.

### Prerequisites
```bash
# Install Docker if you don't have it
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo systemctl start docker
sudo usermod -aG docker $USER
# Log out and back in for group change to take effect
```

### Single-node Elasticsearch (Dev Mode)

```bash
# Pull and run Elasticsearch (security disabled for local dev)
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  docker.elastic.co/elasticsearch/elasticsearch:8.13.0
```

### With Docker Compose (recommended)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.13.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

  kibana:
    image: docker.elastic.co/kibana/kibana:8.13.0
    container_name: kibana
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  es_data:
```

```bash
# Start both services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f elasticsearch
```

---

## Option B — Native Install on Ubuntu

### Step 1: Import the Elasticsearch GPG Key
```bash
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | \
  sudo gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg
```

### Step 2: Add the Repository
```bash
sudo apt-get install apt-transport-https -y

echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] \
  https://artifacts.elastic.co/packages/8.x/apt stable main" | \
  sudo tee /etc/apt/sources.list.d/elastic-8.x.list
```

### Step 3: Install Elasticsearch
```bash
sudo apt-get update
sudo apt-get install elasticsearch -y
```

### Step 4: Disable Security for Local Dev
```bash
sudo nano /etc/elasticsearch/elasticsearch.yml
```

Add/modify these lines:
```yaml
xpack.security.enabled: false
xpack.security.http.ssl.enabled: false
network.host: localhost
http.port: 9200
discovery.type: single-node
```

### Step 5: Start Elasticsearch
```bash
sudo systemctl daemon-reload
sudo systemctl enable elasticsearch
sudo systemctl start elasticsearch

# Check status
sudo systemctl status elasticsearch
```

---

## Verify Elasticsearch Is Running

```bash
curl http://localhost:9200
```

Expected response:
```json
{
  "name" : "my-node",
  "cluster_name" : "elasticsearch",
  "version" : {
    "number" : "8.13.0",
    ...
  },
  "tagline" : "You Know, for Search"
}
```

---

## Install the Python Client

```bash
# Create a virtual environment (recommended)
python3 -m venv es-env
source es-env/bin/activate

# Install the official Python client
pip install elasticsearch==8.13.0

# Also install these — you'll need them later
pip install fastapi uvicorn python-dotenv sentence-transformers
```

---

## Verify with Python

```python
from elasticsearch import Elasticsearch

# Connect to local Elasticsearch (no auth, dev mode)
es = Elasticsearch("http://localhost:9200")

# Check connection
info = es.info()
print(f"Connected to cluster: {info['cluster_name']}")
print(f"Elasticsearch version: {info['version']['number']}")

# Health check
health = es.cluster.health()
print(f"Cluster status: {health['status']}")  # green / yellow / red
```

Expected output:
```
Connected to cluster: elasticsearch
Elasticsearch version: 8.13.0
Cluster status: yellow   ← yellow is fine on single-node (no replicas)
```

> **Yellow status on single node is normal.** It means replica shards can't be assigned (there's only one node). Green = all shards assigned (multi-node). Red = some primary shards missing (problem!).

---

## Environment Variables Setup

Create a `.env` file for your project:
```bash
# .env
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=my_index
```

Load it in Python:
```python
from dotenv import load_dotenv
import os

load_dotenv()

ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
es = Elasticsearch(ES_URL)
```

---

## Kibana (Optional but Helpful)

If you started Kibana via Docker Compose, open:  
**http://localhost:5601**

Kibana's **Dev Tools** (left sidebar → Management → Dev Tools) lets you run queries interactively — very useful for debugging.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Connection refused` | ES isn't running. Check `docker ps` or `systemctl status elasticsearch` |
| `Out of memory` | Reduce heap: set `ES_JAVA_OPTS=-Xms256m -Xmx256m` |
| `max virtual memory areas` error | Run `sudo sysctl -w vm.max_map_count=262144` |
| Cluster status RED | A primary shard is unassigned — check logs |

---

## Reference Links

- [Install Elasticsearch on Debian/Ubuntu (official)](https://www.elastic.co/guide/en/elasticsearch/reference/current/deb.html)
- [Docker install guide](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html)
- [Python client docs](https://elasticsearch-py.readthedocs.io/en/v8.13.0/)

---

**← Previous:** [02 · Core Concepts](./02_core_concepts.md)  
**Next →** [04 · CRUD Operations](./04_crud_operations.md)
