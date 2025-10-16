from functools import wraps
import json
from Osdental.Grpc.Generated import Common_pb2

def grpc_response(func):
    """
    Decorator that:
    - Converts request.data to a dict and passes it to the function as 'payload'.
    - Returns a Common_pb2.Response with status, message, and data.
    """
    @wraps(func)
    async def wrapper(self, request, context, *args, **kwargs):
        try:
            try:
                payload = json.loads(request.data)
            except (ValueError, TypeError):
                payload = request.data
            
            result = await func(self, payload, context, *args, **kwargs)
            
            return Common_pb2.Response(
                status=result.get('status'),
                message=result.get('message'),
                data=result.get('data')
            )
        except Exception as e:
            return Common_pb2.Response(
                status='DB_ERROR',
                message=str(e),
                data=None
            )
    return wrapper
