package main

import (
	"context"
	"log"
	"net/http"
	"os"

	"github.com/prometheus/client_golang/prometheus/promhttp"
	"nexpulse/anomaly/alert"
	"nexpulse/anomaly/detector"
)

func main() {
	log.Println("┌─────────────────────────────────────────┐")
	log.Println("│  🔍 NexPulse — Anomaly Detector         │")
	log.Println("│  Phase 2 | Port :8083                   │")
	log.Println("└─────────────────────────────────────────┘")

	redisAddr := os.Getenv("REDIS_ADDR")
	if redisAddr == "" {
		redisAddr = "127.0.0.1:6379"
	}

	alert.InitRedis(redisAddr)
	detector.StartEMAEvaluator()
	log.Println("✅ EMA anomaly evaluator started")

	mux := http.NewServeMux()
	mux.Handle("/metrics", promhttp.Handler())
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"status":"healthy","service":"anomaly","phase":"2"}`))
	})

	// Expose an internal endpoint so gateway/aggregator can record events
	mux.HandleFunc("/record", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "POST only", http.StatusMethodNotAllowed)
			return
		}
		detector.RecordEvent()
		w.WriteHeader(http.StatusNoContent)
	})

	log.Println("✅ Anomaly Detector listening on :8083")
	if err := http.ListenAndServe(":8083", mux); err != nil {
		log.Fatalf("❌ Anomaly Detector failed: %v\n", err)
	}

	_ = context.Background() // suppress unused import if alert uses it internally
}
