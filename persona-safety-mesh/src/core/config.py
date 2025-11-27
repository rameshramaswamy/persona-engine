from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Use a small, fast model for input filtering (latency < 50ms)
    INPUT_MODEL: str = "unitary/unbiased-toxic-roberta" 
    ENABLE_OPA: bool = False # Set to True if OPA server is deployed
    OPA_URL: str = "http://localhost:8181/v1/data/safety/allow"
    
    # Thresholds
    TOXICITY_THRESHOLD: float = 0.95 # Only block extreme toxicity
    
    class Config:
        env_file = ".env"

settings = Settings()