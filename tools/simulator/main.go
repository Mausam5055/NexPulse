package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"sync"
	"time"
)

var (
	rate    int
	workers int
	gateway string
)

func init() {
	flag.IntVar(&rate, "rate", 100, "Events per second")
	flag.IntVar(&workers, "workers", 10, "Number of concurrent workers")
	flag.StringVar(&gateway, "gateway", "http://localhost:8080/ingest", "Gateway URL")
}

func main() {
	flag.Parse()

	log.Printf("🚀 Starting Simulator: %d events/sec with %d workers\n", rate, workers)

	var wg sync.WaitGroup
	eventsPerWorker := rate / workers

	// If rate is less than workers, cap workers to rate.
	if eventsPerWorker < 1 {
		workers = rate
		eventsPerWorker = 1
	}

	for i := 0; i < workers; i++ {
		wg.Add(1)
		go worker(&wg, eventsPerWorker)
	}

	wg.Wait()
}

func worker(wg *sync.WaitGroup, rps int) {
	defer wg.Done()

	ticker := time.NewTicker(time.Second / time.Duration(rps))
	defer ticker.Stop()

	client := &http.Client{Timeout: 5 * time.Second}

	for range ticker.C {
		event := map[string]interface{}{
			"user_id":    fmt.Sprintf("user_%d", rand.Intn(10000)),
			"event_type": randomEventType(),
			"timestamp":  time.Now().UnixMilli(),
		}

		payload, _ := json.Marshal(event)
		req, _ := http.NewRequest("POST", gateway, bytes.NewBuffer(payload))
		req.Header.Set("Content-Type", "application/json")

		resp, err := client.Do(req)
		if err != nil {
			// Don't spam logs on high rates
			if rand.Float32() < 0.05 {
				log.Printf("⚠️ Failed to send event (sampled): %v", err)
			}
			continue
		}
		resp.Body.Close()
	}
}

func randomEventType() string {
	types := []string{"click", "view", "purchase", "login"}
	return types[rand.Intn(len(types))]
}
