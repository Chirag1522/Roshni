"""
Configuration management for ROSHNI backend.
Loads from .env and environment variables with validation.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # ================= SYSTEM =================
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # ================= API =================
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"
    allowed_hosts: str = "localhost,127.0.0.1"

    # ================= DATABASE =================
    database_url: str = "sqlite:///./roshni.db"

    # ================= ALGORAND =================
    algorand_network: str = "testnet"
    algorand_node_url: str = "https://testnet-api.algonode.cloud"
    algorand_indexer_url: str = "https://testnet-idx.algonode.cloud"

    # 🔥 Support BOTH (only one required)
    algorand_admin_mnemonic: Optional[str] = None
    algorand_admin_private_key: Optional[str] = None

    sun_asa_id: int = 756341116

    # ================= ELEVENLABS VOICE =================
    elevenlabs_api_key: Optional[str] = None

    # ================= GEMINI AI =================
    gemini_api_key: Optional[str] = None

    # ================= DISCOM CONFIG =================
    discom_fixed_charge: float = 100.0
    discom_admin_fee_percent: float = 2.0
    discom_export_rate: float = 8.0
    discom_grid_rate: float = 12.0

    # ================= SOLAR PRICING =================
    solar_export_rate: float = 10.0
    solar_pool_rate: float = 9.0

    # ================= IOT =================
    iot_auth_token: str = "iot_secret_token_12345"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"   # 🔥 prevents crash if extra env vars exist

    # ================= HELPERS =================
    @property
    def cors_origins(self) -> list:
        return [self.frontend_url]

    @property
    def allowed_hosts_list(self) -> list:
        return [h.strip() for h in self.allowed_hosts.split(",")]


settings = Settings()