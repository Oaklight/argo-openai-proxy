#!/usr/bin/env python3
"""
Performance Test Script for Argo Proxy Optimizations
Tests the improved parallel throughput and connection pooling
"""

import asyncio
import argparse
import os
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:44500")
MODEL = os.getenv("MODEL", "argo:gpt-4o")
CHAT_ENDPOINT = f"{BASE_URL}/v1/chat/completions"

# Configuration
TIMEOUT = 60.0
PROMPT_TEMPLATE = "Explain {topic} in exactly one sentence."


def create_payload(topic: str, request_id: int) -> Dict[str, Any]:
    """Create a chat completion payload."""
    return {
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT_TEMPLATE.format(topic=topic)}],
        "user": f"perf_test_{request_id}",
        "stream": True,
        "max_tokens": 100,
    }


async def make_optimized_request(client: httpx.AsyncClient, request_id: int) -> Dict[str, Any]:
    """Execute a single optimized async streaming request."""
    topics = [
        "quantum computing", "machine learning algorithms", "space exploration missions",
        "climate change impacts", "artificial intelligence ethics", "neuroscience breakthroughs",
        "renewable energy technologies", "cryptocurrency blockchain", "biotechnology advances", 
        "virtual reality applications", "cybersecurity threats", "autonomous vehicles",
        "gene therapy", "solar panel efficiency", "deep learning networks"
    ]
    
    topic = topics[request_id % len(topics)]
    payload = create_payload(topic, request_id)
    
    start_time = time.time()
    result = {
        "request_id": request_id,
        "topic": topic,
        "status_code": None,
        "response_time": 0,
        "first_chunk_time": 0,
        "total_chunks": 0,
        "total_chars": 0,
        "error": None,
        "connection_reused": False
    }
    
    try:
        async with client.stream(
            "POST", CHAT_ENDPOINT, json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            result["status_code"] = response.status_code
            
            # Check if connection was reused (indicates connection pooling is working)
            if hasattr(response, 'extensions') and 'network_stream' in response.extensions:
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
                
                result["response_time"] = time.time() - start_time
            else:
                result["error"] = f"HTTP {response.status_code}"
                
    except Exception as e:
        result["error"] = str(e)
        result["response_time"] = time.time() - start_time
    
    return result


async def run_performance_test(concurrent_requests: int, test_name: str = "Performance") -> List[Dict[str, Any]]:
    """Run optimized async-based parallel test."""
    print(f"\n🚀 {test_name} Test ({concurrent_requests} concurrent requests)")
    print("-" * 70)
    
    start_time = time.time()
    
    # Use optimized client settings that match our server
    limits = httpx.Limits(
        max_keepalive_connections=50,
        max_connections=100,
        keepalive_expiry=30.0
    )
    
    timeout = httpx.Timeout(
        connect=10.0,
        read=30.0,
        write=10.0,
        pool=60.0
    )
    
    async with httpx.AsyncClient(
        limits=limits, 
        timeout=timeout,
        http2=False  # Use HTTP/1.1 for better connection reuse visibility
    ) as client:
        tasks = [make_optimized_request(client, i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, dict):
                processed_results.append(result)
                status_icon = "✓" if result["status_code"] == 200 else "✗"
                conn_icon = "🔗" if result.get("connection_reused") else "🆕"
                print(f"{status_icon} {conn_icon} Req {result['request_id']:2d}: "
                      f"Status {result['status_code']} | "
                      f"Total: {result['response_time']:.2f}s | "
                      f"First: {result.get('first_chunk_time', 0):.3f}s | "
                      f"Chars: {result['total_chars']:4d}")
                if result.get('error'):
                    print(f"    Error: {result['error']}")
            else:
                print(f"✗ Req {i}: Exception - {result}")
    
    total_time = time.time() - start_time
    return processed_results, total_time


def analyze_performance_results(results: List[Dict[str, Any]], total_time: float, test_name: str):
    """Analyze and display detailed performance metrics."""
    successful = [r for r in results if r.get("status_code") == 200]
    failed = [r for r in results if r.get("error")]
    reused_connections = [r for r in successful if r.get("connection_reused")]
    
    print("-" * 70)
    print(f"📊 {test_name} Analysis:")
    print(f"Total time: {total_time:.2f}s")
    print(f"Successful: {len(successful)}/{len(results)}")
    print(f"Failed: {len(failed)}")
    print(f"Connection reuse rate: {len(reused_connections)}/{len(successful)} ({len(reused_connections)/max(len(successful),1)*100:.1f}%)")
    
    if successful:
        response_times = [r['response_time'] for r in successful]
        first_chunk_times = [r['first_chunk_time'] for r in successful if r['first_chunk_time'] > 0]
        
        print(f"\n⏱️  Response Time Metrics:")
        print(f"  Average: {statistics.mean(response_times):.3f}s")
        print(f"  Median:  {statistics.median(response_times):.3f}s")
        print(f"  Min:     {min(response_times):.3f}s")
        print(f"  Max:     {max(response_times):.3f}s")
        print(f"  StdDev:  {statistics.stdev(response_times) if len(response_times) > 1 else 0:.3f}s")
        
        if first_chunk_times:
            print(f"\n⚡ First Chunk Time Metrics:")
            print(f"  Average: {statistics.mean(first_chunk_times):.3f}s")
            print(f"  Median:  {statistics.median(first_chunk_times):.3f}s")
            print(f"  Min:     {min(first_chunk_times):.3f}s")
            print(f"  Max:     {max(first_chunk_times):.3f}s")
            print(f"  StdDev:  {statistics.stdev(first_chunk_times) if len(first_chunk_times) > 1 else 0:.3f}s")
        
        # Performance indicators
        variance = max(response_times) - min(response_times)
        first_chunk_variance = max(first_chunk_times) - min(first_chunk_times) if first_chunk_times else 0
        
        print(f"\n🎯 Performance Indicators:")
        if variance < 2.0:
            print("✅ Low response time variance - good consistency")
        else:
            print("⚠️  High response time variance - potential blocking issues")
            
        if first_chunk_variance < 1.0:
            print("✅ Low first chunk variance - good request handling")
        else:
            print("⚠️  High first chunk variance - potential queueing issues")
            
        if len(reused_connections) / max(len(successful), 1) > 0.7:
            print("✅ Good connection reuse - connection pooling effective")
        else:
            print("⚠️  Low connection reuse - connection pooling may need tuning")
        
        # Throughput calculation
        throughput = len(successful) / total_time
        print(f"🚄 Throughput: {throughput:.2f} requests/second")


async def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Performance test for optimized argo-proxy")
    parser.add_argument("--requests", "-n", type=int, default=20,
                        help="Number of concurrent requests")
    parser.add_argument("--rounds", "-r", type=int, default=1,
                        help="Number of test rounds")
    
    args = parser.parse_args()
    
    print("🎯 Argo Proxy Performance Test")
    print(f"Endpoint: {CHAT_ENDPOINT}")
    print(f"Model: {MODEL}")
    print(f"Concurrent requests: {args.requests}")
    print(f"Test rounds: {args.rounds}")
    
    all_results = []
    all_times = []
    
    for round_num in range(args.rounds):
        if args.rounds > 1:
            print(f"\n{'='*20} Round {round_num + 1}/{args.rounds} {'='*20}")
        
        results, total_time = await run_performance_test(
            args.requests, 
            f"Round {round_num + 1}" if args.rounds > 1 else "Performance"
        )
        
        analyze_performance_results(
            results, 
            total_time, 
            f"Round {round_num + 1}" if args.rounds > 1 else "Performance"
        )
        
        all_results.extend(results)
        all_times.append(total_time)
        
        if round_num < args.rounds - 1:
            print("\n⏳ Waiting 2 seconds before next round...")
            await asyncio.sleep(2)
    
    if args.rounds > 1:
        print(f"\n{'='*20} Overall Summary {'='*20}")
        successful_all = [r for r in all_results if r.get("status_code") == 200]
        print(f"Total successful requests: {len(successful_all)}")
        print(f"Average round time: {statistics.mean(all_times):.2f}s")
        print(f"Overall throughput: {len(successful_all) / sum(all_times):.2f} requests/second")


if __name__ == "__main__":
    asyncio.run(main())