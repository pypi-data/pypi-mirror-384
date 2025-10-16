from typing import List, Literal, Self
from datetime import datetime, timezone
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import find_dotenv
import importlib


class Settings(BaseSettings):
    APP_ENV: str = "dev"
    ZENX_VERSION: str = importlib.metadata.version("zenx")
    LOG_LEVEL: str = "DEBUG"
    START_DATETIME: datetime | None = None
    END_DATETIME: datetime | None = None

    SESSION_BACKEND: str = "memory"
    SESSION_POOL_SIZE: int = 1
    SESSION_AGE: int = 600 # 10 minutes
    SESSION_BLUEPRINT_SPARE: int = 1
    ACCESS_DENIAL_STATUS_CODES: List[int] = [401, 403, 429]
    REDIS_RESULT_QUEUE: str | None = None
    REDIS_MESSAGE_QUEUE: str | None = None

    SCHEDULAR: str = "workers"
    CONCURRENCY: int = 1
    TASK_INTERVAL_SECONDS: float = 1.0
    START_OFFSET_SECONDS: float = 60.0

    MAX_SCRAPE_DELAY: float = 0.0 # disabled

    DB_TYPE: Literal["memory", "redis", "sqlite"] = "memory"
    DB_NAME: str | None = None
    DB_USER: str | None = None
    DB_PASS: str | None = None
    DB_HOST: str | None = "localhost"
    DB_PORT: int | None = 6379
    DB_PATH: str | None = ".zenx/data.db"
    DQ_MAX_SIZE: int = 1000  # max size of the deque for memory database
    REDIS_RECORD_EXPIRY_SECONDS: int = 3456000 # 40 days (40*24*60*60)

    PROXY: str | None = None

    SYNOPTIC_GRPC_SERVER_URI: str = "ingress.opticfeeds.com"
    SYNOPTIC_GRPC_TOKEN: str | None = None
    SYNOPTIC_GRPC_ID: str | None = None
    # enterprise
    SYNOPTIC_ENTERPRISE_USEAST1_GRPC_SERVER_URI: str | None = "us-east-1.enterprise.synoptic.com:50051"
    SYNOPTIC_ENTERPRISE_EUCENTRAL1_GRPC_SERVER_URI: str | None = "eu-central-1.enterprise.synoptic.com:50051"
    SYNOPTIC_ENTERPRISE_EUWEST2_GRPC_SERVER_URI: str | None = "eu-west-2.enterprise.synoptic.com:50051"
    SYNOPTIC_ENTERPRISE_USEAST1CHI2A_GRPC_SERVER_URI: str | None = "us-east-1-chi-2a.enterprise.synoptic.com:50051"
    SYNOPTIC_ENTERPRISE_USEAST1NYC2A_GRPC_SERVER_URI: str | None = "us-east-1-nyc-2a.enterprise.synoptic.com:50051"
    SYNOPTIC_ENTERPRISE_APNORTHEAST1_GRPC_SERVER_URI: str | None = "ap-northeast-1.enterprise.synoptic.com:50051"
    SYNOPTIC_ENTERPRISE_GRPC_TOKEN: str | None = None
    SYNOPTIC_ENTERPRISE_GRPC_ID: str | None = None

    SYNOPTIC_DISCORD_WEBHOOK: str | None = None

    SYNOPTIC_WS_API_KEY: str | None = None
    SYNOPTIC_WS_STREAM_ID: str | None = None
    SYNOPTIC_FREE_WS_API_KEY: str | None = None
    SYNOPTIC_FREE_WS_STREAM_ID: str | None = None

    ITXP_SOCKET_PATH: str | None = "/tmp/itxpmonitor.sock"

    MONITOR_ITXP_SOCKET_PATH: str | None = "/tmp/itxpmonitor.sock"
    MONITOR_ITXP_TRIGGER_STATUS_CODE: int | None = 200
    MONITORING_ENABLED: bool | None = None

    # MITM
    SOLVER_REDIS_HOST: str = "5.161.249.237"
    SOLVER_REDIS_PORT: int = 6379
    SOLVER_REDIS_PASS: str | None = None

    model_config = SettingsConfigDict(env_file=find_dotenv(".env"), extra="allow", case_sensitive=True)

    @model_validator(mode="after")
    def model_created(self) -> Self:
        if self.APP_ENV == "dev":
            self.DB_TYPE = "memory"
        elif self.APP_ENV == "prod" and self.MONITORING_ENABLED is None:
            self.MONITORING_ENABLED = True

        if self.START_DATETIME and self.END_DATETIME:
            if self.START_DATETIME > self.END_DATETIME:
                raise ValueError("START_DATETIME must be before END_DATETIME")
            if self.START_DATETIME < datetime.now(timezone.utc):
                raise ValueError("START_DATETIME must be in the future")
            if self.END_DATETIME < datetime.now(timezone.utc):
                raise ValueError("END_DATETIME must be in the future")
            if self.START_DATETIME == self.END_DATETIME:
                raise ValueError("START_DATETIME and END_DATETIME must be different")
        return self

settings = Settings()
