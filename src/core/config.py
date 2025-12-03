# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv
import os
load_dotenv()

# class Settings(BaseSettings):
#     # Application
#     APP_NAME: str = Field("Real Estate Agency System")
#     API_PREFIX: str = Field("/api")

#     # MongoDB
#     MONGO_URI: str = Field("mongodb://localhost:27017")
#     MONGO_DB_NAME: str = Field("realestate")

#     # Logging
#     LOG_LEVEL: str = Field("INFO")

#     # Other global configs
#     MAX_CLIENT_FETCH_LIMIT: int = Field(1000)

#     GOOGLE_MODEL: str = Field("gemini-2.5-flash")
#     GOOGLE_API_KEY: str = Field(os.getenv("GOOGLE_API_KEY"))

#     # MinIO
#     MINIO_ENDPOINT: str = Field(os.getenv("MINIO_ENDPOINT"))
#     MINIO_PORT: str = Field(os.getenv("MINIO_PORT"))
#     MINIO_ACCESS_KEY: str = Field(os.getenv("MINIO_ACCESS_KEY"))
#     MINIO_SECRET_KEY: str = Field(os.getenv("MINIO_SECRET_KEY"))
#     MINIO_BUCKET_NAME: str = Field(os.getenv("MINIO_BUCKET_NAME"))
#     MINIO_SECURE: bool = Field(os.getenv("MINIO_SECURE"))

#     class Config:
#         env_file = ".env"
#         env_file_encoding = "utf-8"


class Settings(BaseSettings):
    APP_NAME: str = "Real Estate API"
    API_PREFIX: str = "/api"

    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "realestate"

    LOG_LEVEL: str = "INFO"
    MAX_CLIENT_FETCH_LIMIT: int = 1000

    GOOGLE_MODEL: str = "gemini-2.0-flash"
    GOOGLE_API_KEY: str

    # MinIO
    MINIO_ENDPOINT: str
    MINIO_PORT: int
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_NAME: str
    MINIO_SECURE: bool = False  # Pydantic converts "false" correctly

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
