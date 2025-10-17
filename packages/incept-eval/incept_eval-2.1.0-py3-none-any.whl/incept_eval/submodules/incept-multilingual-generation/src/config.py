import os
from dotenv import load_dotenv
load_dotenv()


class Config:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    MONGODB_URI = os.getenv("MONGODB_URI")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    ARK_API_KEY = os.getenv("ARK_API_KEY")  # BytePlus ARK API for Seedream 4.0

    # Feature flags
    ENABLE_IMAGE_GENERATION = os.getenv('ENABLE_IMAGE_GENERATION', 'false').lower() == 'true'

    # HRM Configuration
    HRM_MODEL_SIZE = os.getenv(
        "HRM_MODEL_SIZE", "large")  # small, medium, large
    HRM_DEVICE = os.getenv("HRM_DEVICE", "cpu")  # cpu, cuda
    HF_API_TOKEN = os.getenv("HUGGINGFACE_TOKEN", "")
    ANTROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    HRM_CACHE_SIZE = int(os.getenv("HRM_CACHE_SIZE", "1000"))
    
    # Falcon H1 Configuration (Gradio API only)
    # No configuration needed - uses public Gradio playground at tiiuae/Falcon-H1-playground
    
    # Database Configuration
    POSTGRES_URI = os.getenv('POSTGRES_URI')

    # API Authentication
    APP_API_KEYS = os.getenv("APP_API_KEYS", "")

    # Concurrency Configuration
    MAX_WORKERS = 30

    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "CRITICAL").upper()
