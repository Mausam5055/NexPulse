package main

import (
	"log"
	"net/http"
	"os"

	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"nexpulse/query/rdb"
	"nexpulse/query/ws"
)

func main() {
	log.Println("┌─────────────────────────────────────────┐")
	log.Println("│  📡 NexPulse — Query & WebSocket        │")
	log.Println("│  Phase 2 | Port :8081                   │")
	log.Println("└─────────────────────────────────────────┘")

	redisAddr := os.Getenv("REDIS_ADDR")
	if redisAddr == "" {
		redisAddr = "127.0.0.1:6379"
	}

	// Init Redis
	rdb.InitRedis(redisAddr)

	// Init WebSocket Hub
	hub := ws.NewHub()
	go hub.Run()

	// Subscribe to Redis pub/sub
	rdb.SubscribeToUpdates(hub)

	// Setup Gin router
	gin.SetMode(gin.ReleaseMode)
	router := gin.New()
	router.Use(gin.Recovery())

	// Routes
	router.GET("/ws", hub.ServeWS)
	
	router.GET("/leaderboard", func(c *gin.Context) {
		res, err := rdb.GetLeaderboard(c.Request.Context(), "leaderboard:users", 10)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		c.JSON(http.StatusOK, gin.H{"leaderboard": res})
	})

	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":  "healthy",
			"service": "query",
			"phase":   "2",
		})
	})

	router.GET("/metrics", gin.WrapH(promhttp.Handler()))

	log.Println("✅ Query service listening on :8081")
	if err := router.Run(":8081"); err != nil {
		log.Fatalf("❌ Query service failed: %v", err)
	}
}
