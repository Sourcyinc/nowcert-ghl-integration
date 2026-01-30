# Documentación Técnica Completa: Integración NowCerts + GoHighLevel

## 📋 Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Sincronización Bidireccional](#sincronización-bidireccional)
4. [Flujo Técnico Detallado](#flujo-técnico-detallado)
5. [Componentes del Sistema](#componentes-del-sistema)
6. [Gestión de Tokens y Autenticación](#gestión-de-tokens-y-autenticación)
7. [Control de Duplicados (Idempotencia)](#control-de-duplicados-idempotencia)
8. [Sistema de Reintentos](#sistema-de-reintentos)
9. [Mapeo de Datos](#mapeo-de-datos)
10. [Testing en Entorno Seguro](#testing-en-entorno-seguro)
11. [Mejoras Recomendadas](#mejoras-recomendadas)

---

## Resumen Ejecutivo

### ¿Qué hace esta implementación?

**SÍ, esta implementación permite sincronización bidireccional completa:**

✅ **GHL → NowCerts**: Cuando se crea/actualiza un prospecto/contacto en GHL, se sincroniza automáticamente como asegurado en NowCerts.

✅ **NowCerts → GHL**: Cuando se crea/actualiza un asegurado en NowCerts, se sincroniza automáticamente como contacto en GHL.

✅ **Pólizas/Cotizaciones**: Las pólizas y cotizaciones de NowCerts se convierten en oportunidades en GHL.

### Funcionalidades Principales

1. **Webhooks Bidireccionales**: Escucha eventos de ambos sistemas
2. **Sincronización Automática**: Procesa cambios en tiempo real
3. **Control de Duplicados**: Evita procesar el mismo evento múltiples veces
4. **Gestión Automática de Tokens**: Renueva tokens de NowCerts automáticamente
5. **Reintentos Inteligentes**: Maneja errores temporales con backoff exponencial
6. **Logging Completo**: Registra todos los eventos para auditoría

---

## Arquitectura del Sistema

### Diagrama de Flujo

```
┌─────────────┐                    ┌──────────────┐                    ┌─────────────┐
│  NowCerts   │                    │  Middleware  │                    │     GHL     │
│   (API)     │                    │   (FastAPI)  │                    │   (API)     │
└──────┬──────┘                    └──────┬──────┘                    └──────┬──────┘
       │                                    │                                    │
       │  1. Evento (INSURED_UPDATE)        │                                    │
       │───────────────────────────────────>│                                    │
       │                                    │                                    │
       │                                    │  2. Validar duplicado              │
       │                                    │  3. Mapear datos                   │
       │                                    │  4. Obtener token (auto)           │
       │                                    │                                    │
       │                                    │  5. Crear/Actualizar Contacto      │
       │                                    │───────────────────────────────────>│
       │                                    │                                    │
       │                                    │  6. Respuesta                      │
       │                                    │<───────────────────────────────────│
       │                                    │                                    │
       │  7. Confirmación                   │                                    │
       │<───────────────────────────────────│                                    │
       │                                    │                                    │
       │                                    │                                    │
       │                                    │  1. Evento (contact.created)       │
       │                                    │<───────────────────────────────────│
       │                                    │                                    │
       │                                    │  2. Validar duplicado              │
       │                                    │  3. Mapear datos                   │
       │                                    │  4. Obtener token (auto)           │
       │                                    │                                    │
       │  5. Crear/Actualizar Asegurado     │                                    │
       │<───────────────────────────────────│                                    │
       │                                    │                                    │
       │  6. Respuesta                      │                                    │
       │───────────────────────────────────>│                                    │
       │                                    │                                    │
       │                                    │  7. Confirmación                   │
       │                                    │───────────────────────────────────>│
```

### Componentes Principales

```
nowcert_ghl/
├── app/
│   ├── main.py                    # Punto de entrada FastAPI
│   ├── core/                      # Núcleo del sistema
│   │   ├── config.py              # Configuración centralizada
│   │   ├── exceptions.py          # Manejo de errores
│   │   ├── logger.py              # Sistema de logging
│   │   ├── idempotency.py         # Control de duplicados
│   │   └── retry.py               # Sistema de reintentos
│   ├── services/                  # Lógica de negocio
│   │   ├── token_manager.py       # Gestión de tokens NowCerts
│   │   ├── nowcerts_service.py    # Cliente API NowCerts
│   │   ├── ghl_service.py         # Cliente API GHL
│   │   └── mapper.py               # Transformación de datos
│   ├── models/                    # Validación de datos
│   │   └── webhooks.py            # Modelos Pydantic
│   └── api/                       # Endpoints HTTP
│       └── v1/
│           └── endpoints/
│               ├── webhooks.py    # POST /webhooks/nowcerts, /webhooks/ghl
│               └── sync.py        # POST /sync/manual
```

---

## Sincronización Bidireccional

### Flujo 1: NowCerts → GHL (Asegurado → Contacto)

**Escenario**: Un asegurado se crea o actualiza en NowCerts

1. **NowCerts envía webhook** a `POST /api/v1/webhooks/nowcerts`
   ```json
   {
     "event_type": "INSURED_INSERT",
     "timestamp": "2024-01-15T10:30:00Z",
     "data": {
       "firstName": "Juan",
       "lastName": "Pérez",
       "email": "juan@example.com",
       "phone": "+1234567890",
       "address": {
         "street": "123 Main St",
         "city": "Miami",
         "state": "FL",
         "zip": "33101"
       }
     }
   }
   ```

2. **Middleware procesa el evento**:
   - ✅ Valida el payload con Pydantic
   - ✅ Genera ID único del evento (hash SHA256)
   - ✅ Verifica si es duplicado (idempotencia)
   - ✅ Mapea datos de NowCerts a formato GHL
   - ✅ Obtiene token de NowCerts (si es necesario)
   - ✅ Crea contacto en GHL usando `ghl_service.create_contact()`
   - ✅ Marca evento como procesado
   - ✅ Registra logs

3. **GHL recibe y crea el contacto**:
   - El contacto aparece en GHL con los datos mapeados
   - Se asocia a la ubicación configurada (`GHL_LOCATION_ID`)

### Flujo 2: GHL → NowCerts (Contacto → Asegurado)

**Escenario**: Un prospecto/contacto se crea o actualiza en GHL

1. **GHL envía webhook** a `POST /api/v1/webhooks/ghl`
   ```json
   {
     "event": "contact.created",
     "contact": {
       "firstName": "María",
       "lastName": "González",
       "email": "maria@example.com",
       "phone": "+1987654321",
       "address1": "456 Oak Ave",
       "city": "Orlando",
       "state": "FL",
       "postalCode": "32801"
     },
     "locationId": "abc123"
   }
   ```

2. **Middleware procesa el evento**:
   - ✅ Valida el payload con Pydantic
   - ✅ Genera ID único del evento
   - ✅ Verifica duplicados
   - ✅ Mapea datos de GHL a formato NowCerts
   - ✅ Obtiene/renueva token de NowCerts automáticamente
   - ✅ Crea asegurado en NowCerts usando `nowcerts_service.create_contact()`
   - ✅ Marca evento como procesado
   - ✅ Registra logs

3. **NowCerts recibe y crea el asegurado**:
   - El asegurado aparece en NowCerts con los datos mapeados
   - Se marca la fuente como "GHL"

### Flujo 3: Pólizas/Cotizaciones → Oportunidades

**Escenario**: Una póliza se crea en NowCerts

1. **NowCerts envía webhook**:
   ```json
   {
     "event_type": "POLICY_INSERT",
     "data": {
       "policyNumber": "POL-12345",
       "policyType": "Auto",
       "premium": 1200.00,
       "carrier": "State Farm",
       "effectiveDate": "2024-02-01",
       "expirationDate": "2025-02-01"
     }
   }
   ```

2. **Middleware convierte a oportunidad GHL**:
   - Mapea tipo de póliza a pipeline
   - Convierte premium a `monetaryValue`
   - Crea campos personalizados con metadata
   - **Nota**: Requiere `contact_id` en GHL (ver mejoras)

---

## Flujo Técnico Detallado

### Procesamiento de Webhook (Paso a Paso)

#### 1. Recepción del Request

```python
# app/api/v1/endpoints/webhooks.py

@router.post("/nowcerts")
async def webhook_nowcerts(payload: NowCertsWebhookPayload, request: Request):
```

**Qué sucede**:
- FastAPI recibe el HTTP POST
- Pydantic valida automáticamente el payload contra `NowCertsWebhookPayload`
- Si hay errores de validación, retorna 422 (Unprocessable Entity)

#### 2. Logging Inicial

```python
payload_dict = payload.model_dump()
log_payload("NOWCERTS_WEBHOOK", payload_dict, "incoming")
```

**Qué sucede**:
- Convierte el modelo Pydantic a diccionario
- Registra el payload completo en el logger
- Formato: `[INCOMING] NOWCERTS_WEBHOOK - Payload: {...}`

#### 3. Generación de ID de Evento (Idempotencia)

```python
event_id = generate_event_id(payload_dict, "nowcerts")
```

**Qué sucede**:
- Crea un hash SHA256 del payload + fuente
- Formato: `nowcerts_<hash_64_chars>`
- Este ID es único para cada evento específico

**Ejemplo**:
```python
# Payload idéntico siempre genera el mismo hash
event_id = "nowcerts_a1b2c3d4e5f6..."
```

#### 4. Verificación de Duplicados

```python
if is_duplicate(event_id):
    raise DuplicateEventError("Evento ya procesado")
```

**Qué sucede**:
- Busca el `event_id` en el cache en memoria
- Si existe y no ha expirado (24 horas), lanza excepción 409
- Si no existe o expiró, continúa el procesamiento

**Por qué es importante**:
- Evita procesar el mismo evento múltiples veces
- Previene duplicados en los sistemas destino
- Protege contra webhooks duplicados de los proveedores

#### 5. Procesamiento según Tipo de Evento

```python
if event_type in ["INSURED_INSERT", "INSURED_UPDATE"]:
    # Mapear y sincronizar contacto
    ghl_contact_data = mapper.nowcerts_to_ghl_contact(contact_data)
    result = await ghl_service.create_contact(ghl_contact_data)
```

**Qué sucede**:
- Identifica el tipo de evento
- Selecciona el mapeador correspondiente
- Transforma los datos al formato destino
- Llama al servicio correspondiente

#### 6. Mapeo de Datos

```python
# app/services/mapper.py

def nowcerts_to_ghl_contact(nowcerts_data):
    return {
        "firstName": nowcerts_data.get("firstName", ""),
        "lastName": nowcerts_data.get("lastName", ""),
        # ... transformaciones
    }
```

**Qué sucede**:
- Transforma estructura de datos de NowCerts a GHL
- Maneja campos opcionales con valores por defecto
- Preserva la información relevante

#### 7. Llamada a API Externa (con Reintentos)

```python
# app/services/ghl_service.py

async def create_contact(contact_data):
    return await self._make_request("POST", "/contacts/", contact_data)
```

**Qué sucede**:
- Construye la URL completa
- Obtiene headers de autenticación
- Ejecuta la petición HTTP
- Si falla, el sistema de reintentos lo maneja automáticamente

#### 8. Sistema de Reintentos

```python
# app/core/retry.py

async def retry_with_backoff(func, max_retries=3, ...):
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except ExternalAPIError as e:
            if attempt < max_retries:
                delay = initial_delay * (backoff_factor ** attempt)
                await asyncio.sleep(delay)
```

**Qué sucede**:
- Intento 1: Inmediato
- Intento 2: Espera 1 segundo (1.0 * 2^0)
- Intento 3: Espera 2 segundos (1.0 * 2^1)
- Intento 4: Espera 4 segundos (1.0 * 2^2)

**No reintenta**:
- Errores 4xx (excepto 429 - Too Many Requests)
- Errores de validación

#### 9. Marcar Evento como Procesado

```python
mark_event_processed(event_id)
```

**Qué sucede**:
- Guarda el `event_id` en el cache con timestamp
- El evento queda protegido contra duplicados por 24 horas

#### 10. Logging de Respuesta

```python
log_response("NOWCERTS_WEBHOOK", result_data, "outgoing")
```

**Qué sucede**:
- Registra la respuesta del sistema destino
- Formato: `[OUTGOING] NOWCERTS_WEBHOOK - Response: {...}`

#### 11. Retorno de Respuesta HTTP

```python
return WebhookResponse(
    success=True,
    message="Evento procesado exitosamente",
    event_id=event_id,
    data=result_data
)
```

**Qué sucede**:
- FastAPI serializa la respuesta a JSON
- Retorna HTTP 200 con el resultado
- El sistema origen (NowCerts/GHL) recibe confirmación

---

## Componentes del Sistema

### 1. Token Manager (`app/services/token_manager.py`)

**Responsabilidad**: Gestionar el ciclo de vida de tokens de NowCerts

**Funcionamiento**:

```python
class TokenManager:
    _access_token: str          # Token actual
    _refresh_token: str         # Token para renovación
    _token_expires_at: datetime  # Fecha de expiración
```

**Flujo de Autenticación**:

1. **Login Inicial**:
   ```python
   POST /api/auth/login
   {
     "username": "...",
     "password": "..."
   }
   ```
   - Retorna: `access_token`, `refresh_token`, `expires_in`

2. **Renovación Automática**:
   - Antes de cada petición, verifica si el token expira pronto
   - Si expira en menos de 5 minutos (configurable), renueva
   - Usa `refresh_token` si está disponible
   - Si falla, hace login completo

3. **Manejo de Errores 401**:
   - Si una petición retorna 401 (Unauthorized)
   - Fuerza renovación del token
   - Reintenta la petición automáticamente

**Ventajas**:
- ✅ Transparente para el resto del sistema
- ✅ No requiere intervención manual
- ✅ Maneja expiración proactivamente

### 2. NowCerts Service (`app/services/nowcerts_service.py`)

**Responsabilidad**: Cliente HTTP para API de NowCerts

**Métodos Principales**:
- `create_contact()`: Crea asegurado
- `update_contact()`: Actualiza asegurado
- `create_policy()`: Crea póliza
- `create_quote()`: Crea cotización

**Características**:
- Usa `TokenManager` para autenticación automática
- Implementa reintentos con backoff
- Maneja errores HTTP apropiadamente

### 3. GHL Service (`app/services/ghl_service.py`)

**Responsabilidad**: Cliente HTTP para API de GoHighLevel

**Métodos Principales**:
- `create_contact()`: Crea contacto
- `update_contact()`: Actualiza contacto
- `create_opportunity()`: Crea oportunidad
- `update_opportunity()`: Actualiza oportunidad

**Características**:
- Autenticación con API Key (Bearer Token)
- Soporta `locationId` como parámetro
- Implementa reintentos

### 4. Data Mapper (`app/services/mapper.py`)

**Responsabilidad**: Transformar datos entre formatos

**Métodos**:
- `ghl_to_nowcerts_contact()`: GHL → NowCerts
- `nowcerts_to_ghl_contact()`: NowCerts → GHL
- `nowcerts_to_ghl_opportunity()`: Póliza → Oportunidad

**Ejemplo de Transformación**:

```python
# Entrada (GHL)
{
  "firstName": "Juan",
  "address1": "123 Main St",
  "postalCode": "33101"
}

# Salida (NowCerts)
{
  "firstName": "Juan",
  "address": {
    "street": "123 Main St",
    "zip": "33101"
  }
}
```

### 5. Idempotency Manager (`app/core/idempotency.py`)

**Responsabilidad**: Prevenir procesamiento duplicado

**Algoritmo**:
1. Genera hash SHA256 del payload + fuente
2. Almacena en cache en memoria con timestamp
3. Verifica antes de procesar cada evento
4. Limpia eventos expirados (24 horas)

**Limitación Actual**:
- Cache en memoria (se pierde al reiniciar)
- **Mejora recomendada**: Usar Redis o base de datos

### 6. Retry Manager (`app/core/retry.py`)

**Responsabilidad**: Reintentar peticiones fallidas

**Estrategia**: Backoff Exponencial

```
Intento 1: 0 segundos
Intento 2: 1 segundo (1.0 * 2^0)
Intento 3: 2 segundos (1.0 * 2^1)
Intento 4: 4 segundos (1.0 * 2^2)
```

**Configuración**:
- `MAX_RETRIES`: 3 (4 intentos totales)
- `RETRY_BACKOFF_FACTOR`: 2.0
- `RETRY_INITIAL_DELAY`: 1.0

---

## Gestión de Tokens y Autenticación

### Flujo Completo de Autenticación

```
┌─────────────────┐
│  TokenManager    │
└────────┬─────────┘
         │
         │ 1. get_access_token()
         │
         ├─ ¿Token existe?
         │  └─ NO → Login completo
         │
         ├─ ¿Token expira pronto? (< 5 min)
         │  └─ SÍ → Refresh token
         │     └─ ¿Refresh falla?
         │        └─ SÍ → Login completo
         │
         └─ Retorna token válido
```

### Código de Ejemplo

```python
# Antes de cada petición a NowCerts
access_token = await token_manager.get_access_token()

# TokenManager internamente:
# 1. Verifica si _token_expires_at - now < 5 minutos
# 2. Si es así, llama a _refresh_access_token()
# 3. Si refresh falla, llama a _login()
# 4. Actualiza _access_token, _refresh_token, _token_expires_at
# 5. Retorna el token válido
```

### Seguridad

- ✅ Tokens almacenados en memoria (no en disco)
- ✅ Renovación proactiva (antes de expirar)
- ✅ Manejo automático de expiración
- ✅ No expone tokens en logs

---

## Control de Duplicados (Idempotencia)

### ¿Por qué es necesario?

**Problema**: Los sistemas pueden enviar el mismo webhook múltiples veces:
- Reintentos automáticos del proveedor
- Errores de red que causan duplicados
- Reprocesamiento manual

**Solución**: Sistema de idempotencia basado en hash

### Algoritmo

```python
def generate_event_id(payload, source):
    # 1. Serializar payload a JSON ordenado
    event_str = json.dumps(payload, sort_keys=True)
    
    # 2. Agregar fuente
    event_data = {"source": source, "payload": event_str}
    
    # 3. Generar hash SHA256
    event_hash = hashlib.sha256(
        json.dumps(event_data).encode()
    ).hexdigest()
    
    # 4. Retornar ID único
    return f"{source}_{event_hash}"
```

### Ejemplo

```python
# Mismo payload siempre genera mismo hash
payload1 = {"name": "Juan", "email": "juan@example.com"}
payload2 = {"name": "Juan", "email": "juan@example.com"}

id1 = generate_event_id(payload1, "nowcerts")
id2 = generate_event_id(payload2, "nowcerts")

assert id1 == id2  # True - mismo hash
```

### Verificación

```python
# Antes de procesar
if is_duplicate(event_id):
    raise DuplicateEventError("Ya procesado")

# Después de procesar exitosamente
mark_event_processed(event_id)
```

### Limitaciones Actuales

- ⚠️ Cache en memoria (se pierde al reiniciar)
- ⚠️ No persiste entre reinicios
- ✅ Funciona perfectamente durante ejecución continua

**Mejora recomendada**: Usar Redis o base de datos para persistencia

---

## Sistema de Reintentos

### Estrategia: Exponential Backoff

**Fórmula**: `delay = initial_delay * (backoff_factor ^ attempt)`

**Ejemplo con configuración por defecto**:
- `initial_delay = 1.0`
- `backoff_factor = 2.0`
- `max_retries = 3`

```
Intento 1: 0 segundos (inmediato)
Intento 2: 1.0 * (2.0 ^ 0) = 1 segundo
Intento 3: 1.0 * (2.0 ^ 1) = 2 segundos
Intento 4: 1.0 * (2.0 ^ 2) = 4 segundos
```

### ¿Cuándo Reintenta?

✅ **SÍ reintenta**:
- Errores 5xx (Server Error)
- Errores 429 (Too Many Requests)
- Errores de conexión (timeout, network error)

❌ **NO reintenta**:
- Errores 4xx (excepto 429)
- Errores de validación
- Errores de autenticación (401) - se maneja separadamente

### Código

```python
async def retry_with_backoff(func, max_retries=3, ...):
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except ExternalAPIError as e:
            # No reintentar errores 4xx (excepto 429)
            if 400 <= e.status_code < 500 and e.status_code != 429:
                raise
            
            if attempt < max_retries:
                delay = initial_delay * (backoff_factor ** attempt)
                await asyncio.sleep(delay)
            else:
                raise  # Todos los intentos fallaron
```

---

## Mapeo de Datos

### Mapeo: GHL → NowCerts (Contacto)

| Campo GHL | Campo NowCerts | Transformación |
|-----------|----------------|----------------|
| `firstName` | `firstName` | Directo |
| `lastName` | `lastName` | Directo |
| `email` | `email` | Directo |
| `phone` | `phone` | Directo |
| `address1` | `address.street` | Anidado |
| `city` | `address.city` | Anidado |
| `state` | `address.state` | Anidado |
| `postalCode` | `address.zip` | Anidado |
| `source` | `source` | Directo |

### Mapeo: NowCerts → GHL (Contacto)

| Campo NowCerts | Campo GHL | Transformación |
|----------------|-----------|----------------|
| `firstName` | `firstName` | Directo |
| `lastName` | `lastName` | Directo |
| `email` | `email` | Directo |
| `phone` | `phone` | Directo |
| `address.street` | `address1` | Desanidado |
| `address.city` | `city` | Desanidado |
| `address.state` | `state` | Desanidado |
| `address.zip` | `postalCode` | Desanidado |
| `source` | `source` | Directo |

### Mapeo: NowCerts → GHL (Oportunidad)

| Campo NowCerts | Campo GHL | Transformación |
|----------------|-----------|----------------|
| `policyType` | `name` (prefijo) | "Auto Policy - POL-123" |
| `premium` | `monetaryValue` | Directo |
| `policyNumber` | `customFields.policy_number` | Campo personalizado |
| `carrier` | `customFields.carrier` | Campo personalizado |
| `effectiveDate` | `customFields.effective_date` | Campo personalizado |
| `expirationDate` | `customFields.expiration_date` | Campo personalizado |

---

## Testing en Entorno Seguro

### Configuración de Entorno de Pruebas

#### 1. Variables de Entorno de Pruebas

Crea un archivo `.env.test`:

```env
# Servidor de prueba
HOST=127.0.0.1
PORT=8001
DEBUG=True

# NowCerts (Sandbox/Test)
NOWCERTS_BASE_URL=https://sandbox-api.nowcerts.com
NOWCERTS_USERNAME=test_user
NOWCERTS_PASSWORD=test_password

# GHL (Test Account)
GHL_BASE_URL=https://services.leadconnectorhq.com
GHL_API_KEY=test_api_key
GHL_LOCATION_ID=test_location_id

# Logging detallado
LOG_LEVEL=DEBUG
LOG_FILE=logs/test.log
```

#### 2. Usar ngrok para Webhooks Locales

**Problema**: Los webhooks requieren URL pública HTTPS

**Solución**: Usar ngrok para crear túnel

```bash
# Instalar ngrok
# https://ngrok.com/download

# Iniciar túnel
ngrok http 8001

# Obtendrás una URL como:
# https://abc123.ngrok.io -> http://localhost:8001
```

**Configurar webhooks**:
- NowCerts: `https://abc123.ngrok.io/api/v1/webhooks/nowcerts`
- GHL: `https://abc123.ngrok.io/api/v1/webhooks/ghl`

### Testing Manual Paso a Paso

#### Test 1: Health Check

```bash
curl http://localhost:8001/health
```

**Respuesta esperada**:
```json
{
  "status": "healthy",
  "service": "NowCerts GHL Integration API",
  "version": "1.0.0"
}
```

#### Test 2: Webhook NowCerts (Simulado)

```bash
curl -X POST http://localhost:8001/api/v1/webhooks/nowcerts \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "INSURED_INSERT",
    "timestamp": "2024-01-15T10:30:00Z",
    "data": {
      "firstName": "Test",
      "lastName": "User",
      "email": "test@example.com",
      "phone": "+1234567890",
      "address": {
        "street": "123 Test St",
        "city": "Miami",
        "state": "FL",
        "zip": "33101"
      }
    }
  }'
```

**Qué verificar**:
1. ✅ Respuesta HTTP 200
2. ✅ `success: true` en la respuesta
3. ✅ Logs muestran el procesamiento
4. ✅ Contacto creado en GHL (verificar en dashboard)

#### Test 3: Webhook GHL (Simulado)

```bash
curl -X POST http://localhost:8001/api/v1/webhooks/ghl \
  -H "Content-Type: application/json" \
  -d '{
    "event": "contact.created",
    "contact": {
      "firstName": "Test",
      "lastName": "Contact",
      "email": "test2@example.com",
      "phone": "+1987654321",
      "address1": "456 Test Ave",
      "city": "Orlando",
      "state": "FL",
      "postalCode": "32801"
    },
    "locationId": "test_location"
  }'
```

**Qué verificar**:
1. ✅ Respuesta HTTP 200
2. ✅ `success: true`
3. ✅ Logs muestran el procesamiento
4. ✅ Asegurado creado en NowCerts (verificar en dashboard)

#### Test 4: Sincronización Manual

```bash
curl -X POST http://localhost:8001/api/v1/sync/manual \
  -H "Content-Type: application/json" \
  -d '{
    "source": "nowcerts",
    "entity_type": "contact",
    "direction": "to_ghl",
    "data": {
      "firstName": "Manual",
      "lastName": "Sync",
      "email": "manual@example.com",
      "phone": "+1555555555"
    }
  }'
```

#### Test 5: Verificar Idempotencia (Duplicados)

```bash
# Enviar el mismo webhook dos veces
curl -X POST http://localhost:8001/api/v1/webhooks/nowcerts \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "INSURED_INSERT",
    "data": {
      "firstName": "Duplicate",
      "email": "duplicate@example.com"
    }
  }'

# Enviar exactamente el mismo payload otra vez
curl -X POST http://localhost:8001/api/v1/webhooks/nowcerts \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "INSURED_INSERT",
    "data": {
      "firstName": "Duplicate",
      "email": "duplicate@example.com"
    }
  }'
```

**Respuesta esperada en segunda llamada**:
```json
{
  "detail": "Evento ya procesado: nowcerts_<hash>"
}
```
**Status Code**: 409 (Conflict)

### Testing con Postman

#### Colección de Postman

1. **Crear colección**: "NowCerts GHL Integration"

2. **Variables de entorno**:
   - `base_url`: `http://localhost:8001`
   - `ngrok_url`: `https://abc123.ngrok.io` (si usas ngrok)

3. **Requests**:

   **Health Check**:
   ```
   GET {{base_url}}/health
   ```

   **Webhook NowCerts**:
   ```
   POST {{base_url}}/api/v1/webhooks/nowcerts
   Body (JSON):
   {
     "event_type": "INSURED_INSERT",
     "data": { ... }
   }
   ```

   **Webhook GHL**:
   ```
   POST {{base_url}}/api/v1/webhooks/ghl
   Body (JSON):
   {
     "event": "contact.created",
     "contact": { ... }
   }
   ```

### Testing Automatizado (Futuro)

#### Estructura de Tests (Pytest)

```python
# tests/test_webhooks.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_webhook_nowcerts():
    response = client.post(
        "/api/v1/webhooks/nowcerts",
        json={
            "event_type": "INSURED_INSERT",
            "data": {
                "firstName": "Test",
                "email": "test@example.com"
            }
        }
    )
    assert response.status_code == 200
    assert response.json()["success"] == True

def test_duplicate_event():
    payload = {"event_type": "INSURED_INSERT", "data": {...}}
    
    # Primera llamada
    response1 = client.post("/api/v1/webhooks/nowcerts", json=payload)
    assert response1.status_code == 200
    
    # Segunda llamada (duplicado)
    response2 = client.post("/api/v1/webhooks/nowcerts", json=payload)
    assert response2.status_code == 409  # Conflict
```

### Monitoreo Durante Testing

#### 1. Logs en Tiempo Real

```bash
# Ver logs en consola
tail -f logs/test.log

# O si no hay archivo, ver en consola del servidor
uvicorn app.main:app --reload --log-level debug
```

#### 2. Verificar en Dashboards

- **GHL Dashboard**: Verificar que contactos se crean
- **NowCerts Dashboard**: Verificar que asegurados se crean
- **Logs del Middleware**: Verificar procesamiento

#### 3. Usar Swagger UI

```
http://localhost:8001/docs
```

- Probar endpoints directamente desde el navegador
- Ver esquemas de request/response
- Validar payloads

### Checklist de Testing

- [ ] Health check funciona
- [ ] Webhook NowCerts crea contacto en GHL
- [ ] Webhook GHL crea asegurado en NowCerts
- [ ] Duplicados son rechazados (409)
- [ ] Logs se registran correctamente
- [ ] Tokens se renuevan automáticamente
- [ ] Reintentos funcionan en caso de error
- [ ] Mapeo de datos es correcto
- [ ] Errores se manejan apropiadamente

---

## Mejoras Recomendadas

### 1. Búsqueda de Contactos Existentes

**Problema Actual**: 
- En `INSURED_UPDATE`, no sabemos el `contact_id` en GHL
- Siempre intenta crear nuevo contacto

**Solución**:

```python
# Agregar método en GHLService
async def find_contact_by_email(self, email: str) -> Optional[str]:
    """Busca contacto por email y retorna su ID"""
    endpoint = "/contacts/search"
    params = {"locationId": self.location_id, "email": email}
    response = await self._make_request("GET", endpoint, params=params)
    contacts = response.get("contacts", [])
    return contacts[0].get("id") if contacts else None

# Usar en webhook
if event_type == "INSURED_UPDATE":
    # Buscar contacto existente
    contact_id = await ghl_service.find_contact_by_email(contact_data.get("email"))
    
    if contact_id:
        # Actualizar existente
        result = await ghl_service.update_contact(contact_id, ghl_contact_data)
    else:
        # Crear nuevo
        result = await ghl_service.create_contact(ghl_contact_data)
```

### 2. Persistencia de Idempotencia

**Problema Actual**: Cache en memoria se pierde al reiniciar

**Solución**: Usar Redis

```python
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def is_duplicate(event_id: str) -> bool:
    key = f"event:{event_id}"
    exists = redis_client.exists(key)
    return exists == 1

def mark_event_processed(event_id: str):
    key = f"event:{event_id}"
    redis_client.setex(key, 86400, "processed")  # 24 horas
```

### 3. Base de Datos para Mapeo de IDs

**Problema**: No hay relación entre IDs de NowCerts y GHL

**Solución**: Tabla de mapeo

```sql
CREATE TABLE contact_mapping (
    id SERIAL PRIMARY KEY,
    nowcerts_contact_id VARCHAR(255),
    ghl_contact_id VARCHAR(255),
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 4. Webhook Signature Verification

**Seguridad**: Verificar firma de webhooks

```python
import hmac
import hashlib

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)
```

### 5. Rate Limiting

**Protección**: Limitar requests por minuto

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/webhooks/nowcerts")
@limiter.limit("100/minute")
async def webhook_nowcerts(...):
    ...
```

### 6. Métricas y Monitoreo

**Observabilidad**: Agregar métricas

```python
from prometheus_client import Counter, Histogram

webhook_requests = Counter('webhook_requests_total', 'Total webhook requests', ['source', 'status'])
webhook_duration = Histogram('webhook_duration_seconds', 'Webhook processing time', ['source'])
```

---

## Conclusión

Esta implementación proporciona:

✅ **Sincronización bidireccional completa** entre NowCerts y GHL
✅ **Arquitectura robusta** con manejo de errores
✅ **Control de duplicados** para prevenir procesamiento múltiple
✅ **Gestión automática de tokens** sin intervención manual
✅ **Sistema de reintentos** para manejar errores temporales
✅ **Logging completo** para debugging y auditoría

**Para producción**, considera implementar las mejoras recomendadas, especialmente:
- Búsqueda de contactos existentes
- Persistencia de idempotencia (Redis)
- Base de datos para mapeo de IDs
- Verificación de firmas de webhooks

---

**Última actualización**: 2024-01-15

