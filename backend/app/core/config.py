from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Resume Coach"
    PROJECT_DESCRIPTION: str = "AI Resume & Interview Coaching Agent for College Students"

    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    DATABASE_URL: str = "sqlite:///./resume_coach.db"

    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_API_BASE: str = ""
    EMBEDDING_MODEL_NAME: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536
    EMBEDDING_ENABLE_REMOTE: bool = True
    LOG_LEVEL: str = "INFO"

    LLM_MODEL_PRESET: str = "deepseek-v4-pro"
    LLM_PROVIDER: str = ""
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = ""
    LLM_MODEL_NAME: str = ""
    LLM_TIMEOUT: int = 60
    LLM_MAX_RETRIES: int = 1
    LLM_ENABLE_REMOTE: bool = True
    # Reasoning models (e.g. qwen3.8-max) spend the token budget on
    # reasoning_content before emitting the answer, which truncates the JSON
    # payloads this app depends on. When enabled, requests carry
    # enable_thinking=false (supported by DashScope's OpenAI-compatible mode).
    LLM_DISABLE_THINKING: bool = False

    # Legacy OpenAI-compatible names, kept for existing .env files.
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_MODEL_NAME: str = ""
    DEEPSEEK_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    QWEN_API_KEY: str = ""
    DASHSCOPE_API_KEY: str = ""
    GLM_API_KEY: str = ""
    ZHIPU_API_KEY: str = ""

    MAX_FILE_SIZE: int = 10 * 1024 * 1024

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

CORS_ORIGINS = settings.BACKEND_CORS_ORIGINS
