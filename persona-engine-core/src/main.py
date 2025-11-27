from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.routes import router
from src.core.config import settings
from src.services.inference_client import InferenceClient
from src.memory.cache_manager import CacheManager
from src.memory.vector_store import LoreStore

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    inference = InferenceClient() # Initialize
    # Warm up vector store (load models into RAM)
    logger.info("Warming up AI models...")
    _ = LoreStore() 
    
    yield
    
    # Shutdown
    await inference._client.aclose()
    # Close Redis/Qdrant if explicit close methods exist (mostly handled by client destuctors)
    logger.info("System Shutdown complete.")

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    # OPTIMIZATION: Use 'uvloop' for faster async handling if on Linux/Mac
    uvicorn.run("src.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)