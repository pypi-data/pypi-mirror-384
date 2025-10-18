from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_HOST: str = ""
    DB_NAME: str = ""
    FRONTEND_URL: str = ""
    JWT_SECRET_KEY: str = ""
    ENVIRONMENT: str = ""
    SSL_CERT_PATH: str = "certs/DigiCertGlobalRootCA.crt.pem"

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")


settings = Settings()
