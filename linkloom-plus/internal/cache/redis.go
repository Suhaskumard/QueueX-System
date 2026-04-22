package cache

import (
	"context"
	"log/slog"

	"github.com/redis/go-redis/v9"
)

func NewRedisClient(ctx context.Context, url string) (*redis.Client, error) {
	opts, err := redis.ParseURL(url)
	if err != nil {
		return nil, err
	}

	client := redis.NewClient(opts)
	if err := client.Ping(ctx).Err(); err != nil {
		return nil, err
	}

	slog.Info("Connected to Redis successfully")
	return client, nil
}
