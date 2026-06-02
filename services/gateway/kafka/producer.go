package kafka

import (
	"context"
	"encoding/json"
	"log"
	"time"

	"github.com/segmentio/kafka-go"
	"nexpulse/gateway/metrics"
)

var writer *kafka.Writer

func InitProducer(brokers []string, topic string) {
	writer = &kafka.Writer{
		Addr:                   kafka.TCP(brokers...),
		Topic:                  topic,
		Balancer:               &kafka.Hash{},
		BatchSize:              1000,
		BatchTimeout:           10 * time.Millisecond, // Send often
		Async:                  true, // Non-blocking!
		AllowAutoTopicCreation: true,
	}
	log.Println("✅ Kafka Producer initialized for topic:", topic)
}

func ProduceEvent(event map[string]any) error {
	start := time.Now()
	
	bytes, err := json.Marshal(event)
	if err != nil {
		return err
	}

	userID := event["user_id"].(string)

	err = writer.WriteMessages(context.Background(),
		kafka.Message{
			Key:   []byte(userID), // Partition by user_id
			Value: bytes,
		},
	)

	metrics.KafkaProduceDuration.Observe(time.Since(start).Seconds())
	return err
}

func Close() {
	if writer != nil {
		writer.Close()
	}
}
