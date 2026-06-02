package main

import (
	"log"
	"net/http"
	"os"

	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"nexpulse/gateway/handlers"
	"nexpulse/gateway/kafka"
	"nexpulse/gateway/ratelimit"
)

func main() {
	log.Println("┌─────────────────────────────────────────┐")
	log.Println("│  ⚡ NexPulse — API Gateway              │")
	log.Println("│  Phase 2 | Port :8080                   │")
	log.Println("└─────────────────────────────────────────┘")

	// Get environment variables or default to local infrastructure
	redisAddr := os.Getenv("REDIS_ADDR")
	if redisAddr == "" {
		redisAddr = "127.0.0.1:6379"
	}
	kafkaBroker := os.Getenv("KAFKA_BROKER")
	if kafkaBroker == "" {
		kafkaBroker = "127.0.0.1:9092"
	}

	// Initialize dependencies
	ratelimit.InitRedis(redisAddr)
	kafka.InitProducer([]string{kafkaBroker}, "raw-events")
	defer kafka.Close()

	// Setup Gin router
	gin.SetMode(gin.ReleaseMode)
	router := gin.New()
	
	// Add a simple recovery middleware
	router.Use(gin.Recovery())

	// Routes
	router.POST("/ingest", handlers.HandleIngest)

	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":  "healthy",
			"service": "gateway",
			"phase":   "2",
		})
	})

	router.GET("/metrics", gin.WrapH(promhttp.Handler()))

	log.Println("✅ Gateway listening on :8080")
	if err := router.Run(":8080"); err != nil {
		log.Fatalf("❌ Gateway failed: %v", err)
	}
}
