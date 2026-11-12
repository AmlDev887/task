from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field, EmailStr


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_DATABASE: str

    SMTP_SENDER = EmailStr
    SMTP_PASSWORD = str
    SMTP_SERVER = str
    SMTP_PORT = int

    SECRET_KEY: str
    SECRET_KEY_2: str
    REDIS_PORT: int
    REDIS_HOST: str
    model_config = SettingsConfigDict(env_file=".env")

    @computed_field
    @property
    def ASYNC_DATABASE_URI(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"
        )


settings = Settings()