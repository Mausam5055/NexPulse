# ─────────────────────────────────────────────────────────────
#  NexPulse Makefile
#  Run: make <target>
#  Windows: install make via: winget install GnuWin32.Make
#           OR use start.ps1 instead
# ─────────────────────────────────────────────────────────────

.PHONY: up down logs clean gateway aggregator anomaly query simulate simulate-burst simulate-max check

# ─── Infrastructure ───────────────────────────────────────────

up:
	@echo "⚡ Starting NexPulse Infrastructure..."
	docker-compose -f infra/docker-compose.yml up -d
	@echo ""
	@echo "✅ All services up!"
	@echo "   📊 Grafana:     http://localhost:3000  (admin / nexpulse)"
	@echo "   📈 Prometheus:  http://localhost:9090"
	@echo "   🔴 Redis CLI:   redis-cli -p 6379"
	@echo "   📨 Kafka:       localhost:9092"
	@echo ""
	@echo "Next: run Go services in separate terminals:"
	@echo "   make gateway | make aggregator | make anomaly | make query"

down:
	docker-compose -f infra/docker-compose.yml down

clean:
	docker-compose -f infra/docker-compose.yml down -v --remove-orphans
	@echo "🗑️  All containers and volumes removed."

logs:
	docker-compose -f infra/docker-compose.yml logs -f

# ─── Go Services (run in separate terminals) ──────────────────

gateway:
	@echo "🚦 Starting Gateway on :8080"
	cd services/gateway && go run .

aggregator:
	@echo "⚙️  Starting Aggregator on :8082"
	cd services/aggregator && go run .

anomaly:
	@echo "🔍 Starting Anomaly Detector on :8083"
	cd services/anomaly && go run .

query:
	@echo "📡 Starting Query/WebSocket on :8081"
	cd services/query && go run .

dashboard:
	@echo "📊 Starting React Dashboard on :5173"
	cd dashboard && npm run dev

# ─── Traffic Simulator ────────────────────────────────────────

simulate:
	@echo "🚀 Simulating 1,000 events/sec..."
	cd tools/simulator && go run . --rate 1000 --workers 20

simulate-medium:
	@echo "🚀 Simulating 10,000 events/sec..."
	cd tools/simulator && go run . --rate 10000 --workers 100

simulate-max:
	@echo "🚀 MAX POWER — 50,000 events/sec!"
	cd tools/simulator && go run . --rate 50000 --workers 500

# ─── Verification ─────────────────────────────────────────────

check:
	@echo "🔍 Checking all services..."
	@curl -sf http://localhost:8080/health | python -m json.tool || echo "❌ Gateway not running"
	@curl -sf http://localhost:8081/health | python -m json.tool || echo "❌ Query not running"
	@curl -sf http://localhost:8082/health | python -m json.tool || echo "❌ Aggregator not running"
	@curl -sf http://localhost:8083/health | python -m json.tool || echo "❌ Anomaly not running"
	@curl -sf http://localhost:9090/-/ready && echo "✅ Prometheus OK" || echo "❌ Prometheus not running"
	@curl -sf http://localhost:3000/api/health && echo "✅ Grafana OK" || echo "❌ Grafana not running"

build:
	@echo "🔨 Building all Go services..."
	cd services/gateway   && go build -o ../../bin/gateway .
	cd services/aggregator && go build -o ../../bin/aggregator .
	cd services/anomaly    && go build -o ../../bin/anomaly .
	cd services/query      && go build -o ../../bin/query .
	cd tools/simulator     && go build -o ../../bin/simulator .
	@echo "✅ All binaries in ./bin/"

redis-cli:
	docker exec -it nexpulse-redis redis-cli

redis-monitor:
	docker exec -it nexpulse-redis redis-cli MONITOR

# ─── Git ──────────────────────────────────────────────────────

init-git:
	git init
	git add .
	git commit -m "feat: Phase 0 scaffold — infra + service stubs + 6 Grafana dashboards"
	@echo "✅ Git initialized. Push to GitHub:"
	@echo "   git remote add origin https://github.com/YOUR_USERNAME/nexpulse.git"
	@echo "   git push -u origin main"
