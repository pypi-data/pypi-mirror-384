"""
File name: azure_apps_job_handler.py
 * Last updated: 25/09/2025
 * Author: Sanjeev Shaji
 * Azure Container Apps Job process
"""

import time
from azure.storage.queue import QueueServiceClient, QueueMessage
from azure.core.exceptions import AzureError

from shared_kernel.batch_job.batch_job_status_tracker.container_job_status_tracker import ContainerAppJobTracker
from shared_kernel.batch_job.job_handlers.job_status_mapper import JOB_STATUS_TO_TASK_STATUS
from shared_kernel.config import Config
from shared_kernel.dataclasses.azure_container_app_job_context import AzureContainerAppJobContext
from shared_kernel.dataclasses.job_record_dataclasses import JobRecord
from shared_kernel.exceptions.batch_job_exceptions import BatchJobFailedException
from shared_kernel.interfaces.base_job_handler import BaseJobHandler
from shared_kernel.interfaces.storage_manager import JobStorageManager
from shared_kernel.logger import Logger
from shared_kernel.status_tracker.status_tracker import StatusTracker
from shared_kernel.enums.status_tracker import TaskStatus


config = Config()
logger = Logger(config.get("APP_NAME"))


class AzureContainerAppsJobHandler(BaseJobHandler):
    """
    Handles the lifecycle of Azure Container Apps jobs with Azure Blob Storage payload exchange.

    Core Responsibilities:
    - Submitting Azure Container Apps jobs with the given configuration.
    - Polling job status until completion or failure.
    - Uploading input payloads to the configured storage.
    - Downloading job results from the configured storage.
    - Updating and tracking job status using StatusTracker.
    """
    def __init__(self, storage_manager: JobStorageManager):
        """
        Initialize the AzureBatchJobHandler.

        Args:
            storage_manager (JobStorageManager): The storage manager for payload and result handling.
        """
        self.container_apps_client = None
        self.container_app_job_tracker = None
        self.storage_manager: JobStorageManager = storage_manager
        self.status_tracker = StatusTracker()
        

    def submit_job(self, job_context: AzureContainerAppJobContext) -> str:
        """
        Submit an Azure Container Apps job to the queue.

        Steps:
        1. Push job payload into Azure Queue.
        2. Record job submission in the ContainerAppJobTracker.
        3. Create an initial QUEUED task in the StatusTracker.

        Args:
            job_context (AzureContainerAppJobContext): Context containing job name,
                queue information, and payload.

        Returns:
            str: The Azure queue message ID that acts as the job_id.

        Raises:
            BatchJobFailedException: If the job submission fails.
        """
        try:
            
            job_context.job_id = self.submit_job_to_queue(job_context=job_context)
            logger.info(f"Submitted Azure Batch job {job_context.job_name} with ID {job_context.job_id}")
            self.record_job_submission(job_context=job_context)
            self.status_tracker.create_task(
                event_msg=job_context.to_status_event(),
                status=TaskStatus.QUEUED.value
            )
            return job_context.job_id
        except Exception as e:
            logger.error(f"Failed to submit Azure Batch job {job_context.job_name}: {str(e)}")
            raise

    def submit_job_to_queue(self, job_context: AzureContainerAppJobContext) -> str:
        """
        Submit a job message to the Azure Queue and ensure it was successfully sent.
        
        Args:
            job_context (AzureContainerAppJobContext): Contains queue info and payload.
            
        Returns:
            str: The ID of the enqueued message.
        
        Raises:
            BatchJobFailedException: If message could not be sent.
        """
        try:
            queue_service = QueueServiceClient.from_connection_string(job_context.job_queue_connection_string)
            self.container_apps_client = queue_service.get_queue_client(job_context.job_queue)
            job_payload = job_context.to_message_payload()
            # Send the message with TTL of 1 hour
            message_info: QueueMessage = self.container_apps_client.send_message(content=job_payload, time_to_live=3600)
            # Check if message_info contains a valid message_id
            if not getattr(message_info, "id", None):
                raise BatchJobFailedException(
                    job_type=job_context.job_type,
                    job_id=None,
                    job_name=job_context.job_name,
                    reason="Failed to enqueue message: no message ID returned."
                )

            return message_info.id
        except AzureError as e:
            # Catch Azure SDK errors explicitly
            raise BatchJobFailedException(
                job_type=job_context.job_type,
                job_id=None,
                job_name=job_context.job_name,
                reason=f"Azure Queue error: {str(e)}"
            )
        except Exception as e:
            # Catch any other unexpected errors
            raise BatchJobFailedException(
                job_type=job_context.job_type,
                job_id=None,
                job_name=job_context.job_name,
                reason=f"Unexpected error sending job message: {str(e)}"
            )
        
    def record_job_submission(self, job_context: AzureContainerAppJobContext):
        self.container_app_job_tracker = ContainerAppJobTracker(connection_string=job_context.job_queue_connection_string, table_name=config.get("CONTAINER_APP_JOB_TRACKER_TABLE"))
        job_record = JobRecord(job_id=job_context.job_id, job_type=job_context.job_type, job_status="SUBMITTED", payload=job_context.metadata)
        self.container_app_job_tracker.create_job(job=job_record)


    def wait_for_job_completion(
        self,
        job_context: AzureContainerAppJobContext,
        timeout: int = 240,
        poll_interval: int = 10
    ) -> None:
        """
        Poll the ContainerAppJobTracker for job completion status.

        This loop:
        - Continuously checks job status in the tracker.
        - Updates StatusTracker whenever job status changes.
        - Stops when job is COMPLETED, FAILED, or times out.

        Args:
            job_context (AzureContainerAppJobContext): Context with job details.
            timeout (int): Maximum wait time (seconds) before giving up.
            poll_interval (int): Time interval (seconds) between polls.

        Raises:
            TimeoutError: If the job does not complete within the timeout.
            BatchJobFailedException: If job fails during execution.
        """
        start_time = time.time()
        while True:
            try:
                status_str = self.container_app_job_tracker.get_job_status(job_type=job_context.job_type, job_id=job_context.job_id)
                new_status = JOB_STATUS_TO_TASK_STATUS.get(status_str)

                if new_status and new_status != job_context.job_status:
                    logger.info(f"Job {job_context.job_id} status changed from {job_context.job_status} to {new_status.value}")
                    self.status_tracker.update_task(
                        event_msg=job_context.to_status_event(),
                        status=new_status.value
                    )
                    job_context.job_status = new_status

                if status_str == "COMPLETED":
                    logger.info(f"Job {job_context.job_id} completed successfully.")
                    return

                if status_str == "FAILED":
                    self.handle_failed_batch_job(job_context=job_context)

                if time.time() - start_time > timeout:
                    logger.error(f"Timeout waiting for job {job_context.job_id}")
                    raise TimeoutError(f"Job {job_context.job_id} did not complete within {timeout} seconds.")

                time.sleep(poll_interval)
            except BatchJobFailedException:
                raise
            except Exception as e:
                logger.error(f"Error while polling job {job_context.job_id}: {str(e)}")
                raise

    def process_job(self, payload: dict, job_context: AzureContainerAppJobContext) -> dict:
        """
        Orchestrates the full lifecycle of an Azure Container Apps job.

        Steps:
        1. Upload input payload to configured storage.
        2. Submit job to Azure Queue.
        3. Wait for job to complete (poll status tracker).
        4. Download and validate job result.
        5. Return processed job output.

        Args:
            payload (dict): The input payload for the job.
            job_context (AzureContainerAppJobContext): Context containing job metadata.

        Returns:
            dict: Job result data.

        Raises:
            BatchJobFailedException: If job fails or no output is found.
        """
        try:
            logger.info(f"Starting Azure container apps job process for: {job_context.job_name}")
            self.storage_manager.upload_payload(job_storage_key=job_context.job_storage_key, payload=payload)
            self.submit_job(job_context=job_context)
            self.wait_for_job_completion(job_context=job_context)
            result = self.storage_manager.download_result(job_storage_key=job_context.job_storage_key)

            if not result or not isinstance(result, dict):
                raise BatchJobFailedException(
                    job_type=job_context.job_type,
                    job_id=job_context.job_id,
                    job_name=job_context.job_name,
                    reason="Job succeeded but no output found in configured storage"
                )
            if result.get("error"):
                raise BatchJobFailedException(
                    job_type=job_context.job_type,
                    job_id=job_context.job_id,
                    job_name=job_context.job_name,
                    reason=result.get("message")
                )
            logger.info(f"Completed Azure container apps job process for: {job_context.job_name}")
            return result.get("data")
        except BatchJobFailedException:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch result for {job_context.job_name}: {str(e)}")
            raise BatchJobFailedException(
                job_type=job_context.job_type,
                job_id=job_context.job_id,
                job_name=job_context.job_name,
                reason=f"{str(e)}"
            )

    def handle_failed_batch_job(self, job_context: AzureContainerAppJobContext):
        """
        Handles failed Azure Container Apps jobs.

        Steps:
        - Extract failure reason (from result storage if available).
        - Update StatusTracker with failure details.
        - Raise BatchJobFailedException with error info.

        Args:
            job_context (AzureContainerAppJobContext): The context of the failed job.

        Raises:
            BatchJobFailedException: Always raised to propagate failure upstream.
        """
        failure_reason = self._extract_failure_reason(job_context)
        logger.error(f"Job {job_context.job_id} failed during execution due to {failure_reason}.")
        self.status_tracker.mark_task_as_failure(
            **job_context.get_failure_event_info(failure_reason)
        )
        raise BatchJobFailedException(
            job_type=job_context.job_type,
            job_id=job_context.job_id,
            reason=failure_reason,
            job_name=job_context.job_name
        )

    def _extract_failure_reason(self, job_context: AzureContainerAppJobContext) -> str:
        """
        Extract failure reason for a failed Azure job.

        - Attempts to download job result from storage.
        - If result contains an error, use its message.
        - Otherwise, return "Unknown failure".

        Args:
            job_context (AzureContainerAppJobContext): Context containing job metadata.

        Returns:
            str: Failure reason string.
        """
        failure_reason = None
        try:
            result = self.storage_manager.download_result(job_storage_key=job_context.job_storage_key)
            if result and result.get("error"):
                failure_reason = result.get("message")
        except Exception as e:
            logger.warning(f"[Failure Reason Fallback] Could not download failure result from Blob for job {job_context.job_id}: {str(e)}")
        return failure_reason  
