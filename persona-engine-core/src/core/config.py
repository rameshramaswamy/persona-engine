from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Persona Engine Core"
    VLLM_ENDPOINT: str = "http://localhost:8000/v1"
    MODEL_NAME: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080
    TOXICITY_THRESHOLD: float = 0.95 # Only block extreme toxicity   
    
    class Config:
        env_file = ".env"

settings = Settings()