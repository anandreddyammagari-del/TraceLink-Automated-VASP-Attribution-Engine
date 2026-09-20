from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "TraceLink Forensic Workstation"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    OFFLINE_MODE: bool = True
    LOG_LEVEL: str = "INFO"

    # Cyber Officer Authentication & Security
    SECRET_KEY: str = "tracelink_super_secret_forensic_jwt_signing_key_94bnss_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    WORKSTATION_ID: str = "CYBER-UNIT-DELHI-01"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./tracelink_offline.db"
    
    # Cache and Messaging
    REDIS_URL: str = "redis://localhost:6379/0"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TRACE_TOPIC: str = "tracelink-traces-v1"

    # Graph Database
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "police_graph_secure_2026"

    # External APIs (Optional in offline mode)
    COVALENT_API_KEY: Optional[str] = "cqt_demo_key"
    CHAINALYSIS_API_KEY: Optional[str] = "chainalysis_demo_key"
    ETHERSCAN_API_KEY: Optional[str] = "etherscan_demo_key"

    # Statutory Notice & Seizure Settings
    DEFAULT_POLICE_STATION: str = "Special Cyber Cell, State Crime Branch"
    JURISDICTION: str = "State Cyber Operations Division"
    MANDATORY_LEGAL_CAVEAT: str = (
        "Investigative draft generated locally for officer review. "
        "Direct electronic submission to external portals is deactivated."
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
