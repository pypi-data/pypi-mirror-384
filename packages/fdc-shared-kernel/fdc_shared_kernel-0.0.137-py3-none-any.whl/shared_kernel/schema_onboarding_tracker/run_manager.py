"""
Run management for Schema Onboarding Tracker.

This module handles all run-related operations including
creation, status updates, and retrieval of schema onboarding runs.
"""

from typing import Dict, Any, Optional

from .base_tracker import BaseSchemaOnboardingTracker
from .enums import RunStatus
from .exceptions import InvalidRunDataException


class RunManager(BaseSchemaOnboardingTracker):
    """
    Manages schema onboarding runs.
    
    This class handles all operations related to schema onboarding runs
    including creation, status updates, and retrieval.
    """

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
        self._validate_run_creation_data(template_name, model_id)
        
        payload = {
            "template_name": template_name,
            "model_id": model_id,
            "metadata": metadata
        }
        
        return self._make_request("CREATE_RUN", payload)

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
        self._validate_run_id(run_id)
        
        payload = {
            "run_id": run_id,
            "status": status.value,
            "metadata": metadata
        }
        
        return self._make_request("UPDATE_RUN_STATUS", payload)

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
        self._validate_run_query_params(run_id, model_id)
        
        payload = {}
        if run_id:
            payload["run_id"] = run_id
        elif model_id:
            payload["model_id"] = model_id
        
        response = self._make_request("GET_RUN", payload)
        return self._get_data_from_response(response)

    def _validate_run_creation_data(self, template_name: str, model_id: str) -> None:
        """
        Validate run creation data.
        
        Args:
            template_name (str): Template name to validate
            model_id (str): Model ID to validate
            
        Raises:
            InvalidRunDataException: If data is invalid
        """
        if not template_name or not isinstance(template_name, str):
            raise InvalidRunDataException("Template name must be a non-empty string")
        
        if not model_id or not isinstance(model_id, str):
            raise InvalidRunDataException("Model ID must be a non-empty string")

    def _validate_run_id(self, run_id: str) -> None:
        """
        Validate run ID.
        
        Args:
            run_id (str): Run ID to validate
            
        Raises:
            InvalidRunDataException: If run ID is invalid
        """
        if not run_id or not isinstance(run_id, str):
            raise InvalidRunDataException("Run ID must be a non-empty string")

    def _validate_run_query_params(self, run_id: Optional[str], 
                                  model_id: Optional[str]) -> None:
        """
        Validate run query parameters.
        
        Args:
            run_id (Optional[str]): Run ID parameter
            model_id (Optional[str]): Model ID parameter
            
        Raises:
            InvalidRunDataException: If parameters are invalid
        """
        if not run_id and not model_id:
            raise InvalidRunDataException("Either run_id or model_id must be provided")
