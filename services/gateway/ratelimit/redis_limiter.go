package ratelimit

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/redis/go-redis/v9"
)

var client *redis.Client

func InitRedis(addr string) {
	client = redis.NewClient(&redis.Options{
		Addr: addr,
		PoolSize: 100, // Handle high concurrency
	})

	if err := client.Ping(context.Background()).Err(); err != nil {
		log.Fatalf("❌ Failed to connect to Redis: %v", err)
	}
	log.Println("✅ Redis Rate Limiter connected to:", addr)
}

// AllowRequest implements a sliding window rate limit using Redis Sorted Sets
func AllowRequest(ctx context.Context, userID string, limit int, window time.Duration) (bool, error) {
	key := "rl:user:" + userID
	now := time.Now().UnixNano()
	windowStart := now - window.Nanoseconds()

	// Use a pipeline for atomic execution (minimizes network roundtrips)
	pipe := client.Pipeline()

	// 1. Remove old events outside the sliding window
	pipe.ZRemRangeByScore(ctx, key, "0", fmt.Sprintf("%d", windowStart))

	// 2. Add current request
	pipe.ZAdd(ctx, key, redis.Z{
		Score:  float64(now),
		Member: now, 
	})

	// 3. Count current valid requests
	countCmd := pipe.ZCard(ctx, key)

	// 4. Set key expiration to window size to clean up idle users
	pipe.Expire(ctx, key, window)

	_, err := pipe.Exec(ctx)
	if err != nil {
		return false, err
	}

	count := countCmd.Val()

	// count includes the one we just added. 
	// So if count > limit, we are over the limit.
	return count <= int64(limit), nil
}
