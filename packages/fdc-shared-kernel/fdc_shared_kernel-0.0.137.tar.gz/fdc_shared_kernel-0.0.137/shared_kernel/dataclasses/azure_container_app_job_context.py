"""
File name: azure_container_app_job_context.py
 * Last upadted: 23/09/2025
 * Author: Sanjeev Shaji
 * Last Change: FWDF-33 - Added azure container app job context
"""

from dataclasses import dataclass
import json
from typing import Dict, Optional
from .job_context import JobContext

@dataclass
class AzureContainerAppJobContext(JobContext):
    """
    Azure container apps job-specific job context.

    Attributes:
        job_name (str): Name of the job.
        job_queue (str): Target container job queue where the job will be submitted.
        job_queue_connection_string (str): Azure storage account connection string.
        job_id (Optional[str]): The AWS Batch job ID (assigned after submission).
        metadata (Optional[Dict[str, str]]): Additional message payload
                                            to pass to the job container.
    """
    job_name: Optional[str] = None
    job_queue: Optional[str] = None
    job_queue_connection_string: Optional[str] = None
    job_id: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None  # Additional env vars

    def __post_init__(self):
        """
        Validates that required azure container job message fields are set.
        """
        if not self.job_name:
            raise ValueError("AzureContainerAppsJob requires 'job_name' to be set.")
        if not self.job_queue:
            raise ValueError("AzureContainerAppsJob requires 'job_queue' to be set.")
        if not self.job_queue_connection_string:
            raise ValueError("AzureContainerAppsJob requires 'job_queue_connection_string' to be set.")
    
    def to_message_payload(self) -> Dict[str, any]:
        """
        Constructs the AzureContainerAppJob submission payload.

        Returns:
            Dict[str, any]: A dictionary containing:
                            - jobName: Name of the job.
                            - jobQueue: Target AWS Batch queue.
                            - job_queue_connection_string (str): Azure storage account connection string.
                            - metadata: job specific payload like metric_id
        """

        message_payload = {
                "jobName": self.job_name,
                "jobQueue": self.job_queue,
                "jobDefinition": self.job_queue_connection_string,
                "JOB_STORAGE_TYPE": self.job_storage_type,
                "JOB_STORAGE_KEY": self.job_storage_key,
                "JOB_TYPE": self.job_type
            }
        message_payload.update({k.upper(): str(v) for k, v in self.metadata.items()})
        return json.dumps(message_payload)