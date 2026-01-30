# Servicio API: Integración NowCerts + GoHighLevel

Middleware profesional para integración bidireccional entre NowCerts y GoHighLevel (GHL), implementando webhooks, sincronización de datos, control de duplicados y gestión automática de tokens.

## 🏗️ Arquitectura

```
NowCerts → Webhook → Middleware → API de GHL
GHL → Webhook/Workflow → Middleware → API de NowCerts
```

## ✨ Características

- ✅ **Webhooks bidireccionales**: Recibe eventos de NowCerts y GHL
- ✅ **Gestión automática de tokens**: Renovación automática de tokens de NowCerts
- ✅ **Control de duplicados**: Sistema de idempotencia para evitar procesamiento duplicado
- ✅ **Reintentos con backoff exponencial**: Manejo robusto de errores temporales
- ✅ **Logging completo**: Registro de payloads y respuestas para debugging
- ✅ **Sincronización manual**: Endpoint para pruebas y sincronización manual
- ✅ **Mapeo de datos**: Conversión automática entre formatos de NowCerts y GHL

## 📋 Requisitos

- Python 3.8+
- Cuenta de NowCerts con acceso a API
- Cuenta de GoHighLevel con API Key

## 🚀 Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Copia el archivo `.env.example` a `.env`:

```bash
# Windows (PowerShell)
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Edita el archivo `.env` y configura las variables necesarias:

```env
# NowCerts
NOWCERTS_USERNAME=tu_usuario
NOWCERTS_PASSWORD=tu_contraseña

# GoHighLevel
GHL_API_KEY=tu_api_key
GHL_LOCATION_ID=tu_location_id
```

### 3. Ejecutar el servidor

```bash
# Desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Producción
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 📚 Endpoints

### Webhooks

#### POST `/api/v1/webhooks/nowcerts`
Recibe eventos desde NowCerts y los sincroniza con GHL.

**Eventos soportados:**
- `INSURED_INSERT` / `INSURED_UPDATE`: Sincroniza contactos con GHL
- `POLICY_INSERT` / `POLICY_UPDATE`: Crea/actualiza oportunidades en GHL
- `QUOTE_INSERT` / `QUOTE_UPDATE`: Crea/actualiza oportunidades en GHL

**Ejemplo de payload:**
```json
{
  "event_type": "INSURED_INSERT",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "firstName": "Juan",
    "lastName": "Pérez",
    "email": "juan@example.com",
    "phone": "+1234567890"
  }
}
```

#### POST `/api/v1/webhooks/ghl`
Recibe eventos desde GHL y los sincroniza con NowCerts.

**Ejemplo de payload:**
```json
{
  "event": "contact.created",
  "contact": {
    "firstName": "Juan",
    "lastName": "Pérez",
    "email": "juan@example.com",
    "phone": "+1234567890"
  },
  "locationId": "abc123"
}
```

### Sincronización Manual

#### POST `/api/v1/sync/manual`
Endpoint para pruebas y sincronización manual de datos.

**Ejemplo de request:**
```json
{
  "source": "nowcerts",
  "entity_type": "contact",
  "direction": "to_ghl",
  "data": {
    "firstName": "Juan",
    "lastName": "Pérez",
    "email": "juan@example.com",
    "phone": "+1234567890"
  }
}
```

### Health Check

#### GET `/health`
Verifica el estado del servicio.

## 🔧 Configuración en NowCerts

1. Ingresar a NowCerts como administrador
2. Ir a **Agency Profile → Configure API**
3. Configurar el **Webhook URL** apuntando a: `https://tu-dominio.com/api/v1/webhooks/nowcerts`
4. Seleccionar eventos:
   - `INSURED_INSERT` / `INSURED_UPDATE`
   - `POLICY_INSERT` / `POLICY_UPDATE`
   - `QUOTE_INSERT` / `QUOTE_UPDATE`
5. Guardar cambios

## 🔧 Configuración en GoHighLevel

### Opción A - Pruebas rápidas:

1. Crear un **Workflow** en GHL
2. Agregar acción **Custom Webhook**
3. Configurar URL: `https://tu-dominio.com/api/v1/webhooks/ghl`
4. Enviar datos JSON al middleware

### Opción B - Producto multincliente:

Usar OAuth de GHL y Webhooks oficiales para manejar múltiples ubicaciones/clientes.

## 📊 Mapeo de Datos

### GHL → NowCerts (Contacto/Asegurado)
- `firstName` / `lastName` → Nombre / Apellido
- `email` → Email
- `phone` → Teléfono
- `address1`, `city`, `state`, `postalCode` → Dirección
- `source` → Fuente del lead

### NowCerts → GHL (Oportunidad)
- `policyType` → Pipeline/Stage
- `premium` → `monetaryValue`
- `carrier` → Campo personalizado
- `effectiveDate` / `expirationDate` → Campos personalizados

## 🛡️ Características de Seguridad

- **Control de duplicados**: Sistema de idempotencia basado en hash SHA256
- **Gestión segura de tokens**: Tokens almacenados en memoria, renovación automática
- **Logging de payloads**: Registro completo para auditoría y debugging
- **Reintentos inteligentes**: No reintenta errores 4xx (excepto 429)

## 📝 Logs

Los logs se registran en:
- **Consola**: Por defecto
- **Archivo**: Si `LOG_FILE` está configurado en `.env`

Formato de logs:
```
2024-01-01 12:00:00 - NowCerts GHL Integration API - INFO - [INCOMING] NOWCERTS_WEBHOOK - Payload: {...}
```

## 🧪 Pruebas

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Webhook de NowCerts (ejemplo)
```bash
curl -X POST http://localhost:8000/api/v1/webhooks/nowcerts \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "INSURED_INSERT",
    "data": {
      "firstName": "Juan",
      "lastName": "Pérez",
      "email": "juan@example.com"
    }
  }'
```

### 3. Sincronización Manual
```bash
curl -X POST http://localhost:8000/api/v1/sync/manual \
  -H "Content-Type: application/json" \
  -d '{
    "source": "nowcerts",
    "entity_type": "contact",
    "direction": "to_ghl",
    "data": {
      "firstName": "Juan",
      "lastName": "Pérez",
      "email": "juan@example.com"
    }
  }'
```

## 📖 Documentación API

Una vez que el servidor esté corriendo, accede a:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔍 Troubleshooting

### Error: "Token expirado"
- El sistema renueva tokens automáticamente
- Verifica que `NOWCERTS_USERNAME` y `NOWCERTS_PASSWORD` estén correctos

### Error: "Evento duplicado"
- Es normal si el mismo evento se envía múltiples veces
- El sistema previene procesamiento duplicado automáticamente

### Error de conexión
- Verifica que las URLs de las APIs estén correctas
- Revisa la conectividad de red
- Los reintentos se ejecutan automáticamente

## 📁 Estructura del Proyecto

```
nowcert_ghl/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Aplicación principal
│   ├── core/                   # Configuración y utilidades
│   │   ├── config.py          # Configuración centralizada
│   │   ├── exceptions.py      # Excepciones personalizadas
│   │   ├── logger.py          # Sistema de logging
│   │   ├── idempotency.py    # Control de duplicados
│   │   └── retry.py           # Sistema de reintentos
│   ├── services/              # Lógica de negocio
│   │   ├── token_manager.py  # Gestión de tokens NowCerts
│   │   ├── nowcerts_service.py # Servicio NowCerts
│   │   ├── ghl_service.py     # Servicio GHL
│   │   └── mapper.py          # Mapeo de datos
│   ├── models/                # Modelos Pydantic
│   │   └── webhooks.py        # Modelos de webhooks
│   └── api/                   # Endpoints
│       └── v1/
│           ├── __init__.py
│           └── endpoints/
│               ├── webhooks.py # Endpoints de webhooks
│               └── sync.py     # Endpoint de sincronización
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 Despliegue

### Recomendaciones para producción:

1. **HTTPS obligatorio**: Los webhooks requieren HTTPS
2. **Variables de entorno**: Usar un gestor de secretos (AWS Secrets Manager, etc.)
3. **Base de datos**: Considerar usar Redis o PostgreSQL para idempotencia en lugar de memoria
4. **Monitoreo**: Implementar logging estructurado y métricas
5. **Rate limiting**: Considerar implementar rate limiting para los endpoints

### Ejemplo con Docker:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📄 Licencia

Este proyecto es parte de Sourcy Services.

## 🤝 Soporte

Para problemas o preguntas, contacta al equipo de desarrollo.

