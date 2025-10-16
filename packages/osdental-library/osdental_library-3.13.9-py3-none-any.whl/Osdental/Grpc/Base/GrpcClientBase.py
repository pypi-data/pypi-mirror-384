import json
from abc import ABC, abstractmethod
import grpc
from Osdental.Exception.ControlledException import OSDException
from Osdental.Grpc.Generated import Common_pb2
from Osdental.Models.Response import Response


class GrpcClientBase(ABC):

    def __init__(self, host: str, port: str | None = None):
        if not host:
            raise OSDException(f"{self.__class__.__name__}: host is not set")

        self.host = host
        self.port = port.strip() if port else None
        self.channel = None
        self.stub = None

        self.url = f"{self.host}:{self.port}" if self.port else self.host

    @property
    @abstractmethod
    def stub_class(self):
        pass

    def _ensure_connected(self):
        if not self.channel or not self.stub:
            if self.port:
                self.channel = grpc.aio.insecure_channel(self.url)
            else:
                creds = grpc.ssl_channel_credentials()
                self.channel = grpc.aio.secure_channel(self.url, creds)

            self.stub = self.stub_class(self.channel)


    async def _call(self, method_name: str, request_data: str) -> Response:
        self._ensure_connected()

        method = getattr(self.stub, method_name)
        to_json = json.dumps(request_data)
        request = Common_pb2.Request(data=to_json)

        proto_response = await method(request)

        mapped = Response(
            status=proto_response.status,
            message=proto_response.message,
            data=json.loads(proto_response.data)
        )
        return mapped
