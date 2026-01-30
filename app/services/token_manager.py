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
        # NowCerts usa 'ngAuthApp' como client_id por defecto
        self.client_id = settings.NOWCERTS_CLIENT_ID or "ngAuthApp"
        
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_type: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    async def _login(self) -> Dict[str, Any]:
        """
        Realiza login en NowCerts y obtiene tokens
        
        NowCerts usa OAuth2 con form-urlencoded, no JSON.
        Endpoint: POST /api/token
        Body: grant_type=password&username=...&password=...&client_id=ngAuthApp
        
        Returns:
            Respuesta con access_token y refresh_token
        """
        url = f"{self.base_url}/api/token"
        
        # NowCerts requiere form-urlencoded, no JSON
        data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
            "client_id": self.client_id
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Enviar como form-urlencoded
                response = await client.post(
                    url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
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
        
        NowCerts usa el mismo endpoint /api/token pero con grant_type=refresh_token
        
        Returns:
            Nueva respuesta con tokens
        """
        if not self._refresh_token:
            # Si no hay refresh_token, hacer login completo
            return await self._login()
        
        url = f"{self.base_url}/api/token"
        
        # Obtener client_id de la respuesta anterior o usar el por defecto
        client_id = getattr(self, '_client_id_from_response', self.client_id)
        
        # NowCerts requiere form-urlencoded para refresh también
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
            "client_id": client_id
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
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
            self._token_type = token_data.get("token_type", "Bearer")
            
            # Guardar client_id de la respuesta si está presente
            if "as:client_id" in token_data:
                self._client_id_from_response = token_data.get("as:client_id")
            
            # Calcular expiración
            # NowCerts puede retornar expires_in o .expires
            expires_in = token_data.get("expires_in")
            if not expires_in and ".expires" in token_data:
                # Parsear fecha de expiración
                expires_str = token_data.get(".expires")
                try:
                    expires_date = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                    expires_in = int((expires_date - now).total_seconds())
                except:
                    expires_in = 3600  # Default 1 hora
            else:
                expires_in = expires_in or 3600  # Default 1 hora
            
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
        
        token_type = self._token_type or "Bearer"
        
        return {
            "Authorization": f"{token_type} {self._access_token}",
            "Content-Type": "application/json"
        }


# Instancia global del gestor de tokens
token_manager = TokenManager()

