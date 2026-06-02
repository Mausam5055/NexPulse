package metrics

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	EventsIngested = promauto.NewCounter(prometheus.CounterOpts{
		Name: "gateway_events_ingested_total",
		Help: "Total events successfully accepted and published to Kafka",
	})

	EventsRejected = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "gateway_events_rejected_total",
		Help: "Total events rejected",
	}, []string{"reason"})

	RateLimitHits = promauto.NewCounter(prometheus.CounterOpts{
		Name: "gateway_rate_limit_hits_total",
		Help: "Total requests blocked by rate limiter",
	})

	ActiveConnections = promauto.NewGauge(prometheus.GaugeOpts{
		Name: "gateway_active_connections",
		Help: "Current active incoming requests",
	})

	RequestDuration = promauto.NewHistogram(prometheus.HistogramOpts{
		Name:    "gateway_request_duration_seconds",
		Help:    "Histogram of request latencies",
		Buckets: prometheus.DefBuckets,
	})

	KafkaProduceDuration = promauto.NewHistogram(prometheus.HistogramOpts{
		Name:    "gateway_kafka_produce_duration_seconds",
		Help:    "Histogram of Kafka publish latencies",
		Buckets: []float64{0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1},
	})
)

func init() {
	EventsIngested.Add(0)
	EventsRejected.WithLabelValues("rate_limit").Add(0)
	RateLimitHits.Add(0)
	ActiveConnections.Set(0)
}
