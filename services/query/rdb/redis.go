package rdb

import (
	"context"
	"log"

	"github.com/redis/go-redis/v9"
	"nexpulse/query/ws"
	"nexpulse/query/metrics"
)

var Client *redis.Client

func InitRedis(addr string) {
	Client = redis.NewClient(&redis.Options{
		Addr: addr,
	})

	if err := Client.Ping(context.Background()).Err(); err != nil {
		log.Fatalf("❌ Failed to connect to Redis: %v", err)
	}
	log.Println("✅ Query service connected to Redis:", addr)
}

func SubscribeToUpdates(hub *ws.Hub) {
	ctx := context.Background()
	pubsub := Client.Subscribe(ctx, "dashboard_updates")

	_, err := pubsub.Receive(ctx)
	if err != nil {
		log.Fatalf("❌ Failed to subscribe to Redis: %v", err)
	}

	ch := pubsub.Channel()
	go func() {
		for msg := range ch {
			hub.Broadcast([]byte(msg.Payload))
		}
	}()
	log.Println("📡 Subscribed to Redis channel: dashboard_updates")
}

func GetLeaderboard(ctx context.Context, key string, count int64) ([]redis.Z, error) {
	res, err := Client.ZRevRangeWithScores(ctx, key, 0, count-1).Result()
	if err != nil {
		metrics.RedisErrors.Inc()
		return nil, err
	}
	return res, nil
}
