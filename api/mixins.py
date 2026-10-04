from rest_framework.response import Response
from rest_framework import status as http_status


class EnvelopeMixin:
    """
    Wraps responses in {"status": bool, "message": str, "data": ...}.
    List responses add a top-level "pagination" object next to "data".
    Works alongside APIView / generic views without changing URLs or response shape.
    """

    def success(self, data=None, message='', http_code=http_status.HTTP_200_OK, pagination=None):
        payload = {'status': True, 'message': message, 'data': data}
        if pagination is not None:
            payload['pagination'] = pagination
        return Response(payload, status=http_code)

    def created(self, data=None, message='Created successfully'):
        return Response({'status': True, 'message': message, 'data': data}, status=http_status.HTTP_201_CREATED)

    def deleted(self, message='Deleted successfully'):
        return Response({'status': True, 'message': message, 'data': None}, status=http_status.HTTP_204_NO_CONTENT)

    def bad_request(self, message='Invalid data', errors=None):
        payload = {'status': False, 'message': message}
        if errors is not None:
            payload['errors'] = errors
        return Response(payload, status=http_status.HTTP_400_BAD_REQUEST)

    def not_found(self, message='Not found'):
        return Response({'status': False, 'message': message, 'data': None}, status=http_status.HTTP_404_NOT_FOUND)
