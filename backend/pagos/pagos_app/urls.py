"""
URLs para el microservicio de pagos

Define todas las rutas REST para el sistema de pagos,
planillas, boletas y adelantos.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Crear router principal
router = DefaultRouter()

# Registrar ViewSets en el router
router.register(r'pagos', views.PagoViewSet, basename='pago')
router.register(r'planillas', views.PlanillaViewSet, basename='planilla')
router.register(r'boletas', views.BoletaViewSet, basename='boleta')
router.register(r'adelantos', views.AdelantoViewSet, basename='adelanto')
router.register(r'descuentos', views.DescuentoViewSet, basename='descuento')
router.register(r'bonificaciones', views.BonificacionViewSet, basename='bonificacion')

# URLs de la aplicación
urlpatterns = [
    # API endpoints principales
    path('api/v1/', include(router.urls)),
    
    # Endpoints adicionales de autenticación si es necesario
    # path('api/auth/', include('rest_framework.urls')),
]

"""
URLs disponibles:

PAGOS:
- GET /api/v1/pagos/ - Listar pagos con filtros
- POST /api/v1/pagos/ - Crear nuevo pago
- GET /api/v1/pagos/{id}/ - Obtener pago específico
- PUT /api/v1/pagos/{id}/ - Actualizar pago completo
- PATCH /api/v1/pagos/{id}/ - Actualizar pago parcial
- DELETE /api/v1/pagos/{id}/ - Eliminar pago
- POST /api/v1/pagos/{id}/aprobar/ - Aprobar pago
- POST /api/v1/pagos/{id}/marcar_pagado/ - Marcar como pagado
- POST /api/v1/pagos/{id}/anular/ - Anular pago
- GET /api/v1/pagos/estadisticas/ - Estadísticas de pagos
- GET /api/v1/pagos/por_trabajador/ - Pagos por trabajador

PLANILLAS:
- GET /api/v1/planillas/ - Listar planillas
- POST /api/v1/planillas/ - Crear planilla
- GET /api/v1/planillas/{id}/ - Obtener planilla
- PUT /api/v1/planillas/{id}/ - Actualizar planilla
- PATCH /api/v1/planillas/{id}/ - Actualizar planilla parcial
- DELETE /api/v1/planillas/{id}/ - Eliminar planilla
- POST /api/v1/planillas/generar_planilla/ - Generar planilla completa
- POST /api/v1/planillas/{id}/aprobar/ - Aprobar planilla
- GET /api/v1/planillas/{id}/pagos/ - Pagos de una planilla
- GET /api/v1/planillas/{id}/exportar_excel/ - Exportar a Excel
- GET /api/v1/planillas/estadisticas_anuales/ - Estadísticas anuales

BOLETAS:
- GET /api/v1/boletas/ - Listar boletas
- POST /api/v1/boletas/ - Crear boleta
- GET /api/v1/boletas/{id}/ - Obtener boleta
- PUT /api/v1/boletas/{id}/ - Actualizar boleta
- PATCH /api/v1/boletas/{id}/ - Actualizar boleta parcial
- DELETE /api/v1/boletas/{id}/ - Eliminar boleta
- POST /api/v1/boletas/generar_boleta/ - Generar boleta individual
- GET /api/v1/boletas/{id}/descargar_pdf/ - Descargar PDF
- POST /api/v1/boletas/{id}/enviar_email/ - Enviar por email
- POST /api/v1/boletas/generar_masivo/ - Generar boletas masivas

ADELANTOS:
- GET /api/v1/adelantos/ - Listar adelantos
- POST /api/v1/adelantos/ - Crear adelanto
- GET /api/v1/adelantos/{id}/ - Obtener adelanto
- PUT /api/v1/adelantos/{id}/ - Actualizar adelanto
- PATCH /api/v1/adelantos/{id}/ - Actualizar adelanto parcial
- DELETE /api/v1/adelantos/{id}/ - Eliminar adelanto
- POST /api/v1/adelantos/{id}/aprobar/ - Aprobar adelanto
- POST /api/v1/adelantos/{id}/rechazar/ - Rechazar adelanto
- POST /api/v1/adelantos/{id}/marcar_pagado/ - Marcar como pagado
- GET /api/v1/adelantos/por_trabajador/ - Adelantos por trabajador
- GET /api/v1/adelantos/estadisticas/ - Estadísticas de adelantos

DESCUENTOS:
- GET /api/v1/descuentos/ - Listar descuentos
- POST /api/v1/descuentos/ - Crear descuento
- GET /api/v1/descuentos/{id}/ - Obtener descuento
- PUT /api/v1/descuentos/{id}/ - Actualizar descuento
- PATCH /api/v1/descuentos/{id}/ - Actualizar descuento parcial
- DELETE /api/v1/descuentos/{id}/ - Eliminar descuento

BONIFICACIONES:
- GET /api/v1/bonificaciones/ - Listar bonificaciones
- POST /api/v1/bonificaciones/ - Crear bonificación
- GET /api/v1/bonificaciones/{id}/ - Obtener bonificación
- PUT /api/v1/bonificaciones/{id}/ - Actualizar bonificación
- PATCH /api/v1/bonificaciones/{id}/ - Actualizar bonificación parcial
- DELETE /api/v1/bonificaciones/{id}/ - Eliminar bonificación

FILTROS Y PARÁMETROS:

Para Pagos:
- ?estado=CALCULADO,APROBADO,PAGADO,ANULADO
- ?planilla__año=2024
- ?planilla__mes=1
- ?trabajador_id=123
- ?fecha_inicio=2024-01-01&fecha_fin=2024-01-31
- ?monto_min=1000&monto_max=5000
- ?search=nombre_trabajador o documento
- ?ordering=-fecha_calculo,monto_neto

Para Planillas:
- ?año=2024
- ?mes=1
- ?procesada=true
- ?aprobada=true
- ?search=nombre_planilla
- ?ordering=-año,-mes

Para Boletas:
- ?pago__estado=APROBADO
- ?pago__trabajador_id=123
- ?search=nombre_trabajador
- ?ordering=-fecha_generacion

Para Adelantos:
- ?estado=PENDIENTE,APROBADO,RECHAZADO,PAGADO
- ?trabajador_id=123
- ?solo_pendientes=true
- ?fecha_inicio=2024-01-01&fecha_fin=2024-01-31
- ?search=nombre_trabajador,motivo
- ?ordering=-fecha_solicitud

Para Descuentos/Bonificaciones:
- ?tipo=PORCENTAJE,MONTO_FIJO
- ?obligatorio=true (solo descuentos)
- ?imponible=true (solo bonificaciones)
- ?search=nombre,descripcion
- ?ordering=nombre

PAGINACIÓN:
Todos los endpoints soportan paginación:
- ?page=1
- ?page_size=20

RESPUESTAS:
- 200: OK - Operación exitosa
- 201: Created - Recurso creado
- 400: Bad Request - Error de validación
- 401: Unauthorized - No autenticado
- 403: Forbidden - Sin permisos
- 404: Not Found - Recurso no encontrado
- 500: Internal Server Error - Error interno
"""