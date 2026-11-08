"""Application configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "querymind-mcp"
    env: str = Field("development", alias="QUERYMIND_ENV")
    log_level: str = Field("info", alias="LOG_LEVEL")

    # Internal (application) database
    database_url: str = Field(
        "postgresql+psycopg2://querymind:querymind@localhost:5433/querymind",
        alias="DATABASE_URL",
    )

    # Default target database (overridable per connection profile)
    target_database_url: str = Field(
        "postgresql+psycopg2://readonly:readonly@localhost:5432/ecommerce",
        alias="TARGET_DATABASE_URL",
    )

    # Security
    secret_key: str = Field("change-me-in-production", alias="SECRET_KEY")
    encryption_key: str = Field(
        "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=", alias="ENCRYPTION_KEY"
    )

    # Authentication
    jwt_secret_key: str = Field(
        "change-me-in-production-32-bytes-min", alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    bcrypt_rounds: int = Field(12, alias="BCRYPT_ROUNDS")
    registration_enabled: bool = Field(True, alias="REGISTRATION_ENABLED")

    # Rate limiting
    rate_limit_requests: int = Field(100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(60, alias="RATE_LIMIT_WINDOW_SECONDS")

    # LLM provider
    llm_provider: str = Field("mock", alias="LLM_PROVIDER")
    llm_api_key: str = Field("", alias="LLM_API_KEY")
    llm_base_url: str = Field("", alias="LLM_BASE_URL")

    # Execution limits
    max_result_rows: int = Field(1000, alias="MAX_RESULT_ROWS")
    statement_timeout_ms: int = Field(10000, alias="STATEMENT_TIMEOUT_MS")

    # MCP transport
    mcp_transport: str = Field("stdio", alias="MCP_TRANSPORT")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
