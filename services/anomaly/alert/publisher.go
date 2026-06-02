package alert

import (
	"context"
	"fmt"
	"log"

	"github.com/redis/go-redis/v9"
)

var client *redis.Client

func InitRedis(addr string) {
	client = redis.NewClient(&redis.Options{
		Addr: addr,
	})

	if err := client.Ping(context.Background()).Err(); err != nil {
		log.Fatalf("❌ Failed to connect to Redis: %v", err)
	}
	log.Println("✅ Anomaly Detector connected to Redis:", addr)
}

func PublishSpikeAlert(ctx context.Context, currentRPS int, ema float64) {
	// Log it prominently
	log.Printf("🚨 ANOMALY DETECTED: Traffic spiked to %d req/sec (Average: %.2f)", currentRPS, ema)

	// Publish to the dashboard_updates channel so the UI can show a notification
	payload := fmt.Sprintf(`{"type": "anomaly", "message": "Traffic spiked to %d req/sec", "rps": %d, "ema": %.2f}`, currentRPS, currentRPS, ema)
	
	if err := client.Publish(ctx, "dashboard_updates", payload).Err(); err != nil {
		log.Printf("⚠️ Failed to publish anomaly alert: %v", err)
	}
}
