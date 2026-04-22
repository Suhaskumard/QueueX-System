package analytics

import (
	"context"
	"encoding/json"
	"log/slog"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	amqp "github.com/rabbitmq/amqp091-go"
	"github.com/user/linkloom-plus/internal/queue"
)

type Worker struct {
	DB *pgxpool.Pool
	MQ *queue.RabbitMQ
}

func (w *Worker) Start(ctx context.Context) error {
	msgs, err := w.MQ.ConsumeClickEvents()
	if err != nil {
		return err
	}

	slog.Info("Worker started consuming click events")

	for {
		select {
		case <-ctx.Done():
			return nil
		case d, ok := <-msgs:
			if !ok {
				return nil
			}

			w.processMessage(ctx, d)
		}
	}
}

func (w *Worker) processMessage(ctx context.Context, d amqp.Delivery) {
	var event queue.ClickEvent
	if err := json.Unmarshal(d.Body, &event); err != nil {
		slog.Error("Failed to decode click event", "error", err)
		d.Nack(false, false) // discard malformed messages
		return
	}

	// 1. Enrichment (Mock Geo-IP)
	country := "Unknown"
	if event.IP != "" && event.IP != "127.0.0.1" && event.IP != "::1" {
		// Mock implementation - in prod, query maxmind or ipstack
		country = "US" 
	}

	// 2. Parse UserAgent (Mock Implementation)
	device := "Desktop"
	if event.UserAgent == "Mobile" {
		device = "Mobile"
	}

	// 3. Persist to PostgreSQL click_events (partitioned table)
	query := `
		INSERT INTO click_events (short_code, ip_address, country, user_agent, device_type, clicked_at)
		VALUES ($1, $2, $3, $4, $5, $6)
	`
	clickedAt := time.Unix(event.Timestamp, 0)
	
	_, err := w.DB.Exec(ctx, query, event.ShortCode, event.IP, country, event.UserAgent, device, clickedAt)
	if err != nil {
		slog.Error("Failed to insert click event to DB", "error", err, "event", event)
		// requeue on db error for retry
		d.Nack(false, true)
		return
	}

	slog.Info("Processed click event successfully", "short_code", event.ShortCode)
	d.Ack(false)
}
