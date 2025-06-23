"""Zendesk integration provider."""

import logging
from typing import Dict, Any, List, Optional
import aiohttp
import base64
from datetime import datetime

from ..base_provider import CustomerDataProvider, IntegrationConfig, ProviderConnectionError
from entities.customer import Customer

logger = logging.getLogger(__name__)


class ZendeskProvider(CustomerDataProvider):
    """Zendesk data provider."""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.subdomain = config.custom_config.get("subdomain")
        self.email = config.username
        self.api_token = config.api_key
        self.base_url = f"https://{self.subdomain}.zendesk.com/api/v2"
    
    def _get_auth_header(self) -> str:
        """Get basic auth header for Zendesk API."""
        credentials = f"{self.email}/token:{self.api_token}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"
    
    async def _make_api_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """Make authenticated API request to Zendesk."""
        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                if method == "GET":
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            raise ProviderConnectionError(f"Zendesk API error: {error_text}")
                elif method == "POST":
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status in [200, 201]:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            raise ProviderConnectionError(f"Zendesk API error: {error_text}")
                elif method == "PUT":
                    async with session.put(url, headers=headers, json=data) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            raise ProviderConnectionError(f"Zendesk API error: {error_text}")
        except Exception as e:
            raise ProviderConnectionError(f"Zendesk connection error: {str(e)}")
    
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by Zendesk User ID."""
        try:
            endpoint = f"users/{customer_id}"
            user_data = await self._make_api_request(endpoint)
            
            if user_data.get("user"):
                mapped_data = self.map_fields(user_data["user"])
                return Customer.from_provider_data(mapped_data, "zendesk")
            
            return None
        except Exception as e:
            logger.error(f"Error getting Zendesk customer {customer_id}: {str(e)}")
            return None
    
    async def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email address."""
        try:
            endpoint = f"users/search.json?query=email:{email}"
            result = await self._make_api_request(endpoint)
            
            if result.get("users") and len(result["users"]) > 0:
                user_data = result["users"][0]
                mapped_data = self.map_fields(user_data)
                return Customer.from_provider_data(mapped_data, "zendesk")
            
            return None
        except Exception as e:
            logger.error(f"Error getting Zendesk customer by email {email}: {str(e)}")
            return None
    
    async def get_customer_by_phone(self, phone: str) -> Optional[Customer]:
        """Get customer by phone number."""
        try:
            endpoint = f"users/search.json?query=phone:{phone}"
            result = await self._make_api_request(endpoint)
            
            if result.get("users") and len(result["users"]) > 0:
                user_data = result["users"][0]
                mapped_data = self.map_fields(user_data)
                return Customer.from_provider_data(mapped_data, "zendesk")
            
            return None
        except Exception as e:
            logger.error(f"Error getting Zendesk customer by phone {phone}: {str(e)}")
            return None
    
    async def create_customer(self, customer_data: Dict[str, Any]) -> Customer:
        """Create new customer in Zendesk."""
        try:
            # Map standard fields to Zendesk user fields
            zd_data = {
                "user": {
                    "name": customer_data.get("name", f"{customer_data.get('first_name', '')} {customer_data.get('last_name', '')}").strip(),
                    "email": customer_data.get("email"),
                    "phone": customer_data.get("phone"),
                    "role": "end-user",
                    "verified": False
                }
            }
            
            # Add custom fields
            user_fields = {}
            for key, value in customer_data.get("custom_fields", {}).items():
                user_fields[key] = value
            
            if user_fields:
                zd_data["user"]["user_fields"] = user_fields
            
            endpoint = "users"
            result = await self._make_api_request(endpoint, "POST", zd_data)
            
            if result.get("user"):
                mapped_data = self.map_fields(result["user"])
                return Customer.from_provider_data(mapped_data, "zendesk")
            else:
                raise Exception(f"Failed to create customer: {result}")
                
        except Exception as e:
            logger.error(f"Error creating Zendesk customer: {str(e)}")
            raise
    
    async def update_customer(self, customer: Customer) -> bool:
        """Update existing customer in Zendesk."""
        try:
            zd_data = {
                "user": {
                    "name": f"{customer.first_name} {customer.last_name}".strip(),
                    "email": customer.email,
                    "phone": customer.phone
                }
            }
            
            # Add custom fields
            if customer.custom_fields:
                zd_data["user"]["user_fields"] = customer.custom_fields
            
            endpoint = f"users/{customer.customer_id}"
            result = await self._make_api_request(endpoint, "PUT", zd_data)
            
            return result.get("user") is not None
            
        except Exception as e:
            logger.error(f"Error updating Zendesk customer {customer.customer_id}: {str(e)}")
            return False
    
    async def get_customer_history(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get customer interaction history from Zendesk."""
        try:
            # Get tickets for the user
            endpoint = f"users/{customer_id}/tickets/requested"
            result = await self._make_api_request(endpoint)
            
            history = []
            for ticket in result.get("tickets", []):
                history.append({
                    "id": ticket.get("id"),
                    "type": "ticket",
                    "subject": ticket.get("subject", ""),
                    "description": ticket.get("description", ""),
                    "status": ticket.get("status", ""),
                    "priority": ticket.get("priority", ""),
                    "created_date": ticket.get("created_at", ""),
                    "updated_date": ticket.get("updated_at", ""),
                    "source": "zendesk"
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting Zendesk customer history {customer_id}: {str(e)}")
            return []
    
    async def search_customers(self, query: str, limit: int = 10) -> List[Customer]:
        """Search customers in Zendesk."""
        try:
            endpoint = f"users/search.json?query={query}"
            result = await self._make_api_request(endpoint)
            
            customers = []
            for user in result.get("users", [])[:limit]:
                mapped_data = self.map_fields(user)
                customer = Customer.from_provider_data(mapped_data, "zendesk")
                customers.append(customer)
            
            return customers
            
        except Exception as e:
            logger.error(f"Error searching Zendesk customers: {str(e)}")
            return []
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Zendesk connection."""
        try:
            endpoint = "users/me"
            await self._make_api_request(endpoint)
            
            return {
                "status": "success",
                "provider": "zendesk",
                "message": "Connection successful"
            }
        except Exception as e:
            return {
                "status": "error",
                "provider": "zendesk",
                "error": str(e)
            }