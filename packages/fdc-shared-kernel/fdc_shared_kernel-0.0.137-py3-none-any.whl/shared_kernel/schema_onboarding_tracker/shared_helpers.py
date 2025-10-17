"""
Shared helper methods for Schema Onboarding Tracker.

This module contains common helper methods used across multiple managers
to avoid code duplication and maintain consistency.
"""

from typing import Dict, Any, List

from .base_tracker import BaseSchemaOnboardingTracker


class SharedHelpers(BaseSchemaOnboardingTracker):
    """
    Shared helper methods for schema onboarding tracker operations.
    
    This class contains common helper methods that are used across
    multiple managers to avoid code duplication.
    """

    def get_run_data(self, run_id: str) -> Dict[str, Any]:
        """
        Get run data from master service.
        
        Args:
            run_id (str): Run ID
            
        Returns:
            Dict[str, Any]: Run data
        """
        payload = {"run_id": run_id}
        response = self._make_request("GET_RUN", payload)
        return self._get_data_from_response(response)

    def get_template_data(self, template_name: str) -> Dict[str, Any]:
        """
        Get template data from master service.
        
        Args:
            template_name (str): Template name
            
        Returns:
            Dict[str, Any]: Template data
        """
        payload = {"template_name": template_name}
        response = self._make_request("GET_TEMPLATE", payload)
        return self._get_data_from_response(response)

    def get_all_tasks_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Get all tasks for a run from master service.
        
        Args:
            run_id (str): Run ID
            
        Returns:
            List[Dict[str, Any]]: List of task data
        """
        payload = {"run_id": run_id}
        response = self._make_request("GET_TASKS_BY_RUN", payload)
        return self._get_data_from_response(response)
