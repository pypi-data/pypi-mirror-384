"""
Main Schema Onboarding Status Tracker.

This module provides the main SchemaOnboardingTracker class that orchestrates
all the individual managers for a unified interface.
"""

from typing import Dict, Any, Optional, List

from .base_tracker import BaseSchemaOnboardingTracker
from .template_manager import TemplateManager
from .run_manager import RunManager
from .task_manager import TaskManager
from .task_determination import TaskDetermination
from .utility_manager import UtilityManager
from .enums import RunStatus, TaskStatus


class SchemaOnboardingTracker(BaseSchemaOnboardingTracker):
    """
    Main Schema Onboarding Status Tracker.
    
    This class provides a unified interface for managing schema onboarding processes,
    including run management, task management, and next task determination.
    It orchestrates all the individual managers for a cohesive API.
    """
    
    def __init__(self):
        """Initialize the tracker with all managers."""
        super().__init__()
        self._template_manager = TemplateManager()
        self._run_manager = RunManager()
        self._task_manager = TaskManager()
        self._task_determination = TaskDetermination()
        self._utility_manager = UtilityManager()

    # Template Management Methods
    def create_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new schema onboarding template.
        
        Args:
            template_data (Dict[str, Any]): Template data containing name, nodes, next, and conditions
            
        Returns:
            Dict[str, Any]: Response from master service
        """
        return self._template_manager.create_template(template_data)

    def get_template(self, template_name: str) -> Dict[str, Any]:
        """
        Fetch template by name.
        
        Args:
            template_name (str): Name of the template
            
        Returns:
            Dict[str, Any]: Template data from master service
        """
        return self._template_manager.get_template(template_name)

    # Run Management Methods
    def create_run(self, template_name: str, model_id: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new onboarding run.
        
        Args:
            template_name (str): Name of the template to use
            model_id (str): Model ID for this run
            metadata (Optional[Dict[str, Any]]): Additional metadata
            
        Returns:
            Dict[str, Any]: Response from master service containing run_id
        """
        return self._run_manager.create_run(template_name, model_id, metadata)

    def update_run_status(self, run_id: str, status: RunStatus, 
                         metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update run status and timestamps.
        
        Args:
            run_id (str): Run ID
            status (RunStatus): New status
            metadata (Optional[Dict[str, Any]]): Additional metadata to update
            
        Returns:
            Dict[str, Any]: Response from master service
        """
        return self._run_manager.update_run_status(run_id, status, metadata)

    def get_run(self, run_id: Optional[str] = None, 
                model_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch run details by run_id or model_id.
        
        Args:
            run_id (Optional[str]): Run ID
            model_id (Optional[str]): Model ID
            
        Returns:
            Dict[str, Any]: Run data from master service
        """
        return self._run_manager.get_run(run_id, model_id)

    # Task Management Methods
    def create_tasks_for_run(self, run_id: str) -> List[str]:
        """
        Create tasks for a run dynamically based on the template.
        
        Args:
            run_id (str): Run ID
            
        Returns:
            List[str]: List of created task IDs
        """
        return self._task_manager.create_tasks_for_run(run_id)

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
        return self._task_manager.update_task_status(
            task_id, status, output, error, error_message, metadata
        )

    def increment_task_attempts(self, task_id: str) -> Dict[str, Any]:
        """
        Increment attempts for retries.
        
        Args:
            task_id (str): Task ID
            
        Returns:
            Dict[str, Any]: Response from master service containing new attempt count
        """
        return self._task_manager.increment_task_attempts(task_id)

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
        return self._task_manager.get_task(task_id, task_name, run_id)

    def get_tasks_by_run(self, run_id: str) -> Dict[str, Any]:
        """
        Fetch all tasks for a run.
        
        Args:
            run_id (str): Run ID
            
        Returns:
            Dict[str, Any]: List of task data from master service
        """
        return self._task_manager.get_tasks_by_run(run_id)

    # Task Determination Methods
    def get_next_eligible_tasks(self, run_id: str, completed_task_name: str) -> List[Dict[str, Any]]:
        """
        Determine eligible next tasks based on completed task and template rules.
        
        Args:
            run_id (str): Run ID
            completed_task_name (str): Name of the completed task
            
        Returns:
            List[Dict[str, Any]]: List of eligible next tasks
        """
        return self._task_determination.get_next_eligible_tasks(run_id, completed_task_name)

    def get_initial_tasks(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Get initial tasks that have no dependencies and are ready to start.
        
        Args:
            run_id (str): Run ID
            
        Returns:
            List[Dict[str, Any]]: List of initial tasks
        """
        return self._task_determination.get_initial_tasks(run_id)

    # Utility Methods
    def is_run_complete(self, run_id: str) -> bool:
        """
        Check if all tasks in a run are completed.
        
        Args:
            run_id (str): Run ID
            
        Returns:
            bool: True if all tasks are completed
        """
        return self._utility_manager.is_run_complete(run_id)

    def get_run_summary(self, run_id: str) -> Dict[str, Any]:
        """
        Get a summary of run status and task counts.
        
        Args:
            run_id (str): Run ID
            
        Returns:
            Dict[str, Any]: Run summary from master service
        """
        return self._utility_manager.get_run_summary(run_id)