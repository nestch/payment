from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "dev"

    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "payments"
    db_user: str = "payments"
    db_password: str = "payments"

    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "payments"
    rabbitmq_pass: str = "payments"

    jwt_secret: str = "nestch"
    jwt_algorithm: str = "HS256"

    rabbitmq_exchange: str = "payments.ex"
    rabbitmq_queue: str = "payments.requested.q"
    rabbitmq_dlq: str = "payments.requested.dlq"

    rabbitmq_prefetch: int = 20

    @property
    def sqlalchemy_database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
