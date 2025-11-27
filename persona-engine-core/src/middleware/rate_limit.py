import time
import redis.asyncio as redis
from fastapi import HTTPException
from src.core.config import settings

class RateLimiter:
    def __init__(self, host="redis", port=6379):
        self.redis = redis.Redis(host=host, port=port, decode_responses=True)

    async def check_limit(self, key: str, limit: int, window_seconds: int):
        """
        Returns True if allowed, False if limited.
        """
        # Simple fixed window for MVP. 
        # For Enterprise, use Lua script for sliding window.
        current_window = int(time.time() / window_seconds)
        redis_key = f"rate_limit:{key}:{current_window}"
        
        # Increment
        current_count = await self.redis.incr(redis_key)
        
        # Set expiry on first increment
        if current_count == 1:
            await self.redis.expire(redis_key, window_seconds + 5)
            
        if current_count > limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")