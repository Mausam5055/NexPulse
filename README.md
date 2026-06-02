<div align="center">
  
# 🚀 NexPulse

**A blazingly fast, distributed real-time event analytics engine.**

[![Go](https://img.shields.io/badge/Go-00ADD8?style=for-the-badge&logo=go&logoColor=white)](https://go.dev/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Apache Kafka](https://img.shields.io/badge/Kafka-231F20?style=for-the-badge&logo=apachekafka&logoColor=white)](https://kafka.apache.org/)
[![Grafana](https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white)](https://grafana.com/)
[![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)](https://prometheus.io/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

</div>

<br>

NexPulse is a **production-grade, distributed real-time event analytics engine**. Built entirely in Go, it is designed to ingest massive volumes of arbitrary events (100,000+ events/sec), process them through a fault-tolerant Kafka pipeline, compute sub-millisecond aggregations using Redis, and expose deep system observability through Prometheus and Grafana.

---

## 📸 Previews

<table>
  <tr>
    <td><img src="preview/DOcker1.png" alt="Docker Setup 1" /></td>
    <td><img src="preview/docker2.png" alt="Docker Setup 2" /></td>
  </tr>
  <tr>
    <td><img src="preview/grafnadashboard1.png" alt="Grafana Dashboard 1" /></td>
    <td><img src="preview/grafnadashboard2.png" alt="Grafana Dashboard 2" /></td>
  </tr>
  <tr>
    <td><img src="preview/grafnadashboard3.png" alt="Grafana Dashboard 3" /></td>
    <td><img src="preview/grafnadashboard4.png" alt="Grafana Dashboard 4" /></td>
  </tr>
</table>

---

## 📁 Project Structure & Organization

NexPulse is highly modular, with concerns cleanly separated across specialized microservices.

```text
nexpulse/
├── services/
│   ├── gateway/                  - Ingestion front-door (POST /ingest)
│   │   ├── main.go               - Entrypoint & Gin router setup
│   │   ├── kafka/producer.go     - Queues validated events into Kafka
│   │   └── ratelimit/redis_limiter.go - Strict sliding-window rate limiting
│   ├── aggregator/               - High-speed analytics engine
│   │   └── metrics/prometheus.go - Computes optimized aggregations into Redis
│   ├── anomaly/                  - Background worker for spike detection
│   │   ├── alert/publisher.go    - Publishes anomaly alerts to Kafka
│   │   └── detector/ema.go       - Exponential Moving Average math logic
│   └── query/                    - Isolates read traffic from dashboards
│       ├── rdb/redis.go          - Fetches live state from Redis
│       └── ws/hub.go             - WebSocket connections for live pushes
├── tools/
│   └── simulator/                - Heavy-duty traffic generator
│       └── simulator.exe         - Blasts up to 100k events/sec
├── infra/                        - Infrastructure definitions
│   ├── docker-compose.yml        - Spins up Kafka, Redis, Prometheus, Grafana
│   ├── prometheus/prometheus.yml - Scrape configs for all microservices
│   ├── redis/redis.conf          - Custom Redis memory configurations
│   └── grafana/                  - Automated JSON dashboard provisioning
├── Makefile                      - Shortcut commands (make up, make clean)
└── README.md                     - You are here!
```

---

## 🏗️ System Architecture

To achieve massive scale without data loss, NexPulse relies on a strictly decoupled, event-driven architecture. 

```mermaid
graph TD
    subgraph External
        P[Traffic Simulator / Clients]
        D[Dashboard Viewers]
    end

    subgraph NexPulse Core
        G[API Gateway :8080]
        K[Apache Kafka :9092]
        A[Aggregator :8082]
        AD[Anomaly Detector :8083]
        Q[Query Service :8081]
        R[(Redis :6379)]
    end

    subgraph Observability
        PR[Prometheus]
        GR[Grafana]
    end

    P -- POST /ingest --> G
    G -- 1. Check Rate Limit --> R
    G -- 2. Produce Event --> K
    K -- Consume Events --> A
    K -- Consume Events --> AD
    A -- Live Metrics & Leaderboards --> R
    AD -- Alert Triggers --> K
    Q -- Fetch State & Pub/Sub --> R
    Q -- WebSockets --> D
    
    G & A & AD & Q -. /metrics .-> PR
    PR -. PromQL .-> GR
```

---

## 🔄 Data Flow & Rate Limiting

NexPulse avoids traditional SQL databases entirely to prevent write-locking bottlenecks. Instead, it relies on highly specific Redis algorithms.

### Sliding Window Rate Limiting
To prevent API abuse, the Gateway enforces a strict rate limit. Instead of a simple "token bucket" that can allow sudden bursts, we use a precise **Sliding Window** in Redis via Sorted Sets (`ZSET`).

```mermaid
sequenceDiagram
    participant C as Client
    participant G as API Gateway
    participant R as Redis
    participant K as Kafka

    C->>G: POST /ingest
    G->>R: ZADD (Current Timestamp)
    G->>R: ZREMRANGE (Drop > 60s old)
    R-->>G: Current Request Count in Window
    alt Over Limit
        G-->>C: 429 Too Many Requests
    else Under Limit
        G->>K: Produce Event to "raw-events"
        G-->>C: 202 Accepted
    end
```

### Constant-Memory Unique Counting
Once events hit Kafka, the **Aggregator** consumes them and updates Redis in real-time.
- **Unique Users:** We do not store every User ID to run an expensive `COUNT DISTINCT`. Instead, we use Redis **HyperLogLog** (`PFADD`). This allows us to estimate the exact number of unique visitors using a maximum of **12 KB of memory**, regardless of whether there are 1,000 or 1,000,000 visitors.
- **Leaderboards:** We track the most hit endpoints and top countries dynamically using Redis **Sorted Sets** (`ZINCRBY`). Fetching the top 10 is an $O(\log N)$ operation, guaranteeing sub-millisecond dashboard updates.

---

## 🚀 Quick Start

NexPulse is incredibly easy to run locally. You only need **Docker** and **Go 1.22+**.

### 1. Launch the Infrastructure
| Command | Action |
|---------|--------|
| `docker-compose -f infra/docker-compose.yml up -d` | Starts all Docker containers. |
| `docker-compose -f infra/docker-compose.yml down` | Stops all containers. |
| `docker-compose -f infra/docker-compose.yml down -v` | Wipes all data and resets the environment. |

### 2. Start the Microservices
Open **4 separate terminal windows** and run one of these commands in each:

| Command | Service | Description |
|---------|---------|-------------|
| `cd services/gateway && go run .` | **Gateway** | Starts the ingestion API on `:8080`. |
| `cd services/aggregator && go run .`| **Aggregator** | Consumes Kafka and computes live Redis metrics. |
| `cd services/anomaly && go run .` | **Detector** | Hunts for statistical traffic spikes. |
| `cd services/query && go run .` | **Query API** | Exposes WebSockets and REST APIs. |

### 3. Unleash the Traffic Simulator
Open one final terminal to generate synthetic traffic and watch the dashboards come alive!

| Command | Load Level |
|---------|------------|
| `cd tools/simulator && go run . --rate 1000 --workers 20` | Normal traffic (~1,000 requests/sec). |
| `cd tools/simulator && go run . --rate 10000 --workers 100` | Heavy traffic (~10,000 requests/sec). |
| `cd tools/simulator && go run . --rate 50000 --workers 500` | **MAX POWER** (~50,000+ requests/sec). |

### 4. View Live Analytics in PowerShell (Optional)
If you want to feel like a true hacker, you can watch the Redis data aggregate in real-time straight from your terminal without opening Grafana. Run this infinite loop in PowerShell:
```powershell
while ($true) { Clear-Host; Write-Host "--- LIVE TOP ENDPOINTS ---" -ForegroundColor Cyan; docker exec nexpulse-redis redis-cli ZREVRANGE leaderboard:endpoints 0 5 WITHSCORES; Start-Sleep -Seconds 1 }
```

---

## 📊 God-Mode Observability

Observability is a first-class citizen in NexPulse. Every microservice automatically exposes a Prometheus `/metrics` endpoint out of the box. 

When you run `make up`, Grafana is automatically provisioned with 6 breathtaking, real-time dashboards to track everything from Kafka consumer lag down to Go garbage collection pauses.

- **URL:** [http://localhost:3000](http://localhost:3000)
- **Username:** `admin`
- **Password:** `nexpulse`

---

## 🛠️ Commands Reference

| Command | Description |
|---------|-------------|
| `make up` | Starts all Docker infrastructure. |
| `make down` | Gracefully stops all containers. |
| `make clean` | Wipes all data volumes for a fresh reset. |
| `make check` | Runs an automated health check against all API and infra endpoints. |
| `make build` | Compiles all Go binaries into the `./bin/` directory. |

<br>

<div align="center">
  <b>Developed by Mausam5055</b>
</div>
