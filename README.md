# QueueMind

QueueMind is a distributed task queue demo built with a FastAPI backend and a real-time React dashboard. It simulates a multi-agent processing pipeline where workloads are planned, scheduled, assigned to workers, executed, validated, retried when necessary, and streamed live to the UI via WebSockets.

This project demonstrates queue orchestration, worker health monitoring, retry mechanisms, live metrics, and task inspection—without requiring a full production infrastructure.

---

## Features

* Multi-agent orchestration: planner, scheduler, load balancer, workers, critic, retry agent, and monitor
* Real-time dashboard with task counts, pipeline progress, worker health, logs, and metrics
* Workload submission API with a built-in demo workload
* In-memory development mode for fast local execution
* Kafka-based worker mode using Docker Compose
* Automatic retry handling with configurable failure rates and retry limits
* Task detail view for inspecting results and errors

---

## Tech Stack

| Layer      | Technology                                    |
| ---------- | --------------------------------------------- |
| Backend    | Python, FastAPI, Pydantic, Uvicorn            |
| Frontend   | React, Vite, Zustand, Recharts, Lucide React  |
| Realtime   | WebSocket                                     |
| Queue      | In-memory queue (dev), Kafka (container mode) |
| Containers | Docker Compose                                |

---

## Prerequisites

* Python 3.12 or newer
* Node.js 20 or newer
* npm
* Docker Desktop (only for Kafka mode)

---

## Project Structure

```text
QueueMind/
  backend/
    agents/          # Core orchestration agents
    models/          # Pydantic schemas
    queue/           # Queue implementations (in-memory + Kafka)
    scripts/         # Demo + healthcheck scripts
    store/           # Task state + metrics
    tests/           # Backend tests
    websocket/       # WebSocket manager
    config.py        # Environment configuration
    main.py          # FastAPI app entrypoint

  frontend/
    src/components/  # UI components
    src/hooks/       # WebSocket hooks
    src/store/       # Zustand state

  docs/
    architecture.md

  docker-compose.yml
  README.md
```

---

## Quick Start

### 1. Start Backend

#### Windows (PowerShell)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

#### macOS/Linux

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Backend runs at:

```
http://localhost:8000
```

---

### 2. Start Frontend

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:

```
http://localhost:5173
```

---

### 3. Run Demo Workload

#### Using UI

* Open `http://localhost:5173`
* Click **Run Demo**

#### Using API

**PowerShell**

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/demo
```

**macOS/Linux**

```bash
curl -X POST http://localhost:8000/api/demo
```

---

## Dashboard Usage

1. Open `http://localhost:5173`
2. Click **Run Demo** or submit a custom workload
3. Monitor task lifecycle:

   * queued → running → completed → validated → failed → retry
4. Open **Task Queue**
5. Click a task to inspect its result payload

---

## API Reference

| Method | Endpoint               | Description              |
| ------ | ---------------------- | ------------------------ |
| POST   | `/api/workloads`       | Submit a custom workload |
| POST   | `/api/demo`            | Run demo workload        |
| GET    | `/api/tasks`           | List all tasks           |
| GET    | `/api/tasks/{task_id}` | Get task details         |
| GET    | `/api/workers`         | Worker status            |
| GET    | `/api/metrics`         | Metrics summary          |
| GET    | `/api/summary`         | System overview          |
| GET    | `/api/logs`            | Event logs               |
| GET    | `/api/failures`        | Failure logs             |
| WS     | `/ws`                  | Live event stream        |

---

## Example Workload

```bash
curl -X POST http://localhost:8000/api/workloads \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Log Processing Pipeline",
    "description": "Process logs and generate reports",
    "total_chunks": 5,
    "priority": 7
  }'
```

---

## Configuration

The backend reads configuration from environment variables.

| Variable                | Default        | Description                         |
| ----------------------- | -------------- | ----------------------------------- |
| QUEUEMIND_MODE          | dev            | dev = in-memory queue, prod = Kafka |
| KAFKA_BOOTSTRAP_SERVERS | localhost:9092 | Kafka broker                        |
| NUM_CPU_WORKERS         | 2              | CPU workers                         |
| NUM_IO_WORKERS          | 2              | IO workers                          |
| WORKER_FAILURE_RATE     | 0.15           | Failure probability                 |
| MAX_RETRIES             | 3              | Retry limit                         |
| RETRY_BASE_DELAY        | 2.0            | Base delay (seconds)                |
| RETRY_MAX_DELAY         | 60.0           | Max delay                           |
| HOST                    | 0.0.0.0        | Backend host                        |
| PORT                    | 8000           | Backend port                        |

---

## Docker Setup

Run the full Kafka-based system:

```bash
docker compose up --build
```

This starts:

* Kafka (KRaft mode)
* FastAPI orchestrator
* CPU worker containers
* IO worker containers

⚠️ The frontend is not included in Docker Compose. Run it separately.

---

## Testing

### Backend Tests

```bash
cd backend
pip install pytest
pytest tests/ -v
```

### Frontend Build

```bash
cd frontend
npm run build
```

### Health Check

```bash
python backend/scripts/healthcheck.py
```

---

## Notes

* In-memory mode resets all data on restart
* The root endpoint `/` is not defined
* Default endpoints:

  * API → `http://localhost:8000`
  * WebSocket → `ws://localhost:8000/ws`

---

## 👨‍💻 Team

* **Madhavi** – Backend & UI Development
* **Suhas Kumar** – Frontend & System Design

---

