# Guía Práctica de Testing - Integración NowCerts + GHL

## 🎯 Objetivo

Esta guía te permitirá testear la integración de forma segura sin afectar datos de producción.

---

## 📋 Prerequisitos

1. ✅ Python 3.8+ instalado
2. ✅ Dependencias instaladas (`pip install -r requirements.txt`)
3. ✅ Variables de entorno configuradas (`.env`)
4. ✅ Acceso a cuentas de prueba de NowCerts y GHL
5. ✅ ngrok instalado (para webhooks locales)

---

## 🚀 Configuración Inicial

### 1. Configurar Entorno de Pruebas

Crea un archivo `.env.test`:

```bash
# Copiar archivo de ejemplo
cp env.example .env.test
```

Edita `.env.test` con credenciales de prueba:

```env
# Servidor
HOST=127.0.0.1
PORT=8001
DEBUG=True

# NowCerts (Sandbox/Test)
NOWCERTS_BASE_URL=https://sandbox-api.nowcerts.com
NOWCERTS_USERNAME=test_user
NOWCERTS_PASSWORD=test_password

# GHL (Test Account)
GHL_BASE_URL=https://services.leadconnectorhq.com
GHL_API_KEY=test_api_key_ghl
GHL_LOCATION_ID=test_location_id

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=logs/test.log
```

### 2. Iniciar Servidor de Pruebas

```bash
# Opción 1: Usando el script
python run.py

# Opción 2: Directo con uvicorn
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload

# Opción 3: Con variables de entorno de prueba
export $(cat .env.test | xargs) && uvicorn app.main:app --reload
```

**Verificar que funciona**:
```bash
curl http://localhost:8001/health
```

Deberías ver:
```json
{
  "status": "healthy",
  "service": "NowCerts GHL Integration API",
  "version": "1.0.0"
}
```

### 3. Configurar ngrok (Para Webhooks)

```bash
# Iniciar ngrok
ngrok http 8001
```

**Obtendrás una URL pública**:
```
Forwarding: https://abc123.ngrok.io -> http://localhost:8001
```

**Guarda esta URL** - la necesitarás para configurar webhooks.

---

## 🧪 Tests Paso a Paso

### Test 1: Verificar Servidor

**Objetivo**: Confirmar que el servidor está funcionando

```bash
curl http://localhost:8001/health
```

**Resultado esperado**: HTTP 200 con status "healthy"

---

### Test 2: Webhook NowCerts → GHL (Crear Contacto)

**Objetivo**: Simular que NowCerts envía un evento de asegurado nuevo

**Comando**:
```bash
curl -X POST http://localhost:8001/api/v1/webhooks/nowcerts \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "INSURED_INSERT",
    "timestamp": "2024-01-15T10:30:00Z",
    "data": {
      "firstName": "Juan",
      "lastName": "Pérez",
      "email": "juan.perez.test@example.com",
      "phone": "+1234567890",
      "address": {
        "street": "123 Main Street",
        "city": "Miami",
        "state": "FL",
        "zip": "33101"
      },
      "source": "NowCerts"
    }
  }'
```

**Qué verificar**:
1. ✅ Respuesta HTTP 200
2. ✅ `"success": true` en el JSON
3. ✅ `"event_id"` presente en la respuesta
4. ✅ Logs muestran el procesamiento
5. ✅ **Ir a GHL Dashboard** y verificar que el contacto se creó

**Respuesta esperada**:
```json
{
  "success": true,
  "message": "Evento INSURED_INSERT procesado exitosamente",
  "event_id": "nowcerts_a1b2c3d4e5f6...",
  "data": {
    "id": "ghl_contact_id_123",
    "firstName": "Juan",
    "lastName": "Pérez",
    ...
  }
}
```

---

### Test 3: Webhook GHL → NowCerts (Crear Asegurado)

**Objetivo**: Simular que GHL envía un evento de contacto nuevo

**Comando**:
```bash
curl -X POST http://localhost:8001/api/v1/webhooks/ghl \
  -H "Content-Type: application/json" \
  -d '{
    "event": "contact.created",
    "contact": {
      "firstName": "María",
      "lastName": "González",
      "email": "maria.gonzalez.test@example.com",
      "phone": "+1987654321",
      "address1": "456 Oak Avenue",
      "city": "Orlando",
      "state": "FL",
      "postalCode": "32801",
      "source": "GHL"
    },
    "locationId": "test_location_id"
  }'
```

**Qué verificar**:
1. ✅ Respuesta HTTP 200
2. ✅ `"success": true`
3. ✅ Logs muestran el procesamiento
4. ✅ **Ir a NowCerts Dashboard** y verificar que el asegurado se creó

---

### Test 4: Verificar Idempotencia (Duplicados)

**Objetivo**: Confirmar que eventos duplicados son rechazados

**Paso 1**: Enviar webhook por primera vez
```bash
curl -X POST http://localhost:8001/api/v1/webhooks/nowcerts \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "INSURED_INSERT",
    "data": {
      "firstName": "Duplicate",
      "lastName": "Test",
      "email": "duplicate.test@example.com"
    }
  }'
```

**Resultado esperado**: HTTP 200, `"success": true`

**Paso 2**: Enviar **exactamente el mismo** webhook otra vez
```bash
# Mismo comando exacto
curl -X POST http://localhost:8001/api/v1/webhooks/nowcerts \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "INSURED_INSERT",
    "data": {
      "firstName": "Duplicate",
      "lastName": "Test",
      "email": "duplicate.test@example.com"
    }
  }'
```

**Resultado esperado**: HTTP 409 (Conflict)
```json
{
  "detail": "Evento ya procesado: nowcerts_<hash>"
}
```

**✅ Éxito**: El sistema rechazó el duplicado correctamente.

---

### Test 5: Sincronización Manual

**Objetivo**: Probar el endpoint de sincronización manual

**Comando**:
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
      "email": "manual.sync.test@example.com",
      "phone": "+1555555555",
      "address": {
        "street": "789 Test Blvd",
        "city": "Tampa",
        "state": "FL",
        "zip": "33601"
      }
    }
  }'
```

**Qué verificar**:
1. ✅ Respuesta HTTP 200
2. ✅ `"success": true`
3. ✅ `"target_id"` presente (ID del contacto creado en GHL)
4. ✅ Contacto aparece en GHL

---

### Test 6: Actualización de Contacto (UPDATE)

**Objetivo**: Simular actualización de asegurado en NowCerts

**Comando**:
```bash
curl -X POST http://localhost:8001/api/v1/webhooks/nowcerts \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "INSURED_UPDATE",
    "data": {
      "firstName": "Juan",
      "lastName": "Pérez Updated",
      "email": "juan.perez.test@example.com",
      "phone": "+1234567890",
      "address": {
        "street": "123 Main Street Updated",
        "city": "Miami",
        "state": "FL",
        "zip": "33101"
      }
    }
  }'
```

**Nota**: Actualmente el sistema intenta crear un nuevo contacto. Ver "Mejoras Recomendadas" en la documentación técnica para implementar búsqueda de contactos existentes.

---

### Test 7: Póliza → Oportunidad

**Objetivo**: Convertir una póliza de NowCerts en oportunidad en GHL

**Comando**:
```bash
curl -X POST http://localhost:8001/api/v1/webhooks/nowcerts \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "POLICY_INSERT",
    "data": {
      "policyNumber": "POL-TEST-001",
      "policyType": "Auto",
      "premium": 1200.00,
      "carrier": "State Farm",
      "effectiveDate": "2024-02-01",
      "expirationDate": "2025-02-01"
    }
  }'
```

**Nota**: Actualmente requiere `contact_id` en GHL. Ver documentación técnica para mejoras.

---

## 🔍 Verificación en Dashboards

### Verificar en GoHighLevel

1. **Acceder a GHL Dashboard**
2. **Ir a Contacts**
3. **Buscar contactos creados**:
   - `juan.perez.test@example.com`
   - `maria.gonzalez.test@example.com`
   - `manual.sync.test@example.com`

**Qué verificar**:
- ✅ Nombre correcto
- ✅ Email correcto
- ✅ Teléfono correcto
- ✅ Dirección correcta
- ✅ Source = "NowCerts"

### Verificar en NowCerts

1. **Acceder a NowCerts Dashboard**
2. **Ir a Insureds/Asegurados**
3. **Buscar asegurados creados**:
   - `maria.gonzalez.test@example.com`

**Qué verificar**:
- ✅ Nombre correcto
- ✅ Email correcto
- ✅ Teléfono correcto
- ✅ Dirección correcta
- ✅ Source = "GHL"

---

## 📊 Monitoreo de Logs

### Ver Logs en Tiempo Real

**Opción 1: Consola del servidor**
```bash
# Si iniciaste con --reload, verás logs en la consola
uvicorn app.main:app --reload --log-level debug
```

**Opción 2: Archivo de log**
```bash
# Si configuraste LOG_FILE
tail -f logs/test.log
```

**Formato de logs**:
```
2024-01-15 10:30:00 - NowCerts GHL Integration API - INFO - [INCOMING] NOWCERTS_WEBHOOK - Payload: {...}
2024-01-15 10:30:01 - NowCerts GHL Integration API - INFO - Contacto sincronizado con GHL: ghl_contact_id_123
2024-01-15 10:30:01 - NowCerts GHL Integration API - INFO - [OUTGOING] NOWCERTS_WEBHOOK - Response: {...}
```

---

## 🛠️ Scripts de Testing Automatizado

### Script 1: Test Completo (Bash)

Crea `test_integration.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:8001"

echo "🧪 Testing NowCerts GHL Integration"
echo "===================================="

# Test 1: Health Check
echo "1. Testing Health Check..."
response=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/health)
if [ $response -eq 200 ]; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed: $response"
    exit 1
fi

# Test 2: Webhook NowCerts
echo "2. Testing NowCerts Webhook..."
response=$(curl -s -X POST $BASE_URL/api/v1/webhooks/nowcerts \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "INSURED_INSERT",
    "data": {
      "firstName": "Test",
      "lastName": "User",
      "email": "test.user@example.com"
    }
  }')

if echo "$response" | grep -q '"success":true'; then
    echo "✅ NowCerts webhook passed"
else
    echo "❌ NowCerts webhook failed"
    echo "Response: $response"
    exit 1
fi

# Test 3: Webhook GHL
echo "3. Testing GHL Webhook..."
response=$(curl -s -X POST $BASE_URL/api/v1/webhooks/ghl \
  -H "Content-Type: application/json" \
  -d '{
    "event": "contact.created",
    "contact": {
      "firstName": "Test",
      "lastName": "Contact",
      "email": "test.contact@example.com"
    }
  }')

if echo "$response" | grep -q '"success":true'; then
    echo "✅ GHL webhook passed"
else
    echo "❌ GHL webhook failed"
    echo "Response: $response"
    exit 1
fi

# Test 4: Duplicate Detection
echo "4. Testing Duplicate Detection..."
payload='{"event_type":"INSURED_INSERT","data":{"email":"duplicate@example.com"}}'

# First request
response1=$(curl -s -X POST $BASE_URL/api/v1/webhooks/nowcerts \
  -H "Content-Type: application/json" \
  -d "$payload")

# Second request (duplicate)
response2=$(curl -s -w "%{http_code}" -X POST $BASE_URL/api/v1/webhooks/nowcerts \
  -H "Content-Type: application/json" \
  -d "$payload")

if echo "$response2" | grep -q "409"; then
    echo "✅ Duplicate detection passed"
else
    echo "❌ Duplicate detection failed"
    exit 1
fi

echo ""
echo "✅ All tests passed!"
```

**Ejecutar**:
```bash
chmod +x test_integration.sh
./test_integration.sh
```

### Script 2: Test con Python

Crea `test_integration.py`:

```python
#!/usr/bin/env python3
"""Script de testing automatizado"""

import requests
import json
import sys

BASE_URL = "http://localhost:8001"

def test_health_check():
    """Test 1: Health Check"""
    print("1. Testing Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ Health check passed")

def test_nowcerts_webhook():
    """Test 2: NowCerts Webhook"""
    print("2. Testing NowCerts Webhook...")
    payload = {
        "event_type": "INSURED_INSERT",
        "data": {
            "firstName": "Test",
            "lastName": "User",
            "email": "test.user@example.com"
        }
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/webhooks/nowcerts",
        json=payload
    )
    assert response.status_code == 200
    assert response.json()["success"] == True
    print("✅ NowCerts webhook passed")

def test_ghl_webhook():
    """Test 3: GHL Webhook"""
    print("3. Testing GHL Webhook...")
    payload = {
        "event": "contact.created",
        "contact": {
            "firstName": "Test",
            "lastName": "Contact",
            "email": "test.contact@example.com"
        }
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/webhooks/ghl",
        json=payload
    )
    assert response.status_code == 200
    assert response.json()["success"] == True
    print("✅ GHL webhook passed")

def test_duplicate_detection():
    """Test 4: Duplicate Detection"""
    print("4. Testing Duplicate Detection...")
    payload = {
        "event_type": "INSURED_INSERT",
        "data": {
            "email": "duplicate@example.com"
        }
    }
    
    # First request
    response1 = requests.post(
        f"{BASE_URL}/api/v1/webhooks/nowcerts",
        json=payload
    )
    assert response1.status_code == 200
    
    # Second request (duplicate)
    response2 = requests.post(
        f"{BASE_URL}/api/v1/webhooks/nowcerts",
        json=payload
    )
    assert response2.status_code == 409
    print("✅ Duplicate detection passed")

if __name__ == "__main__":
    try:
        print("🧪 Testing NowCerts GHL Integration")
        print("=" * 40)
        
        test_health_check()
        test_nowcerts_webhook()
        test_ghl_webhook()
        test_duplicate_detection()
        
        print("\n✅ All tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
```

**Ejecutar**:
```bash
python test_integration.py
```

---

## 🐛 Troubleshooting

### Problema: "Connection refused"

**Causa**: El servidor no está corriendo

**Solución**:
```bash
# Verificar que el servidor esté corriendo
ps aux | grep uvicorn

# Iniciar servidor
python run.py
```

### Problema: "401 Unauthorized" en NowCerts

**Causa**: Credenciales incorrectas o token expirado

**Solución**:
1. Verificar `.env` tiene credenciales correctas
2. Verificar logs para ver mensaje de error específico
3. El sistema debería renovar tokens automáticamente

### Problema: "Evento duplicado" en primera llamada

**Causa**: El evento ya fue procesado anteriormente

**Solución**:
- Cambiar algún campo en el payload (ej: email diferente)
- O esperar 24 horas para que expire del cache
- O reiniciar el servidor (si es cache en memoria)

### Problema: Contacto no aparece en GHL

**Causa**: Error en la API de GHL o credenciales incorrectas

**Solución**:
1. Verificar logs para ver el error específico
2. Verificar `GHL_API_KEY` y `GHL_LOCATION_ID` en `.env`
3. Probar crear contacto directamente en GHL API

### Problema: ngrok no funciona

**Causa**: ngrok no está corriendo o URL incorrecta

**Solución**:
```bash
# Verificar ngrok
curl http://localhost:4040/api/tunnels

# Reiniciar ngrok
pkill ngrok
ngrok http 8001
```

---

## ✅ Checklist Final

Antes de considerar los tests completos, verifica:

- [ ] Health check funciona
- [ ] Webhook NowCerts crea contacto en GHL
- [ ] Webhook GHL crea asegurado en NowCerts
- [ ] Duplicados son rechazados (409)
- [ ] Logs se registran correctamente
- [ ] Contactos aparecen en dashboards
- [ ] Datos se mapean correctamente
- [ ] Errores se manejan apropiadamente
- [ ] Tokens se renuevan automáticamente
- [ ] Reintentos funcionan

---

## 📝 Notas Importantes

1. **Usa emails únicos**: Cada test debe usar un email diferente para evitar conflictos
2. **Limpia datos de prueba**: Después de testing, elimina contactos/asegurados de prueba
3. **No uses producción**: Asegúrate de usar cuentas de sandbox/test
4. **Monitorea logs**: Los logs te darán información valiosa sobre qué está pasando
5. **Verifica dashboards**: Siempre verifica en los dashboards que los datos se crearon correctamente

---

**Última actualización**: 2024-01-15

