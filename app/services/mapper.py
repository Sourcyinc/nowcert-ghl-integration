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
        
        Args:
            ghl_data: Datos del contacto desde GHL
        
        Returns:
            Datos en formato NowCerts
        """
        return {
            "firstName": ghl_data.get("firstName", ""),
            "lastName": ghl_data.get("lastName", ""),
            "email": ghl_data.get("email", ""),
            "phone": ghl_data.get("phone", ""),
            "address": {
                "street": ghl_data.get("address1", ""),
                "city": ghl_data.get("city", ""),
                "state": ghl_data.get("state", ""),
                "zip": ghl_data.get("postalCode", "")
            },
            "source": ghl_data.get("source", "GHL")
        }
    
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

