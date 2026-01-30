"""
Sistema de control de duplicados (idempotencia)
"""
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logger import logger

# Almacenamiento en memoria (en producción usar Redis o base de datos)
_event_cache: Dict[str, datetime] = {}
CACHE_EXPIRY_HOURS = 24


def generate_event_id(payload: dict, source: str) -> str:
    """
    Genera un ID único para un evento basado en su contenido
    
    Args:
        payload: Payload del evento
        source: Fuente del evento (nowcerts, ghl)
    
    Returns:
        ID único del evento
    """
    # Crear un hash del payload y la fuente
    event_data = {
        "source": source,
        "payload": payload
    }
    event_str = json.dumps(event_data, sort_keys=True)
    event_hash = hashlib.sha256(event_str.encode()).hexdigest()
    return f"{source}_{event_hash}"


def is_duplicate(event_id: str) -> bool:
    """
    Verifica si un evento es duplicado
    
    Args:
        event_id: ID del evento
    
    Returns:
        True si es duplicado, False si no
    """
    if event_id in _event_cache:
        # Verificar si el evento aún está en el período de validez
        event_time = _event_cache[event_id]
        expiry_time = event_time + timedelta(hours=CACHE_EXPIRY_HOURS)
        if datetime.now() < expiry_time:
            logger.warning(f"Evento duplicado detectado: {event_id}")
            return True
        else:
            # El evento expiró, removerlo
            del _event_cache[event_id]
    
    return False


def mark_event_processed(event_id: str):
    """
    Marca un evento como procesado
    
    Args:
        event_id: ID del evento
    """
    _event_cache[event_id] = datetime.now()
    logger.debug(f"Evento marcado como procesado: {event_id}")


def cleanup_expired_events():
    """Limpia eventos expirados del cache"""
    now = datetime.now()
    expired_keys = [
        key for key, timestamp in _event_cache.items()
        if now - timestamp > timedelta(hours=CACHE_EXPIRY_HOURS)
    ]
    for key in expired_keys:
        del _event_cache[key]
    if expired_keys:
        logger.debug(f"Limpiados {len(expired_keys)} eventos expirados")

