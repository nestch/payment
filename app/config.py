from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "dev"

    db_host: str
    db_port: int = 3306
    db_name: str
    db_user: str
    db_password: str

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

    stripe_secret_key: str = ""
    stripe_public_key: str = ""
    stripe_webhook_secret: str = ""

    stripe_success_url: str = "http://localhost:3000/payment/success?payment_id={CHECKOUT_SESSION_ID}"
    stripe_cancel_url: str = "http://localhost:3000/payment/cancel"

    @property
    def sqlalchemy_database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
