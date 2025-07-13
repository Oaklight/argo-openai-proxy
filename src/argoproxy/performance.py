"""
Performance optimization utilities for argo-proxy.
"""

import asyncio
from typing import Optional

import aiohttp
from loguru import logger


class OptimizedHTTPSession:
    """Optimized HTTP session with connection pooling and performance tuning."""

    def __init__(
        self,
        *,
        total_connections: int = 100,
        connections_per_host: int = 30,
        keepalive_timeout: int = 30,
        connect_timeout: int = 10,
        read_timeout: int = 30,
        total_timeout: int = 60,
        dns_cache_ttl: int = 300,
        user_agent: str = "argo-proxy",
    ):
        """
        Initialize optimized HTTP session.

        Args:
            total_connections: Maximum total connections in pool
            connections_per_host: Maximum connections per host
            keepalive_timeout: Keep-alive timeout in seconds
            connect_timeout: Connection timeout in seconds
            read_timeout: Socket read timeout in seconds
            total_timeout: Total request timeout in seconds
            dns_cache_ttl: DNS cache TTL in seconds
            user_agent: User agent string
        """
        self.connector = aiohttp.TCPConnector(
            limit=total_connections,
            limit_per_host=connections_per_host,
            ttl_dns_cache=dns_cache_ttl,
            use_dns_cache=True,
            keepalive_timeout=keepalive_timeout,
            enable_cleanup_closed=True,
            # Enable TCP_NODELAY for lower latency
            tcp_nodelay=True,
        )

        self.timeout = aiohttp.ClientTimeout(
            total=total_timeout,
            connect=connect_timeout,
            sock_read=read_timeout,
        )

        self.session: Optional[aiohttp.ClientSession] = None
        self.user_agent = user_agent

    async def create_session(self) -> aiohttp.ClientSession:
        """Create and return the HTTP session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
            )
            logger.info(
                f"HTTP session created with {self.connector.limit} total connections, "
                f"{self.connector.limit_per_host} per host"
            )
        return self.session

    async def close(self):
        """Close the HTTP session and connector."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("HTTP session closed")

        if not self.connector.closed:
            await self.connector.close()
            logger.info("HTTP connector closed")


async def optimize_event_loop():
    """Apply event loop optimizations for better performance."""
    try:
        # Get current event loop
        loop = asyncio.get_running_loop()

        # Set debug mode to False for production performance
        loop.set_debug(False)

        # Optimize task factory if available
        if hasattr(loop, "set_task_factory"):
            loop.set_task_factory(None)

        logger.info("Event loop optimizations applied")

    except Exception as e:
        logger.warning(f"Could not apply event loop optimizations: {e}")


def get_performance_config() -> dict:
    """Get performance configuration based on system capabilities."""
    import multiprocessing
    import os

    # Get CPU count for scaling connection limits
    cpu_count = multiprocessing.cpu_count()

    # Scale connection limits based on CPU cores
    base_connections = max(50, cpu_count * 10)
    base_per_host = max(20, cpu_count * 5)

    # Check for environment overrides
    total_connections = int(os.getenv("ARGO_PROXY_MAX_CONNECTIONS", base_connections))
    connections_per_host = int(
        os.getenv("ARGO_PROXY_MAX_CONNECTIONS_PER_HOST", base_per_host)
    )

    return {
        "total_connections": total_connections,
        "connections_per_host": connections_per_host,
        "keepalive_timeout": int(os.getenv("ARGO_PROXY_KEEPALIVE_TIMEOUT", "30")),
        "connect_timeout": int(os.getenv("ARGO_PROXY_CONNECT_TIMEOUT", "10")),
        "read_timeout": int(os.getenv("ARGO_PROXY_READ_TIMEOUT", "30")),
        "total_timeout": int(os.getenv("ARGO_PROXY_TOTAL_TIMEOUT", "60")),
        "dns_cache_ttl": int(os.getenv("ARGO_PROXY_DNS_CACHE_TTL", "300")),
    }
