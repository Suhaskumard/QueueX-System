package queue

import (
	"context"
	"encoding/json"
	"log/slog"

	amqp "github.com/rabbitmq/amqp091-go"
)

const (
	ClickEventsQueue = "click_events"
)

type ClickEvent struct {
	ShortCode string `json:"short_code"`
	IP        string `json:"ip"`
	UserAgent string `json:"user_agent"`
	Timestamp int64  `json:"timestamp"`
}

type RabbitMQ struct {
	conn    *amqp.Connection
	channel *amqp.Channel
}

func NewRabbitMQ(url string) (*RabbitMQ, error) {
	conn, err := amqp.Dial(url)
	if err != nil {
		return nil, err
	}

	ch, err := conn.Channel()
	if err != nil {
		return nil, err
	}

	_, err = ch.QueueDeclare(
		ClickEventsQueue, // name
		true,             // durable
		false,            // delete when unused
		false,            // exclusive
		false,            // no-wait
		nil,              // arguments
	)
	if err != nil {
		return nil, err
	}

	slog.Info("Connected to RabbitMQ successfully")
	return &RabbitMQ{conn: conn, channel: ch}, nil
}

func (r *RabbitMQ) PublishClickEvent(ctx context.Context, event ClickEvent) error {
	body, err := json.Marshal(event)
	if err != nil {
		return err
	}

	return r.channel.PublishWithContext(ctx,
		"",               // exchange
		ClickEventsQueue, // routing key
		false,            // mandatory
		false,            // immediate
		amqp.Publishing{
			ContentType:  "application/json",
			DeliveryMode: amqp.Persistent,
			Body:         body,
		})
}

func (r *RabbitMQ) ConsumeClickEvents() (<-chan amqp.Delivery, error) {
	return r.channel.Consume(
		ClickEventsQueue, // queue
		"",               // consumer
		false,            // auto-ack (we want manual ack for reliability)
		false,            // exclusive
		false,            // no-local
		false,            // no-wait
		nil,              // args
	)
}

func (r *RabbitMQ) Close() {
	if r.channel != nil {
		r.channel.Close()
	}
	if r.conn != nil {
		r.conn.Close()
	}
}
