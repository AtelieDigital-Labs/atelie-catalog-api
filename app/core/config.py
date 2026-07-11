from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    DATABASE_URL: str
    DATABASE_SCHEMA: str
    MESSAGING_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    MINIO_ENDPOINT_URL: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str

settings = Settings()