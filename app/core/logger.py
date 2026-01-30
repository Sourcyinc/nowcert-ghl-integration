"""
Sistema de logging centralizado
"""
import logging
import sys
from pathlib import Path
from app.core.config import settings

# Configurar logger
logger = logging.getLogger(settings.APP_NAME)
logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

# Formato de logs
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Handler para consola
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Handler para archivo (si está configurado)
if settings.LOG_FILE:
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(settings.LOG_FILE)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def log_payload(event_type: str, payload: dict, direction: str = "incoming"):
    """Registra un payload para debugging"""
    logger.info(f"[{direction.upper()}] {event_type} - Payload: {payload}")


def log_response(event_type: str, response: dict, direction: str = "outgoing"):
    """Registra una respuesta para debugging"""
    logger.info(f"[{direction.upper()}] {event_type} - Response: {response}")

