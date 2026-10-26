from pydantic_settings import BaseSettings, SettingsConfigDict 

class Settings(BaseSettings):
    USER : str
    PASSWORD : str
    HOST : str
    PORT : int
    DATABASE : str

    SECRET_KEY : str
    SECRET_KEY_2 : str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

