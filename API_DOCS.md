# Documentación de APIs - Sistema Pontificia

## 📋 Resumen Ejecutivo

Esta documentación detalla todos los endpoints REST disponibles en el Sistema Pontificia, incluyendo autenticación, parámetros, respuestas, códigos de error y ejemplos de uso para cada microservicio.

## 🏗️ Arquitectura de APIs

### Patrón de URLs

```
Base URL: http://localhost:8000 (Gateway)
Direct Access: http://localhost:300X (Microservicio específico)

Pattern: /{service}/{version}/{resource}/{action}/
Example: /users/v1/profile/update/
```

### Autenticación Global

Todos los endpoints (excepto login/register) requieren autenticación JWT:

```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### Códigos de Respuesta Estándar

| Código | Significado | Uso |
|--------|-------------|-----|
| 200 | OK | Operación exitosa |
| 201 | Created | Recurso creado |
| 400 | Bad Request | Datos inválidos |
| 401 | Unauthorized | Token inválido/expirado |
| 403 | Forbidden | Sin permisos |
| 404 | Not Found | Recurso no encontrado |
| 500 | Server Error | Error interno |

## 🔐 Auth Service (Puerto 3001)

### Base URL: `http://localhost:3001/auth/`

#### POST /auth/login/
Autenticar usuario y obtener token JWT.

**Request:**
```json
{
    "username": "usuario@pontificia.com",
    "password": "password123"
}
```

**Response (200):**
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
        "id": 123,
        "username": "usuario@pontificia.com",
        "email": "usuario@pontificia.com",
        "first_name": "Usuario",
        "last_name": "Ejemplo"
    }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:3001/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "usuario@pontificia.com",
    "password": "password123"
  }'
```

#### POST /auth/register/
Registrar nuevo usuario.

**Request:**
```json
{
    "username": "nuevo@pontificia.com",
    "email": "nuevo@pontificia.com",
    "password": "password123",
    "password_confirm": "password123",
    "first_name": "Nuevo",
    "last_name": "Usuario"
}
```

**Response (201):**
```json
{
    "message": "Usuario creado exitosamente",
    "user": {
        "id": 124,
        "username": "nuevo@pontificia.com",
        "email": "nuevo@pontificia.com",
        "first_name": "Nuevo",
        "last_name": "Usuario"
    }
}
```

#### POST /auth/refresh/
Renovar token JWT.

**Request:**
```json
{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200):**
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "Bearer",
    "expires_in": 3600
}
```

#### POST /auth/logout/
Cerrar sesión (invalidar token).

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
    "message": "Sesión cerrada exitosamente"
}
```

#### GET /auth/verify/
Verificar validez del token.

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
    "valid": true,
    "user_id": 123,
    "expires_at": "2024-12-25T15:30:00Z"
}
```

---

## 👥 Users Service (Puerto 3002)

### Base URL: `http://localhost:3002/users/`

#### GET /users/
Listar usuarios (con paginación).

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page`: Número de página (default: 1)
- `page_size`: Elementos por página (default: 20)
- `search`: Buscar por nombre/email
- `role`: Filtrar por rol
- `is_active`: Filtrar por estado activo

**Response (200):**
```json
{
    "count": 150,
    "next": "http://localhost:3002/users/?page=2",
    "previous": null,
    "results": [
        {
            "id": 123,
            "username": "usuario@pontificia.com",
            "email": "usuario@pontificia.com",
            "first_name": "Usuario",
            "last_name": "Ejemplo",
            "is_active": true,
            "date_joined": "2024-01-15T10:30:00Z",
            "last_login": "2024-12-20T14:25:00Z",
            "role": "student",
            "profile": {
                "phone": "+1234567890",
                "address": "123 Calle Principal",
                "birth_date": "1995-05-15"
            }
        }
    ]
}
```

**cURL Example:**
```bash
curl -X GET "http://localhost:3002/users/?page=1&search=usuario" \
  -H "Authorization: Bearer <access_token>"
```

#### GET /users/{id}/
Obtener usuario específico.

**Response (200):**
```json
{
    "id": 123,
    "username": "usuario@pontificia.com",
    "email": "usuario@pontificia.com",
    "first_name": "Usuario",
    "last_name": "Ejemplo",
    "is_active": true,
    "date_joined": "2024-01-15T10:30:00Z",
    "last_login": "2024-12-20T14:25:00Z",
    "role": "student",
    "permissions": ["view_profile", "edit_profile"],
    "profile": {
        "phone": "+1234567890",
        "address": "123 Calle Principal",
        "birth_date": "1995-05-15",
        "photo": "http://localhost:3002/media/photos/user_123.jpg"
    }
}
```

#### POST /users/
Crear nuevo usuario.

**Request:**
```json
{
    "username": "nuevo@pontificia.com",
    "email": "nuevo@pontificia.com",
    "password": "password123",
    "first_name": "Nuevo",
    "last_name": "Usuario",
    "role": "student",
    "profile": {
        "phone": "+1234567890",
        "address": "123 Calle Principal",
        "birth_date": "1995-05-15"
    }
}
```

**Response (201):**
```json
{
    "id": 124,
    "username": "nuevo@pontificia.com",
    "email": "nuevo@pontificia.com",
    "first_name": "Nuevo",
    "last_name": "Usuario",
    "is_active": true,
    "role": "student",
    "message": "Usuario creado exitosamente"
}
```

#### PUT/PATCH /users/{id}/
Actualizar usuario.

**Request (PATCH):**
```json
{
    "first_name": "Nombre Actualizado",
    "profile": {
        "phone": "+0987654321"
    }
}
```

**Response (200):**
```json
{
    "id": 123,
    "username": "usuario@pontificia.com",
    "first_name": "Nombre Actualizado",
    "profile": {
        "phone": "+0987654321"
    },
    "message": "Usuario actualizado exitosamente"
}
```

#### DELETE /users/{id}/
Eliminar usuario (soft delete).

**Response (200):**
```json
{
    "message": "Usuario eliminado exitosamente"
}
```

#### GET /users/profile/
Obtener perfil del usuario autenticado.

**Response (200):**
```json
{
    "id": 123,
    "username": "usuario@pontificia.com",
    "email": "usuario@pontificia.com",
    "first_name": "Usuario",
    "last_name": "Ejemplo",
    "profile": {
        "phone": "+1234567890",
        "address": "123 Calle Principal",
        "birth_date": "1995-05-15",
        "photo": "http://localhost:3002/media/photos/user_123.jpg",
        "bio": "Estudiante de ingeniería...",
        "preferences": {
            "language": "es",
            "timezone": "America/Lima",
            "notifications": true
        }
    }
}
```

#### POST /users/upload-photo/
Subir foto de perfil.

**Request (multipart/form-data):**
```http
Content-Type: multipart/form-data

photo: [file]
```

**Response (200):**
```json
{
    "message": "Foto subida exitosamente",
    "photo_url": "http://localhost:3002/media/photos/user_123.jpg"
}
```

---

## 📝 Asistencia Service (Puerto 3003)

### Base URL: `http://localhost:3003/asistencia/`

#### GET /asistencia/
Listar registros de asistencia.

**Query Parameters:**
- `fecha_inicio`: Fecha de inicio (YYYY-MM-DD)
- `fecha_fin`: Fecha de fin (YYYY-MM-DD)
- `estudiante_id`: ID del estudiante
- `curso_id`: ID del curso
- `presente`: true/false

**Response (200):**
```json
{
    "count": 50,
    "results": [
        {
            "id": 1,
            "estudiante": {
                "id": 123,
                "nombre": "Usuario Ejemplo",
                "email": "usuario@pontificia.com"
            },
            "curso": {
                "id": 456,
                "nombre": "Matemáticas I",
                "codigo": "MAT101"
            },
            "fecha": "2024-12-20",
            "hora_inicio": "08:00:00",
            "hora_fin": "10:00:00",
            "presente": true,
            "tardanza": false,
            "justificacion": null,
            "created_at": "2024-12-20T08:05:00Z"
        }
    ]
}
```

#### POST /asistencia/registro/
Registrar asistencia.

**Request:**
```json
{
    "estudiante_id": 123,
    "curso_id": 456,
    "fecha": "2024-12-20",
    "hora_inicio": "08:00:00",
    "presente": true,
    "tardanza": false,
    "justificacion": null
}
```

**Response (201):**
```json
{
    "id": 2,
    "message": "Asistencia registrada exitosamente",
    "estudiante_id": 123,
    "curso_id": 456,
    "fecha": "2024-12-20",
    "presente": true
}
```

#### GET /asistencia/reporte/
Generar reporte de asistencia.

**Query Parameters:**
- `tipo`: "estudiante" | "curso" | "fecha"
- `estudiante_id`: ID del estudiante (si tipo=estudiante)
- `curso_id`: ID del curso (si tipo=curso)
- `fecha_inicio`: Fecha de inicio
- `fecha_fin`: Fecha de fin
- `formato`: "json" | "pdf" | "excel"

**Response (200):**
```json
{
    "reporte": {
        "tipo": "estudiante",
        "estudiante": {
            "id": 123,
            "nombre": "Usuario Ejemplo"
        },
        "periodo": {
            "inicio": "2024-12-01",
            "fin": "2024-12-20"
        },
        "estadisticas": {
            "total_clases": 20,
            "asistencias": 18,
            "faltas": 2,
            "tardanzas": 1,
            "porcentaje_asistencia": 90.0
        },
        "detalle": [
            {
                "fecha": "2024-12-20",
                "curso": "Matemáticas I",
                "presente": true,
                "tardanza": false
            }
        ]
    }
}
```

#### PUT /asistencia/{id}/
Actualizar registro de asistencia.

**Request:**
```json
{
    "presente": false,
    "justificacion": "Cita médica"
}
```

**Response (200):**
```json
{
    "id": 1,
    "presente": false,
    "justificacion": "Cita médica",
    "message": "Asistencia actualizada exitosamente"
}
```

---

## 📄 Documentos Service (Puerto 3004)

### Base URL: `http://localhost:3004/documentos/`

#### GET /documentos/
Listar documentos.

**Query Parameters:**
- `tipo`: Filtrar por tipo de documento
- `propietario_id`: ID del propietario
- `fecha_inicio`: Fecha de creación inicio
- `fecha_fin`: Fecha de creación fin

**Response (200):**
```json
{
    "count": 25,
    "results": [
        {
            "id": 1,
            "nombre": "Certificado de Notas.pdf",
            "tipo": "certificado",
            "descripcion": "Certificado de notas del semestre 2024-I",
            "propietario": {
                "id": 123,
                "nombre": "Usuario Ejemplo"
            },
            "archivo_url": "http://localhost:3004/media/documentos/cert_123.pdf",
            "tamaño": 245760,
            "fecha_creacion": "2024-12-20T10:30:00Z",
            "fecha_modificacion": "2024-12-20T10:30:00Z",
            "estado": "activo",
            "publico": false,
            "metadata": {
                "semestre": "2024-I",
                "tipo_certificado": "notas"
            }
        }
    ]
}
```

#### POST /documentos/upload/
Subir documento.

**Request (multipart/form-data):**
```http
Content-Type: multipart/form-data

archivo: [file]
nombre: "Mi Documento.pdf"
tipo: "certificado"
descripcion: "Descripción del documento"
publico: false
metadata: {"key": "value"}
```

**Response (201):**
```json
{
    "id": 2,
    "nombre": "Mi Documento.pdf",
    "tipo": "certificado",
    "archivo_url": "http://localhost:3004/media/documentos/doc_124.pdf",
    "tamaño": 512000,
    "message": "Documento subido exitosamente"
}
```

#### GET /documentos/{id}/download/
Descargar documento.

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Response (200):**
```http
Content-Type: application/pdf
Content-Disposition: attachment; filename="documento.pdf"

[Binary file content]
```

#### DELETE /documentos/{id}/
Eliminar documento.

**Response (200):**
```json
{
    "message": "Documento eliminado exitosamente"
}
```

#### GET /documentos/tipos/
Obtener tipos de documentos disponibles.

**Response (200):**
```json
{
    "tipos": [
        {
            "codigo": "certificado",
            "nombre": "Certificado",
            "descripcion": "Certificados académicos",
            "extensiones_permitidas": [".pdf", ".jpg", ".png"]
        },
        {
            "codigo": "transcript",
            "nombre": "Transcript",
            "descripcion": "Transcripts oficiales",
            "extensiones_permitidas": [".pdf"]
        }
    ]
}
```

---

## 💰 Pagos Service (Puerto 3005)

### Base URL: `http://localhost:3005/pagos/`

#### GET /pagos/
Listar pagos.

**Query Parameters:**
- `estado`: "pendiente" | "procesando" | "completado" | "fallido"
- `estudiante_id`: ID del estudiante
- `fecha_inicio`: Fecha inicio
- `fecha_fin`: Fecha fin
- `monto_min`: Monto mínimo
- `monto_max`: Monto máximo

**Response (200):**
```json
{
    "count": 100,
    "results": [
        {
            "id": 1,
            "estudiante": {
                "id": 123,
                "nombre": "Usuario Ejemplo"
            },
            "concepto": "Matrícula Semestre 2024-I",
            "monto": 1500.00,
            "moneda": "PEN",
            "estado": "completado",
            "fecha_creacion": "2024-12-15T10:00:00Z",
            "fecha_pago": "2024-12-15T10:05:00Z",
            "metodo_pago": "tarjeta_credito",
            "referencia_pago": "TXN123456789",
            "comprobante_url": "http://localhost:3005/media/comprobantes/comp_1.pdf"
        }
    ]
}
```

#### POST /pagos/procesar/
Procesar nuevo pago.

**Request:**
```json
{
    "estudiante_id": 123,
    "concepto": "Matrícula Semestre 2024-II",
    "monto": 1500.00,
    "moneda": "PEN",
    "metodo_pago": "tarjeta_credito",
    "datos_pago": {
        "numero_tarjeta": "4111111111111111",
        "mes_vencimiento": "12",
        "año_vencimiento": "2025",
        "cvv": "123",
        "nombre_titular": "Usuario Ejemplo"
    }
}
```

**Response (201):**
```json
{
    "id": 2,
    "estado": "procesando",
    "referencia_pago": "TXN123456790",
    "mensaje": "Pago en proceso de validación",
    "url_seguimiento": "http://localhost:3005/pagos/2/seguimiento/"
}
```

#### GET /pagos/{id}/
Obtener detalles de pago.

**Response (200):**
```json
{
    "id": 1,
    "estudiante": {
        "id": 123,
        "nombre": "Usuario Ejemplo",
        "email": "usuario@pontificia.com"
    },
    "concepto": "Matrícula Semestre 2024-I",
    "monto": 1500.00,
    "moneda": "PEN",
    "estado": "completado",
    "fecha_creacion": "2024-12-15T10:00:00Z",
    "fecha_pago": "2024-12-15T10:05:00Z",
    "metodo_pago": "tarjeta_credito",
    "referencia_pago": "TXN123456789",
    "detalles_transaccion": {
        "gateway": "visa",
        "codigo_autorizacion": "AUTH123",
        "ultimos_4_digitos": "1111"
    },
    "comprobante_url": "http://localhost:3005/media/comprobantes/comp_1.pdf"
}
```

#### GET /pagos/historial/
Obtener historial de pagos del usuario autenticado.

**Response (200):**
```json
{
    "estudiante": {
        "id": 123,
        "nombre": "Usuario Ejemplo"
    },
    "resumen": {
        "total_pagado": 4500.00,
        "pagos_completados": 3,
        "pagos_pendientes": 1,
        "ultimo_pago": "2024-12-15T10:05:00Z"
    },
    "pagos": [
        {
            "id": 1,
            "concepto": "Matrícula Semestre 2024-I",
            "monto": 1500.00,
            "estado": "completado",
            "fecha_pago": "2024-12-15T10:05:00Z"
        }
    ]
}
```

#### POST /pagos/{id}/reembolso/
Solicitar reembolso.

**Request:**
```json
{
    "motivo": "Cancelación de matrícula",
    "monto_reembolso": 1500.00,
    "datos_bancarios": {
        "banco": "BCP",
        "numero_cuenta": "123456789",
        "tipo_cuenta": "ahorro"
    }
}
```

**Response (201):**
```json
{
    "id_reembolso": 10,
    "estado": "solicitado",
    "mensaje": "Solicitud de reembolso creada exitosamente",
    "tiempo_estimado": "5-7 días hábiles"
}
```

---

## 📊 Reportes Service (Puerto 3006)

### Base URL: `http://localhost:3006/reportes/`

#### GET /reportes/
Listar reportes disponibles.

**Response (200):**
```json
{
    "categorias": [
        {
            "nombre": "Académicos",
            "reportes": [
                {
                    "id": "notas_estudiante",
                    "nombre": "Reporte de Notas por Estudiante",
                    "descripcion": "Reporte detallado de notas de un estudiante",
                    "parametros": ["estudiante_id", "semestre"]
                },
                {
                    "id": "asistencia_curso",
                    "nombre": "Reporte de Asistencia por Curso",
                    "descripcion": "Estadísticas de asistencia de un curso",
                    "parametros": ["curso_id", "fecha_inicio", "fecha_fin"]
                }
            ]
        },
        {
            "nombre": "Financieros",
            "reportes": [
                {
                    "id": "pagos_periodo",
                    "nombre": "Reporte de Pagos por Período",
                    "descripcion": "Resumen de pagos en un período específico",
                    "parametros": ["fecha_inicio", "fecha_fin", "estado"]
                }
            ]
        }
    ]
}
```

#### POST /reportes/generar/
Generar reporte.

**Request:**
```json
{
    "tipo_reporte": "notas_estudiante",
    "parametros": {
        "estudiante_id": 123,
        "semestre": "2024-I"
    },
    "formato": "pdf",
    "opciones": {
        "incluir_graficos": true,
        "idioma": "es"
    }
}
```

**Response (202):**
```json
{
    "id_tarea": "task_abc123",
    "estado": "procesando",
    "mensaje": "Reporte en proceso de generación",
    "url_seguimiento": "http://localhost:3006/reportes/estado/task_abc123/",
    "tiempo_estimado": "2-5 minutos"
}
```

#### GET /reportes/estado/{id_tarea}/
Verificar estado de generación de reporte.

**Response (200):**
```json
{
    "id_tarea": "task_abc123",
    "estado": "completado",
    "progreso": 100,
    "resultado": {
        "url_descarga": "http://localhost:3006/media/reportes/reporte_abc123.pdf",
        "tamaño": 245760,
        "fecha_generacion": "2024-12-20T15:30:00Z",
        "valido_hasta": "2024-12-27T15:30:00Z"
    }
}
```

#### GET /reportes/descargar/{id_reporte}/
Descargar reporte generado.

**Response (200):**
```http
Content-Type: application/pdf
Content-Disposition: attachment; filename="reporte_notas_2024.pdf"

[Binary file content]
```

#### GET /reportes/dashboard/
Obtener datos para dashboard.

**Query Parameters:**
- `periodo`: "dia" | "semana" | "mes" | "año"
- `fecha_inicio`: Fecha de inicio
- `fecha_fin`: Fecha de fin

**Response (200):**
```json
{
    "resumen": {
        "total_estudiantes": 1500,
        "total_cursos": 45,
        "total_pagos": 2250000.00,
        "asistencia_promedio": 87.5
    },
    "graficos": {
        "pagos_mensuales": [
            {"mes": "2024-01", "monto": 450000.00},
            {"mes": "2024-02", "monto": 475000.00}
        ],
        "asistencia_cursos": [
            {"curso": "Matemáticas I", "porcentaje": 92.0},
            {"curso": "Física I", "porcentaje": 85.5}
        ]
    }
}
```

---

## 🔍 Auditoria Service (Puerto 3007)

### Base URL: `http://localhost:3007/auditoria/`

#### GET /auditoria/logs/
Obtener logs de auditoría.

**Query Parameters:**
- `usuario_id`: ID del usuario
- `accion`: Tipo de acción
- `recurso`: Tipo de recurso
- `fecha_inicio`: Fecha de inicio
- `fecha_fin`: Fecha de fin
- `nivel`: "info" | "warning" | "error"

**Response (200):**
```json
{
    "count": 500,
    "results": [
        {
            "id": 1,
            "timestamp": "2024-12-20T14:30:00Z",
            "usuario": {
                "id": 123,
                "username": "usuario@pontificia.com",
                "nombre": "Usuario Ejemplo"
            },
            "accion": "LOGIN",
            "recurso_tipo": "auth",
            "recurso_id": null,
            "detalles": {
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "exitoso": true
            },
            "nivel": "info",
            "servicio": "auth_service"
        }
    ]
}
```

#### POST /auditoria/evento/
Registrar evento de auditoría.

**Request:**
```json
{
    "usuario_id": 123,
    "accion": "UPDATE_PROFILE",
    "recurso_tipo": "user",
    "recurso_id": 123,
    "detalles": {
        "campos_modificados": ["first_name", "email"],
        "valores_anteriores": {
            "first_name": "Nombre Anterior",
            "email": "anterior@pontificia.com"
        },
        "valores_nuevos": {
            "first_name": "Nuevo Nombre",
            "email": "nuevo@pontificia.com"
        }
    },
    "nivel": "info"
}
```

**Response (201):**
```json
{
    "id": 2,
    "mensaje": "Evento de auditoría registrado exitosamente",
    "timestamp": "2024-12-20T14:35:00Z"
}
```

#### GET /auditoria/reportes/
Generar reportes de auditoría.

**Query Parameters:**
- `tipo`: "accesos" | "modificaciones" | "errores"
- `periodo`: "dia" | "semana" | "mes"
- `usuario_id`: ID del usuario específico

**Response (200):**
```json
{
    "reporte": {
        "tipo": "accesos",
        "periodo": "semana",
        "fecha_inicio": "2024-12-14",
        "fecha_fin": "2024-12-20",
        "estadisticas": {
            "total_accesos": 1250,
            "accesos_exitosos": 1200,
            "accesos_fallidos": 50,
            "usuarios_unicos": 300
        },
        "usuarios_mas_activos": [
            {
                "usuario": "admin@pontificia.com",
                "accesos": 45
            }
        ],
        "ips_sospechosas": [
            {
                "ip": "192.168.1.999",
                "intentos_fallidos": 25
            }
        ]
    }
}
```

#### GET /auditoria/compliance/
Generar reporte de cumplimiento.

**Response (200):**
```json
{
    "cumplimiento": {
        "periodo": "2024-12",
        "politicas_evaluadas": [
            {
                "politica": "Retención de logs",
                "cumple": true,
                "detalles": "Logs retenidos por 365 días"
            },
            {
                "politica": "Trazabilidad de cambios",
                "cumple": true,
                "detalles": "100% de cambios auditados"
            }
        ],
        "metricas": {
            "eventos_auditados": 15000,
            "cobertura_auditoria": 95.5,
            "tiempo_respuesta_promedio": "150ms"
        }
    }
}
```

---

## 🚪 Gateway Service (Puerto 8000)

### Base URL: `http://localhost:8000/`

El Gateway actúa como proxy reverso y punto de entrada único. Redirige las peticiones a los microservicios correspondientes.

#### GET /health/
Health check general del sistema.

**Response (200):**
```json
{
    "status": "healthy",
    "services": {
        "auth": {
            "status": "healthy",
            "response_time": "45ms",
            "last_check": "2024-12-20T15:00:00Z"
        },
        "users": {
            "status": "healthy",
            "response_time": "32ms",
            "last_check": "2024-12-20T15:00:00Z"
        },
        "database": {
            "status": "healthy",
            "connections": 15
        },
        "cache": {
            "status": "healthy",
            "memory_usage": "45%"
        }
    },
    "version": "1.0.0",
    "uptime": "5 days, 12 hours"
}
```

#### Routing Rules

El Gateway redirige peticiones usando las siguientes reglas:

```
/auth/*     → http://auth:8000/auth/*
/users/*    → http://users:8000/users/*
/asistencia/* → http://asistencia:8000/asistencia/*
/documentos/* → http://documentos:8000/documentos/*
/pagos/*    → http://pagos:8000/pagos/*
/reportes/* → http://reportes:8000/reportes/*
/auditoria/* → http://auditoria:8000/auditoria/*
```

#### Rate Limiting

El Gateway implementa rate limiting:

- **Por IP**: 100 requests/minuto
- **Por usuario autenticado**: 200 requests/minuto
- **Endpoints de login**: 5 requests/minuto

#### CORS Configuration

```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 3600
```

---

## 🔧 Utilidades Comunes

### Paginación Estándar

Todos los endpoints que retornan listas implementan paginación:

```json
{
    "count": 150,
    "next": "http://localhost:300X/endpoint/?page=3",
    "previous": "http://localhost:300X/endpoint/?page=1",
    "results": [...]
}
```

### Filtros Comunes

**Filtros de fecha:**
- `fecha_inicio`: YYYY-MM-DD
- `fecha_fin`: YYYY-MM-DD
- `created_at__gte`: ISO timestamp
- `updated_at__lte`: ISO timestamp

**Filtros de búsqueda:**
- `search`: Búsqueda de texto libre
- `ordering`: Campo de ordenamiento (ej: `-created_at`)

### Códigos de Error Detallados

#### 400 Bad Request
```json
{
    "error": "validation_error",
    "message": "Los datos enviados no son válidos",
    "details": {
        "email": ["Este campo es requerido"],
        "password": ["La contraseña debe tener al menos 8 caracteres"]
    }
}
```

#### 401 Unauthorized
```json
{
    "error": "authentication_failed",
    "message": "Token de autenticación inválido o expirado",
    "code": "token_expired"
}
```

#### 403 Forbidden
```json
{
    "error": "permission_denied",
    "message": "No tiene permisos para realizar esta acción",
    "required_permission": "view_user_details"
}
```

#### 500 Internal Server Error
```json
{
    "error": "internal_server_error",
    "message": "Error interno del servidor",
    "request_id": "req_abc123",
    "timestamp": "2024-12-20T15:30:00Z"
}
```

---

## 🧪 Testing de APIs

### Postman Collection

Importar colección de Postman:

```json
{
    "info": {
        "name": "Sistema Pontificia API",
        "description": "Colección completa de endpoints",
        "version": "1.0.0"
    },
    "variable": [
        {
            "key": "base_url",
            "value": "http://localhost:8000"
        },
        {
            "key": "auth_token",
            "value": ""
        }
    ],
    "auth": {
        "type": "bearer",
        "bearer": [
            {
                "key": "token",
                "value": "{{auth_token}}"
            }
        ]
    }
}
```

### cURL Examples

#### Login y obtener token:
```bash
curl -X POST http://localhost:8000/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@pontificia.com",
    "password": "admin123"
  }'
```

#### Usar token para obtener perfil:
```bash
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

curl -X GET http://localhost:8000/users/profile/ \
  -H "Authorization: Bearer $TOKEN"
```

#### Subir documento:
```bash
curl -X POST http://localhost:8000/documentos/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "archivo=@documento.pdf" \
  -F "nombre=Mi Documento" \
  -F "tipo=certificado"
```

### Scripts de Testing

#### test_apis.py
```python
import requests
import json

BASE_URL = "http://localhost:8000"

def test_auth_flow():
    # Login
    response = requests.post(f"{BASE_URL}/auth/login/", json={
        "username": "admin@pontificia.com",
        "password": "admin123"
    })
    
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Use token
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/users/profile/", headers=headers)
    
    assert response.status_code == 200
    print("✅ Auth flow test passed")

def test_crud_operations():
    # Test CRUD operations here
    pass

if __name__ == "__main__":
    test_auth_flow()
    test_crud_operations()
```

---

## 📚 SDK y Clientes

### Python SDK

```python
# pontificia_sdk.py
import requests
from typing import Optional, Dict, Any

class PontificiaAPI:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token: Optional[str] = None
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        response = requests.post(f"{self.base_url}/auth/login/", json={
            "username": username,
            "password": password
        })
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        return data
    
    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def get_users(self, page: int = 1, search: str = "") -> Dict[str, Any]:
        params = {"page": page}
        if search:
            params["search"] = search
        
        response = requests.get(
            f"{self.base_url}/users/",
            headers=self._headers(),
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/users/",
            headers=self._headers(),
            json=user_data
        )
        response.raise_for_status()
        return response.json()

# Uso del SDK
api = PontificiaAPI()
api.login("admin@pontificia.com", "admin123")
users = api.get_users(search="juan")
```

### JavaScript SDK

```javascript
// pontificia-sdk.js
class PontificiaAPI {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.token = null;
    }

    async login(username, password) {
        const response = await fetch(`${this.baseUrl}/auth/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (!response.ok) throw new Error('Login failed');
        
        const data = await response.json();
        this.token = data.access_token;
        return data;
    }

    async getUsers(page = 1, search = '') {
        const params = new URLSearchParams({ page });
        if (search) params.append('search', search);
        
        const response = await fetch(`${this.baseUrl}/users/?${params}`, {
            headers: this._headers()
        });
        
        if (!response.ok) throw new Error('Failed to fetch users');
        return await response.json();
    }

    _headers() {
        const headers = { 'Content-Type': 'application/json' };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    }
}

// Uso del SDK
const api = new PontificiaAPI();
await api.login('admin@pontificia.com', 'admin123');
const users = await api.getUsers(1, 'juan');
```

---

## 📞 Soporte y Contacto

### Documentación Adicional
- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Soporte Técnico
Para issues relacionados con las APIs:
- **GitHub Issues**: Crear un issue específico
- **Email**: api-support@pontificia.com
- **Documentación**: Consultar archivos `.md` del proyecto

### Versionado de APIs
- **Versión Actual**: v1
- **Compatibilidad**: Backward compatible por al menos 6 meses
- **Deprecation Notice**: 3 meses antes de remover endpoints

---

**Versión**: 1.0.0  
**Última actualización**: Diciembre 2024  
**Mantenido por**: API Team - Sistema Pontificia