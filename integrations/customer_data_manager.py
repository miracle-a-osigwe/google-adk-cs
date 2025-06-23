"""Customer data manager for handling multiple providers and data gathering."""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from .base_provider import CustomerDataProvider, IntegrationConfig
from .crm.salesforce_provider import SalesforceProvider
from .crm.hubspot_provider import HubSpotProvider
from .crm.zendesk_provider import ZendeskProvider
from .ecommerce.shopify_provider import ShopifyProvider
from .database.postgres_provider import PostgreSQLProvider
from entities.customer import Customer
from models.business_config import BusinessConfig

logger = logging.getLogger(__name__)


class CustomerDataManager:
    """Manages customer data across multiple providers with fallback strategies."""
    
    def __init__(self, business_config: BusinessConfig):
        self.business_config = business_config
        self.providers: Dict[str, CustomerDataProvider] = {}
        self.primary_provider: Optional[CustomerDataProvider] = None
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize configured data providers."""
        for provider_config in self.business_config.data_providers:
            if not provider_config.enabled:
                continue
            
            try:
                provider = self._create_provider(provider_config)
                self.providers[provider_config.provider_name] = provider
                
                # Set primary provider
                if provider_config.provider_name == self.business_config.primary_data_provider:
                    self.primary_provider = provider
                    
            except Exception as e:
                logger.error(f"Failed to initialize provider {provider_config.provider_name}: {str(e)}")
    
    def _create_provider(self, config: IntegrationConfig) -> CustomerDataProvider:
        """Create provider instance based on type."""
        provider_classes = {
            "salesforce": SalesforceProvider,
            "hubspot": HubSpotProvider,
            "zendesk": ZendeskProvider,
            "shopify": ShopifyProvider,
            "postgresql": PostgreSQLProvider
        }
        
        provider_class = provider_classes.get(config.provider_type)
        if not provider_class:
            raise ValueError(f"Unknown provider type: {config.provider_type}")
        
        return provider_class(config)
    
    async def get_customer(
        self, 
        identifier: str, 
        identifier_type: str = "id",
        provider_name: Optional[str] = None
    ) -> Optional[Customer]:
        """
        Get customer by identifier with fallback strategy.
        
        Args:
            identifier: Customer identifier (ID, email, phone)
            identifier_type: Type of identifier ("id", "email", "phone")
            provider_name: Specific provider to use (optional)
        
        Returns:
            Customer object or None if not found
        """
        providers_to_try = []
        
        if provider_name and provider_name in self.providers:
            providers_to_try = [self.providers[provider_name]]
        else:
            # Try primary provider first, then others
            if self.primary_provider:
                providers_to_try.append(self.primary_provider)
            
            for provider in self.providers.values():
                if provider != self.primary_provider:
                    providers_to_try.append(provider)
        
        for provider in providers_to_try:
            try:
                customer = None
                
                if identifier_type == "id":
                    customer = await provider.get_customer(identifier)
                elif identifier_type == "email":
                    customer = await provider.get_customer_by_email(identifier)
                elif identifier_type == "phone":
                    customer = await provider.get_customer_by_phone(identifier)
                
                if customer:
                    logger.info(f"Customer found in {provider.provider_name}")
                    return customer
                    
            except Exception as e:
                logger.warning(f"Error getting customer from {provider.provider_name}: {str(e)}")
                continue
        
        logger.info(f"Customer not found with {identifier_type}: {identifier}")
        return None
    
    async def create_customer(
        self, 
        customer_data: Dict[str, Any],
        provider_name: Optional[str] = None
    ) -> Optional[Customer]:
        """
        Create customer in specified or primary provider.
        
        Args:
            customer_data: Customer data dictionary
            provider_name: Specific provider to use (optional)
        
        Returns:
            Created Customer object or None if failed
        """
        provider = None
        
        if provider_name and provider_name in self.providers:
            provider = self.providers[provider_name]
        elif self.primary_provider:
            provider = self.primary_provider
        else:
            logger.error("No provider available for customer creation")
            return None
        
        try:
            customer = await provider.create_customer(customer_data)
            logger.info(f"Customer created in {provider.provider_name}")
            return customer
        except Exception as e:
            logger.error(f"Error creating customer in {provider.provider_name}: {str(e)}")
            return None
    
    async def update_customer(
        self, 
        customer: Customer,
        provider_name: Optional[str] = None
    ) -> bool:
        """
        Update customer in specified or source provider.
        
        Args:
            customer: Customer object to update
            provider_name: Specific provider to use (optional)
        
        Returns:
            True if successful, False otherwise
        """
        provider = None
        
        if provider_name and provider_name in self.providers:
            provider = self.providers[provider_name]
        elif customer.data_source and customer.data_source in self.providers:
            provider = self.providers[customer.data_source]
        elif self.primary_provider:
            provider = self.primary_provider
        
        if not provider:
            logger.error("No provider available for customer update")
            return False
        
        try:
            success = await provider.update_customer(customer)
            if success:
                logger.info(f"Customer updated in {provider.provider_name}")
            return success
        except Exception as e:
            logger.error(f"Error updating customer in {provider.provider_name}: {str(e)}")
            return False
    
    async def get_customer_history(
        self, 
        customer_id: str,
        provider_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get customer interaction history.
        
        Args:
            customer_id: Customer identifier
            provider_name: Specific provider to use (optional)
        
        Returns:
            List of interaction history records
        """
        provider = None
        
        if provider_name and provider_name in self.providers:
            provider = self.providers[provider_name]
        elif self.primary_provider:
            provider = self.primary_provider
        
        if not provider:
            return []
        
        try:
            history = await provider.get_customer_history(customer_id)
            return history
        except Exception as e:
            logger.error(f"Error getting customer history from {provider.provider_name}: {str(e)}")
            return []
    
    async def search_customers(
        self, 
        query: str, 
        limit: int = 10,
        provider_name: Optional[str] = None
    ) -> List[Customer]:
        """
        Search customers across providers.
        
        Args:
            query: Search query
            limit: Maximum number of results
            provider_name: Specific provider to use (optional)
        
        Returns:
            List of matching customers
        """
        if provider_name and provider_name in self.providers:
            providers_to_search = [self.providers[provider_name]]
        else:
            providers_to_search = list(self.providers.values())
        
        all_customers = []
        
        for provider in providers_to_search:
            try:
                customers = await provider.search_customers(query, limit)
                all_customers.extend(customers)
            except Exception as e:
                logger.warning(f"Error searching in {provider.provider_name}: {str(e)}")
                continue
        
        # Remove duplicates based on email
        unique_customers = {}
        for customer in all_customers:
            if customer.email and customer.email not in unique_customers:
                unique_customers[customer.email] = customer
        
        return list(unique_customers.values())[:limit]
    
    async def test_all_connections(self) -> Dict[str, Dict[str, Any]]:
        """Test connections to all configured providers."""
        results = {}
        
        for name, provider in self.providers.items():
            try:
                result = await provider.test_connection()
                results[name] = result
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "provider": name,
                    "error": str(e)
                }
        
        return results
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about configured providers."""
        return {
            "total_providers": len(self.providers),
            "primary_provider": self.primary_provider.provider_name if self.primary_provider else None,
            "available_providers": list(self.providers.keys()),
            "business_name": self.business_config.business_name,
            "industry": self.business_config.industry
        }
    
    async def get_or_create_customer(
        self,
        identifier: str,
        identifier_type: str = "email",
        fallback_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Customer]:
        """
        Get existing customer or create new one with fallback data.
        
        Args:
            identifier: Customer identifier
            identifier_type: Type of identifier
            fallback_data: Data to use if customer needs to be created
        
        Returns:
            Customer object or None
        """
        # Try to find existing customer
        customer = await self.get_customer(identifier, identifier_type)
        
        if customer:
            return customer
        
        # If not found and fallback data provided, create new customer
        if fallback_data:
            if identifier_type == "email":
                fallback_data["email"] = identifier
            elif identifier_type == "phone":
                fallback_data["phone"] = identifier
            
            return await self.create_customer(fallback_data)
        
        return None