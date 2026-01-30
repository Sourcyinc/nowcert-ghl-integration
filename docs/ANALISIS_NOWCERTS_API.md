# Análisis de la API Real de NowCerts

## 📋 Resumen del Análisis

He revisado el repositorio de ejemplo oficial de NowCerts (`NowCertsTestWebServices`) y encontré información crítica sobre cómo funciona realmente su API REST.

## 🔑 Autenticación

### Endpoint de Login
```
POST https://api.nowcerts.com/api/token
Content-Type: text/plain (o application/x-www-form-urlencoded)
```

**Body (form-urlencoded)**:
```
grant_type=password&username={username}&password={password}&client_id=ngAuthApp
```

**Respuesta**:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "abc123...",
  ".expires": "2024-01-15T12:00:00Z",
  "as:client_id": "ngAuthApp"
}
```

### Endpoint de Refresh Token
```
POST https://api.nowcerts.com/api/token
Content-Type: text/plain
```

**Body (form-urlencoded)**:
```
grant_type=refresh_token&refresh_token={refresh_token}&client_id={client_id}
```

**Respuesta**: Misma estructura que login

### Uso del Token
```
Authorization: {token_type} {access_token}
```

Ejemplo:
```
Authorization: Bearer eyJhbGc...
```

## 📝 Endpoints REST Identificados

### 1. Insert Insured (Crear Asegurado)
```
POST https://api.nowcerts.com/api/Insured/Insert
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Body**:
```json
{
  "commercialName": "Empresa ABC",  // Opcional (para empresas)
  "firstName": "Juan",              // Opcional (si no hay commercialName)
  "lastName": "Pérez",               // Opcional (si no hay commercialName)
  "active": true,
  "addressLine1": "123 Main St",
  "stateNameOrAbbreviation": "FL",
  "description": "imported from Web Services"
}
```

**Notas**:
- Puede ser `commercialName` (empresa) O `firstName` + `lastName` (persona)
- `active` debe ser boolean
- `stateNameOrAbbreviation` acepta nombre completo o abreviatura

### 2. Insert Policy (Crear Póliza)
```
POST https://api.nowcerts.com/api/Policy/Insert
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Body**:
```json
{
  "number": "POL-12345",
  "insuredName": "Juan Pérez"
}
```

## 🔄 Diferencias con Nuestra Implementación Actual

### ❌ Lo que teníamos incorrecto:

1. **URL de autenticación**:
   - ❌ Teníamos: `https://api.nowcerts.com/api/auth/login`
   - ✅ Correcto: `https://api.nowcerts.com/api/token`

2. **Formato de autenticación**:
   - ❌ Teníamos: JSON body
   - ✅ Correcto: Form-urlencoded (`grant_type=password&username=...`)

3. **Client ID**:
   - ❌ No lo teníamos
   - ✅ Requerido: `client_id=ngAuthApp`

4. **Endpoint de Insured**:
   - ❌ Teníamos: `/api/contacts`
   - ✅ Correcto: `/api/Insured/Insert`

5. **Estructura de datos**:
   - ❌ Teníamos: `{ firstName, lastName, email, phone, address: {...} }`
   - ✅ Correcto: `{ firstName, lastName, addressLine1, stateNameOrAbbreviation, active, description }`

6. **Refresh token**:
   - ❌ Teníamos: `/api/auth/refresh`
   - ✅ Correcto: `/api/token` con `grant_type=refresh_token`

## ✅ Correcciones Necesarias

1. Actualizar `token_manager.py` para usar el formato correcto
2. Actualizar `nowcerts_service.py` para usar los endpoints correctos
3. Actualizar `mapper.py` para mapear a la estructura correcta de NowCerts
4. Agregar `client_id` a la configuración

## 📚 Referencias

- Repositorio oficial: `NowCertsTestWebServices/TestNowCertsAPI`
- Archivos clave:
  - `AuthenticateRestApi.aspx` - Autenticación
  - `RefreshToken.aspx` - Renovación de tokens
  - `InsuredsRestApi.aspx` - Operaciones con asegurados
  - `PoliciesRestApi.aspx` - Operaciones con pólizas
  - `Web.config` - Configuración de URLs

