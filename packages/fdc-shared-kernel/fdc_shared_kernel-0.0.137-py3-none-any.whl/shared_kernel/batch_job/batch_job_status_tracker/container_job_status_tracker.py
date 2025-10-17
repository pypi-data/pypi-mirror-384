from azure.data.tables import TableServiceClient, UpdateMode
from azure.core.exceptions import ResourceNotFoundError

from shared_kernel.dataclasses.job_record_dataclasses import JobRecord
from shared_kernel.utils.date_utils import utc_now_iso



class ContainerAppJobTracker:
    """
    Tracks Azure Container Apps jobs in Table Storage.
    Each job is a row in the table, similar to AWS Batch job tracking.
    """

    def __init__(self, connection_string: str, table_name: str):
        self.table_service = TableServiceClient.from_connection_string(conn_str=connection_string)
        self.table_client = self.table_service.create_table_if_not_exists(table_name)

    def create_job(self, job: JobRecord):
        """
        Create or overwrite a job record.
        """
        job.created_at=utc_now_iso()
        job.updated_at=utc_now_iso()
        self.table_client.upsert_entity(entity=job.to_entity(), mode=UpdateMode.REPLACE)

    def update_job_status(self, job_group: str, job_id: str, new_status: str, **kwargs):
        """
        Update status of an existing job.
        """
        try:
            entity = self.table_client.get_entity(partition_key=job_group, row_key=job_id)
            entity["Status"] = new_status
            entity["UpdatedAt"] = utc_now_iso()
            entity.update(kwargs)
            self.table_client.update_entity(entity=entity, mode=UpdateMode.REPLACE)
        except ResourceNotFoundError:
            raise ValueError(f"Job {job_group}/{job_id} not found.")

    def mark_job_failed(self, job_type: str, job_id: str, reason: str, **kwargs):
        """
        Mark a job as failed with a failure reason.
        """
        self.update_job_status(job_type, job_id, new_status="FAILED", FailureReason=reason, **kwargs)

    def get_job_status(self, job_type: str, job_id: str) -> str:
        """
        Get the current status of a job.
        """
        try:
            entity = self.table_client.get_entity(partition_key=job_type, row_key=job_id)
            return entity.get("Status", "UNKNOWN")
        except ResourceNotFoundError:
            raise ValueError(f"Job {job_type}/{job_id} not found.")