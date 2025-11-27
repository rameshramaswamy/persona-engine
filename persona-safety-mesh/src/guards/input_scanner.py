from transformers import pipeline
from src.core.config import settings
import logging
from optimum.pipelines import pipeline
from src.core.config import settings
from src.memory.cache_manager import CacheManager # Reuse from Phase 2
import logging
import orjson
import hashlib

logger = logging.getLogger("safety_mesh")

class InputScanner:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InputScanner, cls).__new__(cls)
            logger.info(f"🛡️ Loading Safety Model (ONNX): {settings.INPUT_MODEL}")
            
            # OPTIMIZATION: Use ONNX Runtime for 5x speedup
            cls._instance.classifier = pipeline(
                "text-classification", 
                model=settings.INPUT_MODEL, 
                accelerator="ort", # ONNX Runtime
                top_k=None,
                device=-1 # CPU is fine for ONNX quantized models
            )
            # Link to Phase 2 Redis
            cls._instance.cache = CacheManager(host="redis") 
        return cls._instance

    def _get_hash(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    async def scan(self, text: str) -> dict:
        if not text or len(text.strip()) == 0:
            return {"safe": 1.0}

        # OPTIMIZATION: Check Redis Cache first
        text_hash = self._get_hash(text)
        cache_key = f"safety:scan:{text_hash}"
        
        # We need a raw redis call here, assuming CacheManager exposes .redis or we add a method
        cached_result = await self._instance.cache.redis.get(cache_key)
        if cached_result:
            return orjson.loads(cached_result)

        # Run Inference (Sync task in async wrapper)
        try:
            # Truncate to 512 to prevent DoS via massive context
            results = self.classifier(text[:512]) 
            scores = {item['label']: item['score'] for item in results[0]}
            
            # OPTIMIZATION: Cache result for 24 hours
            await self._instance.cache.redis.setex(
                cache_key, 
                3600 * 24, 
                orjson.dumps(scores)
            )
            return scores
        except Exception as e:
            logger.error(f"Input Scan Failed: {e}")
            return {"error": True, "toxicity": 1.0}