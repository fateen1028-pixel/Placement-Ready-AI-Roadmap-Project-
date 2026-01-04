from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MONGO_URI: str
    MONGO_DB_NAME: str
    MONGO_MAX_POOL_SIZE: int = 10
    JWT_SECRET: str 
    
    # App Settings
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    LOG_LEVEL: str = "INFO"
    
    # AI Settings
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GOOGLE_API_KEY: str | None = None
    
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra='allow'
    )



settings = Settings() # type: ignore
