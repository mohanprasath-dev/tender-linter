"""Keepalive and cold-start verification utility for Tender Linter demo hosting.
Maintains warm container state on serverless/free tiers and measures latency.
Usage:
    python scripts/keepalive.py --url https://demo.tender-linter.gov.in/health/ready --once
    python scripts/keepalive.py --url http://localhost:8000/health/ready --interval 300
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import UTC, datetime

import httpx


def ping_endpoint(url: str, timeout: float = 10.0) -> dict[str, str | float | int | bool]:
    """Ping health endpoint and measure response time and cold-start latency."""
    t0 = time.perf_counter()
    status_code = 0
    is_live = False
    error_msg = ""

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url)
            status_code = resp.status_code
            is_live = status_code == 200
    except Exception as exc:
        error_msg = str(exc)
    finally:
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    is_cold_start = latency_ms > 3000.0

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "url": url,
        "is_live": is_live,
        "status_code": status_code,
        "latency_ms": latency_ms,
        "is_cold_start": is_cold_start,
        "error": error_msg,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Tender Linter Keepalive and Cold-start Monitor")
    parser.add_argument("--url", type=str, default="http://localhost:8000/health/ready", help="Target URL to ping")
    parser.add_argument("--interval", type=int, default=300, help="Interval in seconds between pings (default: 300)")
    parser.add_argument("--once", action="store_true", help="Run a single ping check and exit")
    parser.add_argument("--timeout", type=float, default=10.0, help="Request timeout in seconds")

    args = parser.parse_args()

    print(f"Keepalive monitor targeting: {args.url}")

    if args.once:
        res = ping_endpoint(args.url, timeout=args.timeout)
        print(f"[{res['timestamp']}] Status: {res['status_code']}, Latency: {res['latency_ms']} ms")
        if res["is_cold_start"]:
            print("ALERT: Response latency exceeded 3000 ms (possible container cold-start delay).")
        if res["is_live"]:
            print("Target is warm and healthy.")
            return 0
        else:
            print(f"Target check failed: {res['error']}")
            return 1

    print(f"Running continuous keepalive daemon every {args.interval} seconds (Press Ctrl+C to stop)...")
    try:
        while True:
            res = ping_endpoint(args.url, timeout=args.timeout)
            print(f"[{res['timestamp']}] HTTP {res['status_code']} in {res['latency_ms']} ms (warm: {not res['is_cold_start']})")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nKeepalive monitor stopped.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
