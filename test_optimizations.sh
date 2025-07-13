#!/bin/bash

# Test script for argo-proxy performance optimizations

echo "🚀 Testing Argo Proxy Performance Optimizations"
echo "================================================"

# Check if the server is running
if ! curl -s http://localhost:44500/health > /dev/null; then
    echo "❌ Argo proxy server is not running on localhost:44500"
    echo "Please start the server first with: python -m argoproxy"
    exit 1
fi

echo "✅ Server is running"

# Set performance environment variables for testing
export ARGO_PROXY_MAX_CONNECTIONS=150
export ARGO_PROXY_MAX_CONNECTIONS_PER_HOST=50
export ARGO_PROXY_KEEPALIVE_TIMEOUT=30
export ARGO_PROXY_CONNECT_TIMEOUT=10
export ARGO_PROXY_READ_TIMEOUT=30
export ARGO_PROXY_TOTAL_TIMEOUT=60

echo "🔧 Performance environment variables set:"
echo "  MAX_CONNECTIONS: $ARGO_PROXY_MAX_CONNECTIONS"
echo "  MAX_CONNECTIONS_PER_HOST: $ARGO_PROXY_MAX_CONNECTIONS_PER_HOST"
echo ""

# Run the original test for comparison
echo "📊 Running original parallel test (10 requests)..."
python dev_scripts/chat_completions_parallel_test.py -m async -n 10

echo ""
echo "🚄 Running optimized performance test (20 requests)..."
python dev_scripts/performance_test.py -n 20

echo ""
echo "🏁 Running high concurrency test (30 requests)..."
python dev_scripts/performance_test.py -n 30

echo ""
echo "✨ Performance testing completed!"
echo ""
echo "Key improvements to look for:"
echo "✅ Lower response time variance"
echo "✅ More consistent first chunk times"
echo "✅ Higher connection reuse rate"
echo "✅ Better overall throughput"