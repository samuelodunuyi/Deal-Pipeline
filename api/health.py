from django.db import connection, OperationalError
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        checks = {}
        http_code = status.HTTP_200_OK

        try:
            connection.ensure_connection()
            checks['db'] = 'ok'
        except OperationalError as exc:
            checks['db'] = str(exc)
            http_code = status.HTTP_503_SERVICE_UNAVAILABLE

        try:
            cache.set('__health__', 'ok', 5)
            val = cache.get('__health__')
            checks['cache'] = 'ok' if val == 'ok' else 'miss'
        except Exception as exc:
            checks['cache'] = str(exc)

        ok = http_code == status.HTTP_200_OK
        return Response(
            {'status': ok, 'message': 'ok' if ok else 'degraded', 'data': checks},
            status=http_code,
        )
