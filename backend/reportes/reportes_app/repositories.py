"""
Repositorios para el microservicio de reportes

Implementa el patrón Repository para abstracción de datos
y consultas especializadas para reportes y métricas.
"""

from django.db import models
from django.db.models import Q, Count, Sum, Avg, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Any
from decimal import Decimal

from .models import Reporte, Metrica, ReporteMetrica, TipoReporte, EstadoReporte, PeriodoMetrica


class BaseRepository:
    """
    Repositorio base con operaciones comunes
    """
    
    def __init__(self, model):
        self.model = model
    
    def crear(self, **kwargs):
        """Crea una nueva instancia"""
        return self.model.objects.create(**kwargs)
    
    def obtener_por_id(self, id):
        """Obtiene una instancia por ID"""
        try:
            return self.model.objects.get(id=id, activo=True)
        except self.model.DoesNotExist:
            return None
    
    def listar_activos(self):
        """Lista todas las instancias activas"""
        return self.model.objects.filter(activo=True)
    
    def actualizar(self, id, **kwargs):
        """Actualiza una instancia por ID"""
        try:
            instance = self.model.objects.get(id=id, activo=True)
            for key, value in kwargs.items():
                setattr(instance, key, value)
            instance.save()
            return instance
        except self.model.DoesNotExist:
            return None
    
    def eliminar_logico(self, id):
        """Eliminación lógica (marca como inactivo)"""
        try:
            instance = self.model.objects.get(id=id)
            instance.activo = False
            instance.save()
            return True
        except self.model.DoesNotExist:
            return False
    
    def contar_activos(self):
        """Cuenta las instancias activas"""
        return self.model.objects.filter(activo=True).count()


class ReporteRepository(BaseRepository):
    """
    Repositorio especializado para reportes
    """
    
    def __init__(self):
        super().__init__(Reporte)
    
    def buscar_por_autor(self, autor_id: str):
        """Busca reportes por autor"""
        return self.model.objects.filter(
            autor_id=autor_id,
            activo=True
        ).order_by('-fecha_creacion')
    
    def buscar_por_tipo(self, tipo: str):
        """Busca reportes por tipo"""
        return self.model.objects.filter(
            tipo=tipo,
            activo=True
        ).order_by('-fecha_creacion')
    
    def buscar_por_estado(self, estado: str):
        """Busca reportes por estado"""
        return self.model.objects.filter(
            estado=estado,
            activo=True
        ).order_by('-fecha_creacion')
    
    def buscar_por_fecha_rango(self, fecha_inicio: date, fecha_fin: date):
        """Busca reportes en un rango de fechas"""
        return self.model.objects.filter(
            fecha_creacion__date__gte=fecha_inicio,
            fecha_creacion__date__lte=fecha_fin,
            activo=True
        ).order_by('-fecha_creacion')
    
    def buscar_publicos(self):
        """Busca reportes públicos"""
        return self.model.objects.filter(
            publico=True,
            estado=EstadoReporte.COMPLETADO,
            activo=True
        ).order_by('-fecha_creacion')
    
    def buscar_por_tags(self, tags: List[str]):
        """Busca reportes que contengan alguno de los tags"""
        q_objects = Q()
        for tag in tags:
            q_objects |= Q(tags__contains=tag)
        
        return self.model.objects.filter(
            q_objects,
            activo=True
        ).order_by('-fecha_creacion')
    
    def obtener_pendientes(self):
        """Obtiene reportes pendientes de procesamiento"""
        return self.model.objects.filter(
            estado=EstadoReporte.PENDIENTE,
            activo=True
        ).order_by('fecha_creacion')
    
    def obtener_procesando(self):
        """Obtiene reportes en procesamiento"""
        return self.model.objects.filter(
            estado=EstadoReporte.PROCESANDO,
            activo=True
        ).order_by('fecha_inicio_procesamiento')
    
    def obtener_completados_recientes(self, dias: int = 7):
        """Obtiene reportes completados en los últimos días"""
        fecha_limite = timezone.now() - timedelta(days=dias)
        return self.model.objects.filter(
            estado=EstadoReporte.COMPLETADO,
            fecha_fin_procesamiento__gte=fecha_limite,
            activo=True
        ).order_by('-fecha_fin_procesamiento')
    
    def obtener_expirados(self):
        """Obtiene reportes expirados"""
        return self.model.objects.filter(
            fecha_expiracion__lt=timezone.now(),
            activo=True
        )
    
    def obtener_estadisticas_por_autor(self, autor_id: str):
        """Obtiene estadísticas de reportes por autor"""
        reportes = self.model.objects.filter(autor_id=autor_id, activo=True)
        
        return {
            'total': reportes.count(),
            'completados': reportes.filter(estado=EstadoReporte.COMPLETADO).count(),
            'pendientes': reportes.filter(estado=EstadoReporte.PENDIENTE).count(),
            'procesando': reportes.filter(estado=EstadoReporte.PROCESANDO).count(),
            'con_error': reportes.filter(estado=EstadoReporte.ERROR).count(),
            'por_tipo': {
                tipo.value: reportes.filter(tipo=tipo.value).count()
                for tipo in TipoReporte
            }
        }
    
    def obtener_estadisticas_generales(self, fecha_inicio: date = None, fecha_fin: date = None):
        """Obtiene estadísticas generales de reportes"""
        queryset = self.model.objects.filter(activo=True)
        
        if fecha_inicio and fecha_fin:
            queryset = queryset.filter(
                fecha_creacion__date__gte=fecha_inicio,
                fecha_creacion__date__lte=fecha_fin
            )
        
        # Estadísticas por estado
        stats_estado = {}
        for estado in EstadoReporte:
            stats_estado[estado.value] = queryset.filter(estado=estado.value).count()
        
        # Estadísticas por tipo
        stats_tipo = {}
        for tipo in TipoReporte:
            stats_tipo[tipo.value] = queryset.filter(tipo=tipo.value).count()
        
        # Tiempo promedio de procesamiento
        completados = queryset.filter(
            estado=EstadoReporte.COMPLETADO,
            tiempo_procesamiento__isnull=False
        )
        
        tiempo_promedio = None
        if completados.exists():
            tiempo_total = sum(
                (r.tiempo_procesamiento.total_seconds() for r in completados),
                0
            )
            tiempo_promedio = tiempo_total / completados.count()
        
        return {
            'total': queryset.count(),
            'por_estado': stats_estado,
            'por_tipo': stats_tipo,
            'tiempo_promedio_segundos': tiempo_promedio,
            'registros_procesados_total': queryset.aggregate(
                total=Sum('registros_procesados')
            )['total'] or 0
        }
    
    def buscar_similares(self, reporte_id: str, limite: int = 5):
        """Busca reportes similares basado en tipo y parámetros"""
        try:
            reporte = self.obtener_por_id(reporte_id)
            if not reporte:
                return self.model.objects.none()
            
            return self.model.objects.filter(
                tipo=reporte.tipo,
                activo=True
            ).exclude(
                id=reporte_id
            ).order_by('-fecha_creacion')[:limite]
            
        except Exception:
            return self.model.objects.none()
    
    def marcar_procesando(self, reporte_id: str):
        """Marca un reporte como procesando"""
        try:
            reporte = self.obtener_por_id(reporte_id)
            if reporte and reporte.estado == EstadoReporte.PENDIENTE:
                reporte.iniciar_procesamiento()
                return reporte
        except Exception:
            pass
        return None
    
    def completar_reporte(self, reporte_id: str, archivo_path: str = None, registros: int = 0):
        """Completa un reporte"""
        try:
            reporte = self.obtener_por_id(reporte_id)
            if reporte and reporte.estado == EstadoReporte.PROCESANDO:
                reporte.completar_procesamiento(archivo_path, registros)
                return reporte
        except Exception:
            pass
        return None
    
    def marcar_error(self, reporte_id: str, mensaje_error: str):
        """Marca un reporte con error"""
        try:
            reporte = self.obtener_por_id(reporte_id)
            if reporte:
                reporte.marcar_error(mensaje_error)
                return reporte
        except Exception:
            pass
        return None


class MetricaRepository(BaseRepository):
    """
    Repositorio especializado para métricas
    """
    
    def __init__(self):
        super().__init__(Metrica)
    
    def buscar_por_nombre(self, nombre: str):
        """Busca métricas por nombre"""
        return self.model.objects.filter(
            nombre__icontains=nombre,
            activo=True
        ).order_by('-fecha_calculo')
    
    def buscar_por_categoria(self, categoria: str):
        """Busca métricas por categoría"""
        return self.model.objects.filter(
            categoria=categoria,
            activo=True
        ).order_by('-fecha_calculo')
    
    def buscar_por_periodo(self, periodo: str, fecha_inicio: date, fecha_fin: date):
        """Busca métricas por período y rango de fechas"""
        return self.model.objects.filter(
            periodo=periodo,
            fecha_inicio__gte=fecha_inicio,
            fecha_fin__lte=fecha_fin,
            activo=True
        ).order_by('fecha_inicio')
    
    def obtener_metricas_recientes(self, nombre: str, limite: int = 10):
        """Obtiene las métricas más recientes de un nombre específico"""
        return self.model.objects.filter(
            nombre=nombre,
            activo=True
        ).order_by('-fecha_calculo')[:limite]
    
    def obtener_tendencia(self, nombre: str, periodo: str, numero_periodos: int = 12):
        """Obtiene tendencia de una métrica en varios períodos"""
        return self.model.objects.filter(
            nombre=nombre,
            periodo=periodo,
            activo=True
        ).order_by('-fecha_inicio')[:numero_periodos]
    
    def calcular_estadisticas_metrica(self, nombre: str, fecha_inicio: date, fecha_fin: date):
        """Calcula estadísticas de una métrica en un rango de fechas"""
        metricas = self.model.objects.filter(
            nombre=nombre,
            fecha_inicio__gte=fecha_inicio,
            fecha_fin__lte=fecha_fin,
            activo=True
        )
        
        if not metricas.exists():
            return None
        
        agregados = metricas.aggregate(
            promedio=Avg('valor'),
            maximo=Max('valor'),
            minimo=Min('valor'),
            suma=Sum('valor'),
            total=Count('id')
        )
        
        # Calcular variación
        valores = list(metricas.values_list('valor', flat=True))
        variacion = None
        if len(valores) >= 2:
            primer_valor = valores[-1]  # Más antiguo
            ultimo_valor = valores[0]   # Más reciente
            if primer_valor != 0:
                variacion = float(((ultimo_valor - primer_valor) / primer_valor) * 100)
        
        return {
            **agregados,
            'variacion_porcentual': variacion,
            'valores': valores
        }
    
    def obtener_metricas_por_alerta(self):
        """Obtiene métricas que están fuera de sus umbrales"""
        metricas_alerta = []
        
        # Métricas con valor menor al umbral mínimo
        minimo_alerta = self.model.objects.filter(
            valor__lt=models.F('umbral_minimo'),
            umbral_minimo__isnull=False,
            activo=True
        )
        
        # Métricas con valor mayor al umbral máximo
        maximo_alerta = self.model.objects.filter(
            valor__gt=models.F('umbral_maximo'),
            umbral_maximo__isnull=False,
            activo=True
        )
        
        for metrica in minimo_alerta:
            metricas_alerta.append({
                'metrica': metrica,
                'tipo_alerta': 'MINIMO',
                'mensaje': f'{metrica.nombre} está por debajo del umbral mínimo'
            })
        
        for metrica in maximo_alerta:
            metricas_alerta.append({
                'metrica': metrica,
                'tipo_alerta': 'MAXIMO',
                'mensaje': f'{metrica.nombre} está por encima del umbral máximo'
            })
        
        return metricas_alerta
    
    def obtener_resumen_categorias(self):
        """Obtiene resumen de métricas por categoría"""
        return self.model.objects.filter(activo=True).values('categoria').annotate(
            total_metricas=Count('id'),
            promedio_valor=Avg('valor'),
            suma_valor=Sum('valor')
        ).order_by('categoria')
    
    def comparar_periodos(self, nombre: str, periodo_actual: tuple, periodo_anterior: tuple):
        """Compara métricas entre dos períodos"""
        fecha_ini_actual, fecha_fin_actual = periodo_actual
        fecha_ini_anterior, fecha_fin_anterior = periodo_anterior
        
        metricas_actual = self.model.objects.filter(
            nombre=nombre,
            fecha_inicio__gte=fecha_ini_actual,
            fecha_fin__lte=fecha_fin_actual,
            activo=True
        )
        
        metricas_anterior = self.model.objects.filter(
            nombre=nombre,
            fecha_inicio__gte=fecha_ini_anterior,
            fecha_fin__lte=fecha_fin_anterior,
            activo=True
        )
        
        actual_valor = metricas_actual.aggregate(promedio=Avg('valor'))['promedio'] or 0
        anterior_valor = metricas_anterior.aggregate(promedio=Avg('valor'))['promedio'] or 0
        
        variacion = None
        if anterior_valor != 0:
            variacion = float(((actual_valor - anterior_valor) / anterior_valor) * 100)
        
        return {
            'periodo_actual': {
                'valor_promedio': float(actual_valor),
                'total_registros': metricas_actual.count()
            },
            'periodo_anterior': {
                'valor_promedio': float(anterior_valor),
                'total_registros': metricas_anterior.count()
            },
            'variacion_porcentual': variacion,
            'tendencia': 'SUBIDA' if variacion and variacion > 0 else 'BAJADA' if variacion and variacion < 0 else 'ESTABLE'
        }
    
    def crear_metrica_calculada(self, nombre: str, fuente_metricas: List[str], 
                              operacion: str, **kwargs):
        """Crea una métrica calculada basada en otras métricas"""
        try:
            # Obtener valores de las métricas fuente
            valores = []
            for metrica_nombre in fuente_metricas:
                metrica_reciente = self.model.objects.filter(
                    nombre=metrica_nombre,
                    activo=True
                ).order_by('-fecha_calculo').first()
                
                if metrica_reciente:
                    valores.append(float(metrica_reciente.valor))
            
            if not valores:
                return None
            
            # Aplicar operación
            resultado = None
            if operacion == 'SUMA':
                resultado = sum(valores)
            elif operacion == 'PROMEDIO':
                resultado = sum(valores) / len(valores)
            elif operacion == 'MAXIMO':
                resultado = max(valores)
            elif operacion == 'MINIMO':
                resultado = min(valores)
            elif operacion == 'DIFERENCIA' and len(valores) >= 2:
                resultado = valores[0] - valores[1]
            elif operacion == 'RATIO' and len(valores) >= 2 and valores[1] != 0:
                resultado = valores[0] / valores[1]
            
            if resultado is not None:
                return self.crear(
                    nombre=nombre,
                    valor=Decimal(str(resultado)),
                    fecha_inicio=date.today(),
                    fecha_fin=date.today(),
                    fuente=f"Calculada de: {', '.join(fuente_metricas)}",
                    **kwargs
                )
        
        except Exception as e:
            print(f"Error creando métrica calculada: {e}")
            return None


class ReportesRepositoryManager:
    """
    Manager principal que coordina todos los repositorios
    """
    
    def __init__(self):
        self.reportes = ReporteRepository()
        self.metricas = MetricaRepository()
    
    def obtener_dashboard_data(self, autor_id: str = None):
        """Obtiene datos para el dashboard principal"""
        data = {
            'reportes': {
                'total': self.reportes.contar_activos(),
                'completados_recientes': self.reportes.obtener_completados_recientes(7).count(),
                'pendientes': self.reportes.obtener_pendientes().count(),
                'procesando': self.reportes.obtener_procesando().count()
            },
            'metricas': {
                'total': self.metricas.contar_activos(),
                'por_categoria': list(self.metricas.obtener_resumen_categorias()),
                'alertas': len(self.metricas.obtener_metricas_por_alerta())
            }
        }
        
        if autor_id:
            data['mis_reportes'] = self.reportes.obtener_estadisticas_por_autor(autor_id)
        
        return data
    
    def buscar_contenido(self, query: str, tipo_contenido: str = 'ambos'):
        """Búsqueda unificada en reportes y métricas"""
        resultados = {'reportes': [], 'metricas': []}
        
        if tipo_contenido in ['ambos', 'reportes']:
            # Buscar en reportes por nombre y descripción
            reportes = self.reportes.model.objects.filter(
                Q(nombre__icontains=query) | 
                Q(descripcion__icontains=query) |
                Q(tags__contains=[query]),
                activo=True
            ).order_by('-fecha_creacion')[:10]
            
            resultados['reportes'] = list(reportes)
        
        if tipo_contenido in ['ambos', 'metricas']:
            # Buscar en métricas por nombre y descripción
            metricas = self.metricas.model.objects.filter(
                Q(nombre__icontains=query) |
                Q(descripcion__icontains=query) |
                Q(categoria__icontains=query),
                activo=True
            ).order_by('-fecha_calculo')[:10]
            
            resultados['metricas'] = list(metricas)
        
        return resultados