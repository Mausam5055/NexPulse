# NexPulse — Product Requirements Document (PRD)
### Version 1.0 | Status: Ready for Development

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Goals & Success Metrics](#2-goals--success-metrics)
3. [User Personas & Stories](#3-user-personas--stories)
4. [System Architecture](#4-system-architecture)
5. [Infrastructure & Docker Setup](#5-infrastructure--docker-setup)
6. [Microservice Specifications](#6-microservice-specifications)
   - 6.1 API Gateway
   - 6.2 Aggregator Service
   - 6.3 Anomaly Detector
   - 6.4 Query / WebSocket Service
   - 6.5 Traffic Simulator
7. [Kafka Topic Contracts](#7-kafka-topic-contracts)
8. [Redis Data Model](#8-redis-data-model)
9. [Prometheus Metrics Specification](#9-prometheus-metrics-specification)
10. [Grafana Dashboard Specification](#10-grafana-dashboard-specification)
11. [React Dashboard Specification](#11-react-dashboard-specification)
12. [API Reference](#12-api-reference)
13. [Implementation Phases](#13-implementation-phases)
14. [Non-Functional Requirements](#14-non-functional-requirements)
15. [Repository Structure](#15-repository-structure)

---

## 1. Product Overview

### 1.1 Vision Statement

NexPulse is a **self-hostable, production-grade, distributed real-time event analytics engine** that ingests arbitrary events at high volume, processes them through a fault-tolerant Kafka streaming pipeline, computes live aggregations in Redis, and surfaces every metric through a professional Grafana monitoring suite and a custom React live dashboard — all powered by Go microservices.

### 1.2 Problem Statement

Traditional web stacks (Node.js + PostgreSQL, Django + MySQL) fundamentally fail when:
- Event volume exceeds ~5,000/sec (DB write bottleneck)
- You need sub-100ms latency from event ingestion to dashboard update
- You need to serve 10,000+ concurrent real-time connections
- You need approximate unique counting without storing every user ID
- You need ordered, replayable event history without losing a single event on crash
- You need rate limiting that works across distributed instances

NexPulse is the demonstration of exactly *why* Go, Redis, Kafka, Prometheus, and Grafana exist.

### 1.3 What NexPulse Does

```
Event Producers → API Gateway → Kafka → Aggregator → Redis → Query Service → Dashboard
                                    ↓                    ↓
                               Anomaly Detector     Redis Pub/Sub
                                    ↓
                              Notifier Service
                                    ↓
                           Grafana + Prometheus
```

**Core capabilities:**
- Ingest events at 100,000+ events/second
- Compute rolling-window aggregations (per-second, per-minute, per-hour)
- Maintain live leaderboards ranked by event frequency
- Count unique visitors using HyperLogLog (12KB RAM for millions of users)
- Apply distributed rate limiting using sliding window algorithm
- Detect anomalies (traffic spikes, error surges) in real time
- Push all live data to browsers via WebSockets
- Expose all internal metrics to Prometheus
- Render professional Grafana dashboards for every service

### 1.4 Scope

**In Scope:**
- 5 Go microservices
- Apache Kafka (event bus)
- Redis (real-time data store)
- Prometheus (metrics collection)
- Grafana (professional dashboards — mandatory, not optional)
- React + Vite (custom live dashboard)
- Docker Compose (local orchestration)
- Traffic simulator tool

**Out of Scope (for this build):**
- User authentication
- Persistent historical storage (Postgres/Cassandra)
- Kubernetes deployment
- Multi-region setup

---

## 2. Goals & Success Metrics

### 2.1 Technical Goals

| Goal | Metric | Target |
|---|---|---|
| Throughput | Events ingested per second | ≥ 50,000 events/sec |
| Latency | Time from event ingestion to dashboard update | < 200ms p99 |
| Concurrency | Simultaneous WebSocket connections served | ≥ 5,000 |
| Redis performance | Redis ops/sec during peak load | ≥ 500,000 ops/sec |
| Kafka lag | Consumer group processing lag | < 500ms |
| Uptime | Any single service crash recovery | Kafka buffers; no data lost |
| Memory efficiency | RAM used to count 1M unique users | ≤ 12KB (HyperLogLog) |

### 2.2 Learning Goals

| Concept | Demonstrated By |
|---|---|
| Go goroutines & channels | Concurrent Kafka consumers, WebSocket fan-out |
| Redis Sorted Sets | Live leaderboard with O(log N) updates |
| Redis HyperLogLog | Unique user counting in constant memory |
| Redis Pub/Sub | Event-driven dashboard updates |
| Redis Sliding Window | Distributed rate limiting |
| Kafka producer/consumer groups | Decoupled multi-service event processing |
| Prometheus metrics | Every service exposes `/metrics` endpoint |
| Grafana dashboards | Professional monitoring for every service |
| System design | Bottleneck identification, capacity planning |

---

## 3. User Personas & Stories

### Persona: Developer (You)

> "As the developer, I want to stress-test the system at 100K events/sec and watch all dashboards respond in real time, so I can demonstrate Go and Redis's capabilities concretely."

**User Stories:**

- **US-01:** As a developer, I can start the entire platform with `docker-compose up` so I don't need to install anything manually.
- **US-02:** As a developer, I can run the traffic simulator and choose events/sec rate so I can demonstrate different load levels.
- **US-03:** As a developer, I can open the React dashboard and see all metrics updating live so I can demo the real-time capabilities.
- **US-04:** As a developer, I can open Grafana and see professional dashboards for every microservice so I can show production-grade observability.
- **US-05:** As a developer, I can trigger anomaly conditions (spike the simulator) and see real-time alerts on the dashboard.
- **US-06:** As a developer, I can view the Redis Internals panel showing live memory, ops/sec, and hit rate so I can explain Redis's efficiency.
- **US-07:** As a developer, I can view Kafka consumer lag metrics in Grafana so I can explain event-driven resilience.
- **US-08:** As a developer, I can see Go runtime metrics (goroutine count, GC pauses, memory) in Grafana so I can explain Go's concurrency model.

---

## 4. System Architecture

### 4.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         NexPulse Platform                           │
│                                                                     │
│  ┌──────────────┐    HTTP     ┌─────────────────────────────────┐   │
│  │   Simulator  │ ──POST──▶  │     API Gateway  :8080          │   │
│  │  (Go tool)   │            │  • Rate limiting (Redis ZADD)   │   │
│  └──────────────┘            │  • Event validation             │   │
│                              │  • Kafka producer               │   │
│  ┌──────────────┐            │  • /metrics (Prometheus)        │   │
│  │  React       │ ◀─WS────── │                                 │   │
│  │  Dashboard   │            └──────────────┬──────────────────┘   │
│  │  :5173       │                           │                       │
│  └──────────────┘                    Kafka: raw-events             │
│                                             │                       │
│  ┌──────────────┐                           ▼                       │
│  │   Grafana    │◀──scrape──  ┌─────────────────────────────────┐   │
│  │   :3000      │            │    Aggregator Service :8082      │   │
│  └──────┬───────┘            │  • Kafka consumer                │   │
│         │                    │  • ZINCRBY (leaderboard)         │   │
│  ┌──────▼───────┐            │  • PFADD (HyperLogLog)           │   │
│  │  Prometheus  │            │  • INCR (counters)               │   │
│  │  :9090       │            │  • PUBLISH (Pub/Sub)             │   │
│  └──────────────┘            │  • /metrics (Prometheus)         │   │
│                              └──────────────┬──────────────────┘    │
│                                             │                       │
│                              ┌──────────────▼──────────────────┐    │
│                              │    Anomaly Detector  :8083       │   │
│                              │  • Kafka consumer                │   │
│                              │  • EMA spike detection           │   │
│                              │  • Publishes to anomalies topic  │   │
│                              │  • /metrics (Prometheus)         │   │
│                              └──────────────┬──────────────────┘    │
│                                             │                       │
│                              ┌──────────────▼──────────────────┐    │
│                              │    Query Service  :8081          │   │
│                              │  • WebSocket server              │   │
│                              │  • Redis SUBSCRIBE               │   │
│                              │  • REST API for dashboard        │   │
│                              │  • /metrics (Prometheus)         │   │
│                              └─────────────────────────────────┘    │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                         Redis  :6379                          │  │
│  │  Sorted Sets │ HyperLogLog │ Pub/Sub │ Hashes │ Strings       │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Kafka + Zookeeper  :9092                   │  │
│  │  raw-events │ aggregated-metrics │ anomalies                  │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Data Flow

```
1. Simulator generates event → POST /ingest (Gateway)
2. Gateway checks rate limit in Redis → If OK, produce to Kafka "raw-events"
3. Aggregator consumes "raw-events" → writes Redis ZINCRBY, PFADD, INCR, HINCR
4. Aggregator PUBLISH to Redis "dashboard:updates" channel with JSON metrics
5. Anomaly Detector consumes "raw-events" → detects spikes → produces to "anomalies"
6. Query Service SUBSCRIBES to Redis "dashboard:updates" → fans out to all WebSocket clients
7. React Dashboard receives WebSocket push → updates all widgets in real time
8. Prometheus scrapes /metrics on all 4 services every 5s
9. Grafana queries Prometheus → renders professional dashboards
```

### 4.3 Port Map

| Service | Port | Purpose |
|---|---|---|
| API Gateway | 8080 | Event ingestion HTTP API |
| Query Service | 8081 | WebSocket + REST for dashboard |
| Aggregator | 8082 | Internal (metrics only) |
| Anomaly Detector | 8083 | Internal (metrics only) |
| Redis | 6379 | Data store |
| Kafka | 9092 | Event streaming |
| Zookeeper | 2181 | Kafka coordination |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Professional dashboards |
| React Dashboard | 5173 | Live custom dashboard |

---

## 5. Infrastructure & Docker Setup

### 5.1 `docker-compose.yml` — Complete Specification

```yaml
version: '3.8'

networks:
  nexpulse-net:
    driver: bridge

volumes:
  redis-data:
  grafana-data:
  prometheus-data:

services:
  # ─────────────────────────────────────────────────
  # Redis
  # ─────────────────────────────────────────────────
  redis:
    image: redis:7.2-alpine
    container_name: nexpulse-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
      - ./infra/redis/redis.conf:/etc/redis/redis.conf
    command: redis-server /etc/redis/redis.conf
    networks:
      - nexpulse-net
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # Redis Exporter — exposes Redis metrics to Prometheus
  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: nexpulse-redis-exporter
    ports:
      - "9121:9121"
    environment:
      REDIS_ADDR: "redis://redis:6379"
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - nexpulse-net

  # ─────────────────────────────────────────────────
  # Zookeeper
  # ─────────────────────────────────────────────────
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    container_name: nexpulse-zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    networks:
      - nexpulse-net

  # ─────────────────────────────────────────────────
  # Kafka
  # ─────────────────────────────────────────────────
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    container_name: nexpulse-kafka
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
      KAFKA_NUM_PARTITIONS: 6
    depends_on:
      - zookeeper
    networks:
      - nexpulse-net
    healthcheck:
      test: ["CMD", "kafka-broker-api-versions", "--bootstrap-server", "localhost:29092"]
      interval: 10s
      timeout: 5s
      retries: 10

  # Kafka Exporter — exposes Kafka consumer lag to Prometheus
  kafka-exporter:
    image: danielqsj/kafka-exporter:latest
    container_name: nexpulse-kafka-exporter
    ports:
      - "9308:9308"
    command:
      - --kafka.server=kafka:29092
    depends_on:
      kafka:
        condition: service_healthy
    networks:
      - nexpulse-net

  # ─────────────────────────────────────────────────
  # Prometheus
  # ─────────────────────────────────────────────────
  prometheus:
    image: prom/prometheus:v2.47.0
    container_name: nexpulse-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./infra/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-lifecycle'
    networks:
      - nexpulse-net

  # ─────────────────────────────────────────────────
  # Grafana
  # ─────────────────────────────────────────────────
  grafana:
    image: grafana/grafana:10.2.0
    container_name: nexpulse-grafana
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: nexpulse
      GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH: /etc/grafana/dashboards/overview.json
      GF_AUTH_ANONYMOUS_ENABLED: "true"
      GF_AUTH_ANONYMOUS_ORG_ROLE: Viewer
    volumes:
      - grafana-data:/var/lib/grafana
      - ./infra/grafana/provisioning:/etc/grafana/provisioning
      - ./infra/grafana/dashboards:/etc/grafana/dashboards
    depends_on:
      - prometheus
    networks:
      - nexpulse-net
```

### 5.2 Prometheus Config — `infra/prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 5s
  evaluation_interval: 5s

scrape_configs:
  - job_name: 'nexpulse-gateway'
    static_configs:
      - targets: ['host.docker.internal:8080']
    metrics_path: '/metrics'

  - job_name: 'nexpulse-aggregator'
    static_configs:
      - targets: ['host.docker.internal:8082']
    metrics_path: '/metrics'

  - job_name: 'nexpulse-anomaly'
    static_configs:
      - targets: ['host.docker.internal:8083']
    metrics_path: '/metrics'

  - job_name: 'nexpulse-query'
    static_configs:
      - targets: ['host.docker.internal:8081']
    metrics_path: '/metrics'

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'kafka'
    static_configs:
      - targets: ['kafka-exporter:9308']
```

### 5.3 Redis Config — `infra/redis/redis.conf`

```
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
appendonly yes
latency-tracking yes
latency-tracking-info-percentiles 50 99 99.9
```

### 5.4 Grafana Provisioning

**`infra/grafana/provisioning/datasources/prometheus.yml`**
```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    jsonData:
      timeInterval: '5s'
```

**`infra/grafana/provisioning/dashboards/dashboards.yml`**
```yaml
apiVersion: 1
providers:
  - name: NexPulse
    type: file
    options:
      path: /etc/grafana/dashboards
      foldersFromFilesStructure: true
```

---

## 6. Microservice Specifications

### 6.1 API Gateway

**Location:** `services/gateway/`  
**Port:** `8080`  
**Language:** Go 1.22  
**Role:** Single entry point for all incoming events. Validates, rate-limits, and produces to Kafka.

#### Directory Structure
```
services/gateway/
├── main.go
├── handler/
│   ├── ingest.go       # POST /ingest handler
│   └── health.go       # GET /health handler
├── ratelimit/
│   └── sliding_window.go  # Redis sliding window implementation
├── kafka/
│   └── producer.go     # Kafka producer wrapper
├── middleware/
│   └── metrics.go      # Prometheus middleware
└── config/
    └── config.go       # Env-based config
```

#### API Endpoints

**`POST /ingest`**
```json
// Request Body
{
  "event_type": "page_view",          // string, required
  "user_id": "usr_abc123",            // string, required
  "session_id": "ses_xyz789",         // string, required
  "endpoint": "/api/products",        // string, optional
  "status_code": 200,                 // int, optional
  "response_time_ms": 45,             // int, optional
  "metadata": {                       // object, optional
    "country": "IN",
    "browser": "Chrome",
    "os": "Windows"
  },
  "timestamp": "2024-06-02T13:00:00Z" // RFC3339, required
}

// Response 202 Accepted
{
  "accepted": true,
  "event_id": "evt_a1b2c3d4"
}

// Response 429 Too Many Requests (rate limited)
{
  "error": "rate_limit_exceeded",
  "retry_after_ms": 1000
}

// Response 400 Bad Request
{
  "error": "validation_failed",
  "details": "event_type is required"
}
```

**`GET /health`**
```json
{
  "status": "healthy",
  "kafka": "connected",
  "redis": "connected",
  "uptime_seconds": 3600
}
```

**`GET /metrics`** — Prometheus metrics endpoint

#### Rate Limiting — Sliding Window Algorithm

```go
// Redis Keys:
// rl:user:{user_id}  → Sorted Set
// rl:global          → Sorted Set

// Algorithm (per user, 1000 req/min limit):
func IsRateLimited(ctx context.Context, userID string) (bool, error) {
    key := fmt.Sprintf("rl:user:%s", userID)
    now := time.Now().UnixMilli()
    windowStart := now - 60000 // 60 seconds ago

    pipe := rdb.Pipeline()
    // Remove old entries outside window
    pipe.ZRemRangeByScore(ctx, key, "0", strconv.FormatInt(windowStart, 10))
    // Count remaining in window
    countCmd := pipe.ZCard(ctx, key)
    // Add current request
    pipe.ZAdd(ctx, key, redis.Z{Score: float64(now), Member: now})
    // Expire key after window
    pipe.Expire(ctx, key, 70*time.Second)
    pipe.Exec(ctx)

    count := countCmd.Val()
    return count >= 1000, nil
}
```

#### Kafka Producer

```go
// Produces to topic: raw-events
// Message key: event_type (for partition locality)
// Message value: JSON-encoded Event struct
// Compression: Snappy
// Batch size: 500 messages or 10ms, whichever comes first
```

---

### 6.2 Aggregator Service

**Location:** `services/aggregator/`  
**Port:** `8082` (metrics only)  
**Language:** Go 1.22  
**Role:** Consumes events from Kafka, computes all real-time aggregations in Redis, publishes dashboard updates via Redis Pub/Sub.

#### Directory Structure
```
services/aggregator/
├── main.go
├── consumer/
│   └── kafka_consumer.go   # Consumer group logic
├── aggregation/
│   ├── counters.go         # INCR-based time-bucket counters
│   ├── leaderboard.go      # Redis Sorted Set operations
│   ├── hyperloglog.go      # Unique user counting
│   ├── hashes.go           # Endpoint stats
│   └── publisher.go        # Redis Pub/Sub publish
├── metrics/
│   └── prometheus.go       # Prometheus metrics definitions
└── config/
    └── config.go
```

#### Kafka Consumer Config

```go
// Consumer Group: aggregator-group
// Topic: raw-events
// Partitions: 6 (parallel consumers = 6 goroutines)
// Offset Reset: earliest
// Commit Interval: 1 second
// Max Fetch Bytes: 10MB
```

#### Aggregation Operations (per consumed event)

**1. Time-Bucket Counters**
```redis
# Per-second bucket
INCR events:count:{yyyy-mm-dd-HH-MM-SS}
EXPIRE events:count:{yyyy-mm-dd-HH-MM-SS} 3600

# Per-minute bucket
INCR events:count:{yyyy-mm-dd-HH-MM}
EXPIRE events:count:{yyyy-mm-dd-HH-MM} 86400

# Error counter (if status_code >= 400)
INCR errors:count:{yyyy-mm-dd-HH-MM-SS}
EXPIRE errors:count:{yyyy-mm-dd-HH-MM-SS} 3600
```

**2. Leaderboard (Sorted Set)**
```redis
# Top event types
ZINCRBY leaderboard:event_types 1 "{event_type}"

# Top endpoints
ZINCRBY leaderboard:endpoints 1 "{endpoint}"

# Top countries
ZINCRBY leaderboard:countries 1 "{country}"

# Top error endpoints
ZINCRBY leaderboard:errors 1 "{endpoint}"   # only if status >= 400
```

**3. Unique Users (HyperLogLog)**
```redis
# Unique users today
PFADD unique_users:{yyyy-mm-dd} {user_id}

# Unique users this hour
PFADD unique_users:{yyyy-mm-dd-HH} {user_id}

# Unique sessions today
PFADD unique_sessions:{yyyy-mm-dd} {session_id}
```

**4. Endpoint Performance (Hash)**
```redis
# Response time sum + count for percentile approximation
HINCRBYFLOAT endpoint:stats:{endpoint} total_response_time {response_time_ms}
HINCRBY       endpoint:stats:{endpoint} request_count 1
HINCRBY       endpoint:stats:{endpoint} error_count 1     # if status >= 400
```

**5. Active Users (Expiring Set)**
```redis
# User is "active" if seen in last 5 minutes
SET user:active:{user_id} 1 EX 300

# Count active users — scan keys matching pattern
# (approximate, good enough for demo)
```

**6. Pub/Sub Dashboard Update**

Every 500ms, the aggregator computes a snapshot and publishes:
```json
// PUBLISH dashboard:updates {payload}
{
  "ts": 1717315200000,
  "events_last_second": 1423,
  "events_last_minute": 84201,
  "errors_last_second": 12,
  "unique_users_today": 94821,
  "unique_sessions_today": 102344,
  "top_event_types": [
    {"name": "page_view", "score": 44821},
    {"name": "api_call", "score": 31204},
    {"name": "click", "score": 19002}
  ],
  "top_endpoints": [
    {"name": "/api/products", "score": 22104}
  ],
  "top_countries": [
    {"name": "IN", "score": 38201}
  ],
  "kafka_consumer_lag": 124,
  "redis_ops_per_sec": 482001
}
```

---

### 6.3 Anomaly Detector Service

**Location:** `services/anomaly/`  
**Port:** `8083` (metrics only)  
**Language:** Go 1.22  
**Role:** Consumes raw events, runs anomaly detection algorithms, produces anomaly alerts to Kafka.

#### Anomaly Algorithms

**1. Exponential Moving Average (EMA) Spike Detection**
```go
// EMA formula: EMA = α × current + (1 - α) × previous_EMA
// α = 0.3 (smoothing factor)
// Spike threshold: current > EMA × 3.0

type EMASpikeDetector struct {
    alpha     float64
    ema       float64
    threshold float64
    mu        sync.Mutex
}

func (d *EMASpikeDetector) Update(value float64) (bool, float64) {
    d.mu.Lock()
    defer d.mu.Unlock()
    d.ema = d.alpha*value + (1-d.alpha)*d.ema
    isSpike := value > d.ema*d.threshold
    return isSpike, d.ema
}
```

**2. Anomaly Types Detected**

| Anomaly Type | Detection Logic | Severity |
|---|---|---|
| `traffic_spike` | events/sec > 3× EMA | WARNING |
| `traffic_drop` | events/sec < 0.2× EMA | WARNING |
| `error_surge` | error_rate > 20% in last 30s | CRITICAL |
| `slow_endpoint` | avg response time > 2000ms | WARNING |
| `rate_limit_storm` | >100 rate-limit hits/min | INFO |

**Kafka Output — `anomalies` topic:**
```json
{
  "anomaly_id": "anm_abc123",
  "type": "traffic_spike",
  "severity": "WARNING",
  "detected_at": "2024-06-02T13:45:00Z",
  "description": "Traffic spike detected: 15,420 events/sec vs EMA baseline of 4,200",
  "current_value": 15420,
  "baseline_value": 4200,
  "ratio": 3.67
}
```

---

### 6.4 Query / WebSocket Service

**Location:** `services/query/`  
**Port:** `8081`  
**Language:** Go 1.22  
**Role:** Serves the React dashboard. Maintains WebSocket connections. Subscribes to Redis Pub/Sub and fans out updates to all connected clients. Also provides REST snapshot API.

#### WebSocket Protocol

**Connection:** `ws://localhost:8081/ws`

**Server → Client messages (pushed every 500ms):**
```json
{
  "type": "metrics_update",
  "payload": { /* same structure as Pub/Sub dashboard:updates */ }
}
```

**Server → Client anomaly push:**
```json
{
  "type": "anomaly",
  "payload": {
    "anomaly_id": "anm_abc123",
    "type": "traffic_spike",
    "severity": "WARNING",
    "description": "Traffic spike detected",
    "detected_at": "2024-06-02T13:45:00Z"
  }
}
```

**Client → Server (control messages):**
```json
{ "type": "ping" }
// Server responds:
{ "type": "pong", "ts": 1717315200000 }
```

#### WebSocket Fan-out Architecture (Go)
```go
// Hub manages all WebSocket connections
type Hub struct {
    clients    map[*Client]bool
    broadcast  chan []byte
    register   chan *Client
    unregister chan *Client
    mu         sync.RWMutex
}

// Each client runs in its own goroutine
// Redis Pub/Sub goroutine feeds the broadcast channel
// Hub goroutine fans out to all connected clients
```

#### REST Endpoints

**`GET /api/snapshot`** — Current metrics snapshot
```json
{
  "events_total": 14820004,
  "events_last_second": 1423,
  "error_rate_percent": 2.4,
  "unique_users_today": 94821,
  "top_event_types": [...],
  "top_endpoints": [...],
  "leaderboard": [...]
}
```

**`GET /api/leaderboard/:type`** — Live leaderboard
- `:type` = `event_types` | `endpoints` | `countries` | `errors`
```json
{
  "leaderboard": [
    {"rank": 1, "name": "page_view", "score": 44821, "delta": 120},
    {"rank": 2, "name": "api_call", "score": 31204, "delta": -5}
  ],
  "updated_at": "2024-06-02T13:45:00Z"
}
```

**`GET /api/redis/info`** — Redis internals
```json
{
  "connected_clients": 12,
  "used_memory_human": "48.20M",
  "ops_per_sec": 482001,
  "keyspace_hits": 9482011,
  "keyspace_misses": 42011,
  "hit_rate_percent": 99.56,
  "total_keys": 2841
}
```

**`GET /api/anomalies`** — Recent anomalies (last 50)

**`GET /metrics`** — Prometheus metrics

---

### 6.5 Traffic Simulator

**Location:** `tools/simulator/`  
**Language:** Go 1.22  
**Role:** Generates realistic event traffic to demonstrate the system under load.

#### CLI Flags
```
Usage: ./simulator [flags]

  --rate          int     Events per second (default: 1000)
  --burst         int     Burst rate for spike simulation (default: 10000)
  --burst-every   int     Trigger burst every N seconds (default: 60)
  --users         int     Number of simulated user IDs (default: 10000)
  --endpoint      string  Gateway URL (default: http://localhost:8080)
  --duration      int     Run duration in seconds, 0 = forever (default: 0)
  --workers       int     Concurrent HTTP workers (default: 50)
```

#### Event Generation Logic
```go
var eventTypes = []string{
    "page_view", "api_call", "click", "form_submit",
    "error", "login", "logout", "purchase", "search",
}

var endpoints = []string{
    "/api/products", "/api/users", "/api/orders",
    "/api/cart", "/api/checkout", "/api/search",
    "/", "/about", "/pricing",
}

var countries = []string{
    "IN", "US", "GB", "DE", "FR", "JP", "BR", "AU",
}

// 95% requests succeed, 5% are errors (realistic distribution)
// Response times follow log-normal distribution (mean: 150ms)
// User IDs follow Zipf distribution (power law — few users, many requests)
```

---

## 7. Kafka Topic Contracts

### 7.1 Topic: `raw-events`
- **Partitions:** 6
- **Retention:** 24 hours
- **Replication:** 1 (local dev)
- **Key:** `event_type` (for partition locality)
- **Value:** JSON-encoded Event (see Gateway `/ingest` request body)
- **Consumers:** Aggregator Service (group: `aggregator-group`), Anomaly Detector (group: `anomaly-group`)

### 7.2 Topic: `aggregated-metrics`
- **Partitions:** 1
- **Retention:** 1 hour
- **Key:** `"metrics"` (single partition)
- **Value:** JSON metrics snapshot (published every 500ms)
- **Consumers:** Query Service (group: `query-group`)

### 7.3 Topic: `anomalies`
- **Partitions:** 1
- **Retention:** 7 days
- **Key:** `anomaly_type`
- **Value:** JSON Anomaly struct
- **Consumers:** Query Service (group: `query-group`) for live push

---

## 8. Redis Data Model

### Complete Key Schema

| Key Pattern | Type | TTL | Purpose |
|---|---|---|---|
| `rl:user:{user_id}` | Sorted Set | 70s | Rate limiting — sliding window |
| `rl:global` | Sorted Set | 70s | Global rate limiting |
| `events:count:{yyyy-mm-dd-HH-MM-SS}` | String (INCR) | 1h | Per-second event count |
| `events:count:{yyyy-mm-dd-HH-MM}` | String (INCR) | 24h | Per-minute event count |
| `errors:count:{yyyy-mm-dd-HH-MM-SS}` | String (INCR) | 1h | Per-second error count |
| `leaderboard:event_types` | Sorted Set | none | Event type leaderboard |
| `leaderboard:endpoints` | Sorted Set | none | Endpoint hit leaderboard |
| `leaderboard:countries` | Sorted Set | none | Country leaderboard |
| `leaderboard:errors` | Sorted Set | none | Error endpoint leaderboard |
| `unique_users:{yyyy-mm-dd}` | HyperLogLog | 7d | Unique users per day |
| `unique_users:{yyyy-mm-dd-HH}` | HyperLogLog | 48h | Unique users per hour |
| `unique_sessions:{yyyy-mm-dd}` | HyperLogLog | 7d | Unique sessions per day |
| `user:active:{user_id}` | String | 5min | Online presence |
| `endpoint:stats:{endpoint}` | Hash | none | Avg response time data |
| `dashboard:updates` | Pub/Sub Channel | — | Live dashboard broadcast |

### 8.1 Leaderboard Read Pattern
```redis
# Get top 10 event types with scores
ZREVRANGE leaderboard:event_types 0 9 WITHSCORES

# Result:
# 1) "page_view"  2) "44821"
# 3) "api_call"   4) "31204"
# ...

# Time complexity: O(log N + M) where M = range size
# This would be O(N log N) in PostgreSQL (ORDER BY + full scan)
```

### 8.2 HyperLogLog Memory Demo
```redis
# After processing 1,000,000 unique users:
PFCOUNT unique_users:2024-06-02          → 998,241 (0.18% error rate)
MEMORY USAGE unique_users:2024-06-02    → 12,304 bytes (12KB)

# PostgreSQL equivalent:
# SELECT COUNT(DISTINCT user_id) FROM events WHERE date = '2024-06-02'
# → Full table scan on 1M+ rows, minutes to run, GB of memory
```

---

## 9. Prometheus Metrics Specification

Every Go service exposes `/metrics` using `prometheus/client_golang`. Below are all custom metrics defined across services.

### 9.1 Gateway Service Metrics

```go
// ─── Counters ───
gateway_events_ingested_total          // Total events accepted
  labels: [event_type]

gateway_events_rejected_total          // Total events rejected
  labels: [reason]  // "rate_limited", "validation_failed"

gateway_rate_limit_hits_total          // Times rate limit was triggered
  labels: [user_id_hash]

// ─── Histograms ───
gateway_request_duration_seconds       // HTTP request latency
  labels: [method, path, status_code]
  buckets: [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1]

gateway_kafka_produce_duration_seconds // Kafka produce latency
  buckets: [0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1]

// ─── Gauges ───
gateway_active_connections             // Current active HTTP connections
gateway_kafka_producer_queue_size      // Events waiting to be produced

// ─── Go Runtime (auto-exposed by prometheus library) ───
go_goroutines                          // Number of goroutines
go_memstats_alloc_bytes                // Heap allocated
go_memstats_heap_inuse_bytes           // Heap in use
go_gc_duration_seconds                 // GC pause duration
```

### 9.2 Aggregator Service Metrics

```go
// ─── Counters ───
aggregator_events_processed_total      // Events successfully aggregated
  labels: [event_type]

aggregator_kafka_messages_consumed_total  // Raw Kafka messages consumed
  labels: [partition]

aggregator_redis_operations_total      // Redis commands executed
  labels: [command]  // "ZINCRBY", "PFADD", "INCR", "PUBLISH"

aggregator_publish_cycles_total        // Dashboard update publishes

// ─── Histograms ───
aggregator_event_processing_duration_seconds  // Time per event batch
  buckets: [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.5]

aggregator_redis_write_duration_seconds  // Redis pipeline write duration
  buckets: [0.0001, 0.0005, 0.001, 0.005, 0.01]

// ─── Gauges ───
aggregator_kafka_consumer_lag          // Current consumer group lag
  labels: [partition]

aggregator_unique_users_today          // HyperLogLog estimate
aggregator_events_per_second           // Rolling events/sec
```

### 9.3 Anomaly Detector Metrics

```go
// ─── Counters ───
anomaly_detected_total                 // Anomalies detected
  labels: [type, severity]  // type: "traffic_spike", severity: "WARNING"

anomaly_events_analyzed_total          // Events processed by detector

// ─── Histograms ───
anomaly_detection_duration_seconds     // Detection algorithm duration

// ─── Gauges ───
anomaly_ema_baseline                   // Current EMA baseline
  labels: [metric]  // "events_per_second", "error_rate"

anomaly_current_value                  // Current observed value
  labels: [metric]
```

### 9.4 Query Service Metrics

```go
// ─── Gauges ───
query_websocket_connections_active     // Current WebSocket clients connected
query_websocket_messages_sent_total    // Total messages pushed to clients

// ─── Histograms ───
query_websocket_broadcast_duration_seconds  // Fan-out duration
query_api_request_duration_seconds     // REST API latency
  labels: [path, status_code]

// ─── Counters ───
query_redis_subscribe_messages_total   // Messages received from Redis Pub/Sub
```

### 9.5 Redis Exporter Metrics (Auto-exposed)

Key metrics from `oliver006/redis_exporter`:
```
redis_connected_clients
redis_instantaneous_ops_per_sec
redis_used_memory_bytes
redis_keyspace_hits_total
redis_keyspace_misses_total
redis_commands_duration_seconds_total{cmd="zadd"}
redis_commands_duration_seconds_total{cmd="zincrby"}
redis_commands_duration_seconds_total{cmd="pfadd"}
redis_commands_duration_seconds_total{cmd="publish"}
redis_pubsub_channels
redis_pubsub_subscribers
redis_db_keys{db="db0"}
```

### 9.6 Kafka Exporter Metrics (Auto-exposed)

```
kafka_consumergroup_lag{consumergroup, topic, partition}
kafka_topic_partition_offset{topic, partition}
kafka_brokers
```

---

## 10. Grafana Dashboard Specification

> All dashboards use dark theme, are auto-provisioned via JSON files, and load automatically at startup.
> Every dashboard auto-refreshes every 5 seconds.

### 10.1 Dashboard 1: NexPulse Overview (`overview.json`)

**Purpose:** Executive summary — the first screen you show in a demo.

| Panel | Visualization | Query | Position |
|---|---|---|---|
| **Events/sec** | Stat (large, green/red threshold) | `rate(gateway_events_ingested_total[10s])` | Top row left |
| **Error Rate %** | Gauge (0-100%, red > 5%) | `rate(aggregator...[10s]) where event_type=error / total` | Top row center |
| **Active WebSocket Clients** | Stat | `query_websocket_connections_active` | Top row right |
| **Unique Users Today** | Stat | `aggregator_unique_users_today` | Second row left |
| **Kafka Consumer Lag** | Stat (red > 1000) | `kafka_consumergroup_lag` | Second row center |
| **Redis Ops/sec** | Stat | `redis_instantaneous_ops_per_sec` | Second row right |
| **Event Throughput Timeline** | Time series (area chart, gradient fill) | `rate(gateway_events_ingested_total[10s])` | Full width |
| **Error Rate Timeline** | Time series (red line) | `rate(errors[10s])` | Full width |

**Thresholds & Colors:**
- Events/sec: Green > 1000, Yellow 100-1000, Red < 100
- Error Rate: Green < 1%, Yellow 1-5%, Red > 5%
- Kafka Lag: Green < 100, Yellow 100-1000, Red > 1000

---

### 10.2 Dashboard 2: Go Runtime & Goroutines (`go_runtime.json`)

**Purpose:** Shows Go's concurrency model in action — the thing that impresses interviewers.

| Panel | Visualization | Query |
|---|---|---|
| **Live Goroutine Count (all services)** | Time series (multi-line) | `go_goroutines{job=~"nexpulse-.*"}` |
| **Memory Allocated** | Time series | `go_memstats_alloc_bytes{job=~"nexpulse-.*"}` |
| **GC Pause Duration p99** | Time series | `histogram_quantile(0.99, go_gc_duration_seconds)` |
| **Goroutines per Service** | Bar chart (current) | `go_goroutines` grouped by job |
| **Heap In Use** | Gauge per service | `go_memstats_heap_inuse_bytes` |
| **Go Version** | Table | `go_info` |

**What to highlight:** A Node.js server handling 1000 WebSocket connections uses 1 goroutine (blocking event loop). Go uses ~1002 goroutines (one per connection + runtime) but each goroutine costs only ~8KB stack. Show this live.

---

### 10.3 Dashboard 3: Redis Deep Dive (`redis.json`)

**Purpose:** Shows Redis's internal efficiency — the "12KB for 1M users" moment.

| Panel | Visualization | Query |
|---|---|---|
| **Ops/sec (live)** | Stat + sparkline | `redis_instantaneous_ops_per_sec` |
| **Memory Used** | Gauge | `redis_used_memory_bytes` |
| **Hit Rate %** | Gauge (99%+ is ideal) | `redis_keyspace_hits / (hits + misses) * 100` |
| **Connected Clients** | Stat | `redis_connected_clients` |
| **Total Keys** | Stat | `redis_db_keys{db="db0"}` |
| **Pub/Sub Active Channels** | Stat | `redis_pubsub_channels` |
| **Pub/Sub Subscribers** | Stat | `redis_pubsub_subscribers` |
| **Command Latency by Type** | Bar chart | `redis_commands_duration_seconds_total` by cmd |
| **Memory Timeline** | Time series | `redis_used_memory_bytes` |
| **Keyspace Hits vs Misses** | Stacked area | hits + misses rates |
| **ZADD Latency p99** | Stat | sorted set command duration |
| **PFADD Latency p99** | Stat | HyperLogLog command duration |

---

### 10.4 Dashboard 4: Kafka Pipeline (`kafka.json`)

**Purpose:** Shows event streaming, consumer lag, and resilience.

| Panel | Visualization | Query |
|---|---|---|
| **Consumer Lag — Aggregator** | Time series (should trend to 0) | `kafka_consumergroup_lag{consumergroup="aggregator-group"}` |
| **Consumer Lag — Anomaly** | Time series | `kafka_consumergroup_lag{consumergroup="anomaly-group"}` |
| **Topic Partition Offsets** | Time series | `kafka_topic_partition_offset` |
| **Messages Consumed/sec** | Time series | `rate(aggregator_kafka_messages_consumed_total[10s])` |
| **Messages Produced/sec** | Time series | `rate(gateway_events_ingested_total[10s])` |
| **Produce vs Consume Gap** | Time series (dual axis) | both above on same chart |
| **Kafka Broker Count** | Stat | `kafka_brokers` |

**What to highlight:** Spike the simulator → consumer lag increases → Kafka buffers everything → simulator returns to normal → lag drains to 0. Zero events lost. This is impossible with traditional HTTP fan-out.

---

### 10.5 Dashboard 5: Anomaly Detection (`anomalies.json`)

| Panel | Visualization | Query |
|---|---|---|
| **Anomalies Detected (total)** | Stat + counter | `anomaly_detected_total` |
| **Anomalies by Type** | Pie chart | `anomaly_detected_total` by type |
| **Anomalies by Severity** | Bar chart | `anomaly_detected_total` by severity |
| **EMA Baseline vs Actual** | Time series (2 lines) | `anomaly_ema_baseline` + `anomaly_current_value` |
| **Spike Events Timeline** | Annotations | when `anomaly_detected_total{type="traffic_spike"}` increases |
| **Error Surge Events** | Annotations | when `anomaly_detected_total{type="error_surge"}` increases |

---

### 10.6 Dashboard 6: Gateway & Rate Limiting (`gateway.json`)

| Panel | Visualization | Query |
|---|---|---|
| **Request Rate** | Time series | `rate(gateway_events_ingested_total[10s])` |
| **Rate Limit Hits/sec** | Time series (orange) | `rate(gateway_rate_limit_hits_total[10s])` |
| **Request Latency p50/p95/p99** | Time series | `histogram_quantile(0.99, gateway_request_duration_seconds)` |
| **Kafka Produce Latency p99** | Stat | `histogram_quantile(0.99, gateway_kafka_produce_duration_seconds)` |
| **Rejection Reasons** | Pie chart | `gateway_events_rejected_total` by reason |
| **Active Connections** | Time series | `gateway_active_connections` |

---

## 11. React Dashboard Specification

**Location:** `dashboard/`  
**Stack:** React 18 + Vite + Recharts + Framer Motion  
**Port:** 5173

### 11.1 Layout

```
┌──────────────────────────────────────────────────────────────┐
│  ⚡ NexPulse  [● LIVE]  Connected Clients: 1  [Grafana ↗]   │  ← Header
├──────────────────────────────────────────────────────────────┤
│  [Events/sec]  [Error Rate]  [Unique Users]  [Kafka Lag]    │  ← KPI Row
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  [── Event Throughput Timeline (area chart) ──────────────] │  ← Full width
│                                                              │
├─────────────────────────────┬────────────────────────────────┤
│  🏆 Event Type Leaderboard  │  🌍 Country Distribution       │
│  (animated rank changes)    │  (bar chart, live)             │
├─────────────────────────────┼────────────────────────────────┤
│  🔴 Error Rate Timeline     │  ⚡ Redis Internals            │
│  (red area chart)           │  (ops/sec, hit rate, memory)  │
├─────────────────────────────┴────────────────────────────────┤
│  🚨 Anomaly Alert Feed (real-time, slide-in animations)      │
├──────────────────────────────────────────────────────────────┤
│  📊 Top Endpoints Heatmap   │  📡 WebSocket Message Feed     │
└──────────────────────────────────────────────────────────────┘
```

### 11.2 Component Specifications

**KPICard Component**
```jsx
// Props: label, value, unit, trend, thresholdRed, thresholdYellow
// Behavior: 
//   - Value animates on change (spring animation)
//   - Background pulses green→normal on positive spike
//   - Background turns red when threshold exceeded
//   - Shows ↑↓ trend indicator with color
```

**ThroughputChart Component**
```jsx
// Recharts AreaChart
// X: last 60 seconds (rolling window)
// Y: events/second
// Fill: gradient (emerald to transparent)
// Stroke: bright emerald
// Tooltip: custom dark tooltip
// Animation: smooth data shift (no re-render flicker)
```

**LeaderboardWidget Component**
```jsx
// Animated list with rank transitions
// When rank changes: item slides to new position (Framer Motion layoutId)
// Each item shows: rank badge, name, count, mini bar
// Updates every 500ms from WebSocket
```

**RedisInternals Component**
```jsx
// Radial gauge for hit rate (0-100%)
// Stat cards: ops/sec, memory, connected clients, total keys
// Mini sparkline for ops/sec last 60s
// All values animate on change
```

**AnomalyFeed Component**
```jsx
// Slide-in from right on new anomaly (Framer Motion)
// Color coded: WARNING=yellow, CRITICAL=red, INFO=blue
// Shows: type, description, ratio, time
// Auto-dismisses after 30 seconds
// Max 5 visible at once, oldest scrolls out
```

**WebSocketMessageFeed Component**
```jsx
// Rolling log of last 20 raw WebSocket messages
// Monospace font, dark background
// New messages animate in from bottom
// Useful for showing the actual data being pushed
```

### 11.3 WebSocket Hook

```jsx
// hooks/useNexPulse.js
export function useNexPulse() {
  const [metrics, setMetrics] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8081/ws');
    ws.onopen = () => setConnected(true);
    ws.onclose = () => { setConnected(false); /* reconnect */ };
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'metrics_update') setMetrics(msg.payload);
      if (msg.type === 'anomaly') setAnomalies(prev => [msg.payload, ...prev].slice(0, 50));
      setLastMessage(msg);
    };
    return () => ws.close();
  }, []);

  return { metrics, anomalies, connected, lastMessage };
}
```

---

## 12. API Reference

### 12.1 Complete Endpoint List

| Method | Path | Service | Description |
|---|---|---|---|
| POST | `/ingest` | Gateway:8080 | Ingest event |
| GET | `/health` | Gateway:8080 | Health check |
| GET | `/metrics` | Gateway:8080 | Prometheus metrics |
| GET | `/metrics` | Aggregator:8082 | Prometheus metrics |
| GET | `/metrics` | Anomaly:8083 | Prometheus metrics |
| GET | `/metrics` | Query:8081 | Prometheus metrics |
| WS | `/ws` | Query:8081 | WebSocket live stream |
| GET | `/api/snapshot` | Query:8081 | Current metrics snapshot |
| GET | `/api/leaderboard/:type` | Query:8081 | Live leaderboard |
| GET | `/api/redis/info` | Query:8081 | Redis internals |
| GET | `/api/anomalies` | Query:8081 | Recent anomalies |
| GET | `/api/goroutines` | Query:8081 | Go runtime stats |

---

## 13. Implementation Phases

### Phase 0: Setup (Day 1)
- [ ] Install Go 1.22, Docker Desktop, Node.js 20
- [ ] Create GitHub repository: `nexpulse`
- [ ] Initialize Go workspace: `go work init`
- [ ] Create directory structure (see Section 15)
- [ ] Write `docker-compose.yml` (Redis + Kafka + Zookeeper + Prometheus + Grafana)
- [ ] Run `docker-compose up` and verify all containers healthy
- [ ] Open `redis-cli` and run first Redis commands manually (ZADD, ZINCRBY, PFADD)
- [ ] Use `kafka-topics.sh --create` to create topics manually
- [ ] Verify Prometheus at `localhost:9090` and Grafana at `localhost:3000`

**Exit Criteria:** All infrastructure running, Redis CLI working, Grafana shows Prometheus datasource connected.

---

### Phase 1: Traffic Simulator (Days 2-3)
- [ ] Create `tools/simulator/main.go`
- [ ] Implement CLI flags with `flag` package
- [ ] Implement realistic event generation (Zipf distribution for users)
- [ ] Implement HTTP worker pool (50 concurrent goroutines)
- [ ] Add burst mode (spike every N seconds)
- [ ] Test: Run simulator at 1000 events/sec, watch with `redis-cli monitor`

**Key learning:** Goroutines as lightweight workers. Compare with threading cost in other languages.

**Exit Criteria:** Simulator produces 10,000 events/sec without crashing.

---

### Phase 2: API Gateway (Days 4-6)
- [ ] Create `services/gateway/main.go` with Gin router
- [ ] Implement `/ingest` handler with JSON validation
- [ ] Create `config/config.go` with env var loading
- [ ] Implement Redis connection with `go-redis`
- [ ] Implement sliding window rate limiter in `ratelimit/sliding_window.go`
- [ ] Implement Kafka producer in `kafka/producer.go`
- [ ] Wire rate limiter + Kafka producer into `/ingest` handler
- [ ] Add Prometheus metrics middleware
- [ ] Implement `/health` and `/metrics` endpoints
- [ ] Test with `curl` — verify 429 after rate limit exceeded

**Key learning:** Redis ZADD/ZREMRANGEBYSCORE for sliding window. Go's Gin middleware pattern.

**Exit Criteria:** Gateway running, rate limiting working, events appearing in Kafka topic.

---

### Phase 3: Aggregator Service (Days 7-10)
- [ ] Create `services/aggregator/main.go`
- [ ] Implement Kafka consumer group in `consumer/kafka_consumer.go`
- [ ] Implement 6-partition concurrent consumers (6 goroutines)
- [ ] Implement Redis pipeline for batch writes in `aggregation/`
  - [ ] `counters.go`: INCR time buckets
  - [ ] `leaderboard.go`: ZINCRBY sorted sets
  - [ ] `hyperloglog.go`: PFADD unique users
  - [ ] `hashes.go`: HINCRBYFLOAT endpoint stats
  - [ ] `publisher.go`: PUBLISH dashboard:updates every 500ms
- [ ] Add Prometheus metrics: consumer lag, processing time, Redis ops
- [ ] Test: Run simulator + aggregator, watch `redis-cli` keys update live

**Key learning:** Kafka consumer groups, Go channels for aggregation pipeline, Redis pipelining for batch efficiency.

**Exit Criteria:** Leaderboard updating in Redis, PFCOUNT returning accurate unique user estimates.

---

### Phase 4: Query Service + WebSockets (Days 11-14)
- [ ] Create `services/query/main.go`
- [ ] Implement WebSocket hub with goroutine fan-out
- [ ] Implement Redis Pub/Sub subscriber goroutine
- [ ] Wire: Pub/Sub → hub.broadcast channel → all WebSocket clients
- [ ] Implement REST endpoints: `/api/snapshot`, `/api/leaderboard/:type`, `/api/redis/info`
- [ ] Add Prometheus metrics: active connections, messages sent, broadcast duration
- [ ] Test with `websocat ws://localhost:8081/ws` — verify live JSON arriving

**Key learning:** Go's channel-based fan-out pattern. gorilla/websocket. Redis Pub/Sub.

**Exit Criteria:** 100 simultaneous WebSocket connections all receive live updates within 200ms.

---

### Phase 5: Anomaly Detector (Days 15-16)
- [ ] Create `services/anomaly/main.go`
- [ ] Implement `EMASpikeDetector` struct
- [ ] Implement Kafka consumer (group: `anomaly-group`)
- [ ] Implement detection for all 5 anomaly types
- [ ] Produce to `anomalies` Kafka topic
- [ ] Query Service consumes `anomalies` → push to WebSocket clients
- [ ] Add Prometheus metrics
- [ ] Test: Spike simulator to 50K events/sec → verify anomaly appears in dashboard

**Exit Criteria:** Anomaly detected within 2 seconds of spike, appears on all connected dashboards.

---

### Phase 6: React Dashboard (Days 17-20)
- [ ] Create Vite project: `npm create vite@latest dashboard -- --template react`
- [ ] Install: `recharts framer-motion`
- [ ] Implement `useNexPulse` hook (WebSocket connection with auto-reconnect)
- [ ] Build all 8 components (KPICard, ThroughputChart, LeaderboardWidget, etc.)
- [ ] Implement dark glassmorphism theme with CSS variables
- [ ] Add Framer Motion animations for leaderboard rank changes
- [ ] Add anomaly slide-in notifications
- [ ] Add "Grafana →" button linking to `localhost:3000`
- [ ] Test with simulator at various rates

**Exit Criteria:** Dashboard feels alive and professional. All widgets update smoothly.

---

### Phase 7: Grafana Dashboards (Days 20-21)
- [ ] Build Dashboard 1: Overview (6 panels)
- [ ] Build Dashboard 2: Go Runtime (6 panels)
- [ ] Build Dashboard 3: Redis Deep Dive (12 panels)
- [ ] Build Dashboard 4: Kafka Pipeline (7 panels)
- [ ] Build Dashboard 5: Anomaly Detection (6 panels)
- [ ] Build Dashboard 6: Gateway & Rate Limiting (6 panels)
- [ ] Export all dashboards as JSON → save to `infra/grafana/dashboards/`
- [ ] Configure auto-provisioning so dashboards load on `docker-compose up`
- [ ] Set all refresh intervals to 5s
- [ ] Set all themes to dark

**Exit Criteria:** `docker-compose up` → `localhost:3000` → all 6 dashboards available and auto-refreshing.

---

### Phase 8: Polish & Demo (Days 22-24)
- [ ] Write comprehensive `README.md` with architecture diagram
- [ ] Record demo video: Start simulator at 1K, 10K, 50K, 100K events/sec
- [ ] Capture screenshots of all Grafana dashboards at peak load
- [ ] Write `ARCHITECTURE.md` explaining every design decision
- [ ] Add `make` commands: `make up`, `make simulate`, `make simulate-burst`, `make down`
- [ ] Write LinkedIn post with video and GitHub link

---

## 14. Non-Functional Requirements

### 14.1 Performance

| Requirement | Value |
|---|---|
| Gateway max throughput | ≥ 50,000 req/sec |
| Aggregator processing latency | < 50ms per batch |
| WebSocket broadcast delay | < 100ms from Kafka to client |
| Redis operation latency | < 1ms p99 |
| Dashboard update frequency | Every 500ms |

### 14.2 Resilience

| Requirement | Behavior |
|---|---|
| Aggregator crash | Kafka retains events; aggregator re-reads from last committed offset |
| Redis restart | Aggregation state resets; fresh accumulation begins |
| WebSocket client disconnect | Client removed from hub; no impact on other clients |
| Kafka broker down | Gateway buffers in memory; produces when Kafka recovers |

### 14.3 Observability

- Every service MUST expose `/metrics` for Prometheus
- Every service MUST log structured JSON to stdout
- Grafana dashboards MUST auto-load on startup
- All custom metrics MUST have meaningful labels

### 14.4 Local Development

- Full platform starts with: `docker-compose up`
- Go services run locally: `go run ./services/gateway`
- Dashboard starts with: `cd dashboard && npm run dev`
- No paid services, no cloud APIs, no credit card required

---

## 15. Repository Structure

```
nexpulse/
│
├── services/
│   ├── gateway/
│   │   ├── main.go
│   │   ├── handler/
│   │   │   ├── ingest.go
│   │   │   └── health.go
│   │   ├── ratelimit/
│   │   │   └── sliding_window.go
│   │   ├── kafka/
│   │   │   └── producer.go
│   │   ├── middleware/
│   │   │   └── metrics.go
│   │   ├── config/
│   │   │   └── config.go
│   │   └── go.mod
│   │
│   ├── aggregator/
│   │   ├── main.go
│   │   ├── consumer/
│   │   │   └── kafka_consumer.go
│   │   ├── aggregation/
│   │   │   ├── counters.go
│   │   │   ├── leaderboard.go
│   │   │   ├── hyperloglog.go
│   │   │   ├── hashes.go
│   │   │   └── publisher.go
│   │   ├── metrics/
│   │   │   └── prometheus.go
│   │   ├── config/
│   │   │   └── config.go
│   │   └── go.mod
│   │
│   ├── anomaly/
│   │   ├── main.go
│   │   ├── detector/
│   │   │   └── ema.go
│   │   ├── consumer/
│   │   │   └── kafka_consumer.go
│   │   └── go.mod
│   │
│   └── query/
│       ├── main.go
│       ├── websocket/
│       │   ├── hub.go
│       │   └── client.go
│       ├── handler/
│       │   ├── api.go
│       │   └── redis_info.go
│       ├── pubsub/
│       │   └── subscriber.go
│       └── go.mod
│
├── tools/
│   └── simulator/
│       ├── main.go
│       ├── generator/
│       │   └── events.go
│       └── go.mod
│
├── dashboard/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── hooks/
│   │   │   └── useNexPulse.js
│   │   ├── components/
│   │   │   ├── KPICard.jsx
│   │   │   ├── ThroughputChart.jsx
│   │   │   ├── LeaderboardWidget.jsx
│   │   │   ├── RedisInternals.jsx
│   │   │   ├── AnomalyFeed.jsx
│   │   │   ├── ErrorRateChart.jsx
│   │   │   └── WebSocketFeed.jsx
│   │   └── styles/
│   │       └── index.css
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── infra/
│   ├── docker-compose.yml
│   ├── redis/
│   │   └── redis.conf
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       ├── provisioning/
│       │   ├── datasources/
│       │   │   └── prometheus.yml
│       │   └── dashboards/
│       │       └── dashboards.yml
│       └── dashboards/
│           ├── overview.json
│           ├── go_runtime.json
│           ├── redis.json
│           ├── kafka.json
│           ├── anomalies.json
│           └── gateway.json
│
├── go.work              # Go workspace file
├── Makefile             # make up, make simulate, make down
├── README.md
└── ARCHITECTURE.md
```

### 15.1 Makefile

```makefile
.PHONY: up down simulate simulate-burst logs clean

up:
	docker-compose -f infra/docker-compose.yml up -d
	@echo "⚡ NexPulse is up!"
	@echo "   Grafana:    http://localhost:3000  (admin/nexpulse)"
	@echo "   Prometheus: http://localhost:9090"
	@echo "   Gateway:    http://localhost:8080"
	@echo "   Dashboard:  http://localhost:5173"

down:
	docker-compose -f infra/docker-compose.yml down -v

gateway:
	cd services/gateway && go run .

aggregator:
	cd services/aggregator && go run .

anomaly:
	cd services/anomaly && go run .

query:
	cd services/query && go run .

dashboard:
	cd dashboard && npm run dev

simulate:
	cd tools/simulator && go run . --rate 5000 --workers 50

simulate-burst:
	cd tools/simulator && go run . --rate 5000 --burst 50000 --burst-every 30

simulate-max:
	cd tools/simulator && go run . --rate 100000 --workers 500

logs:
	docker-compose -f infra/docker-compose.yml logs -f

clean:
	docker-compose -f infra/docker-compose.yml down -v --remove-orphans
```

---

## Appendix: Go Dependencies

```go
// Each service go.mod will include:
require (
    github.com/gin-gonic/gin v1.9.1
    github.com/redis/go-redis/v9 v9.3.0
    github.com/segmentio/kafka-go v0.4.47
    github.com/gorilla/websocket v1.5.1
    github.com/prometheus/client_golang v1.17.0
)
```

## Appendix: Why This Stack Beats Everything Else

| Scenario | Node.js + Express | Python + Django | Go + Redis + Kafka |
|---|---|---|---|
| 100K concurrent WebSocket connections | ❌ Event loop saturated | ❌ Thread per connection = OOM | ✅ 100K goroutines @ 8KB each |
| 100K events/sec ingestion | ❌ Single-threaded | ❌ GIL blocks parallel I/O | ✅ Parallel goroutines, compiled I/O |
| Real-time unique user count | ❌ COUNT DISTINCT (expensive) | ❌ Same SQL issue | ✅ HyperLogLog O(1), 12KB RAM |
| Live leaderboard top 10 | ❌ ORDER BY = O(N log N) | ❌ Same | ✅ ZREVRANGE O(log N + 10) |
| Rate limit across 10 instances | ❌ In-memory (per-process) | ❌ Same | ✅ Redis shared state |
| Message loss on service crash | ❌ Lost in memory | ❌ Same | ✅ Kafka retains, re-reads offset |
| Distributed event fan-out | ❌ Manual pub/sub | ❌ Celery/Redis but complex | ✅ Kafka consumer groups native |

---

*NexPulse PRD v1.0 — Built for learning. Production-grade in design.*
