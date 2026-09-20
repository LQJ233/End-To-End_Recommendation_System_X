import argparse
import asyncio
import json
import statistics
import time

import httpx


def percentile(values: list[float], percent: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round((percent / 100.0) * (len(ordered) - 1))))
    return ordered[index]


async def run_benchmark(args: argparse.Namespace) -> dict:
    semaphore = asyncio.Semaphore(args.concurrency)
    latencies: list[float] = []
    errors = 0

    async with httpx.AsyncClient(timeout=args.timeout) as client:
        async def one_request(index: int) -> None:
            nonlocal errors
            async with semaphore:
                started = time.perf_counter()
                try:
                    if args.mode == "rec":
                        response = await client.post(
                            args.url,
                            json={
                                "user_id": f"{args.user_prefix}-{index}",
                                "scene": "home",
                                "size": args.size,
                                "request_id": f"bench-{index}",
                            },
                        )
                    else:
                        response = await client.get(
                            args.url,
                            headers={"X-User-Id": f"{args.user_prefix}-{index}"},
                        )
                    if response.status_code != 200:
                        errors += 1
                        return
                    latencies.append((time.perf_counter() - started) * 1000.0)
                except Exception:
                    errors += 1

        await asyncio.gather(*(one_request(index) for index in range(args.requests)))

    return {
        "mode": args.mode,
        "url": args.url,
        "requests": args.requests,
        "concurrency": args.concurrency,
        "errors": errors,
        "success": len(latencies),
        "p50_ms": round(percentile(latencies, 50), 3),
        "p95_ms": round(percentile(latencies, 95), 3),
        "p99_ms": round(percentile(latencies, 99), 3),
        "avg_ms": round(statistics.mean(latencies), 3) if latencies else 0.0,
        "max_ms": round(max(latencies), 3) if latencies else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["rec", "backend"], default="rec")
    parser.add_argument("--url", default=None)
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--size", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--user-prefix", default="bench-user")
    args = parser.parse_args()
    if args.url is None:
        args.url = (
            "http://127.0.0.1:8000/v1/recommend"
            if args.mode == "rec"
            else "http://127.0.0.1:8080/api/v1/home"
        )

    print(json.dumps(asyncio.run(run_benchmark(args)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
