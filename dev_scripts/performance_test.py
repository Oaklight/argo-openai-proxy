#!/usr/bin/env python3
"""
Unified Performance Test Script for Argo Proxy
Comprehensive testing with thread-based, async-based, and optimized connection pooling tests
"""

import argparse
import asyncio
import os
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:44500")
MODEL = os.getenv("MODEL", "argo:gpt-4o")
CHAT_ENDPOINT = f"{BASE_URL}/v1/chat/completions"

# Configuration
TIMEOUT_BASIC = 30.0
TIMEOUT_OPTIMIZED = 60.0
PROMPT_TEMPLATE = "Explain {topic} in exactly one sentence."


def create_payload(
    topic: str, request_id: int, test_mode: str = "async"
) -> Dict[str, Any]:
    """Create a chat completion payload."""
    max_tokens = 100  # Use consistent token count for all modes
    user_prefix = f"{test_mode}_test"

    return {
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT_TEMPLATE.format(topic=topic)}],
        "user": f"{user_prefix}_{request_id}",
        "stream": True,
        "max_tokens": max_tokens,
    }


def get_topics() -> List[str]:
    """Get list of topics for testing."""
    return [
        "quantum mechanics",
        "machine learning",
        "space exploration",
        "climate change",
        "artificial intelligence",
        "neuroscience",
        "renewable energy",
        "cryptocurrency",
        "biotechnology",
        "virtual reality",
        "quantum computing",
        "machine learning algorithms",
        "space exploration missions",
        "climate change impacts",
        "artificial intelligence ethics",
        "neuroscience breakthroughs",
        "renewable energy technologies",
        "cryptocurrency blockchain",
        "biotechnology advances",
        "virtual reality applications",
        "cybersecurity threats",
        "autonomous vehicles",
        "gene therapy",
        "solar panel efficiency",
        "deep learning networks",
    ]


def make_thread_request(request_id: int, total_requests: int) -> Dict[str, Any]:
    """Execute a single thread-based streaming request."""
    topics = get_topics()
    topic = topics[request_id % len(topics)]
    payload = create_payload(topic, request_id, "thread")
    headers = {"Content-Type": "application/json"}

    # Scale timeout linearly with number of requests
    timeout = max(60.0, total_requests * 3.0)

    start_time = time.time()
    result = {
        "request_id": request_id,
        "topic": topic,
        "status_code": None,
        "response_time": 0,
        "first_chunk_time": 0,
        "last_chunk_time": 0,
        "streaming_time": 0,
        "total_chunks": 0,
        "total_chars": 0,
        "error": None,
    }

    # Use optimized HTTP configuration
    limits = httpx.Limits(
        max_keepalive_connections=50, max_connections=100, keepalive_expiry=30.0
    )
    timeout_config = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=timeout)

    try:
        with httpx.Client(limits=limits, timeout=timeout_config, http2=False) as client:
            with client.stream(
                "POST", CHAT_ENDPOINT, json=payload, headers=headers
            ) as response:
                result["status_code"] = response.status_code

                if response.status_code == 200:
                    first_chunk = True
                    for chunk in response.iter_bytes():
                        if chunk:
                            chunk_str = chunk.decode(errors="replace")
                            result["total_chars"] += len(chunk_str)
                            result["total_chunks"] += 1

                            if first_chunk:
                                result["first_chunk_time"] = time.time() - start_time
                                first_chunk = False

                            # Update last chunk time for each chunk
                            result["last_chunk_time"] = time.time() - start_time

                    result["response_time"] = time.time() - start_time
                    # Calculate streaming time (first to last chunk)
                    if result["first_chunk_time"] > 0 and result["last_chunk_time"] > 0:
                        result["streaming_time"] = (
                            result["last_chunk_time"] - result["first_chunk_time"]
                        )
                else:
                    result["error"] = f"HTTP {response.status_code}"
                    result["response_time"] = time.time() - start_time

    except Exception as e:
        result["error"] = str(e)
        result["response_time"] = time.time() - start_time

    return result


async def make_async_request(
    client: httpx.AsyncClient, request_id: int
) -> Dict[str, Any]:
    """Execute a single async streaming request with detailed metrics."""
    topics = get_topics()
    topic = topics[request_id % len(topics)]
    payload = create_payload(topic, request_id, "async")

    start_time = time.time()
    result = {
        "request_id": request_id,
        "topic": topic,
        "status_code": None,
        "response_time": 0,
        "first_chunk_time": 0,
        "last_chunk_time": 0,
        "streaming_time": 0,
        "total_chunks": 0,
        "total_chars": 0,
        "error": None,
        "connection_reused": False,
    }

    try:
        async with client.stream(
            "POST",
            CHAT_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as response:
            result["status_code"] = response.status_code

            # Check if connection was reused (indicates connection pooling is working)
            if (
                hasattr(response, "extensions")
                and "network_stream" in response.extensions
            ):
                result["connection_reused"] = True

            if response.status_code == 200:
                first_chunk = True
                async for chunk in response.aiter_bytes():
                    if chunk:
                        chunk_str = chunk.decode(errors="replace")
                        result["total_chars"] += len(chunk_str)
                        result["total_chunks"] += 1

                        if first_chunk:
                            result["first_chunk_time"] = time.time() - start_time
                            first_chunk = False

                        # Update last chunk time for each chunk
                        result["last_chunk_time"] = time.time() - start_time

                result["response_time"] = time.time() - start_time
                # Calculate streaming time (first to last chunk)
                if result["first_chunk_time"] > 0 and result["last_chunk_time"] > 0:
                    result["streaming_time"] = (
                        result["last_chunk_time"] - result["first_chunk_time"]
                    )
            else:
                result["error"] = f"HTTP {response.status_code}"

    except Exception as e:
        result["error"] = str(e)
        result["response_time"] = time.time() - start_time

    return result


def run_thread_test(concurrent_requests: int) -> tuple[List[Dict[str, Any]], float]:
    """Run thread-based parallel test."""
    print(f"\n🔧 Thread-based Parallel Test ({concurrent_requests} requests)")
    print("-" * 70)

    start_time = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=min(concurrent_requests, 20)) as executor:
        future_to_id = {
            executor.submit(make_thread_request, i, concurrent_requests): i
            for i in range(concurrent_requests)
        }

        for future in as_completed(future_to_id):
            try:
                result = future.result()
                results.append(result)
                print(
                    f"✓ Thread Req {result['request_id']:2d}: "
                    f"Status {result['status_code']} | "
                    f"Total: {result['response_time']:.2f}s | "
                    f"First: {result.get('first_chunk_time', 0):.3f}s | "
                    f"Stream: {result.get('streaming_time', 0):.3f}s | "
                    f"Chars: {result['total_chars']:4d}"
                )
                if result["error"]:
                    print(f"  Error: {result['error']}")
            except Exception as e:
                print(f"✗ Thread Req {future_to_id[future]}: Exception - {e}")

    return results, time.time() - start_time


async def run_async_test(
    concurrent_requests: int,
) -> tuple[List[Dict[str, Any]], float]:
    """Run async-based parallel test with optimized configuration."""
    print(f"\n🚀 Async Parallel Test ({concurrent_requests} requests)")
    print("-" * 70)

    start_time = time.time()

    # Use optimized configuration with scaled timeout
    timeout = max(60.0, concurrent_requests * 3.0)

    limits = httpx.Limits(
        max_keepalive_connections=50, max_connections=100, keepalive_expiry=30.0
    )
    timeout_config = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=timeout)

    client_kwargs = {
        "limits": limits,
        "timeout": timeout_config,
        "http2": False,  # Use HTTP/1.1 for better connection reuse visibility
    }

    async with httpx.AsyncClient(**client_kwargs) as client:
        tasks = [make_async_request(client, i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, dict):
                processed_results.append(result)
                status_icon = "✓" if result["status_code"] == 200 else "✗"
                conn_icon = "🔗" if result.get("connection_reused") else "🆕"

                print(
                    f"{status_icon} {conn_icon} Async Req {result['request_id']:2d}: "
                    f"Status {result['status_code']} | "
                    f"Total: {result['response_time']:.2f}s | "
                    f"First: {result.get('first_chunk_time', 0):.3f}s | "
                    f"Stream: {result.get('streaming_time', 0):.3f}s | "
                    f"Chars: {result['total_chars']:4d}"
                )

                if result.get("error"):
                    print(f"    Error: {result['error']}")
            else:
                print(f"✗ Req {i}: Exception - {result}")

    total_time = time.time() - start_time
    return processed_results, total_time


def analyze_results(
    results: List[Dict[str, Any]],
    total_time: float,
    test_name: str,
    detailed: bool = False,
):
    """Analyze and display performance metrics."""
    successful = [r for r in results if r.get("status_code") == 200]
    failed = [r for r in results if r.get("error")]

    print("-" * 70)
    print(f"📊 {test_name} Analysis:")
    print(f"Total time: {total_time:.2f}s")
    print(f"Successful: {len(successful)}/{len(results)}")
    print(f"Failed: {len(failed)}")

    # Connection reuse analysis for optimized tests
    if detailed and successful:
        reused_connections = [r for r in successful if r.get("connection_reused")]
        print(
            f"Connection reuse rate: {len(reused_connections)}/{len(successful)} ({len(reused_connections) / max(len(successful), 1) * 100:.1f}%)"
        )

    if successful:
        response_times = [r["response_time"] for r in successful]
        first_chunk_times = [
            r["first_chunk_time"] for r in successful if r["first_chunk_time"] > 0
        ]
        streaming_times = [
            r["streaming_time"] for r in successful if r.get("streaming_time", 0) > 0
        ]

        if detailed:
            print(f"\n⏱️  Response Time Metrics:")
            print(f"  Average: {statistics.mean(response_times):.3f}s")
            print(f"  Median:  {statistics.median(response_times):.3f}s")
            print(f"  Min:     {min(response_times):.3f}s")
            print(f"  Max:     {max(response_times):.3f}s")
            print(
                f"  StdDev:  {statistics.stdev(response_times) if len(response_times) > 1 else 0:.3f}s"
            )

            if first_chunk_times:
                print(f"\n⚡ First Chunk Time Metrics:")
                print(f"  Average: {statistics.mean(first_chunk_times):.3f}s")
                print(f"  Median:  {statistics.median(first_chunk_times):.3f}s")
                print(f"  Min:     {min(first_chunk_times):.3f}s")
                print(f"  Max:     {max(first_chunk_times):.3f}s")
                print(
                    f"  StdDev:  {statistics.stdev(first_chunk_times) if len(first_chunk_times) > 1 else 0:.3f}s"
                )
            
            if streaming_times:
                print(f"\n🌊 Streaming Time Metrics:")
                print(f"  Average: {statistics.mean(streaming_times):.3f}s")
                print(f"  Median:  {statistics.median(streaming_times):.3f}s")
                print(f"  Min:     {min(streaming_times):.3f}s")
                print(f"  Max:     {max(streaming_times):.3f}s")
                print(
                    f"  StdDev:  {statistics.stdev(streaming_times) if len(streaming_times) > 1 else 0:.3f}s"
                )
        else:
            # Basic analysis
            print(
                f"Response time - Avg: {statistics.mean(response_times):.3f}s, "
                f"Min: {min(response_times):.3f}s, Max: {max(response_times):.3f}s"
            )

            if first_chunk_times:
                print(
                    f"First chunk time - Avg: {statistics.mean(first_chunk_times):.3f}s, "
                    f"Min: {min(first_chunk_times):.3f}s, Max: {max(first_chunk_times):.3f}s"
                )
            
            if streaming_times:
                print(
                    f"Streaming time - Avg: {statistics.mean(streaming_times):.3f}s, "
                    f"Min: {min(streaming_times):.3f}s, Max: {max(streaming_times):.3f}s"
                )

        # Performance indicators
        variance = max(response_times) - min(response_times)
        first_chunk_variance = (
            max(first_chunk_times) - min(first_chunk_times) if first_chunk_times else 0
        )
        streaming_variance = (
            max(streaming_times) - min(streaming_times) if streaming_times else 0
        )

        print(f"\n🎯 Performance Indicators:")
        if variance < 2.0:
            print("✅ Low response time variance - good consistency")
        else:
            print("⚠️  High response time variance - potential blocking issues")

        if first_chunk_variance < 1.0:
            print("✅ Low first chunk variance - good request handling")
        else:
            print("⚠️  High first chunk variance - potential queueing issues")
        
        if streaming_variance < 1.0:
            print("✅ Low streaming variance - consistent data transfer")
        else:
            print("⚠️  High streaming variance - potential network issues")

        if detailed:
            reused_connections = [r for r in successful if r.get("connection_reused")]
            if len(reused_connections) / max(len(successful), 1) > 0.7:
                print("✅ Good connection reuse - connection pooling effective")
            else:
                print("⚠️  Low connection reuse - connection pooling may need tuning")

        # Throughput calculation
        throughput = len(successful) / total_time
        print(f"🚄 Throughput: {throughput:.2f} requests/second")


async def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(
        description="Unified performance test for argo-proxy"
    )
    parser.add_argument(
        "--requests", "-n", type=int, default=10, help="Number of concurrent requests"
    )
    parser.add_argument(
        "--mode",
        "-m",
        choices=["thread", "async", "both"],
        default="async",
        help="Test mode: thread, async, or both",
    )
    parser.add_argument(
        "--rounds", "-r", type=int, default=1, help="Number of test rounds"
    )

    args = parser.parse_args()

    print("🎯 Argo Proxy Unified Performance Test")
    print(f"Endpoint: {CHAT_ENDPOINT}")
    print(f"Model: {MODEL}")
    print(f"Concurrent requests: {args.requests}")
    if args.rounds > 1:
        print(f"Test rounds: {args.rounds}")

    if args.mode in ["thread", "both"]:
        thread_results, thread_time = run_thread_test(args.requests)
        analyze_results(thread_results, thread_time, "Thread-based")

    if args.mode in ["async", "both"]:
        if args.rounds > 1:
            # Multi-round async test
            all_results = []
            all_times = []

            for round_num in range(args.rounds):
                print(f"\n{'=' * 20} Round {round_num + 1}/{args.rounds} {'=' * 20}")

                results, total_time = await run_async_test(args.requests)

                analyze_results(
                    results, total_time, f"Async Round {round_num + 1}", detailed=True
                )

                all_results.extend(results)
                all_times.append(total_time)

                if round_num < args.rounds - 1:
                    print("\n⏳ Waiting 2 seconds before next round...")
                    await asyncio.sleep(2)

            if args.rounds > 1:
                print(f"\n{'=' * 20} Overall Summary {'=' * 20}")
                successful_all = [r for r in all_results if r.get("status_code") == 200]
                print(f"Total successful requests: {len(successful_all)}")
                print(f"Average round time: {statistics.mean(all_times):.2f}s")
                print(
                    f"Overall throughput: {len(successful_all) / sum(all_times):.2f} requests/second"
                )
        else:
            # Single async test
            async_results, async_time = await run_async_test(args.requests)
            analyze_results(async_results, async_time, "Async", detailed=True)


if __name__ == "__main__":
    asyncio.run(main())
