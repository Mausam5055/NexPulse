package handlers

import (
	"bytes"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"nexpulse/gateway/kafka"
	"nexpulse/gateway/metrics"
	"nexpulse/gateway/ratelimit"
)

var anomalySvcURL string

func init() {
	anomalySvcURL = os.Getenv("ANOMALY_SVC_URL")
	if anomalySvcURL == "" {
		anomalySvcURL = "http://127.0.0.1:8083/record"
	}
}

func HandleIngest(c *gin.Context) {
	metrics.ActiveConnections.Inc()
	defer metrics.ActiveConnections.Dec()

	start := time.Now()
	defer func() {
		metrics.RequestDuration.Observe(time.Since(start).Seconds())
	}()

	var event map[string]any
	if err := c.ShouldBindJSON(&event); err != nil {
		metrics.EventsRejected.WithLabelValues("bad_request").Inc()
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid JSON"})
		return
	}

	userID, ok := event["user_id"].(string)
	if !ok || userID == "" {
		metrics.EventsRejected.WithLabelValues("missing_user_id").Inc()
		c.JSON(http.StatusBadRequest, gin.H{"error": "user_id is required"})
		return
	}

	// Ping the anomaly detector to track global requests/sec
	go func() {
		client := &http.Client{Timeout: 1 * time.Second}
		_, _ = client.Post(anomalySvcURL, "application/json", bytes.NewBuffer([]byte{}))
	}()

	// Apply Rate Limiting (e.g., 50 requests per second per user)
	allowed, err := ratelimit.AllowRequest(c.Request.Context(), userID, 50, time.Second)
	if err != nil {
		log.Printf("⚠️ Rate limiter error: %v", err)
		// Fail open or closed? Let's fail open for now.
	} else if !allowed {
		metrics.RateLimitHits.Inc()
		metrics.EventsRejected.WithLabelValues("rate_limit").Inc()
		c.JSON(http.StatusTooManyRequests, gin.H{"error": "Rate limit exceeded"})
		return
	}

	// Publish to Kafka
	if err := kafka.ProduceEvent(event); err != nil {
		log.Printf("❌ Failed to publish to Kafka: %v", err)
		metrics.EventsRejected.WithLabelValues("kafka_error").Inc()
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	metrics.EventsIngested.Inc()
	c.JSON(http.StatusAccepted, gin.H{"status": "accepted"})
}
