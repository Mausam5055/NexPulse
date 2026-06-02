package metrics

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	ActiveWebSockets = promauto.NewGauge(prometheus.GaugeOpts{
		Name: "query_websocket_connections_active",
		Help: "Number of currently active WebSocket clients",
	})

	MessagesBroadcasted = promauto.NewCounter(prometheus.CounterOpts{
		Name: "query_messages_broadcasted_total",
		Help: "Total dashboard updates pushed to clients",
	})

	RedisErrors = promauto.NewCounter(prometheus.CounterOpts{
		Name: "query_redis_errors_total",
		Help: "Errors reading from Redis",
	})
)

func init() {
	ActiveWebSockets.Set(0)
	MessagesBroadcasted.Add(0)
	RedisErrors.Add(0)
}
