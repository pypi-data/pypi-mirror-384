import jwt
from typing import Dict
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from Osdental.Exception.ControlledException import JWTokenException
from Osdental.Shared.Logger import logger
from Osdental.Shared.Enums.Message import Message


class JWT:

    @staticmethod
    def generate_token(
        payload: Dict[str, str], jwt_secret_key: str, algorithm="HS256"
    ) -> str:
        try:
            token = jwt.encode(payload, jwt_secret_key, algorithm=algorithm)
            return token

        except Exception as e:
            logger.error(f"Unexpected jwt generating error: {str(e)}")
            raise JWTokenException(message=Message.UNEXPECTED_ERROR_MSG, error=str(e))

    @staticmethod
    def extract_payload(jwt_token: str, jwt_secret_key: str) -> Dict[str, str]:
        try:
            payload = jwt.decode(jwt_token, jwt_secret_key, algorithms=["HS256"])
            return payload

        except Exception as e:
            logger.error(f"Unexpected jwt extract payload error: {str(e)}")
            raise JWTokenException(message=Message.UNEXPECTED_ERROR_MSG, error=str(e))

    @staticmethod
    def generate_private_key(private_rsa: str):
        try:
            private_key = serialization.load_pem_private_key(
                private_rsa.encode(), password=None, backend=default_backend()
            )
            return private_key
        except Exception as e:
            logger.error(f"Unexpected jwt private key generating error: {str(e)}")
            raise JWTokenException(message=Message.UNEXPECTED_ERROR_MSG, error=str(e))
