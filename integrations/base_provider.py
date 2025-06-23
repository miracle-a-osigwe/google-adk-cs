"""Base classes for customer data providers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime

from entities.customer import Customer


class IntegrationConfig(BaseModel):
    """Configuration for data provider integrations."""
    provider_type: str
    provider_name: str
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database_url: Optional[str] = None
    custom_config: Dict[str, Any] = {}
    field_mappings: Dict[str, str] = {}
    enabled: bool = True


class CustomerDataProvider(ABC):
    """Abstract base class for customer data providers."""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.provider_type = config.provider_type
        self.provider_name = config.provider_name
    
    @abstractmethod
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID."""
        pass
    
    @abstractmethod
    async def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email address."""
        pass
    
    @abstractmethod
    async def get_customer_by_phone(self, phone: str) -> Optional[Customer]:
        """Get customer by phone number."""
        pass
    
    @abstractmethod
    async def create_customer(self, customer_data: Dict[str, Any]) -> Customer:
        """Create new customer record."""
        pass
    
    @abstractmethod
    async def update_customer(self, customer: Customer) -> bool:
        """Update existing customer record."""
        pass
    
    @abstractmethod
    async def get_customer_history(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get customer interaction history."""
        pass
    
    @abstractmethod
    async def search_customers(self, query: str, limit: int = 10) -> List[Customer]:
        """Search customers by query."""
        pass
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test provider connection."""
        try:
            # Basic connection test - override in specific providers
            return {
                "status": "success",
                "provider": self.provider_name,
                "message": "Connection test not implemented"
            }
        except Exception as e:
            return {
                "status": "error",
                "provider": self.provider_name,
                "error": str(e)
            }
    
    def map_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map provider fields to standard Customer model fields."""
        if not self.config.field_mappings:
            return data
        
        mapped_data = {}
        for standard_field, provider_field in self.config.field_mappings.items():
            if provider_field in data:
                mapped_data[standard_field] = data[provider_field]
        
        # Include unmapped fields in custom_fields
        unmapped_fields = {
            k: v for k, v in data.items() 
            if k not in self.config.field_mappings.values()
        }
        if unmapped_fields:
            mapped_data["custom_fields"] = unmapped_fields
        
        return mapped_data


class DataValidationError(Exception):
    """Exception raised for data validation errors."""
    pass


class ProviderConnectionError(Exception):
    """Exception raised for provider connection errors."""
    pass