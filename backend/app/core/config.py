from pydantic_settings import BaseSettings
from typing import Optional
from datetime import timedelta

class Settings(BaseSettings):
    PROJECT_NAME: str = "Vehicle Management"
    DEBUG: bool = True

    # Use asyncmy driver for asyncio MySQL
    SQLALCHEMY_DATABASE_URI: str = "mysql+aiomysql://root@localhost:3306/tw_mgmt"

    JWT_SECRET_KEY: str = "bfdSH^$43&(iU&5FD3@vn<BfY6%3@dvgJki)"   # replace in prod / env var
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours default
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
