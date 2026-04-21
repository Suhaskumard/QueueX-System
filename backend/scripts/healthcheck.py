#!/usr/bin/env python3
"""
healthcheck.py — Check if all QueueMind services are reachable.

Usage:
    python backend/scripts/healthcheck.py
"""
import json
import sys
import urllib.request

CHECKS = [
    ("Backend API",    "http://localhost:8000/api/metrics"),
    ("Tasks endpoint", "http://localhost:8000/api/tasks"),
    ("Workers",        "http://localhost:8000/api/workers"),
    ("Logs",           "http://localhost:8000/api/logs?limit=1"),
]


def check(label: str, url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            data = json.loads(r.read())
            print(f"  ✅  {label:<22} → {url}")
            return True
    except Exception as e:
        print(f"  ❌  {label:<22} → {e}")
        return False


def main():
    print("\n⚙  QueueMind Health Check")
    print("─" * 50)
    results = [check(label, url) for label, url in CHECKS]
    print("─" * 50)
    ok = sum(results)
    total = len(results)
    print(f"\n{'✅ All systems operational' if ok == total else f'⚠  {ok}/{total} checks passed'}")

    if ok == total:
        print("\n🎯 Fire a demo:  python backend/scripts/seed_demo.py --demo")
        print("🌐 Dashboard:    http://localhost:5173\n")
    else:
        print("\n💡 Start backend: cd backend && python main.py")
        print("💡 Start frontend: cd frontend && npm run dev\n")

    sys.exit(0 if ok == total else 1)


if __name__ == "__main__":
    main()
