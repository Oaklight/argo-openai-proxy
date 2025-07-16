import os
import time

import httpx

MODEL = os.getenv("MODEL", "gpt4o")
# API endpoint to POST
url = "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/streamchat/"
# Data to match the working cURL format

data = {
    "user": "pding",
    "model": MODEL,
    # --> OPTION 1 - Send system/prompt fields:
    # "system": "You are a large language model with the name Argo.",
    # "prompt": ["Tell me something interesting about quantum mechanics."],
    # --> OPTION 2 - Send messages object field:
    "messages": [
        {
            "role": "system",
            "content": "You are a large language model with the name Argo",
        },
        {
            "role": "user",
            "content": "Tell me something interesting about quantum mechanics.",
        },
    ],
    "stop": [],
    "temperature": 0.1,
}

# Headers for streaming
headers = {
    "Content-Type": "application/json",
    "Accept": "text/plain",
    "Cache-Control": "no-cache",
    "Accept-Encoding": "identity",  # Disable gzip compression
}

# Use httpx to send the request with streaming enabled
# Retry loop to continue calling until success
attempt = 1
while True:
    try:
        with httpx.stream(
            "POST", url, json=data, headers=headers, timeout=120.0
        ) as response:
            if response.status_code == 200:
                print(f"\nConnected successfully (attempt {attempt})")
                print(f" Status Code: {response.status_code}")
                print(f" Response Headers:\n {dict(response.headers)}")
                print("\nStreaming Response:")
                print("-" * 50)

                # Metadata collection
                chunk_count = 0
                total_chars = 0
                chunk_sizes = []
                chunk_times = []
                start_time = time.time()
                last_chunk_time = start_time
                first_chunk_time = None

                for chunk in response.iter_text():
                    if chunk:
                        current_time = time.time()

                        # Record first chunk timing
                        if first_chunk_time is None:
                            first_chunk_time = current_time

                        chunk_count += 1
                        chunk_size = len(chunk)
                        total_chars += chunk_size
                        chunk_sizes.append(chunk_size)

                        # Time since last chunk
                        time_since_last = current_time - last_chunk_time
                        chunk_times.append(time_since_last)
                        last_chunk_time = current_time

                        print(chunk, end="", flush=True)

                end_time = time.time()
                total_duration = end_time - start_time
                streaming_duration = end_time - (first_chunk_time or start_time)

                print(f"\n{'-' * 50}")
                print("ðŸ“Š STREAMING METADATA")
                print(f"Total chunks received: {chunk_count}")
                print(f"Total characters: {total_chars:,}")
                print(f"Total duration: {total_duration:.2f}s")
                print(
                    f"Time to first chunk: {(first_chunk_time - start_time):.2f}s"
                    if first_chunk_time
                    else "N/A"
                )
                print(f"Streaming duration: {streaming_duration:.2f}s")

                if chunk_count > 0:
                    avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes)
                    min_chunk_size = min(chunk_sizes)
                    max_chunk_size = max(chunk_sizes)

                    print(f"Average chunk size: {avg_chunk_size:.1f} chars")
                    print(
                        f"Chunk size range: {min_chunk_size} - {max_chunk_size} chars"
                    )
                    print(
                        f"Characters per second: {total_chars / streaming_duration:.1f}"
                    )
                    print(f"Chunks per second: {chunk_count / streaming_duration:.1f}")

                    if len(chunk_times) > 1:  # Skip first chunk time (always 0)
                        avg_chunk_interval = sum(chunk_times[1:]) / len(chunk_times[1:])
                        min_interval = min(chunk_times[1:])
                        max_interval = max(chunk_times[1:])
                        print(f"Average time between chunks: {avg_chunk_interval:.3f}s")
                        print(
                            f"Chunk interval range: {min_interval:.3f}s - {max_interval:.3f}s"
                        )

                break  # Exit the loop on success

            else:
                print(
                    f"Attempt {attempt} failed (status {response.status_code}), retrying..."
                )

    except httpx.TimeoutException:
        print("Request timed out")
    except Exception as e:
        print(f"Attempt {attempt} failed ({e}), retrying...")

    attempt += 1
    time.sleep(1)  # Brief pause between retries
