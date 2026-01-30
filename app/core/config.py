"""
Configuración centralizada de la aplicación
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Información de la API
    APP_NAME: str = "NowCerts GHL Integration API"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # NowCerts API
    NOWCERTS_BASE_URL: str = "https://api.nowcerts.com"
    NOWCERTS_USERNAME: Optional[str] = None
    NOWCERTS_PASSWORD: Optional[str] = None
    NOWCERTS_CLIENT_ID: Optional[str] = None
    NOWCERTS_CLIENT_SECRET: Optional[str] = None
    
    # GoHighLevel API
    GHL_BASE_URL: str = "https://services.leadconnectorhq.com"
    GHL_API_KEY: Optional[str] = None
    GHL_LOCATION_ID: Optional[str] = None
    
    # Configuración de tokens
    TOKEN_REFRESH_BUFFER_SECONDS: int = 300  # Renovar token 5 minutos antes de expirar
    
    # Configuración de reintentos
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_FACTOR: float = 2.0
    RETRY_INITIAL_DELAY: float = 1.0
    
    # Configuración del servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Base de datos para control de duplicados (opcional, usar SQLite por defecto)
    DATABASE_URL: Optional[str] = None  # Si es None, usa SQLite en memoria
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None  # Si es None, solo log a consola


# Instancia global de configuración
settings = Settings()

