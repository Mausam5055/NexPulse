package metrics

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	EventsProcessed = promauto.NewCounter(prometheus.CounterOpts{
		Name: "aggregator_events_processed_total",
		Help: "Events successfully aggregated",
	})

	KafkaMessagesConsumed = promauto.NewCounter(prometheus.CounterOpts{
		Name: "aggregator_kafka_messages_consumed_total",
		Help: "Kafka messages consumed",
	})

	KafkaConsumerLag = promauto.NewGaugeVec(prometheus.GaugeOpts{
		Name: "aggregator_kafka_consumer_lag",
		Help: "Current consumer group lag by partition",
	}, []string{"partition"})

	RedisErrors = promauto.NewCounter(prometheus.CounterOpts{
		Name: "aggregator_redis_errors_total",
		Help: "Errors executing Redis pipelines",
	})

	ProcessingDuration = promauto.NewHistogram(prometheus.HistogramOpts{
		Name:    "aggregator_processing_duration_seconds",
		Help:    "Time taken to process a batch of events",
		Buckets: []float64{0.005, 0.01, 0.05, 0.1, 0.25, 0.5},
	})
)
