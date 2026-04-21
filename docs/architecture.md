# QueueMind Architecture

## System Overview

```
┌────────────────────────────────────────────────────────────────┐
│                    React Dashboard                             │
│   Dashboard │ Tasks │ Workers │ Logs │ Retries                │
└──────────────────────┬─────────────────────────────────────────┘
                       │  WebSocket /ws  (live events every 1s)
┌──────────────────────▼─────────────────────────────────────────┐
│              FastAPI Orchestrator  :8000                       │
│                                                                │
│  POST /api/workloads ──► PlannerAgent                         │
│                              │ creates subtasks               │
│                              ▼                                 │
│                       SchedulerAgent                           │
│                     (dependency ordering)                      │
│                              │ routes by task_type            │
│                    ┌─────────┴──────────┐                     │
│                    ▼                    ▼                      │
│             task_queue_cpu      task_queue_io                  │
│                    │                    │                      │
│            ┌───────┘                    └───────┐             │
│            ▼                                    ▼             │
│     LoadBalancerAgent ──────────────────► LoadBalancerAgent   │
│     worker_cpu_1  worker_cpu_2           worker_io_1  _io_2   │
│            │                                    │             │
│            └──────────┬─────────────────────────┘             │
│                       │  WorkerExecutionAgent                  │
│                       │  (15% failure injection)               │
│                       ▼                                        │
│                task_results / task_failures                    │
│                    │          │                                 │
│                    ▼          ▼                                 │
│             CriticAgent    RetryAgent                          │
│           (score 0-10)   (exponential backoff)                 │
│                    │          │                                 │
│                    └────┬─────┘                                │
│                         ▼                                      │
│                   MonitorAgent                                 │
│             (metrics every 1s → WebSocket)                    │
└────────────────────────────────────────────────────────────────┘
```

## Task Lifecycle

```
CREATED → PARTITIONED → QUEUED → ASSIGNED → RUNNING → COMPLETED → VALIDATED → STORED
                                                   ↓
                                                FAILED → (RetryAgent) → QUEUED (retry)
                                                       → FAILED (permanent, max retries)
```

## Queue Modes

| Mode | Queue | How to activate |
|------|-------|----------------|
| Dev  | `asyncio.Queue` (in-memory) | `QUEUEMIND_MODE=dev` (default) |
| Prod | Apache Kafka KRaft | `QUEUEMIND_MODE=prod` |

## Log Processing Pipeline (per chunk)

```
extract_ips (IO)
└── deduplicate (CPU)
    └── classify (CPU)
        ├── blacklist_check (IO)
        └── geolocation (IO)
            └── pattern_detect (CPU)
                └── generate_report (CPU+IO)

All chunks → aggregate_final (CPU)
```
