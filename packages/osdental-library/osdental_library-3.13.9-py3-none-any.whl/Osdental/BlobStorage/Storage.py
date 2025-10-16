from azure.storage.blob.aio import BlobServiceClient
from Osdental.Exception.ControlledException import AzureException
from Osdental.Shared.Logger import logger
from Osdental.Shared.Enums.Message import Message
from Osdental.Shared.Config import Config

class BlobStorage: 

    @staticmethod
    async def get_file(file_path:str) -> bytes:
        """ Download a file from blob storage """
        try:
            blob_service_client = BlobServiceClient.from_connection_string(Config.BLOB_CONNECTION_STRING)
            async with blob_service_client:
                container_client = blob_service_client.get_container_client(Config.BLOB_CONTAINER_NAME)
                blob_client = container_client.get_blob_client(file_path)
                blob_data = await blob_client.download_blob()
                file_bytes = await blob_data.readall()
                return file_bytes
        except Exception as e:
            logger.error(f'Unexpected blob storage error when retrieving file: {str(e)}')
            raise AzureException(message=Message.UNEXPECTED_ERROR_MSG, error=str(e)) 

    @staticmethod
    async def store_file(file_bytes:bytes, file_path:str) -> None:
        """ Upload a file to blob storage """
        try:
            blob_service_client = BlobServiceClient.from_connection_string(Config.BLOB_CONNECTION_STRING)
            async with blob_service_client:
                container_client = blob_service_client.get_container_client(Config.BLOB_CONTAINER_NAME)
                blob_client = container_client.get_blob_client(file_path)
                await blob_client.upload_blob(file_bytes, overwrite=True)
        except Exception as e:
            logger.error(f'Unexpected blob storage error when saving file: {str(e)}')
            raise AzureException(message=Message.UNEXPECTED_ERROR_MSG, error=str(e)) 

    @staticmethod
    async def delete_file(file_path:str) -> None:
        """ Delete a file from blob storage """
        try:
            blob_service_client = BlobServiceClient.from_connection_string(Config.BLOB_CONNECTION_STRING)
            async with blob_service_client:
                container_client = blob_service_client.get_container_client(Config.BLOB_CONTAINER_NAME)
                blob_client = container_client.get_blob_client(file_path)
                await blob_client.delete_blob()
        except Exception as e:
            logger.error(f'Unexpected blob storage error when deleting file: {str(e)}')
            raise AzureException(message=Message.UNEXPECTED_ERROR_MSG, error=str(e)) 
