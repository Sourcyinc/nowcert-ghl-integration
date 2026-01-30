# Cambios Realizados - Actualización a API Real de NowCerts

## 📋 Resumen

Se han actualizado todos los componentes para usar la API real de NowCerts basándose en el repositorio oficial de ejemplo (`NowCertsTestWebServices`).

## ✅ Cambios Implementados

### 1. Token Manager (`app/services/token_manager.py`)

#### Antes:
- ❌ URL: `/api/auth/login`
- ❌ Formato: JSON
- ❌ Sin client_id

#### Ahora:
- ✅ URL: `/api/token`
- ✅ Formato: `application/x-www-form-urlencoded`
- ✅ Body: `grant_type=password&username=...&password=...&client_id=ngAuthApp`
- ✅ Refresh token: Mismo endpoint con `grant_type=refresh_token`
- ✅ Manejo correcto de `.expires` y `as:client_id` en respuesta

### 2. NowCerts Service (`app/services/nowcerts_service.py`)

#### Endpoints Actualizados:

**Antes**:
- ❌ `POST /api/contacts`
- ❌ `POST /api/policies`
- ❌ `POST /api/quotes`

**Ahora**:
- ✅ `POST /api/Insured/Insert` - Crear asegurado
- ✅ `POST /api/Policy/Insert` - Crear póliza
- ✅ `POST /api/Policy/Insert` - Crear cotización (usa mismo endpoint)

#### Estructura de Datos Actualizada:

**Para Insured (Asegurado)**:
```json
{
  "firstName": "Juan",
  "lastName": "Pérez",
  "active": true,
  "addressLine1": "123 Main St",
  "stateNameOrAbbreviation": "FL",
  "description": "imported from Web Services"
}
```

O para empresas:
```json
{
  "commercialName": "Empresa ABC",
  "active": true,
  "addressLine1": "123 Main St",
  "stateNameOrAbbreviation": "FL",
  "description": "imported from Web Services"
}
```

**Para Policy (Póliza)**:
```json
{
  "number": "POL-12345",
  "insuredName": "Juan Pérez"
}
```

### 3. Data Mapper (`app/services/mapper.py`)

#### Actualizado `ghl_to_nowcerts_contact()`:

**Antes**:
```python
{
  "firstName": "...",
  "address": {
    "street": "...",
    "state": "..."
  }
}
```

**Ahora**:
```python
{
  "firstName": "...",
  "lastName": "...",
  "active": True,
  "addressLine1": "...",
  "stateNameOrAbbreviation": "...",
  "description": "imported from GHL"
}
```

### 4. Configuración (`app/core/config.py`)

#### Cambios:
- ✅ `NOWCERTS_CLIENT_ID` ahora tiene valor por defecto: `"ngAuthApp"`
- ✅ Removido `NOWCERTS_CLIENT_SECRET` (no se usa en la API REST)

### 5. Archivo de Ejemplo (`env.example`)

#### Actualizado:
```env
NOWCERTS_CLIENT_ID=ngAuthApp  # Valor por defecto
```

## 🔍 Detalles Técnicos

### Autenticación OAuth2

NowCerts usa OAuth2 con flujo de "Resource Owner Password Credentials":

1. **Login**:
   ```
   POST https://api.nowcerts.com/api/token
   Content-Type: application/x-www-form-urlencoded
   
   grant_type=password&username={user}&password={pass}&client_id=ngAuthApp
   ```

2. **Respuesta**:
   ```json
   {
     "access_token": "...",
     "token_type": "Bearer",
     "expires_in": 3600,
     "refresh_token": "...",
     ".expires": "2024-01-15T12:00:00Z",
     "as:client_id": "ngAuthApp"
   }
   ```

3. **Uso del Token**:
   ```
   Authorization: Bearer {access_token}
   ```

4. **Refresh Token**:
   ```
   POST https://api.nowcerts.com/api/token
   Content-Type: application/x-www-form-urlencoded
   
   grant_type=refresh_token&refresh_token={refresh_token}&client_id={client_id}
   ```

### Estructura de Datos NowCerts

#### Insured (Asegurado):
- **Persona**: `firstName` + `lastName` (requerido si no hay commercialName)
- **Empresa**: `commercialName` (requerido si no hay firstName/lastName)
- `active`: boolean (requerido)
- `addressLine1`: string (opcional)
- `stateNameOrAbbreviation`: string (opcional, acepta "FL" o "Florida")
- `description`: string (opcional)

#### Policy (Póliza):
- `number`: string (requerido)
- `insuredName`: string (requerido)

## 🧪 Testing Actualizado

Los tests deben actualizarse para usar la nueva estructura:

### Ejemplo de Test - Crear Asegurado:

```python
# Antes (incorrecto)
contact_data = {
    "firstName": "Juan",
    "email": "juan@example.com",
    "address": {"street": "123 Main St"}
}

# Ahora (correcto)
contact_data = {
    "firstName": "Juan",
    "lastName": "Pérez",
    "active": True,
    "addressLine1": "123 Main St",
    "stateNameOrAbbreviation": "FL",
    "description": "imported from GHL"
}
```

## 📚 Referencias

- Repositorio oficial: `NowCertsTestWebServices/TestNowCertsAPI`
- Archivos clave analizados:
  - `AuthenticateRestApi.aspx` - Autenticación REST
  - `RefreshToken.aspx` - Renovación de tokens
  - `InsuredsRestApi.aspx` - Operaciones con asegurados
  - `PoliciesRestApi.aspx` - Operaciones con pólizas
  - `Web.config` - Configuración de URLs

## ⚠️ Notas Importantes

1. **Formato de Autenticación**: Ahora usa `form-urlencoded`, no JSON
2. **Client ID**: Siempre usar `ngAuthApp` a menos que se especifique otro
3. **Endpoints**: Usar `/api/Insured/Insert` y `/api/Policy/Insert` (con mayúsculas)
4. **Estructura de Datos**: Cambió significativamente - usar `addressLine1` en lugar de objeto `address`
5. **Refresh Token**: Usa el mismo endpoint `/api/token` con `grant_type=refresh_token`

## ✅ Estado

- ✅ Token Manager actualizado
- ✅ NowCerts Service actualizado
- ✅ Data Mapper actualizado
- ✅ Configuración actualizada
- ✅ Documentación creada

**Listo para testing con la API real de NowCerts**

