"""
Mapeo de datos entre NowCerts y GoHighLevel
"""
from typing import Dict, Any, Optional
from app.core.logger import logger


class DataMapper:
    """Mapea datos entre los formatos de NowCerts y GHL"""
    
    @staticmethod
    def ghl_to_nowcerts_contact(ghl_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convierte datos de contacto de GHL a formato NowCerts
        
        NowCerts espera:
        - firstName + lastName (para personas)
        - commercialName (para empresas)
        - active: true
        - addressLine1
        - stateNameOrAbbreviation
        - description
        
        Args:
            ghl_data: Datos del contacto desde GHL
        
        Returns:
            Datos en formato NowCerts
        """
        nowcerts_data = {
            "firstName": ghl_data.get("firstName", ""),
            "lastName": ghl_data.get("lastName", ""),
            "active": True,
            "addressLine1": ghl_data.get("address1", ""),
            "stateNameOrAbbreviation": ghl_data.get("state", ""),
            "description": f"imported from GHL - {ghl_data.get('source', 'GHL')}"
        }
        
        # Si hay commercialName en GHL, usarlo (empresa)
        if ghl_data.get("commercialName"):
            nowcerts_data["commercialName"] = ghl_data.get("commercialName")
            # Remover firstName/lastName si es empresa
            nowcerts_data.pop("firstName", None)
            nowcerts_data.pop("lastName", None)
        
        return nowcerts_data
    
    @staticmethod
    def nowcerts_to_ghl_contact(nowcerts_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convierte datos de contacto de NowCerts a formato GHL
        
        Args:
            nowcerts_data: Datos del contacto desde NowCerts
        
        Returns:
            Datos en formato GHL
        """
        address = nowcerts_data.get("address", {})
        
        return {
            "firstName": nowcerts_data.get("firstName", ""),
            "lastName": nowcerts_data.get("lastName", ""),
            "email": nowcerts_data.get("email", ""),
            "phone": nowcerts_data.get("phone", ""),
            "address1": address.get("street", ""),
            "city": address.get("city", ""),
            "state": address.get("state", ""),
            "postalCode": address.get("zip", ""),
            "source": nowcerts_data.get("source", "NowCerts")
        }
    
    @staticmethod
    def nowcerts_to_ghl_opportunity(
        nowcerts_data: Dict[str, Any],
        contact_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convierte datos de póliza/cotización de NowCerts a oportunidad en GHL
        
        Args:
            nowcerts_data: Datos de póliza o cotización desde NowCerts
            contact_id: ID del contacto en GHL (opcional)
        
        Returns:
            Datos de oportunidad en formato GHL
        """
        # Mapear tipo de póliza a pipeline/stage
        policy_type = nowcerts_data.get("policyType", "General")
        
        # Mapeo básico de tipos de póliza
        pipeline_mapping = {
            "Auto": "Auto Insurance",
            "Home": "Home Insurance",
            "Life": "Life Insurance",
            "Health": "Health Insurance",
            "General": "General Insurance"
        }
        
        pipeline_name = pipeline_mapping.get(policy_type, "General Insurance")
        
        opportunity = {
            "name": f"{policy_type} Policy - {nowcerts_data.get('policyNumber', 'N/A')}",
            "pipelineId": None,  # Debe configurarse según el setup de GHL
            "pipelineStageId": None,  # Debe configurarse según el setup de GHL
            "monetaryValue": nowcerts_data.get("premium", 0),
            "customFields": [
                {
                    "key": "policy_type",
                    "value": policy_type
                },
                {
                    "key": "policy_number",
                    "value": nowcerts_data.get("policyNumber", "")
                },
                {
                    "key": "carrier",
                    "value": nowcerts_data.get("carrier", "")
                },
                {
                    "key": "effective_date",
                    "value": nowcerts_data.get("effectiveDate", "")
                },
                {
                    "key": "expiration_date",
                    "value": nowcerts_data.get("expirationDate", "")
                },
                {
                    "key": "premium",
                    "value": str(nowcerts_data.get("premium", 0))
                }
            ]
        }
        
        if contact_id:
            opportunity["contactId"] = contact_id
        
        return opportunity

