"""
Base tracker class for Schema Onboarding Tracker.

This module contains the base tracker class with common functionality
and singleton pattern implementation.
"""

from typing import Dict, Any

from shared_kernel.interfaces.databus import DataBus
from shared_kernel.messaging import DataBusFactory
from shared_kernel.registries.schema_onboarding_event_registry import SchemaOnboardingEventRegistry
from .exceptions import SchemaOnboardingTrackerException

schema_onboarding_event_registry = SchemaOnboardingEventRegistry()


class BaseSchemaOnboardingTracker:
    """
    Base class for Schema Onboarding Tracker with common functionality.
    
    This class provides the singleton pattern implementation and common
    databus communication methods.
    """
    
    _instance = None

    def __new__(cls):
        """
        Override __new__ to ensure singleton pattern.
        """
        if cls._instance is None:
            cls._instance = super(BaseSchemaOnboardingTracker, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the databus connection."""
        self.databus: DataBus = DataBusFactory.create_data_bus(
            bus_type="HTTP", config={}
        )

    def _make_request(self, event_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the master service via databus.
        
        Args:
            event_name (str): Name of the event to call
            payload (Dict[str, Any]): Payload to send
            
        Returns:
            Dict[str, Any]: Response from master service
            
        Raises:
            SchemaOnboardingTrackerException: If request fails
        """
        try:
            response = self.databus.request_event(
                getattr(schema_onboarding_event_registry, event_name), payload
            )
            return response
        except Exception as e:
            raise SchemaOnboardingTrackerException(f"Request failed for {event_name}: {str(e)}")

    def _get_data_from_response(self, response: Dict[str, Any]) -> Any:
        """
        Extract data from response.
        
        Args:
            response (Dict[str, Any]): Response from master service
            
        Returns:
            Any: Data from response
        """
        return response.get("data")
