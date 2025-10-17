"""
Task management for Schema Onboarding Tracker.

This module handles all task-related operations including
creation, status updates, and retrieval of schema onboarding tasks.
"""

from typing import Dict, Any, Optional, List

from .base_tracker import BaseSchemaOnboardingTracker
from .enums import TaskStatus
from .exceptions import InvalidTaskDataException
from .task_helpers import TaskHelpers


class TaskManager(BaseSchemaOnboardingTracker):
    """
    Manages schema onboarding tasks.
    
    This class handles all operations related to schema onboarding tasks
    including creation, status updates, and retrieval.
    """

    def __init__(self):
        """Initialize the task manager with helpers."""
        super().__init__()
        self._task_helpers = TaskHelpers()

    def create_tasks_for_run(self, run_id: str) -> List[str]:
        """
        Create tasks for a run dynamically based on the template.
        
        Args:
            run_id (str): Run ID
            
        Returns:
            List[str]: List of created task IDs
        """
        self._validate_run_id(run_id)
        
        # Get run details to get template name
        run_data = self._task_helpers.get_run_data(run_id)
        template_name = run_data.get("template_name")
        
        # Get template to understand the nodes
        template_data = self._task_helpers.get_template_data(template_name)
        
        # Create tasks based on template nodes
        created_task_ids = []
        
        for task_name, task_config in template_data.get("nodes", {}).items():
            # Get dependencies for this task
            dependencies = self._task_helpers.get_task_dependencies(task_name, template_data.get("next", {}))
            
            # Create individual task
            task_id = self._task_helpers.create_single_task(
                run_id=run_id,
                task_name=task_name,
                handler=task_config.get("handler"),
                dependencies=dependencies
            )
            created_task_ids.append(task_id)
        
        return created_task_ids

    def update_task_status(self, task_id: str, status: TaskStatus, 
                          output: Optional[str] = None, error: Optional[str] = None, 
                          error_message: Optional[str] = None, 
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update task status and timestamps.
        
        Args:
            task_id (str): Task ID
            status (TaskStatus): New status
            output (Optional[str]): Task output
            error (Optional[str]): Error details
            error_message (Optional[str]): Error message
            metadata (Optional[Dict[str, Any]]): Additional metadata
            
        Returns:
            Dict[str, Any]: Response from master service
        """
        self._validate_task_id(task_id)
        
        payload = {
            "task_id": task_id,
            "status": status.value,
            "output": output,
            "error": error,
            "error_message": error_message,
            "metadata": metadata
        }
        
        return self._make_request("UPDATE_TASK_STATUS", payload)

    def increment_task_attempts(self, task_id: str) -> Dict[str, Any]:
        """
        Increment attempts for retries.
        
        Args:
            task_id (str): Task ID
            
        Returns:
            Dict[str, Any]: Response from master service containing new attempt count
        """
        self._validate_task_id(task_id)
        
        payload = {"task_id": task_id}
        return self._make_request("INCREMENT_TASK_ATTEMPTS", payload)

    def get_task(self, task_id: Optional[str] = None, 
                 task_name: Optional[str] = None, 
                 run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch task details by task_id, task_name, or run_id.
        
        Args:
            task_id (Optional[str]): Task ID
            task_name (Optional[str]): Task name
            run_id (Optional[str]): Run ID
            
        Returns:
            Dict[str, Any]: Task data from master service
        """
        self._validate_task_query_params(task_id, task_name, run_id)
        
        payload = {}
        if task_id:
            payload["task_id"] = task_id
        elif task_name and run_id:
            payload["task_name"] = task_name
            payload["run_id"] = run_id
        elif run_id:
            payload["run_id"] = run_id
        
        response = self._make_request("GET_TASK", payload)
        return self._get_data_from_response(response)

    def get_tasks_by_run(self, run_id: str) -> Dict[str, Any]:
        """
        Fetch all tasks for a run.
        
        Args:
            run_id (str): Run ID
            
        Returns:
            Dict[str, Any]: List of task data from master service
        """
        self._validate_run_id(run_id)
        
        payload = {"run_id": run_id}
        response = self._make_request("GET_TASKS_BY_RUN", payload)
        return self._get_data_from_response(response)

    def _validate_task_id(self, task_id: str) -> None:
        """
        Validate task ID.
        
        Args:
            task_id (str): Task ID to validate
            
        Raises:
            InvalidTaskDataException: If task ID is invalid
        """
        if not task_id or not isinstance(task_id, str):
            raise InvalidTaskDataException("Task ID must be a non-empty string")

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

    def _validate_task_query_params(self, task_id: Optional[str], 
                                   task_name: Optional[str], 
                                   run_id: Optional[str]) -> None:
        """
        Validate task query parameters.
        
        Args:
            task_id (Optional[str]): Task ID parameter
            task_name (Optional[str]): Task name parameter
            run_id (Optional[str]): Run ID parameter
            
        Raises:
            InvalidTaskDataException: If parameters are invalid
        """
        if not task_id and not (task_name and run_id) and not run_id:
            raise InvalidTaskDataException(
                "Must provide task_id, (task_name and run_id), or run_id"
            )

