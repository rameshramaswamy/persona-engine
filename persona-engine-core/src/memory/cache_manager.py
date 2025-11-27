import redis.asyncio as redis
import orjson # OPTIMIZATION: Faster than json
from src.core.config import settings
from typing import List, Dict

class CacheManager:
    def __init__(self, host: str = "localhost", port: int = 6379):
        self.redis = redis.Redis(host=host, port=port, decode_responses=False) # Keep as bytes for orjson
        self.ttl = 3600 * 24

    async def add_message(self, session_id: str, role: str, content: str):
        key = f"session:{session_id}"
        # OPTIMIZATION: Store as bytes immediately
        msg = orjson.dumps({"role": role, "content": content})
        
        async with self.redis.pipeline() as pipe:
            await pipe.rpush(key, msg)
            await pipe.ltrim(key, -20, -1) 
            await pipe.expire(key, self.ttl)
            await pipe.execute()

    async def get_history(self, session_id: str) -> List[Dict[str, str]]:
        key = f"session:{session_id}"
        messages = await self.redis.lrange(key, 0, -1)
        # OPTIMIZATION: Bulk decode
        return [orjson.loads(m) for m in messages]