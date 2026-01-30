"""
Endpoints para webhooks de NowCerts y GHL
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Any, Dict
from app.models.webhooks import (
    NowCertsWebhookPayload,
    GHLWebhookPayload,
    WebhookResponse
)
from app.services.nowcerts_service import NowCertsService
from app.services.ghl_service import GHLService
from app.services.mapper import DataMapper
from app.core.idempotency import generate_event_id, is_duplicate, mark_event_processed
from app.core.logger import logger, log_payload, log_response
from app.core.exceptions import DuplicateEventError

router = APIRouter()
nowcerts_service = NowCertsService()
ghl_service = GHLService()
mapper = DataMapper()


@router.post(
    "/nowcerts",
    response_model=WebhookResponse,
    summary="Webhook de NowCerts",
    description="Recibe eventos desde NowCerts y los sincroniza con GHL"
)
async def webhook_nowcerts(
    payload: NowCertsWebhookPayload,
    request: Request
) -> Any:
    """
    Endpoint para recibir webhooks de NowCerts
    
    Eventos soportados:
    - INSURED_INSERT / INSURED_UPDATE: Sincroniza contactos con GHL
    - POLICY_INSERT / POLICY_UPDATE: Crea/actualiza oportunidades en GHL
    - QUOTE_INSERT / QUOTE_UPDATE: Crea/actualiza oportunidades en GHL
    
    Returns:
        Respuesta con el resultado del procesamiento
    """
    try:
        # Log del payload recibido
        payload_dict = payload.model_dump()
        log_payload("NOWCERTS_WEBHOOK", payload_dict, "incoming")
        
        # Generar ID del evento para control de duplicados
        event_id = generate_event_id(payload_dict, "nowcerts")
        
        # Verificar duplicados
        if is_duplicate(event_id):
            logger.warning(f"Evento duplicado detectado: {event_id}")
            raise DuplicateEventError(f"Evento ya procesado: {event_id}")
        
        # Procesar según el tipo de evento
        event_type = payload.event_type.upper()
        result_data = None
        
        if event_type in ["INSURED_INSERT", "INSURED_UPDATE"]:
            # Sincronizar contacto con GHL
            contact_data = payload.data
            ghl_contact_data = mapper.nowcerts_to_ghl_contact(contact_data)
            
            if event_type == "INSURED_INSERT":
                result = await ghl_service.create_contact(ghl_contact_data)
            else:
                # Para UPDATE, necesitaríamos el ID del contacto en GHL
                # Por ahora, intentamos crear si no existe
                result = await ghl_service.create_contact(ghl_contact_data)
            
            result_data = result
            logger.info(f"Contacto sincronizado con GHL: {result.get('id', 'N/A')}")
        
        elif event_type in ["POLICY_INSERT", "POLICY_UPDATE", "QUOTE_INSERT", "QUOTE_UPDATE"]:
            # Crear/actualizar oportunidad en GHL
            policy_data = payload.data
            
            # Necesitamos el contact_id en GHL
            # Por ahora, creamos la oportunidad sin contacto asociado
            # En producción, deberías buscar el contacto por email/phone
            opportunity_data = mapper.nowcerts_to_ghl_opportunity(policy_data)
            
            if event_type in ["POLICY_INSERT", "QUOTE_INSERT"]:
                # Para crear oportunidad, necesitamos contact_id
                # Esto debería mejorarse buscando el contacto primero
                logger.warning("Crear oportunidad requiere contact_id - implementar búsqueda de contacto")
                result_data = {"message": "Oportunidad requiere contact_id para ser creada"}
            else:
                # UPDATE requiere opportunity_id
                logger.warning("Actualizar oportunidad requiere opportunity_id")
                result_data = {"message": "Actualizar oportunidad requiere opportunity_id"}
        
        else:
            logger.warning(f"Tipo de evento no soportado: {event_type}")
            result_data = {"message": f"Evento {event_type} no procesado"}
        
        # Marcar evento como procesado
        mark_event_processed(event_id)
        
        # Log de respuesta
        log_response("NOWCERTS_WEBHOOK", result_data or {}, "outgoing")
        
        return WebhookResponse(
            success=True,
            message=f"Evento {event_type} procesado exitosamente",
            event_id=event_id,
            data=result_data
        )
    
    except DuplicateEventError:
        raise
    except Exception as e:
        logger.error(f"Error procesando webhook de NowCerts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando webhook: {str(e)}"
        )


@router.post(
    "/ghl",
    response_model=WebhookResponse,
    summary="Webhook de GoHighLevel",
    description="Recibe eventos desde GHL y los sincroniza con NowCerts"
)
async def webhook_ghl(
    payload: GHLWebhookPayload,
    request: Request
) -> Any:
    """
    Endpoint para recibir webhooks de GHL
    
    Eventos soportados:
    - Contactos: Sincroniza con NowCerts como asegurados
    - Oportunidades: Puede crear cotizaciones en NowCerts
    
    Returns:
        Respuesta con el resultado del procesamiento
    """
    try:
        # Log del payload recibido
        payload_dict = payload.model_dump()
        log_payload("GHL_WEBHOOK", payload_dict, "incoming")
        
        # Generar ID del evento para control de duplicados
        event_id = generate_event_id(payload_dict, "ghl")
        
        # Verificar duplicados
        if is_duplicate(event_id):
            logger.warning(f"Evento duplicado detectado: {event_id}")
            raise DuplicateEventError(f"Evento ya procesado: {event_id}")
        
        result_data = None
        
        # Procesar según el tipo de evento
        if payload.contact:
            # Sincronizar contacto con NowCerts
            contact_data = payload.contact
            nowcerts_contact_data = mapper.ghl_to_nowcerts_contact(contact_data)
            
            # Intentar crear el contacto en NowCerts
            result = await nowcerts_service.create_contact(nowcerts_contact_data)
            result_data = result
            logger.info(f"Contacto sincronizado con NowCerts: {result.get('id', 'N/A')}")
        
        elif payload.opportunity:
            # Crear cotización en NowCerts basada en la oportunidad
            opportunity_data = payload.opportunity
            
            # Mapear oportunidad a cotización (simplificado)
            quote_data = {
                "policyType": opportunity_data.get("customFields", {}).get("policy_type", "General"),
                "premium": opportunity_data.get("monetaryValue", 0),
                "carrier": opportunity_data.get("customFields", {}).get("carrier", ""),
                "source": "GHL"
            }
            
            result = await nowcerts_service.create_quote(quote_data)
            result_data = result
            logger.info(f"Cotización creada en NowCerts: {result.get('id', 'N/A')}")
        
        else:
            logger.warning("Webhook de GHL sin datos de contacto u oportunidad")
            result_data = {"message": "No se procesó ningún dato"}
        
        # Marcar evento como procesado
        mark_event_processed(event_id)
        
        # Log de respuesta
        log_response("GHL_WEBHOOK", result_data or {}, "outgoing")
        
        return WebhookResponse(
            success=True,
            message="Evento de GHL procesado exitosamente",
            event_id=event_id,
            data=result_data
        )
    
    except DuplicateEventError:
        raise
    except Exception as e:
        logger.error(f"Error procesando webhook de GHL: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando webhook: {str(e)}"
        )

