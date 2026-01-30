"""
Gestor de tokens para NowCerts
Maneja access_token, refresh_token y renovación automática
"""
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
from app.core.config import settings
from app.core.exceptions import TokenExpiredError, ExternalAPIError, ExternalAPIConnectionError
from app.core.logger import logger


class TokenManager:
    """Gestiona tokens de autenticación de NowCerts"""
    
    def __init__(self):
        self.base_url = settings.NOWCERTS_BASE_URL
        self.username = settings.NOWCERTS_USERNAME
        self.password = settings.NOWCERTS_PASSWORD
        self.client_id = settings.NOWCERTS_CLIENT_ID
        self.client_secret = settings.NOWCERTS_CLIENT_SECRET
        
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    async def _login(self) -> Dict[str, Any]:
        """
        Realiza login en NowCerts y obtiene tokens
        
        Returns:
            Respuesta con access_token y refresh_token
        """
        url = f"{self.base_url}/api/auth/login"
        
        payload = {
            "username": self.username,
            "password": self.password
        }
        
        # Si hay client_id y client_secret, usarlos
        if self.client_id and self.client_secret:
            payload["client_id"] = self.client_id
            payload["client_secret"] = self.client_secret
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
            
            except httpx.HTTPStatusError as e:
                error_detail = e.response.text if e.response.text else str(e)
                raise ExternalAPIError(
                    status_code=e.response.status_code,
                    detail=f"Error en login de NowCerts: {error_detail}",
                    service_name="NowCerts"
                )
            
            except httpx.RequestError as e:
                raise ExternalAPIConnectionError(
                    detail=f"Error de conexión en login de NowCerts: {str(e)}",
                    service_name="NowCerts"
                )
    
    async def _refresh_access_token(self) -> Dict[str, Any]:
        """
        Renueva el access_token usando el refresh_token
        
        Returns:
            Nueva respuesta con tokens
        """
        if not self._refresh_token:
            # Si no hay refresh_token, hacer login completo
            return await self._login()
        
        url = f"{self.base_url}/api/auth/refresh"
        
        payload = {
            "refresh_token": self._refresh_token
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
            
            except httpx.HTTPStatusError as e:
                # Si el refresh falla, hacer login completo
                if e.response.status_code == 401:
                    logger.warning("Refresh token expirado, realizando login completo")
                    return await self._login()
                else:
                    error_detail = e.response.text if e.response.text else str(e)
                    raise ExternalAPIError(
                        status_code=e.response.status_code,
                        detail=f"Error al refrescar token: {error_detail}",
                        service_name="NowCerts"
                    )
            
            except httpx.RequestError as e:
                raise ExternalAPIConnectionError(
                    detail=f"Error de conexión al refrescar token: {str(e)}",
                    service_name="NowCerts"
                )
    
    async def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Obtiene un access_token válido, renovándolo si es necesario
        
        Args:
            force_refresh: Si es True, fuerza la renovación del token
        
        Returns:
            Access token válido
        """
        now = datetime.now()
        buffer_seconds = settings.TOKEN_REFRESH_BUFFER_SECONDS
        
        # Verificar si necesitamos renovar el token
        needs_refresh = (
            force_refresh or
            not self._access_token or
            not self._token_expires_at or
            (self._token_expires_at - now).total_seconds() < buffer_seconds
        )
        
        if needs_refresh:
            logger.info("Renovando token de NowCerts...")
            
            if self._refresh_token and not force_refresh:
                # Intentar refrescar primero
                try:
                    token_data = await self._refresh_access_token()
                except Exception as e:
                    logger.warning(f"Error al refrescar token, haciendo login completo: {str(e)}")
                    token_data = await self._login()
            else:
                # Hacer login completo
                token_data = await self._login()
            
            # Actualizar tokens
            self._access_token = token_data.get("access_token")
            self._refresh_token = token_data.get("refresh_token")
            
            # Calcular expiración (asumir 1 hora si no se especifica)
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = now + timedelta(seconds=expires_in)
            
            logger.info(f"Token renovado exitosamente. Expira en {expires_in} segundos")
        
        if not self._access_token:
            raise TokenExpiredError("No se pudo obtener un access token válido")
        
        return self._access_token
    
    def get_headers(self) -> Dict[str, str]:
        """
        Obtiene headers con autenticación (debe llamarse después de get_access_token)
        
        Returns:
            Headers con Authorization
        """
        if not self._access_token:
            raise TokenExpiredError("No hay access token disponible")
        
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json"
        }


# Instancia global del gestor de tokens
token_manager = TokenManager()

