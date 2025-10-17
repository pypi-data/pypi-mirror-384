"""
Template management for Schema Onboarding Tracker.

This module handles all template-related operations including
creation, retrieval, and validation of schema onboarding templates.
"""

from typing import Dict, Any, Optional

from .base_tracker import BaseSchemaOnboardingTracker
from .exceptions import InvalidTemplateDataException


class TemplateManager(BaseSchemaOnboardingTracker):
    """
    Manages schema onboarding templates.
    
    This class handles all operations related to schema onboarding templates
    including creation, retrieval, and validation.
    """

    def create_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new schema onboarding template.
        
        Args:
            template_data (Dict[str, Any]): Template data containing name, nodes, next, and conditions
            
        Returns:
            Dict[str, Any]: Response from master service
            
        Raises:
            InvalidTemplateDataException: If template data is invalid
        """
        self._validate_template_data(template_data)
        
        payload = {
            "name": template_data["name"],
            "nodes": template_data["nodes"],
            "next": template_data["next"],
            "conditions": template_data.get("conditions")
        }
        
        return self._make_request("CREATE_TEMPLATE", payload)

    def get_template(self, template_name: str) -> Dict[str, Any]:
        """
        Fetch template by name.
        
        Args:
            template_name (str): Name of the template
            
        Returns:
            Dict[str, Any]: Template data from master service
        """
        payload = {"template_name": template_name}
        response = self._make_request("GET_TEMPLATE", payload)
        return self._get_data_from_response(response)

    def _validate_template_data(self, template_data: Dict[str, Any]) -> None:
        """
        Validate template data structure.
        
        Args:
            template_data (Dict[str, Any]): Template data to validate
            
        Raises:
            InvalidTemplateDataException: If template data is invalid
        """
        required_fields = ["name", "nodes", "next"]
        
        for field in required_fields:
            if field not in template_data:
                raise InvalidTemplateDataException(f"Missing required field: {field}")
        
        if not isinstance(template_data["nodes"], dict):
            raise InvalidTemplateDataException("Nodes must be a dictionary")
        
        if not isinstance(template_data["next"], dict):
            raise InvalidTemplateDataException("Next mapping must be a dictionary")
        
        # Validate that all nodes in 'next' exist in 'nodes'
        for source_task, next_tasks in template_data["next"].items():
            if source_task not in template_data["nodes"]:
                raise InvalidTemplateDataException(f"Source task '{source_task}' not found in nodes")
            
            if not isinstance(next_tasks, list):
                raise InvalidTemplateDataException(f"Next tasks for '{source_task}' must be a list")
            
            for next_task in next_tasks:
                if next_task not in template_data["nodes"]:
                    raise InvalidTemplateDataException(f"Next task '{next_task}' not found in nodes")
