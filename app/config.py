"""
Central configuration, read entirely from environment variables so
nothing sensitive is hardcoded in source (see .env.example).
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    MAX_RESULTS_PER_SOURCE: int = int(os.getenv("MAX_RESULTS_PER_SOURCE", "5"))
    REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "10"))

    HISTORY_FILE: str = os.getenv("HISTORY_FILE", "./data/search_history.json")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "./outputs")


settings = Settings()
