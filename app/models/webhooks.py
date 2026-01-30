"""
Modelos para webhooks de NowCerts y GHL
"""
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class NowCertsWebhookPayload(BaseModel):
    """Modelo para payload de webhook de NowCerts"""
    event_type: str = Field(..., description="Tipo de evento (INSURED_INSERT, POLICY_UPDATE, etc.)")
    timestamp: Optional[str] = Field(None, description="Timestamp del evento")
    data: Dict[str, Any] = Field(..., description="Datos del evento")
    
    class Config:
        extra = "allow"  # Permitir campos adicionales


class GHLWebhookPayload(BaseModel):
    """Modelo para payload de webhook de GHL"""
    event: Optional[str] = Field(None, description="Tipo de evento")
    contact: Optional[Dict[str, Any]] = Field(None, description="Datos del contacto")
    opportunity: Optional[Dict[str, Any]] = Field(None, description="Datos de oportunidad")
    locationId: Optional[str] = Field(None, description="ID de la ubicación")
    
    class Config:
        extra = "allow"


class WebhookResponse(BaseModel):
    """Respuesta estándar para webhooks"""
    success: bool = Field(..., description="Indica si el procesamiento fue exitoso")
    message: str = Field(..., description="Mensaje descriptivo")
    event_id: Optional[str] = Field(None, description="ID del evento procesado")
    data: Optional[Dict[str, Any]] = Field(None, description="Datos adicionales de respuesta")


class SyncRequest(BaseModel):
    """Modelo para solicitud de sincronización manual"""
    source: Literal["nowcerts", "ghl"] = Field(..., description="Fuente de los datos")
    entity_type: Literal["contact", "policy", "quote", "opportunity"] = Field(
        ..., 
        description="Tipo de entidad a sincronizar"
    )
    entity_id: Optional[str] = Field(None, description="ID de la entidad (opcional)")
    direction: Literal["to_ghl", "to_nowcerts"] = Field(
        ..., 
        description="Dirección de la sincronización"
    )
    data: Optional[Dict[str, Any]] = Field(None, description="Datos a sincronizar (opcional)")


class SyncResponse(BaseModel):
    """Respuesta de sincronización manual"""
    success: bool = Field(..., description="Indica si la sincronización fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo")
    source_id: Optional[str] = Field(None, description="ID en el sistema origen")
    target_id: Optional[str] = Field(None, description="ID en el sistema destino")
    data: Optional[Dict[str, Any]] = Field(None, description="Datos sincronizados")

