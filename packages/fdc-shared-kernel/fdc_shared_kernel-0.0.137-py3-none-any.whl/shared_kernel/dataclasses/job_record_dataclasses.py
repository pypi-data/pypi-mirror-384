from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class JobRecord:
    """
    Represents a job/task record stored in Azure Table Storage.
    """
    job_id: str                   # maps to RowKey
    job_type: str                # maps to PartitionKey
    job_status: str               # e.g., SUBMITTED, RUNNING, SUCCEEDED, FAILED
    failure_reason: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None   # custom metadata
    created_at: Optional[str] = None           # ISO timestamp
    updated_at: Optional[str] = None

    def to_entity(self) -> Dict[str, Any]:
        """
        Convert the dataclass into an Azure Table Storage entity.
        """
        entity = {
            "PartitionKey": self.job_type,
            "RowKey": self.job_id,
            "Status": self.job_status
        }
        if self.failure_reason:
            entity["FailureReason"] = self.failure_reason
        if self.payload:
            entity["Payload"] = str(self.payload)   # serialize as string
        if self.created_at:
            entity["CreatedAt"] = self.created_at
        if self.updated_at:
            entity["UpdatedAt"] = self.updated_at
        return entity