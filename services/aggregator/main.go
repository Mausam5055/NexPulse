package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/redis/go-redis/v9"
	kafka "github.com/segmentio/kafka-go"
	"nexpulse/aggregator/metrics"
)

func main() {
	log.Println("┌─────────────────────────────────────────┐")
	log.Println("│  ⚙️  NexPulse — Aggregator              │")
	log.Println("│  Phase 2 | Port :8082                   │")
	log.Println("└─────────────────────────────────────────┘")

	kafkaBroker := os.Getenv("KAFKA_BROKER")
	if kafkaBroker == "" {
		kafkaBroker = "127.0.0.1:9092"
	}
	redisAddr := os.Getenv("REDIS_ADDR")
	if redisAddr == "" {
		redisAddr = "127.0.0.1:6379"
	}

	rdb := redis.NewClient(&redis.Options{Addr: redisAddr})
	if err := rdb.Ping(context.Background()).Err(); err != nil {
		log.Fatalf("❌ Failed to connect to Redis: %v", err)
	}
	log.Println("✅ Aggregator connected to Redis:", redisAddr)

	reader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:        []string{kafkaBroker},
		GroupID:        "aggregator-group",
		Topic:          "raw-events",
		MinBytes:       1,
		MaxBytes:       10e6,
		CommitInterval: time.Second,
	})
	defer reader.Close()
	log.Println("✅ Aggregator connected to Kafka broker:", kafkaBroker)

	// Expose metrics + health on :8082
	go func() {
		mux := http.NewServeMux()
		mux.Handle("/metrics", promhttp.Handler())
		mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			w.Write([]byte(`{"status":"healthy","service":"aggregator","phase":"2"}`))
		})
		log.Println("✅ Aggregator metrics/health on :8082")
		if err := http.ListenAndServe(":8082", mux); err != nil {
			log.Fatalf("❌ Aggregator HTTP server failed: %v", err)
		}
	}()

	log.Println("📥 Consuming from Kafka topic: raw-events")
	ctx := context.Background()
	for {
		msg, err := reader.ReadMessage(ctx)
		if err != nil {
			log.Printf("⚠️ Kafka read error: %v", err)
			continue
		}

		start := time.Now()
		metrics.KafkaMessagesConsumed.Inc()

		var event map[string]any
		if err := json.Unmarshal(msg.Value, &event); err != nil {
			log.Printf("⚠️ Failed to parse event: %v", err)
			continue
		}

		// Aggregate: increment event_type counter and update leaderboard
		pipe := rdb.Pipeline()
		if eventType, ok := event["event_type"].(string); ok {
			pipe.Incr(ctx, "agg:event_type:"+eventType)
		}
		if userID, ok := event["user_id"].(string); ok {
			pipe.ZIncrBy(ctx, "leaderboard:users", 1, userID)
		}
		if _, err := pipe.Exec(ctx); err != nil {
			metrics.RedisErrors.Inc()
			log.Printf("⚠️ Redis pipeline error: %v", err)
		}

		metrics.EventsProcessed.Inc()
		metrics.ProcessingDuration.Observe(time.Since(start).Seconds())
	}
}
