import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env', override=True)

class Config:
    SECURITY_GRPC_HOST = os.getenv('SECURITY_GRPC_HOST')
    SECURITY_GRPC_PORT = os.getenv('SECURITY_GRPC_PORT', None)
    BLOB_CONNECTION_STRING = os.getenv('BLOB_CONNECTION_STRING')
    BLOB_CONTAINER_NAME = os.getenv('BLOB_CONTAINER_NAME')
    APPLICATIONINSIGHTS_CONNECTION_STRING = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
    MICROSERVICE_NAME = os.getenv('MICROSERVICE_NAME')
    JWT_USER_KEY = os.getenv('JWT_USER_KEY')
    ENVIRONMENT = os.getenv('ENVIRONMENT')
    MICROSERVICE_VERSION = os.getenv('MICROSERVICE_VERSION')
