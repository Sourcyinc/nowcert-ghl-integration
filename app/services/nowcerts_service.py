"""
Servicio para interactuar con la API de NowCerts
"""
import httpx
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.exceptions import ExternalAPIError, ExternalAPIConnectionError
from app.core.logger import logger
from app.core.retry import retry_with_backoff
from app.services.token_manager import token_manager


class NowCertsService:
    """Servicio para manejar operaciones con NowCerts API"""
    
    def __init__(self):
        self.base_url = settings.NOWCERTS_BASE_URL
        self.service_name = "NowCerts"
    
    async def _get_headers(self) -> Dict[str, str]:
        """Obtiene los headers necesarios para las peticiones"""
        access_token = await token_manager.get_access_token()
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Realiza una petición a la API de NowCerts con reintentos
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint relativo de la API
            json_data: Datos JSON para el body (opcional)
        
        Returns:
            Respuesta JSON de la API
        """
        url = f"{self.base_url}{endpoint}"
        
        async def _execute_request():
            headers = await self._get_headers()
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    if method.upper() == "GET":
                        response = await client.get(url, headers=headers)
                    elif method.upper() == "POST":
                        response = await client.post(url, json=json_data, headers=headers)
                    elif method.upper() == "PUT":
                        response = await client.put(url, json=json_data, headers=headers)
                    elif method.upper() == "DELETE":
                        response = await client.delete(url, headers=headers)
                    else:
                        raise ExternalAPIError(
                            status_code=400,
                            detail=f"Método {method} no soportado",
                            service_name=self.service_name
                        )
                    
                    # Si es 401, intentar renovar token y reintentar
                    if response.status_code == 401:
                        logger.warning("Token expirado, renovando...")
                        await token_manager.get_access_token(force_refresh=True)
                        headers = await self._get_headers()
                        
                        # Reintentar la petición
                        if method.upper() == "GET":
                            response = await client.get(url, headers=headers)
                        elif method.upper() == "POST":
                            response = await client.post(url, json=json_data, headers=headers)
                        elif method.upper() == "PUT":
                            response = await client.put(url, json=json_data, headers=headers)
                        elif method.upper() == "DELETE":
                            response = await client.delete(url, headers=headers)
                    
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
        Crea un contacto/asegurado en NowCerts
        
        Endpoint: POST /api/Insured/Insert
        Estructura esperada:
        - commercialName (opcional, para empresas)
        - firstName + lastName (opcional, si no hay commercialName)
        - active: true
        - addressLine1
        - stateNameOrAbbreviation
        - description
        
        Args:
            contact_data: Datos del contacto
        
        Returns:
            Contacto creado
        """
        # Mapear a la estructura que NowCerts espera
        nowcerts_data = {
            "active": True,
            "description": contact_data.get("description", "imported from Web Services")
        }
        
        # Si hay commercialName, usarlo (empresa)
        if contact_data.get("commercialName"):
            nowcerts_data["commercialName"] = contact_data.get("commercialName")
        else:
            # Si no, usar firstName y lastName (persona)
            nowcerts_data["firstName"] = contact_data.get("firstName", "")
            nowcerts_data["lastName"] = contact_data.get("lastName", "")
        
        # Dirección
        address = contact_data.get("address", {})
        if address.get("street"):
            nowcerts_data["addressLine1"] = address.get("street")
        elif contact_data.get("addressLine1"):
            nowcerts_data["addressLine1"] = contact_data.get("addressLine1")
        
        # Estado
        if address.get("state"):
            nowcerts_data["stateNameOrAbbreviation"] = address.get("state")
        elif contact_data.get("state"):
            nowcerts_data["stateNameOrAbbreviation"] = contact_data.get("state")
        
        return await self._make_request("POST", "/api/Insured/Insert", nowcerts_data)
    
    async def update_contact(self, contact_id: str, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza un contacto/asegurado en NowCerts
        
        Args:
            contact_id: ID del contacto
            contact_data: Datos actualizados
        
        Returns:
            Contacto actualizado
        """
        return await self._make_request("PUT", f"/api/contacts/{contact_id}", contact_data)
    
    async def create_policy(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea una póliza en NowCerts
        
        Endpoint: POST /api/Policy/Insert
        Estructura esperada:
        - number: Número de póliza
        - insuredName: Nombre del asegurado
        
        Args:
            policy_data: Datos de la póliza
        
        Returns:
            Póliza creada
        """
        # Mapear a la estructura que NowCerts espera
        nowcerts_policy = {
            "number": policy_data.get("policyNumber") or policy_data.get("number", ""),
            "insuredName": policy_data.get("insuredName", "")
        }
        
        return await self._make_request("POST", "/api/Policy/Insert", nowcerts_policy)
    
    async def update_policy(self, policy_id: str, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza una póliza en NowCerts
        
        Args:
            policy_id: ID de la póliza
            policy_data: Datos actualizados
        
        Returns:
            Póliza actualizada
        """
        return await self._make_request("PUT", f"/api/policies/{policy_id}", policy_data)
    
    async def create_quote(self, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea una cotización en NowCerts
        
        Nota: NowCerts puede usar el mismo endpoint de Policy para cotizaciones
        o tener un endpoint específico. Por ahora usamos Policy/Insert.
        
        Args:
            quote_data: Datos de la cotización
        
        Returns:
            Cotización creada
        """
        # Mapear cotización a estructura de póliza (NowCerts puede tratarlas similar)
        policy_data = {
            "number": quote_data.get("quoteNumber") or quote_data.get("number", ""),
            "insuredName": quote_data.get("insuredName", "")
        }
        
        return await self._make_request("POST", "/api/Policy/Insert", policy_data)
    
    async def update_quote(self, quote_id: str, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza una cotización en NowCerts
        
        Args:
            quote_id: ID de la cotización
            quote_data: Datos actualizados
        
        Returns:
            Cotización actualizada
        """
        return await self._make_request("PUT", f"/api/quotes/{quote_id}", quote_data)

