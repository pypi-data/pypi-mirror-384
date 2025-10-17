"""
Utility methods for Schema Onboarding Tracker.

This module provides utility methods for checking run completion
and getting run summaries.
"""

from typing import Dict, Any

from .shared_helpers import SharedHelpers
from .exceptions import InvalidTaskDataException
from .enums import TaskStatus


class UtilityManager(SharedHelpers):
    """
    Provides utility methods for schema onboarding tracker.
    
    This class handles utility operations like checking run completion
    and getting run summaries.
    """

    def is_run_complete(self, run_id: str) -> bool:
        """
        Check if all tasks in a run are completed.
        
        Args:
            run_id (str): Run ID
            
        Returns:
            bool: True if all tasks are completed
        """
        self._validate_run_id(run_id)
        
        # Get all tasks for this run
        all_tasks = self.get_all_tasks_for_run(run_id)
        
        if not all_tasks:
            return False
        
        # Check if all tasks are completed (SUCCESS or FAILED)
        for task in all_tasks:
            if task["status"] not in [TaskStatus.SUCCESS.value, TaskStatus.FAILED.value]:
                return False
        
        return True

    def get_run_summary(self, run_id: str) -> Dict[str, Any]:
        """
        Get a summary of run status and task counts.
        
        Args:
            run_id (str): Run ID
            
        Returns:
            Dict[str, Any]: Run summary
        """
        self._validate_run_id(run_id)
        
        # Get run details
        run_data = self.get_run_data(run_id)
        
        # Get all tasks for this run
        all_tasks = self.get_all_tasks_for_run(run_id)
        
        # Count tasks by status
        task_counts = {
            "total": len(all_tasks),
            "pending": 0,
            "running": 0,
            "success": 0,
            "failed": 0
        }
        
        for task in all_tasks:
            status = task["status"]
            if status == TaskStatus.PENDING.value:
                task_counts["pending"] += 1
            elif status == TaskStatus.RUNNING.value:
                task_counts["running"] += 1
            elif status == TaskStatus.SUCCESS.value:
                task_counts["success"] += 1
            elif status == TaskStatus.FAILED.value:
                task_counts["failed"] += 1
        
        return {
            "run_id": run_data["id"],
            "template_name": run_data["template_name"],
            "model_id": run_data["model_id"],
            "status": run_data["status"],
            "started_at": run_data["started_at"],
            "completed_at": run_data["completed_at"],
            "task_counts": task_counts,
            "is_complete": self.is_run_complete(run_id)
        }

    def _validate_run_id(self, run_id: str) -> None:
        """
        Validate run ID.
        
        Args:
            run_id (str): Run ID to validate
            
        Raises:
            InvalidTaskDataException: If run ID is invalid
        """
        if not run_id or not isinstance(run_id, str):
            raise InvalidTaskDataException("Run ID must be a non-empty string")

