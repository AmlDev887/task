from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field


class Settings(BaseSettings):
    USER: str
    PASSWORD: str
    HOST: str
    PORT: int
    DATABASE: str

    SECRET_KEY: str
    SECRET_KEY_2: str

    model_config = SettingsConfigDict(env_file=".env")

    @computed_field
    @property
    def ASYNC_DATABASE_URI(self) -> str:
        return (
            f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}"
            f"@{self.HOST}:{self.PORT}/{self.DATABASE}"
        )


settings = Settings()