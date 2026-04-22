package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/user/linkloom-plus/internal/analytics"
	"github.com/user/linkloom-plus/internal/config"
	"github.com/user/linkloom-plus/internal/db"
	"github.com/user/linkloom-plus/internal/queue"
)

func main() {
	cfg := config.LoadConfig()

	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	slog.SetDefault(logger)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Initialize Postgres
	dsn := cfg.DatabaseURL
	dbPool, err := db.NewPostgresPool(ctx, dsn)
	if err != nil {
		slog.Error("Failed to connect to database", "error", err)
		os.Exit(1)
	}
	defer dbPool.Close()

	// Initialize RabbitMQ
	mq, err := queue.NewRabbitMQ(cfg.RabbitMQURL)
	if err != nil {
		slog.Error("Failed to connect to RabbitMQ", "error", err)
		os.Exit(1)
	}
	defer mq.Close()

	worker := &analytics.Worker{
		DB: dbPool,
		MQ: mq,
	}

	go func() {
		if err := worker.Start(ctx); err != nil {
			slog.Error("Worker failed", "error", err)
		}
	}()

	// Graceful Shutdown
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
	<-stop

	slog.Info("Shutting down worker gracefully...")
	// Cancel the context to stop the worker loop
	cancel()

	time.Sleep(1 * time.Second) // wait for clean shutdown
	slog.Info("Worker exited properly")
}
