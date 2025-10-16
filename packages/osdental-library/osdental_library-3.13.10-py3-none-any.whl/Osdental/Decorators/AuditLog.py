import json
import asyncio
import logging
import time
from typing import List, Dict, Any
from functools import wraps
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from Osdental.InternalHttp.Request import CustomRequest
from Osdental.InternalHttp.Response import CustomResponse
from Osdental.Encryptor.Rsa import RSAEncryptor
from Osdental.Exception.ControlledException import OSDException, RSAEncryptException, AESEncryptException
from Osdental.Encryptor.Aes import AES
from Osdental.Shared.Utils.TextProcessor import TextProcessor
from Osdental.Shared.Logger import logger as custom_logger
from Osdental.Models.Legacy import Legacy
from Osdental.Grpc.Client.PortalClient import PortalClient
from Osdental.Shared.Enums.Code import Code
from Osdental.Shared.Config import Config
from Osdental.Shared.Enums.Constant import Constant

portal_client = PortalClient()
aes = AES()

# Configuration Azure Monitor
configure_azure_monitor(
    connection_string=Config.APPLICATIONINSIGHTS_CONNECTION_STRING
)
# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('graphql')
logger.setLevel(logging.INFO)
# Tracer for spans
tracer = trace.get_tracer(__name__)

def split_into_batches(data: List[Any], batch:int = 250):
    for i in range(0, len(data), batch):
        yield data[i:i + batch]

def try_decrypt_or_return_raw(data: str, private_key_rsa: str, aes_key: str) -> str:
    try:
        return RSAEncryptor.decrypt(data, private_key_rsa, silent=True)
    except RSAEncryptException:
        try:
            return aes.decrypt(aes_key, data, silent=True)
        except AESEncryptException:
            return data

def enqueue_response(data: Any, batch: int, headers: Dict[str,str], msg_info: str = None):
    if data and isinstance(data, list):
        if batch > 0 and len(data) > batch:
            batches = split_into_batches(data, batch)
            for idx, data_batch in enumerate(batches, start=1):
                custom_response = CustomResponse(content=json.dumps(data_batch), headers=headers, batch=idx)
                _ = asyncio.create_task(custom_response.send_to_service_bus())
        else:
            custom_response = CustomResponse(content=json.dumps(data), headers=headers)
            _ = asyncio.create_task(custom_response.send_to_service_bus())
    else:
        content = json.dumps(data) if isinstance(data, dict) else msg_info
        custom_response = CustomResponse(content=content, headers=headers)
        _ = asyncio.create_task(custom_response.send_to_service_bus())


def handle_audit_and_exception(batch: int = 0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            headers = {}
            operation_name = 'UnknownOperation'
            
            # Extract request and operation name before opening the span
            try:
                _, info = args[:2] 
                request = info.context.get('request')
                headers = info.context.get('headers') or {}
                
                if request:
                    body = await request.body()
                    try:
                        body_data = json.loads(body.decode("utf-8"))
                        operation_name = body_data.get('operationName', 'UnknownOperation')
                    except Exception:
                        pass
                    
                    # Send audit of the request to Service Bus
                    custom_request = CustomRequest(request)
                    _ = asyncio.create_task(custom_request.send_to_service_bus())

            except Exception as ex:
                logger.warning(f"Failed to extract operationName: {ex}")

            # Open the span with the correct operation name
            with tracer.start_as_current_span(f"GraphQL.{operation_name}") as span:
                start_time = time.time()
                try:
                    # Get legacy
                    res = await portal_client.get_legacy()
                    data = json.loads(res.data)
                    legacy = Legacy.from_db(data) if res.status == Code.PROCESS_SUCCESS_CODE else None

                    # Run the resolver
                    response = await func(*args, **kwargs)

                    # Prepare data and message
                    msg_info = TextProcessor.concatenate(response.get('status'), '-', response.get('message'))
                    raw_data = response.get('data')
                    data_to_enqueue = None
                    if raw_data:
                        data_to_enqueue = try_decrypt_or_return_raw(raw_data, legacy.private_key2, legacy.aes_key_auth)

                    # Enqueue response
                    enqueue_response(data_to_enqueue, batch, headers, msg_info)

                    # Measure duration
                    duration = (time.time() - start_time) * 1000

                    # Span attributes
                    span.set_attribute(Constant.GRAPHQL_OPERATION_NAME, operation_name)
                    span.set_attribute(Constant.GRAPHQL_STATUS, response.get('status'))
                    span.set_attribute(Constant.GRAPHQL_MESSAGE, response.get('message'))
                    span.set_attribute(Constant.GRAPHQL_DURATION_MS, duration)

                    return response

                except OSDException as ex:
                    # Controlled log
                    custom_logger.error(f'Controlled error: {str(ex)}')      
                    duration = (time.time() - start_time) * 1000
                    msg = str(ex) if str(ex) else getattr(ex, 'message', 'OSDException')
                    span.set_attribute(Constant.GRAPHQL_OPERATION_NAME, operation_name)
                    span.set_attribute(Constant.GRAPHQL_STATUS, ex.status_code)
                    span.set_attribute(Constant.GRAPHQL_MESSAGE, msg)
                    span.set_attribute(Constant.GRAPHQL_DURATION_MS, duration)
                    ex.headers = headers
                    span.record_exception(ex)

                    _ = asyncio.create_task(ex.send_to_service_bus())
                    return ex.get_response()

                except Exception as e:
                    # Unhandled exception log and span
                    custom_logger.error(f'Unexpected error: {str(e)}')      
                    ex = OSDException(error=str(e), headers=headers)
                    msg = str(e) if str(e) else getattr(ex, 'message', 'Unknown Exception')
                    duration = (time.time() - start_time) * 1000
                    span.set_attribute(Constant.GRAPHQL_OPERATION_NAME, operation_name)
                    span.set_attribute(Constant.GRAPHQL_STATUS, ex.status_code)
                    span.set_attribute(Constant.GRAPHQL_MESSAGE, msg)
                    span.record_exception(e)
                    span.set_status(trace.status.Status(trace.status.StatusCode.ERROR))
                    span.set_attribute(Constant.GRAPHQL_DURATION_MS, duration)
                    
                    _ = asyncio.create_task(ex.send_to_service_bus())
                    return ex.get_response()

        return wrapper
    return decorator