from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Logging
    logs_fraction: float = Field(0.01, alias="LOGS_FRACTION")

    # Model (S3)
    s3_model_path: str | None = Field(default=None, alias="S3_MODEL_PATH")

    # DynamoDB
    features_table: str = Field("features", alias="FEATURES_TABLE")
    stream_pk_prefix: str = "STREAM#"

    # Cache
    cache_maxsize: int = 50_000
    cache_separator: str = "--"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"