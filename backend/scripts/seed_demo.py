#!/usr/bin/env python3
"""
seed_demo.py — Fire a demo workload at the running API.

Usage:
    python backend/scripts/seed_demo.py
    python backend/scripts/seed_demo.py --chunks 5 --priority 8
"""
import argparse
import json
import urllib.request

API = "http://localhost:8000"


def post(path: str, body: dict = None) -> dict:
    data = json.dumps(body or {}).encode()
    req  = urllib.request.Request(
        f"{API}{path}", data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def get(path: str) -> dict:
    with urllib.request.urlopen(f"{API}{path}") as r:
        return json.loads(r.read())


def main():
    parser = argparse.ArgumentParser(description="QueueMind demo seeder")
    parser.add_argument("--demo",     action="store_true", help="Run preset demo workload")
    parser.add_argument("--chunks",   type=int, default=3, help="Number of log chunks")
    parser.add_argument("--priority", type=int, default=5, help="Task priority (1-10)")
    args = parser.parse_args()

    print("🔍 Checking API health...")
    try:
        metrics = get("/api/metrics")
        print(f"✅ API is up — {metrics['summary']['tasks_total']} tasks in store")
    except Exception as e:
        print(f"❌ Cannot reach API at {API}: {e}")
        print("   Make sure the backend is running: python main.py")
        return

    if args.demo:
        print("\n🚀 Firing pre-built demo workload...")
        result = post("/api/demo")
    else:
        print(f"\n🚀 Submitting workload ({args.chunks} chunks, priority {args.priority})...")
        result = post("/api/workloads", {
            "name": "Log Processing Pipeline",
            "description": "Process system logs seed job",
            "total_chunks": args.chunks,
            "priority": args.priority,
        })

    print(f"✅ Accepted — {len(result.get('plan', {}).get('tasks', []))} tasks created")
    print(f"\n👉 Open http://localhost:5173 to watch the dashboard")


if __name__ == "__main__":
    main()
