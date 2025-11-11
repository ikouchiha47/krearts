"""
Simple rate limiter for API calls based on requests per minute (RPM).
"""

import asyncio
import json
import time
from collections import deque
from pathlib import Path
from typing import Dict


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, rpm: int):
        """
        Initialize rate limiter.
        
        Args:
            rpm: Requests per minute allowed
        """
        self.rpm = rpm
        self.interval = 60.0 / rpm  # seconds between requests
        self.timestamps: deque = deque()

    async def acquire(self):
        """Wait until a request can be made within rate limits."""
        now = time.time()
        
        # Remove timestamps older than 1 minute
        while self.timestamps and now - self.timestamps[0] > 60.0:
            self.timestamps.popleft()
        
        # If we've hit the limit, wait
        if len(self.timestamps) >= self.rpm:
            sleep_time = 60.0 - (now - self.timestamps[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                now = time.time()
                # Clean up again after sleep
                while self.timestamps and now - self.timestamps[0] > 60.0:
                    self.timestamps.popleft()
        
        # Record this request
        self.timestamps.append(now)


class RateLimiterManager:
    """Manages rate limiters for different API endpoints."""

    def __init__(self, config_path: str = "config.json"):
        """
        Initialize rate limiter manager from config.
        
        Args:
            config_path: Path to config.json with rate_limits
        """
        self.limiters: Dict[str, RateLimiter] = {}
        self._load_config(config_path)

    def _load_config(self, config_path: str):
        """Load rate limits from config file."""
        config_file = Path(config_path)
        
        if not config_file.exists():
            # Default limits if no config
            self.limiters = {
                "veo-3.1-generate-preview": RateLimiter(rpm=2),
                "gemini-2.5-flash-image": RateLimiter(rpm=500),
            }
            return
        
        with open(config_file) as f:
            config = json.load(f)
        
        rate_limits = config.get("rate_limits", {})
        for model, limits in rate_limits.items():
            rpm = limits.get("rpm", 60)
            self.limiters[model] = RateLimiter(rpm=rpm)

    async def acquire(self, model: str):
        """
        Acquire permission to make a request for the given model.
        
        Args:
            model: Model name (e.g., "veo-3.1-generate-preview")
        """
        if model not in self.limiters:
            # No limit configured, allow immediately
            return
        
        await self.limiters[model].acquire()
