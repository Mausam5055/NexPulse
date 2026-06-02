package detector

import (
	"context"
	"sync/atomic"
	"time"

	"nexpulse/anomaly/alert"
)

var (
	currentSecondEvents int64
	currentEMA          float64
	alpha               float64 = 0.2 // Smoothing factor
	initialized         bool
)

func RecordEvent() {
	atomic.AddInt64(&currentSecondEvents, 1)
}

func StartEMAEvaluator() {
	ticker := time.NewTicker(1 * time.Second)
	go func() {
		for range ticker.C {
			// Get the events for the last second and reset the counter
			rps := atomic.SwapInt64(&currentSecondEvents, 0)

			if !initialized {
				currentEMA = float64(rps)
				if rps > 0 {
					initialized = true
				}
				continue
			}

			// Calculate the new Exponential Moving Average
			currentEMA = alpha*float64(rps) + (1-alpha)*currentEMA

			// If current RPS is > 2.0x the historical EMA (and at least > 100 rps to avoid noise)
			if float64(rps) > currentEMA*2.0 && rps > 100 {
				alert.PublishSpikeAlert(context.Background(), int(rps), currentEMA)
			}
		}
	}()
}
