package api

import (
	"context"
	"encoding/json"
	"log/slog"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/redis/go-redis/v9"
	"github.com/user/linkloom-plus/internal/queue"
	"github.com/user/linkloom-plus/internal/shortener"
)

type Server struct {
	DB    *pgxpool.Pool
	Redis *redis.Client
	MQ    *queue.RabbitMQ
}

type ShortenRequest struct {
	URL string `json:"url"`
}

type ShortenResponse struct {
	ShortCode string `json:"short_code"`
	ShortURL  string `json:"short_url"`
}

func (s *Server) MountRoutes(r chi.Router) {
	r.Post("/api/v1/links", s.handleCreateLink)
	r.Get("/{code}", s.handleRedirect)
}

func (s *Server) handleCreateLink(w http.ResponseWriter, r *http.Request) {
	var req ShortenRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	if !shortener.ValidateURL(req.URL) {
		http.Error(w, "Invalid URL format", http.StatusBadRequest)
		return
	}

	code, err := shortener.GenerateShortCode(7)
	if err != nil {
		slog.Error("Failed to generate short code", "error", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	// Persist to DB
	_, err = s.DB.Exec(r.Context(), "INSERT INTO links (short_code, original_url, created_at) VALUES ($1, $2, $3)", code, req.URL, time.Now())
	if err != nil {
		slog.Error("Database insertion failed", "error", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	// Optionally prepopulate cache
	s.Redis.Set(r.Context(), code, req.URL, 24*time.Hour)

	resp := ShortenResponse{
		ShortCode: code,
		ShortURL:  "http://" + r.Host + "/" + code,
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(resp)
}

func (s *Server) handleRedirect(w http.ResponseWriter, r *http.Request) {
	code := chi.URLParam(r, "code")

	// 1. Try Redis Cache (Cache-Aside Pattern)
	longURL, err := s.Redis.Get(r.Context(), code).Result()
	if err == redis.Nil {
		// Cache miss
		err = s.DB.QueryRow(r.Context(), "SELECT original_url FROM links WHERE short_code = $1", code).Scan(&longURL)
		if err != nil {
			http.NotFound(w, r)
			return
		}
		// Populate cache
		s.Redis.Set(r.Context(), code, longURL, 24*time.Hour)
	} else if err != nil {
		slog.Error("Redis error", "error", err)
	}

	// 2. Publish Click Event to Message Queue asynchronously
	go func(c string, ip string, ua string) {
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		defer cancel()

		event := queue.ClickEvent{
			ShortCode: c,
			IP:        ip, // in prod, parse X-Forwarded-For
			UserAgent: ua,
			Timestamp: time.Now().Unix(),
		}
		if err := s.MQ.PublishClickEvent(ctx, event); err != nil {
			slog.Error("Failed to publish click event", "error", err)
		}
	}(code, r.RemoteAddr, r.UserAgent())

	// 3. Fast Redirect
	w.Header().Set("Cache-Control", "public, max-age=900") // 15 mins client-side cache
	http.Redirect(w, r, longURL, http.StatusFound)
}
