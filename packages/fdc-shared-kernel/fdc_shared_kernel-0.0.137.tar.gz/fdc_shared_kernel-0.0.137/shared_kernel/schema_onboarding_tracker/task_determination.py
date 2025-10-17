"""
Task determination logic for Schema Onboarding Tracker.

This module handles the logic for determining next eligible tasks
and initial tasks based on template rules and dependencies.
"""

from typing import Dict, Any, List

from .shared_helpers import SharedHelpers
from .exceptions import InvalidTaskDataException
from .enums import TaskStatus


class TaskDetermination(SharedHelpers):
    """
    Handles task determination logic.
    
    This class provides methods to determine which tasks are eligible
    to run based on completed tasks and template dependencies.
    """

    def get_next_eligible_tasks(self, run_id: str, completed_task_name: str) -> List[Dict[str, Any]]:
        """
        Determine eligible next tasks based on completed task and template rules.
        
        Args:
            run_id (str): Run ID
            completed_task_name (str): Name of the completed task
            
        Returns:
            List[Dict[str, Any]]: List of eligible next tasks
        """
        self._validate_task_determination_params(run_id, completed_task_name)
        
        # Get run details to get template name
        run_data = self.get_run_data(run_id)
        template_name = run_data.get("template_name")
        
        # Get template to understand the flow
        template_data = self.get_template_data(template_name)
        
        # Get all tasks for this run
        all_tasks = self.get_all_tasks_for_run(run_id)
        task_status_map = {task["task_name"]: task for task in all_tasks}
        
        # Get next tasks from template
        next_tasks = template_data.get("next", {}).get(completed_task_name, [])
        eligible_tasks = []
        
        for next_task_name in next_tasks:
            if next_task_name not in task_status_map:
                continue
            
            next_task = task_status_map[next_task_name]
            
            # Skip if task is already completed or running
            if next_task["status"] in [TaskStatus.SUCCESS.value, TaskStatus.RUNNING.value]:
                continue
            
            # Check if task dependencies are satisfied
            if self._are_dependencies_satisfied(next_task, task_status_map, template_data.get("conditions")):
                eligible_tasks.append(next_task)
        
        return eligible_tasks

    def get_initial_tasks(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Get initial tasks that have no dependencies and are ready to start.
        
        Args:
            run_id (str): Run ID
            
        Returns:
            List[Dict[str, Any]]: List of initial tasks
        """
        self._validate_run_id(run_id)
        
        # Get run details to get template name
        run_data = self.get_run_data(run_id)
        template_name = run_data.get("template_name")
        
        # Get template to understand the flow
        template_data = self.get_template_data(template_name)
        
        # Get all tasks for this run
        all_tasks = self.get_all_tasks_for_run(run_id)
        task_status_map = {task["task_name"]: task for task in all_tasks}
        
        initial_tasks = []
        
        for task in all_tasks:
            # Skip if task is already completed or running
            if task["status"] in [TaskStatus.SUCCESS.value, TaskStatus.RUNNING.value]:
                continue
            
            # Check if task has no dependencies or all dependencies are satisfied
            if self._are_dependencies_satisfied(task, task_status_map, template_data.get("conditions")):
                initial_tasks.append(task)
        
        return initial_tasks

    def _validate_task_determination_params(self, run_id: str, completed_task_name: str) -> None:
        """
        Validate task determination parameters.
        
        Args:
            run_id (str): Run ID to validate
            completed_task_name (str): Completed task name to validate
            
        Raises:
            InvalidTaskDataException: If parameters are invalid
        """
        if not run_id or not isinstance(run_id, str):
            raise InvalidTaskDataException("Run ID must be a non-empty string")
        
        if not completed_task_name or not isinstance(completed_task_name, str):
            raise InvalidTaskDataException("Completed task name must be a non-empty string")

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


    def _are_dependencies_satisfied(self, task: Dict[str, Any], 
                                   task_status_map: Dict[str, Dict[str, Any]], 
                                   conditions: Dict[str, Any]) -> bool:
        """
        Check if task dependencies and conditions are satisfied.
        
        Args:
            task: Task to check
            task_status_map: Map of task names to task objects
            conditions: Template conditions
            
        Returns:
            bool: True if dependencies are satisfied
        """
        # Check basic dependencies
        if task.get("dependencies"):
            for dep_name in task["dependencies"]:
                if dep_name not in task_status_map:
                    return False
                dep_task = task_status_map[dep_name]
                if dep_task["status"] != TaskStatus.SUCCESS.value:
                    return False
        
        # Check template conditions
        if conditions and task["task_name"] in conditions:
            condition = conditions[task["task_name"]]
            condition_type = condition.get("type", "AND")
            required_tasks = condition.get("requires", [])
            
            if condition_type == "AND":
                # All required tasks must be completed
                for req_task_name in required_tasks:
                    if req_task_name not in task_status_map:
                        return False
                    req_task = task_status_map[req_task_name]
                    if req_task["status"] != TaskStatus.SUCCESS.value:
                        return False
            
            elif condition_type == "OR":
                # At least one required task must be completed
                any_completed = False
                for req_task_name in required_tasks:
                    if req_task_name in task_status_map:
                        req_task = task_status_map[req_task_name]
                        if req_task["status"] == TaskStatus.SUCCESS.value:
                            any_completed = True
                            break
                if not any_completed:
                    return False
        
        return True
