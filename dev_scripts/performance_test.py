#!/usr/bin/env python3
"""
Unified Performance Test Script for Argo Proxy
Comprehensive testing with thread-based, async-based, and optimized connection pooling tests
"""

import argparse
import os
import statistics
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
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
MAX_RETRIES = 2
RETRY_DELAY = 0.5  # Initial retry delay in seconds
CONNECTION_POOL_LIMITS = httpx.Limits(
    max_keepalive_connections=10,
    max_connections=20,
    keepalive_expiry=60.0
)


def create_payload(
    topic: str, request_id: int, test_mode: str = "process"
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


def make_request(
    request_id: int,
    total_requests: int,
    test_mode: str = "process",
    track_connection: bool = False
) -> Dict[str, Any]:
    """Execute a single streaming request with detailed metrics.
    
    Args:
        request_id: Unique ID for this request
        total_requests: Total number of concurrent requests
        test_mode: Type of test ("thread" or "process")
        track_connection: Whether to track connection reuse metrics
        
    Returns:
        Dictionary containing request metrics and results
    """
    # Initial delay between retries (increases exponentially)
    retry_delay = RETRY_DELAY
    last_exception = None
    
    for attempt in range(MAX_RETRIES + 1):
        topics = get_topics()
        topic = topics[request_id % len(topics)]
        payload = create_payload(topic, request_id, test_mode)
        headers = {"Content-Type": "application/json"}

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
        
        if track_connection:
            result["connection_reused"] = False

        try:
            with httpx.Client(
                timeout=TIMEOUT_BASIC,
                limits=CONNECTION_POOL_LIMITS,
                transport=httpx.HTTPTransport(retries=0)  # We handle retries ourselves
            ) as client:
                # Throttle requests to avoid overwhelming the server
                time.sleep(0.05 * (request_id % 10))
                
                with client.stream(
                    "POST",
                    CHAT_ENDPOINT,
                    json=payload,
                    headers=headers,
                    timeout=TIMEOUT_BASIC
                ) as response:
                    result["status_code"] = response.status_code

                    # Check connection reuse if requested
                    if track_connection and hasattr(response, "extensions"):
                        result["connection_reused"] = "network_stream" in response.extensions

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

                                result["last_chunk_time"] = time.time() - start_time

                        result["response_time"] = time.time() - start_time
                        if result["first_chunk_time"] > 0 and result["last_chunk_time"] > 0:
                            result["streaming_time"] = (
                                result["last_chunk_time"] - result["first_chunk_time"]
                            )
                        return result  # Success - return immediately
                    else:
                        result["error"] = f"HTTP {response.status_code}"
                        result["response_time"] = time.time() - start_time

        except httpx.TimeoutException as e:
            last_exception = e
            result["error"] = f"Timeout after {TIMEOUT_BASIC}s"
            result["response_time"] = time.time() - start_time
        except httpx.NetworkError as e:
            last_exception = e
            result["error"] = f"Network error: {str(e)}"
            result["response_time"] = time.time() - start_time
        except Exception as e:
            last_exception = e
            result["error"] = f"Unexpected error: {str(e)}"
            result["response_time"] = time.time() - start_time

        # If we get here, the request failed - wait before retrying
        if attempt < MAX_RETRIES:
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff

    # All retries failed - return the last result
    if last_exception:
        result["error"] = f"After {MAX_RETRIES} attempts: {result['error']}"
    return result


def make_thread_request(request_id: int, total_requests: int) -> Dict[str, Any]:
    """Execute a single thread-based streaming request."""
    return make_request(request_id, total_requests, test_mode="thread")


def make_multiprocess_request(request_id: int, total_requests: int) -> Dict[str, Any]:
    """Execute a single multiprocess streaming request with detailed metrics."""
    return make_request(
        request_id,
        total_requests,
        test_mode="process",
        track_connection=True
    )


def format_result_line(result: Dict[str, Any], test_type: str) -> str:
    """Format a result line for display based on test type."""
    status_icon = "✓" if result["status_code"] == 200 else "✗"
    prefix = f"{status_icon} "
    
    if test_type == "process":
        conn_icon = "🔗" if result.get("connection_reused") else "🆕"
        prefix += f"{conn_icon} "
    
    return (
        f"{prefix}{test_type.capitalize()} Req {result['request_id']:2d}: "
        f"Status {result['status_code']} | "
        f"Total: {result['response_time']:.2f}s | "
        f"First: {result.get('first_chunk_time', 0):.3f}s | "
        f"Stream: {result.get('streaming_time', 0):.3f}s | "
        f"Chars: {result['total_chars']:4d}"
    )


def run_concurrent_test(
    concurrent_requests: int,
    test_type: str,
    executor_class,
    max_workers_func,
    request_func,
) -> tuple[List[Dict[str, Any]], float]:
    """Run a concurrent test with the specified executor and configuration.
    
    Args:
        concurrent_requests: Number of concurrent requests
        test_type: Type of test ("thread" or "process")
        executor_class: Executor class (ThreadPoolExecutor or ProcessPoolExecutor)
        max_workers_func: Function to calculate max workers
        request_func: Function to make requests (make_thread_request or make_multiprocess_request)
    """
    print(f"\n{'🔧' if test_type == 'thread' else '🚀'} {test_type.capitalize()}-based Parallel Test ({concurrent_requests} requests)")
    print("-" * 70)

    start_time = time.time()
    results = []

    with executor_class(max_workers=max_workers_func(concurrent_requests)) as executor:
        future_to_id = {
            executor.submit(request_func, i, concurrent_requests): i
            for i in range(concurrent_requests)
        }

        # Track completion order and timing
        start_order_time = time.time()
        completed_count = 0
        
        for future in as_completed(future_to_id):
            try:
                result = future.result()
                results.append(result)
                completed_count += 1
                
                # Calculate timing stats
                elapsed = time.time() - start_order_time
                req_rate = completed_count / elapsed if elapsed > 0 else 0
                
                print(
                    f"{format_result_line(result, test_type)} | "
                    f"Completed {completed_count}/{concurrent_requests} | "
                    f"Rate: {req_rate:.1f} req/s"
                )
                if result.get("error"):
                    print(f"  Error: {result['error']}")
            except Exception as e:
                completed_count += 1
                print(f"✗ {test_type.capitalize()} Req {future_to_id[future]}: Exception - {e}")

    return results, time.time() - start_time


def run_thread_test(concurrent_requests: int) -> tuple[List[Dict[str, Any]], float]:
    """Run thread-based parallel test."""
    return run_concurrent_test(
        concurrent_requests,
        "thread",
        ThreadPoolExecutor,
        lambda n: min(n, 20),
        make_thread_request
    )


def run_multiprocess_test(concurrent_requests: int) -> tuple[List[Dict[str, Any]], float]:
    """Run multiprocess-based parallel test with optimized configuration."""
    return run_concurrent_test(
        concurrent_requests,
        "process",
        ProcessPoolExecutor,
        lambda n: min(n, os.cpu_count() * 2),
        make_multiprocess_request
    )


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
            print("\n⏱️  Response Time Metrics:")
            print(f"  Average: {statistics.mean(response_times):.3f}s")
            print(f"  Median:  {statistics.median(response_times):.3f}s")
            print(f"  Min:     {min(response_times):.3f}s")
            print(f"  Max:     {max(response_times):.3f}s")
            print(
                f"  StdDev:  {statistics.stdev(response_times) if len(response_times) > 1 else 0:.3f}s"
            )

            if first_chunk_times:
                print("\n⚡ First Chunk Time Metrics:")
                print(f"  Average: {statistics.mean(first_chunk_times):.3f}s")
                print(f"  Median:  {statistics.median(first_chunk_times):.3f}s")
                print(f"  Min:     {min(first_chunk_times):.3f}s")
                print(f"  Max:     {max(first_chunk_times):.3f}s")
                print(
                    f"  StdDev:  {statistics.stdev(first_chunk_times) if len(first_chunk_times) > 1 else 0:.3f}s"
                )

            if streaming_times:
                print("\n🌊 Streaming Time Metrics:")
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

        print("\n🎯 Performance Indicators:")
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


def main():
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
        choices=["thread", "process", "both"],
        default="process",
        help="Test mode: thread, process, or both",
    )

    args = parser.parse_args()

    print("🎯 Argo Proxy Unified Performance Test")
    print(f"Endpoint: {CHAT_ENDPOINT}")
    print(f"Model: {MODEL}")
    print(f"Concurrent requests: {args.requests}")

    if args.mode in ["thread", "both"]:
        thread_results, thread_time = run_thread_test(args.requests)
        analyze_results(thread_results, thread_time, "Thread-based")

    if args.mode in ["process", "both"]:
        multiprocess_results, multiprocess_time = run_multiprocess_test(args.requests)
        analyze_results(
            multiprocess_results, multiprocess_time, "process", detailed=True
        )


if __name__ == "__main__":
    main()
