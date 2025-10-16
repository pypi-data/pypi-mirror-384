import grpc
from Osdental.Models.Response import Response
from Osdental.Decorators.Retry import grpc_retry
from Osdental.Grpc.Generated import Common_pb2
from Osdental.Grpc.Generated import Portal_pb2_grpc
from Osdental.Shared.Config import Config
from Osdental.Exception.ControlledException import OSDException


class PortalClient:
    def __init__(self, host=Config.SECURITY_GRPC_HOST, port=Config.SECURITY_GRPC_PORT):
        if not host:
            raise OSDException('SECURITY_GRPC_HOST is not set')

        if port:
            self.url = f'{host}:{port}'
            self.secure = False
        else:
            self.url = host
            self.secure = True

        self.channel = None
        self.stub = None

    def _ensure_connected(self):
        if not self.channel or not self.stub:
            if self.secure:
                creds = grpc.ssl_channel_credentials()
                self.channel = grpc.aio.secure_channel(self.url, creds)
            else:
                self.channel = grpc.aio.insecure_channel(self.url)
            self.stub = Portal_pb2_grpc.PortalStub(self.channel)

    @grpc_retry
    async def get_legacy(self) -> Response:
        self._ensure_connected()
        request = Common_pb2.Empty()
        return await self.stub.GetLegacy(request)

    @grpc_retry
    async def validate_auth_token(self, request) -> Response:
        self._ensure_connected()
        request = Common_pb2.Request(data=request)
        return await self.stub.ValidateAuthToken(request)
