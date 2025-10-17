"""
File name: azure_blob_job_storage_manager.py
 * Last updated: 28/08/2025
 * Author: Prince Antony P
 * Last Change: BI-2135 - Added Azure Blob job handling modules to shared_kernel
"""

from shared_kernel.interfaces.storage_manager import JobStorageManager
from shared_kernel.logger import Logger
from shared_kernel.config import Config
from shared_kernel.storage_handlers.blob_file_handler import BlobFileHandler

config = Config()
logger = Logger(config.get("APP_NAME"))


class AzureBlobJobStorageManager(JobStorageManager):
    """
    Azure Blob-based storage manager for batch jobs.
    Handles uploading and downloading of job input payloads and results to/from Blob Storage.
    """

    def __init__(self, job_type: str, storage_root_folder: str = "batch_jobs"):
        """
        Initializes the Azure Blob storage manager.

        Args:
            job_type (str): Type of the job (used to organize blob paths).
            storage_root_folder (str): Base blob prefix for all jobs.
        """
        self.blob_handler = BlobFileHandler()
        self.storage_root_folder = storage_root_folder
        self.job_type = job_type

    def get_blob_key(self, job_storage_key: str) -> str:
        """
        Constructs the base blob key (path) for a given job.

        Args:
            job_storage_key (str): Unique job storage identifier.

        Returns:
            str: Base blob key for the job folder.
        """
        return f"{self.storage_root_folder}/{self.job_type}/{job_storage_key}"

    def upload_payload(self, job_storage_key: str, payload: dict) -> str:
        """
        Uploads the job input payload (input.json) to Azure Blob Storage.

        Args:
            job_storage_key (str): Unique job storage identifier.
            payload (dict): The job input payload.

        Returns:
            str: The blob key where the payload was uploaded.

        Raises:
            Exception: If the blob upload fails.
        """
        blob_key = self.get_blob_key(job_storage_key)
        blob_input_key = f"{blob_key}/input.json"

        try:
            if not self.blob_handler.upload_json(key=blob_input_key, data=payload):
                raise Exception("Upload returned False")
            logger.info(f"Uploaded job input to blob://{self.blob_handler.container}/{blob_input_key}")
            return blob_input_key
        except Exception as e:
            logger.error(f"Failed to upload payload for job_storage_key={job_storage_key}: {str(e)}")
            raise

    def upload_result(self, job_storage_key: str, result: dict) -> str:
        """
        Uploads the job result data (output.json) to Azure Blob Storage.

        Args:
            job_storage_key (str): Unique job storage identifier.
            result (dict): The job result data.

        Returns:
            str: The blob key where the result was uploaded.

        Raises:
            Exception: If the blob upload fails.
        """
        blob_key = self.get_blob_key(job_storage_key)
        blob_output_key = f"{blob_key}/output.json"

        try:
            self.blob_handler.upload_json(blob_output_key, result)
            logger.info(f"Uploaded job result to blob://{self.blob_handler.container}/{blob_output_key}")
            return blob_output_key
        except Exception as e:
            logger.error(f"Failed to upload result for job_storage_key={job_storage_key}: {str(e)}")
            raise

    def download_input(self, job_storage_key: str) -> dict:
        """
        Downloads the input payload (input.json) for a job from Azure Blob Storage.

        Args:
            job_storage_key (str): Unique job storage identifier.

        Returns:
            dict: The downloaded input payload.

        Raises:
            Exception: If the download fails.
        """
        blob_key = self.get_blob_key(job_storage_key)
        blob_input_key = f"{blob_key}/input.json"

        try:
            data = self.blob_handler.download_json(blob_input_key)
            logger.info(f"Downloaded job input from blob://{self.blob_handler.container}/{blob_input_key}")
            return data
        except Exception as e:
            logger.error(f"Failed to download input for job_storage_key={job_storage_key}: {str(e)}")
            raise

    def download_result(self, job_storage_key: str) -> dict:
        """
        Downloads the job result (output.json) from Azure Blob Storage.

        Args:
            job_storage_key (str): Unique job storage identifier.

        Returns:
            dict: The downloaded job result.

        Raises:
            Exception: If the download fails.
        """
        blob_key = self.get_blob_key(job_storage_key)
        blob_output_key = f"{blob_key}/output.json"

        try:
            result = self.blob_handler.download_json(blob_output_key)
            logger.info(f"Downloaded job result from blob://{self.blob_handler.container}/{blob_output_key}")
            return result
        except Exception as e:
            logger.error(f"Failed to download result for job_storage_key={job_storage_key}: {str(e)}")
            raise
