"""
Servicio para interactuar con la API de GoHighLevel
"""
import httpx
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.exceptions import ExternalAPIError, ExternalAPIConnectionError
from app.core.logger import logger
from app.core.retry import retry_with_backoff


class GHLService:
    """Servicio para manejar operaciones con GoHighLevel API"""
    
    def __init__(self):
        self.base_url = settings.GHL_BASE_URL
        self.api_key = settings.GHL_API_KEY
        self.location_id = settings.GHL_LOCATION_ID
        self.service_name = "GoHighLevel"
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtiene los headers necesarios para las peticiones"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Version": "2021-07-28"
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Realiza una petición a la API de GHL con reintentos
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint relativo de la API
            json_data: Datos JSON para el body (opcional)
            params: Parámetros de query (opcional)
        
        Returns:
            Respuesta JSON de la API
        """
        url = f"{self.base_url}{endpoint}"
        
        async def _execute_request():
            headers = self._get_headers()
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    if method.upper() == "GET":
                        response = await client.get(url, headers=headers, params=params)
                    elif method.upper() == "POST":
                        response = await client.post(url, json=json_data, headers=headers, params=params)
                    elif method.upper() == "PUT":
                        response = await client.put(url, json=json_data, headers=headers, params=params)
                    elif method.upper() == "DELETE":
                        response = await client.delete(url, headers=headers, params=params)
                    else:
                        raise ExternalAPIError(
                            status_code=400,
                            detail=f"Método {method} no soportado",
                            service_name=self.service_name
                        )
                    
                    response.raise_for_status()
                    return response.json()
                
                except httpx.HTTPStatusError as e:
                    error_detail = e.response.text if e.response.text else str(e)
                    raise ExternalAPIError(
                        status_code=e.response.status_code,
                        detail=error_detail,
                        service_name=self.service_name
                    )
                
                except httpx.RequestError as e:
                    raise ExternalAPIConnectionError(
                        detail=str(e),
                        service_name=self.service_name
                    )
        
        return await retry_with_backoff(_execute_request)
    
    async def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un contacto en GHL
        
        Args:
            contact_data: Datos del contacto
        
        Returns:
            Contacto creado
        """
        endpoint = f"/contacts/"
        params = {"locationId": self.location_id} if self.location_id else None
        return await self._make_request("POST", endpoint, contact_data, params)
    
    async def update_contact(self, contact_id: str, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza un contacto en GHL
        
        Args:
            contact_id: ID del contacto
            contact_data: Datos actualizados
        
        Returns:
            Contacto actualizado
        """
        endpoint = f"/contacts/{contact_id}"
        params = {"locationId": self.location_id} if self.location_id else None
        return await self._make_request("PUT", endpoint, contact_data, params)
    
    async def create_opportunity(
        self,
        contact_id: str,
        opportunity_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crea una oportunidad en GHL
        
        Args:
            contact_id: ID del contacto asociado
            opportunity_data: Datos de la oportunidad
        
        Returns:
            Oportunidad creada
        """
        endpoint = f"/opportunities/"
        params = {"locationId": self.location_id} if self.location_id else None
        
        # Asegurar que el contactId esté en los datos
        opportunity_data["contactId"] = contact_id
        
        return await self._make_request("POST", endpoint, opportunity_data, params)
    
    async def update_opportunity(
        self,
        opportunity_id: str,
        opportunity_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Actualiza una oportunidad en GHL
        
        Args:
            opportunity_id: ID de la oportunidad
            opportunity_data: Datos actualizados
        
        Returns:
            Oportunidad actualizada
        """
        endpoint = f"/opportunities/{opportunity_id}"
        params = {"locationId": self.location_id} if self.location_id else None
        return await self._make_request("PUT", endpoint, opportunity_data, params)

