"""
Serializers para el API Gateway
"""

from rest_framework import serializers


class ServiceStatusSerializer(serializers.Serializer):
    """
    Serializer para el estado de un servicio
    """
    service = serializers.CharField()
    status = serializers.CharField()
    response_time = serializers.FloatField(allow_null=True)
    error = serializers.CharField(allow_null=True, required=False)
    details = serializers.JSONField(required=False)


class HealthCheckSerializer(serializers.Serializer):
    """
    Serializer para health check completo
    """
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
    gateway = serializers.JSONField()
    services = serializers.DictField(child=ServiceStatusSerializer())
    summary = serializers.JSONField()


class GatewayInfoSerializer(serializers.Serializer):
    """
    Serializer para información del gateway
    """
    name = serializers.CharField()
    version = serializers.CharField()
    status = serializers.CharField()
    port = serializers.IntegerField()
    timestamp = serializers.DateTimeField()
    services = serializers.ListField(child=serializers.CharField())
    features = serializers.JSONField()
    endpoints = serializers.JSONField()


class RouteInfoSerializer(serializers.Serializer):
    """
    Serializer para información de rutas
    """
    service = serializers.CharField()
    base_url = serializers.URLField()
    gateway_routes = serializers.ListField(child=serializers.CharField())
    health_endpoint = serializers.CharField()
    status = serializers.CharField()


class ErrorResponseSerializer(serializers.Serializer):
    """
    Serializer para respuestas de error
    """
    error = serializers.CharField()
    code = serializers.CharField(required=False)
    details = serializers.CharField(required=False)
    timestamp = serializers.DateTimeField(required=False)
    service = serializers.CharField(required=False)


class ProxyRequestSerializer(serializers.Serializer):
    """
    Serializer para documentar requests proxeadas
    """
    method = serializers.CharField()
    path = serializers.CharField()
    service = serializers.CharField()
    headers = serializers.JSONField(required=False)
    params = serializers.JSONField(required=False)
    data = serializers.JSONField(required=False)


class ProxyResponseSerializer(serializers.Serializer):
    """
    Serializer para documentar responses proxeadas
    """
    status_code = serializers.IntegerField()
    headers = serializers.JSONField()
    data = serializers.JSONField()
    response_time = serializers.FloatField()


class RateLimitErrorSerializer(serializers.Serializer):
    """
    Serializer para errores de rate limiting
    """
    error = serializers.CharField(default="Rate limit exceeded")
    limit = serializers.CharField()
    retry_after = serializers.IntegerField()


class JWTErrorSerializer(serializers.Serializer):
    """
    Serializer para errores de JWT
    """
    error = serializers.CharField()
    code = serializers.CharField()
    details = serializers.CharField(required=False)


class CircuitBreakerSerializer(serializers.Serializer):
    """
    Serializer para estado del circuit breaker
    """
    service = serializers.CharField()
    state = serializers.CharField()  # CLOSED, OPEN, HALF_OPEN
    failure_count = serializers.IntegerField()
    last_failure_time = serializers.FloatField(allow_null=True)
    failure_threshold = serializers.IntegerField()
    recovery_timeout = serializers.IntegerField()


class GatewayStatsSerializer(serializers.Serializer):
    """
    Serializer para estadísticas del gateway
    """
    total_requests = serializers.IntegerField()
    successful_requests = serializers.IntegerField()
    failed_requests = serializers.IntegerField()
    average_response_time = serializers.FloatField()
    active_services = serializers.IntegerField()
    total_services = serializers.IntegerField()
    uptime = serializers.CharField()
    last_reset = serializers.DateTimeField()


class ServiceConnectionTestSerializer(serializers.Serializer):
    """
    Serializer para test de conexión a servicio
    """
    service = serializers.CharField()
    connection_test = serializers.CharField()
    response_time = serializers.CharField(required=False)
    health_status = serializers.CharField(required=False)
    error = serializers.CharField(required=False)
    base_url = serializers.URLField()
    timestamp = serializers.DateTimeField()