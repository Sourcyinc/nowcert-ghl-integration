"""
Sistema de reintentos con backoff exponencial
"""
import asyncio
from typing import Callable, Any, Optional
from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import ExternalAPIError, ExternalAPIConnectionError


async def retry_with_backoff(
    func: Callable,
    max_retries: Optional[int] = None,
    backoff_factor: Optional[float] = None,
    initial_delay: Optional[float] = None,
    *args,
    **kwargs
) -> Any:
    """
    Ejecuta una función con reintentos y backoff exponencial
    
    Args:
        func: Función async a ejecutar
        max_retries: Número máximo de reintentos (default: settings.MAX_RETRIES)
        backoff_factor: Factor de backoff exponencial (default: settings.RETRY_BACKOFF_FACTOR)
        initial_delay: Delay inicial en segundos (default: settings.RETRY_INITIAL_DELAY)
        *args, **kwargs: Argumentos para la función
    
    Returns:
        Resultado de la función
    
    Raises:
        ExternalAPIError: Si todos los reintentos fallan
    """
    max_retries = max_retries or settings.MAX_RETRIES
    backoff_factor = backoff_factor or settings.RETRY_BACKOFF_FACTOR
    initial_delay = initial_delay or settings.RETRY_INITIAL_DELAY
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        except (ExternalAPIError, ExternalAPIConnectionError) as e:
            last_exception = e
            
            # No reintentar en errores 4xx (excepto 429 - Too Many Requests)
            if hasattr(e, 'status_code') and 400 <= e.status_code < 500 and e.status_code != 429:
                logger.warning(f"Error del cliente (no reintentable): {e.detail}")
                raise
            
            if attempt < max_retries:
                delay = initial_delay * (backoff_factor ** attempt)
                logger.warning(
                    f"Intento {attempt + 1}/{max_retries + 1} falló. "
                    f"Reintentando en {delay:.2f} segundos..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"Todos los reintentos fallaron después de {max_retries + 1} intentos")
                raise
        
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                delay = initial_delay * (backoff_factor ** attempt)
                logger.warning(
                    f"Error inesperado en intento {attempt + 1}/{max_retries + 1}. "
                    f"Reintentando en {delay:.2f} segundos... Error: {str(e)}"
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"Todos los reintentos fallaron: {str(e)}")
                raise ExternalAPIError(
                    status_code=500,
                    detail=f"Error después de {max_retries + 1} intentos: {str(e)}"
                )
    
    # Esto no debería ejecutarse, pero por seguridad
    if last_exception:
        raise last_exception

