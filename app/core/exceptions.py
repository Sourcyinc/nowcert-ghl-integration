"""
Excepciones personalizadas para la aplicación
"""
from fastapi import HTTPException, status


class ExternalAPIError(HTTPException):
    """Excepción para errores de APIs externas"""
    
    def __init__(self, status_code: int, detail: str, service_name: str = "External API"):
        super().__init__(
            status_code=status_code,
            detail=f"Error en {service_name}: {detail}"
        )
        self.service_name = service_name


class ExternalAPIConnectionError(HTTPException):
    """Excepción para errores de conexión con APIs externas"""
    
    def __init__(self, detail: str, service_name: str = "External API"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error de conexión con {service_name}: {detail}"
        )
        self.service_name = service_name


class TokenExpiredError(HTTPException):
    """Excepción para tokens expirados"""
    
    def __init__(self, detail: str = "Token expirado"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )


class DuplicateEventError(HTTPException):
    """Excepción para eventos duplicados (idempotencia)"""
    
    def __init__(self, detail: str = "Evento duplicado"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )

