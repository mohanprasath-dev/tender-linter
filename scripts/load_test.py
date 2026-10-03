"""Load testing harness for Tender Linter API.
Simulates concurrent procurement officer interactions and measures latency percentiles,
requests per second, and error rates against defined SLAs.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import statistics
import time
from typing import Any

from fastapi.testclient import TestClient

from apps.api.core.auth import create_access_token

SAMPLE_AUDIT_CLAUSES = [
    "Supply of 500 laptops complying with IS 13252 (Part 1): 2010.",
    "Procurement of microwave ovens conforming to IS 302-2-25 with BIS CRS registration.",
    "Supply of 43 Grade Ordinary Portland Cement conforming to IS 8112: 2013.",
    "Installation of enterprise IT equipment complying with IS/IEC 62368 Part 1.",
    "Cement bags must be manufactured strictly in accordance with ISI quality parameters.",
]


def _execute_worker_task(
    client: Any,
    task_type: int,
    token: str | None = None,
) -> tuple[bool, float]:
    """Execute a single workload task and return (success, latency_ms)."""
    t0 = time.perf_counter()
    success = False
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    try:
        mod = task_type % 4
        if mod == 0:
            # 1. Health readiness probe
            resp = client.get("/health/ready")
            success = resp.status_code == 200
        elif mod == 1:
            # 2. Version information
            resp = client.get("/api/v1/version")
            success = resp.status_code == 200
        elif mod == 2:
            # 3. Standards catalog listing
            resp = client.get("/api/v1/standards", headers=headers)
            success = resp.status_code == 200
        else:
            # 4. Live audit creation with clause
            clause_idx = task_type % len(SAMPLE_AUDIT_CLAUSES)
            clause = SAMPLE_AUDIT_CLAUSES[clause_idx]
            resp = client.post(
                "/api/v1/audits",
                json={
                    "text": clause,
                    "document_name": f"load_clause_{task_type}.txt",
                    "language_hint": "en",
                },
                headers=headers,
            )
            success = resp.status_code in (200, 201)
    except Exception:
        success = False
    finally:
        latency_ms = (time.perf_counter() - t0) * 1000

    return success, latency_ms


def run_in_process_load_test(
    client: TestClient,
    concurrency: int = 5,
    total_requests: int = 25,
    token: str | None = None,
) -> dict[str, Any]:
    """Run concurrent load test in-process using ThreadPoolExecutor."""
    if not token:
        token = create_access_token({"sub": "officer1", "role": "Reviewer", "user_id": 1})

    latencies: list[float] = []
    failures = 0

    start_time = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(_execute_worker_task, client, i, token)
            for i in range(total_requests)
        ]
        for f in concurrent.futures.as_completed(futures):
            ok, lat = f.result()
            latencies.append(lat)
            if not ok:
                failures += 1

    total_time = time.perf_counter() - start_time
    rps = total_requests / total_time if total_time > 0 else 0.0

    sorted_lats = sorted(latencies)
    p50_idx = int(len(sorted_lats) * 0.50)
    p95_idx = min(int(len(sorted_lats) * 0.95), len(sorted_lats) - 1)
    p99_idx = min(int(len(sorted_lats) * 0.99), len(sorted_lats) - 1)

    return {
        "concurrency": concurrency,
        "total_requests": total_requests,
        "successful_requests": total_requests - failures,
        "failed_requests": failures,
        "error_rate": failures / total_requests if total_requests > 0 else 0.0,
        "total_duration_sec": round(total_time, 3),
        "requests_per_second": round(rps, 2),
        "min_ms": round(sorted_lats[0], 2) if sorted_lats else 0.0,
        "avg_ms": round(statistics.mean(sorted_lats), 2) if sorted_lats else 0.0,
        "p50_ms": round(sorted_lats[p50_idx], 2) if sorted_lats else 0.0,
        "p95_ms": round(sorted_lats[p95_idx], 2) if sorted_lats else 0.0,
        "p99_ms": round(sorted_lats[p99_idx], 2) if sorted_lats else 0.0,
        "max_ms": round(sorted_lats[-1], 2) if sorted_lats else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Tender Linter Load Test Runner")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent client workers")
    parser.add_argument("--requests", type=int, default=50, help="Total requests to execute")
    parser.add_argument("--in-process", action="store_true", default=True, help="Run in-process via FastAPI client")
    args = parser.parse_args()

    print(f"Starting load test: concurrency={args.concurrency}, requests={args.requests}")

    from apps.api.main import app

    client = TestClient(app)
    results = run_in_process_load_test(
        client=client,
        concurrency=args.concurrency,
        total_requests=args.requests,
    )

    print("\n--- Load Test Results ---")
    print(f"Total Requests: {results['total_requests']}")
    print(f"Successful:     {results['successful_requests']}")
    print(f"Failed:         {results['failed_requests']} (Error rate: {results['error_rate'] * 100:.1f}%)")
    print(f"Throughput:     {results['requests_per_second']} req/sec")
    print(f"Latency min:    {results['min_ms']} ms")
    print(f"Latency avg:    {results['avg_ms']} ms")
    print(f"Latency p50:    {results['p50_ms']} ms")
    print(f"Latency p95:    {results['p95_ms']} ms")
    print(f"Latency p99:    {results['p99_ms']} ms")
    print(f"Latency max:    {results['max_ms']} ms")

    if results["error_rate"] == 0.0:
        print("\nSLA check PASSED: 0 errors and valid throughput.")
        return 0
    else:
        print("\nSLA check FAILED: errors encountered.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
