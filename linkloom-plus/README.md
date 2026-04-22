# LinkLoom+

LinkLoom+ is a high-performance, infrastructure-heavy backend system designed to demonstrate expertise in system design, scalability, and resilience. This project features a Go-based API and an asynchronous event processing pipeline, focusing on robust backend plumbing.

## Architecture

The system utilizes a microservices-oriented approach, orchestrated via Docker Compose:

* **API Service (`api`)**: A Go-based service handling incoming requests.
* **Worker Service (`worker`)**: A Go-based worker process that consumes background tasks and processes events asynchronously.
* **Traefik (`traefik`)**: Edge router and reverse proxy that handles incoming traffic and dynamically routes it to the API.
* **PostgreSQL (`db`)**: The primary relational database for persistent storage.
* **Redis (`redis`)**: In-memory caching layer to speed up high-frequency reads and reduce database load.
* **RabbitMQ (`rabbitmq`)**: Message broker that decoupling the API and Worker, handling asynchronous event queues.

## Prerequisites

* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/install/)

## Getting Started

The entire infrastructure is containerized and can be launched with a single command.

1. **Navigate to the project directory:**
   ```bash
   cd linkloom-plus
   ```

2. **Start the infrastructure:**
   ```bash
   docker-compose up -d --build
   ```

   This command will build the Go applications (`Dockerfile.api` and `Dockerfile.worker`) and start all necessary services in the background. The `depends_on` configurations with healthchecks ensure services start in the correct order (e.g., API waits for DB, Redis, and RabbitMQ to be healthy).

3. **Verify the services:**
   You can check the status of the containers using:
   ```bash
   docker-compose ps
   ```

## Exposed Services & Ports

* **Main Application Traffic:** `http://localhost:80` (Routed by Traefik)
* **Traefik Dashboard:** `http://localhost:8080` (Monitor active routes and services)
* **RabbitMQ Management UI:** `http://localhost:15672` (Credentials: `guest` / `guest`)
* **PostgreSQL:** `localhost:5432` (Credentials: `postgres` / `password`, DB: `linkloom`)
* **Redis:** `localhost:6379`

## Project Structure

* `cmd/api/` - Entrypoint for the main API service.
* `cmd/worker/` - Entrypoint for the background worker service.
* `internal/` - Core domain logic (`analytics`, `api`, `cache`, `db`, `queue`, `shortener`).
* `db/migrations/` - SQL schema definitions and migrations initialized on database startup.
* `traefik/` - Dynamic configuration for the Traefik router.
* `docker-compose.yml` - Defines the multi-container infrastructure and networking.

## Managing the System

**Viewing Logs:**
To view real-time logs for all services:
```bash
docker-compose logs -f
```
To view logs for a specific service (e.g., the worker):
```bash
docker-compose logs -f worker
```

**Shutting Down:**
To gracefully stop the system:
```bash
docker-compose down
```

To stop the system and completely wipe the persistent database data (use with caution):
```bash
docker-compose down -v
```
