"""
Endpoint para sincronización manual
"""
from fastapi import APIRouter, HTTPException
from typing import Any
from app.models.webhooks import SyncRequest, SyncResponse
from app.services.nowcerts_service import NowCertsService
from app.services.ghl_service import GHLService
from app.services.mapper import DataMapper
from app.core.logger import logger

router = APIRouter()
nowcerts_service = NowCertsService()
ghl_service = GHLService()
mapper = DataMapper()


@router.post(
    "/manual",
    response_model=SyncResponse,
    summary="Sincronización manual",
    description="Endpoint para pruebas y sincronización manual de datos entre NowCerts y GHL"
)
async def sync_manual(request: SyncRequest) -> Any:
    """
    Endpoint para sincronización manual de datos
    
    Permite sincronizar manualmente:
    - Contactos entre NowCerts y GHL
    - Pólizas/Cotizaciones de NowCerts a oportunidades en GHL
    - Oportunidades de GHL a cotizaciones en NowCerts
    
    Args:
        request: Solicitud de sincronización con source, entity_type, direction y datos
    
    Returns:
        Resultado de la sincronización
    """
    try:
        logger.info(
            f"Sincronización manual: {request.source} -> {request.direction} "
            f"({request.entity_type})"
        )
        
        source_id = None
        target_id = None
        result_data = None
        
        if request.direction == "to_ghl":
            # Sincronizar hacia GHL
            if request.source == "nowcerts":
                if request.entity_type == "contact":
                    # Contacto de NowCerts a GHL
                    if request.data:
                        ghl_data = mapper.nowcerts_to_ghl_contact(request.data)
                        result = await ghl_service.create_contact(ghl_data)
                        target_id = result.get("id")
                        result_data = result
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail="Se requieren datos para crear contacto"
                        )
                
                elif request.entity_type in ["policy", "quote"]:
                    # Póliza/Cotización de NowCerts a oportunidad en GHL
                    if request.data:
                        # Necesitamos contact_id, por ahora lo omitimos
                        opportunity_data = mapper.nowcerts_to_ghl_opportunity(request.data)
                        # Nota: crear oportunidad requiere contact_id
                        result_data = {
                            "message": "Crear oportunidad requiere contact_id en GHL",
                            "opportunity_data": opportunity_data
                        }
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail="Se requieren datos para crear oportunidad"
                        )
        
        elif request.direction == "to_nowcerts":
            # Sincronizar hacia NowCerts
            if request.source == "ghl":
                if request.entity_type == "contact":
                    # Contacto de GHL a NowCerts
                    if request.data:
                        nowcerts_data = mapper.ghl_to_nowcerts_contact(request.data)
                        result = await nowcerts_service.create_contact(nowcerts_data)
                        target_id = result.get("id")
                        result_data = result
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail="Se requieren datos para crear contacto"
                        )
                
                elif request.entity_type == "opportunity":
                    # Oportunidad de GHL a cotización en NowCerts
                    if request.data:
                        quote_data = {
                            "policyType": request.data.get("customFields", {}).get("policy_type", "General"),
                            "premium": request.data.get("monetaryValue", 0),
                            "carrier": request.data.get("customFields", {}).get("carrier", ""),
                            "source": "GHL"
                        }
                        result = await nowcerts_service.create_quote(quote_data)
                        target_id = result.get("id")
                        result_data = result
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail="Se requieren datos para crear cotización"
                        )
        
        return SyncResponse(
            success=True,
            message=f"Sincronización {request.entity_type} completada exitosamente",
            source_id=request.entity_id,
            target_id=target_id,
            data=result_data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en sincronización manual: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error en sincronización: {str(e)}"
        )

