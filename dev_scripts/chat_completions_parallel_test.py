#!/usr/bin/env python3
"""
Unified Parallel Chat Completions Test
Comprehensive testing script for argoproxy parallel processing with both thread and async modes
"""

import asyncio
import argparse
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:44500")
MODEL = os.getenv("MODEL", "argo:gpt-4o")
CHAT_ENDPOINT = f"{BASE_URL}/v1/chat/completions"

# Configuration
TIMEOUT = 30.0
PROMPT_TEMPLATE = "Briefly explain {topic} in one sentence."


def create_payload(topic: str, request_id: int) -> Dict[str, Any]:
    """Create a chat completion payload."""
    return {
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT_TEMPLATE.format(topic=topic)}],
        "user": f"test_user_{request_id}",
        "stream": True,
        "max_tokens": 50,
    }


def make_thread_request(request_id: int) -> Dict[str, Any]:
    """Execute a single thread-based streaming request."""
    topics = [
        "quantum mechanics", "machine learning", "space exploration",
        "climate change", "artificial intelligence", "neuroscience",
        "renewable energy", "cryptocurrency", "biotechnology", "virtual reality"
    ]
    
    topic = topics[request_id % len(topics)]
    payload = create_payload(topic, request_id)
    headers = {"Content-Type": "application/json"}
    
    start_time = time.time()
    result = {
        "request_id": request_id,
        "topic": topic,
        "status_code": None,
        "response_time": 0,
        "total_chars": 0,
        "error": None,
        "chunks": []
    }
    
    try:
        with httpx.stream(
            "POST", CHAT_ENDPOINT, json=payload, headers=headers, timeout=TIMEOUT
        ) as response:
            result["status_code"] = response.status_code
            
            if response.status_code == 200:
                for chunk in response.iter_bytes():
                    if chunk:
                        chunk_str = chunk.decode(errors="replace")
                        result["chunks"].append(chunk_str)
                        result["total_chars"] += len(chunk_str)
            else:
                result["error"] = f"HTTP {response.status_code}"
                
    except Exception as e:
        result["error"] = str(e)
    
    result["response_time"] = time.time() - start_time
    return result


async def make_async_request(client: httpx.AsyncClient, request_id: int) -> Dict[str, Any]:
    """Execute a single async streaming request with detailed metrics."""
    topics = [
        "quantum mechanics", "machine learning", "space exploration",
        "climate change", "artificial intelligence", "neuroscience",
        "renewable energy", "cryptocurrency", "biotechnology", "virtual reality"
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
        "error": None
    }
    
    try:
        async with client.stream(
            "POST", CHAT_ENDPOINT, json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            result["status_code"] = response.status_code
            
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


def run_thread_test(concurrent_requests: int) -> List[Dict[str, Any]]:
    """Run thread-based parallel test."""
    print(f"\n🔧 Thread-based Parallel Test ({concurrent_requests} requests)")
    print("-" * 60)
    
    start_time = time.time()
    results = []
    
    with ThreadPoolExecutor(max_workers=min(concurrent_requests, 20)) as executor:
        future_to_id = {
            executor.submit(make_thread_request, i): i 
            for i in range(concurrent_requests)
        }
        
        for future in as_completed(future_to_id):
            try:
                result = future.result()
                results.append(result)
                print(f"✓ Thread Req {result['request_id']:2d}: "
                      f"Status {result['status_code']} | "
                      f"Time {result['response_time']:.2f}s | "
                      f"Chars {result['total_chars']:4d}")
                if result['error']:
                    print(f"  Error: {result['error']}")
            except Exception as e:
                print(f"✗ Thread Req {future_to_id[future]}: Exception - {e}")
    
    return results, time.time() - start_time


async def run_async_test(concurrent_requests: int) -> List[Dict[str, Any]]:
    """Run async-based parallel test."""
    print(f"\n🚀 Async-based Parallel Test ({concurrent_requests} requests)")
    print("-" * 60)
    
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        tasks = [make_async_request(client, i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, dict):
                processed_results.append(result)
                print(f"✓ Async Req {result['request_id']:2d}: "
                      f"Status {result['status_code']} | "
                      f"Total: {result['response_time']:.2f}s | "
                      f"First: {result.get('first_chunk_time', 0):.3f}s | "
                      f"Chars: {result['total_chars']:4d}")
                if result.get('error'):
                    print(f"  Error: {result['error']}")
            else:
                print(f"✗ Async Req {i}: Exception - {result}")
    
    return processed_results, time.time() - start_time


def analyze_results(results: List[Dict[str, Any]], total_time: float, test_name: str):
    """Analyze and display performance metrics."""
    successful = [r for r in results if r.get("status_code") == 200]
    failed = [r for r in results if r.get("error")]
    
    print("-" * 60)
    print(f"📈 {test_name} Summary:")
    print(f"Total time: {total_time:.2f}s")
    print(f"Successful: {len(successful)}/{len(results)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        response_times = [r['response_time'] for r in successful]
        print(f"Response time - Avg: {sum(response_times)/len(response_times):.3f}s, "
              f"Min: {min(response_times):.3f}s, Max: {max(response_times):.3f}s")
        
        variance = max(response_times) - min(response_times)
        print(f"Time variance: {variance:.3f}s")
        
        if 'first_chunk_time' in successful[0]:
            first_chunks = [r['first_chunk_time'] for r in successful]
            print(f"First chunk time - Avg: {sum(first_chunks)/len(first_chunks):.3f}s, "
                  f"Min: {min(first_chunks):.3f}s, Max: {max(first_chunks):.3f}s")
            first_chunk_variance = max(first_chunks) - min(first_chunks)
            print(f"First chunk variance: {first_chunk_variance:.3f}s")
            
            if variance > 2.0:
                print("⚠️  WARNING: High response time variance - potential blocking")
            else:
                print("✅ Response times consistent")
                
            if first_chunk_variance > 1.0:
                print("⚠️  WARNING: High first chunk variance - potential queueing")
            else:
                print("✅ First chunk delivery consistent")


async def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Test parallel chat completions")
    parser.add_argument("--requests", "-n", type=int, default=10,
                        help="Number of concurrent requests")
    parser.add_argument("--mode", "-m", choices=["thread", "async", "both"],
                        default="async", help="Test mode")
    
    args = parser.parse_args()
    
    print("🎯 Parallel Chat Completions Test")
    print(f"Endpoint: {CHAT_ENDPOINT}")
    print(f"Model: {MODEL}")
    
    if args.mode in ["thread", "both"]:
        thread_results, thread_time = run_thread_test(args.requests)
        analyze_results(thread_results, thread_time, "Thread-based")
    
    if args.mode in ["async", "both"]:
        async_results, async_time = await run_async_test(args.requests)
        analyze_results(async_results, async_time, "Async-based")


if __name__ == "__main__":
    asyncio.run(main())