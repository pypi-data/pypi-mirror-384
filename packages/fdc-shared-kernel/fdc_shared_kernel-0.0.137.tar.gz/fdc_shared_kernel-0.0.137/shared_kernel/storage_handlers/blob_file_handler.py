"""
File name: blob_file_handler.py
 * Last updated: 28/08/2025
 * Author: Prince Antony P
 * Last Change: Migration - Added Azure Blob job handling modules to shared_kernel
"""

import json
from azure.storage.blob import BlobServiceClient
from shared_kernel.config import Config
from shared_kernel.logger import Logger

config = Config()
logger = Logger(config.get("APP_NAME"))


class BlobFileHandler:
    """
    Utility class for handling JSON file operations in Azure Blob Storage.

    Provides methods to upload and download JSON content to/from the
    configured data lake blob container.
    """

    def __init__(self):
        """
        Initializes the BlobServiceClient and sets the target container from configuration.
        """
        self.blob_service_client = BlobServiceClient.from_connection_string(config.get("AZURE_STORAGE_CONNECTION_STRING"))
        self.container = config.get("FDC_DATA_LAKE_CONTAINER")

    def upload_json(self, key: str, data: dict):
        """
        Uploads a dictionary as a JSON file to the configured Blob container.

        Args:
            key (str): The blob name (path) to store the file.
            data (dict): The Python dictionary to upload as JSON.

        Returns:
            bool: True if upload is successful.

        Raises:
            Exception: Any error raised by azure-storage-blob during upload.
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(container=self.container, blob=key)
            blob_client.upload_blob(
                json.dumps(data),
                blob_type="BlockBlob",
                overwrite=True,
                content_settings=None
            )
            logger.info(f"Uploaded json file to Blob: {self.container}/{key}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload json to Blob: {str(e)}")
            raise

    def download_json(self, key: str):
        """
        Downloads a JSON file from the configured Blob container and returns it as a dictionary.

        Args:
            key (str): The blob name (path) to fetch.

        Returns:
            dict: Parsed JSON content as a Python dictionary.

        Raises:
            Exception: Any error raised by azure-storage-blob or JSON decoding.
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(container=self.container, blob=key)
            blob_data = blob_client.download_blob().readall()
            result = json.loads(blob_data)
            return result
        except Exception as e:
            logger.error(f"Failed to download json from Blob: {str(e)}")
            raise
