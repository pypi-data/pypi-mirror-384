"""
Helper methods for Task Manager.

This module contains helper methods for task management operations
to keep the main task_manager.py file under 200 lines.
"""

from typing import Dict, Any, List, Optional

from .shared_helpers import SharedHelpers


class TaskHelpers(SharedHelpers):
    """
    Helper methods for task management operations.
    
    This class contains helper methods that support the main TaskManager
    to keep the code organized and maintainable.
    """


    def get_task_dependencies(self, task_name: str, next_mapping: Dict[str, List[str]]) -> List[str]:
        """
        Get dependencies for a task based on the next mapping.
        
        Args:
            task_name (str): Task name
            next_mapping (Dict[str, List[str]]): Next task mapping
            
        Returns:
            List[str]: List of dependency task names
        """
        dependencies = []
        for source_task, next_tasks in next_mapping.items():
            if task_name in next_tasks:
                dependencies.append(source_task)
        return dependencies

    def create_single_task(self, run_id: str, task_name: str, 
                          handler: Optional[str], dependencies: List[str]) -> str:
        """
        Create a single task via master service.
        
        Args:
            run_id (str): Run ID
            task_name (str): Task name
            handler (Optional[str]): Task handler
            dependencies (List[str]): Task dependencies
            
        Returns:
            str: Created task ID
        """
        payload = {
            "run_id": run_id,
            "task_name": task_name,
            "handler": handler,
            "dependencies": dependencies
        }
        
        response = self._make_request("CREATE_SINGLE_TASK", payload)
        return response.get("task_id")
