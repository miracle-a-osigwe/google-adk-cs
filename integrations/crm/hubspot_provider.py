"""HubSpot CRM integration provider."""

import logging
from typing import Dict, Any, List, Optional
import aiohttp
from datetime import datetime

from ..base_provider import CustomerDataProvider, IntegrationConfig, ProviderConnectionError
from entities.customer import Customer

logger = logging.getLogger(__name__)


class HubSpotProvider(CustomerDataProvider):
    """HubSpot CRM data provider."""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.base_url = "https://api.hubapi.com"
    
    async def _make_api_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """Make authenticated API request to HubSpot."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
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
                            raise ProviderConnectionError(f"HubSpot API error: {error_text}")
                elif method == "POST":
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status in [200, 201]:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            raise ProviderConnectionError(f"HubSpot API error: {error_text}")
                elif method == "PATCH":
                    async with session.patch(url, headers=headers, json=data) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            raise ProviderConnectionError(f"HubSpot API error: {error_text}")
        except Exception as e:
            raise ProviderConnectionError(f"HubSpot connection error: {str(e)}")
    
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by HubSpot Contact ID."""
        try:
            endpoint = f"crm/v3/objects/contacts/{customer_id}"
            contact_data = await self._make_api_request(endpoint)
            
            if contact_data:
                mapped_data = self.map_fields(contact_data.get("properties", {}))
                mapped_data["customer_id"] = contact_data.get("id")
                return Customer.from_provider_data(mapped_data, "hubspot")
            
            return None
        except Exception as e:
            logger.error(f"Error getting HubSpot customer {customer_id}: {str(e)}")
            return None
    
    async def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email address."""
        try:
            endpoint = f"crm/v3/objects/contacts/{email}?idProperty=email"
            contact_data = await self._make_api_request(endpoint)
            
            if contact_data:
                mapped_data = self.map_fields(contact_data.get("properties", {}))
                mapped_data["customer_id"] = contact_data.get("id")
                return Customer.from_provider_data(mapped_data, "hubspot")
            
            return None
        except Exception as e:
            logger.error(f"Error getting HubSpot customer by email {email}: {str(e)}")
            return None
    
    async def get_customer_by_phone(self, phone: str) -> Optional[Customer]:
        """Get customer by phone number."""
        try:
            # HubSpot search API
            search_data = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "phone",
                                "operator": "EQ",
                                "value": phone
                            }
                        ]
                    }
                ],
                "limit": 1
            }
            
            endpoint = "crm/v3/objects/contacts/search"
            result = await self._make_api_request(endpoint, "POST", search_data)
            
            if result.get("results"):
                contact_data = result["results"][0]
                mapped_data = self.map_fields(contact_data.get("properties", {}))
                mapped_data["customer_id"] = contact_data.get("id")
                return Customer.from_provider_data(mapped_data, "hubspot")
            
            return None
        except Exception as e:
            logger.error(f"Error getting HubSpot customer by phone {phone}: {str(e)}")
            return None
    
    async def create_customer(self, customer_data: Dict[str, Any]) -> Customer:
        """Create new customer in HubSpot."""
        try:
            # Map standard fields to HubSpot properties
            hs_data = {
                "properties": {
                    "firstname": customer_data.get("first_name", ""),
                    "lastname": customer_data.get("last_name", customer_data.get("name", "Unknown")),
                    "email": customer_data.get("email"),
                    "phone": customer_data.get("phone"),
                    "hs_lead_status": "NEW"
                }
            }
            
            # Add custom properties
            for key, value in customer_data.get("custom_fields", {}).items():
                hs_data["properties"][key] = value
            
            endpoint = "crm/v3/objects/contacts"
            result = await self._make_api_request(endpoint, "POST", hs_data)
            
            if result.get("id"):
                return await self.get_customer(result["id"])
            else:
                raise Exception(f"Failed to create customer: {result}")
                
        except Exception as e:
            logger.error(f"Error creating HubSpot customer: {str(e)}")
            raise
    
    async def update_customer(self, customer: Customer) -> bool:
        """Update existing customer in HubSpot."""
        try:
            hs_data = {
                "properties": {
                    "firstname": customer.first_name,
                    "lastname": customer.last_name,
                    "email": customer.email,
                    "phone": customer.phone
                }
            }
            
            # Add custom fields
            for key, value in customer.custom_fields.items():
                hs_data["properties"][key] = value
            
            endpoint = f"crm/v3/objects/contacts/{customer.customer_id}"
            result = await self._make_api_request(endpoint, "PATCH", hs_data)
            
            return result.get("id") is not None
            
        except Exception as e:
            logger.error(f"Error updating HubSpot customer {customer.customer_id}: {str(e)}")
            return False
    
    async def get_customer_history(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get customer interaction history from HubSpot."""
        try:
            # Get tickets associated with the contact
            endpoint = f"crm/v3/objects/tickets?associations=contact&limit=100"
            result = await self._make_api_request(endpoint)
            
            history = []
            for ticket in result.get("results", []):
                # Check if ticket is associated with this contact
                associations = ticket.get("associations", {}).get("contacts", {}).get("results", [])
                if any(assoc.get("id") == customer_id for assoc in associations):
                    properties = ticket.get("properties", {})
                    history.append({
                        "id": ticket.get("id"),
                        "type": "ticket",
                        "subject": properties.get("subject", ""),
                        "content": properties.get("content", ""),
                        "status": properties.get("hs_ticket_status", ""),
                        "priority": properties.get("hs_ticket_priority", ""),
                        "created_date": properties.get("createdate", ""),
                        "source": "hubspot"
                    })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting HubSpot customer history {customer_id}: {str(e)}")
            return []
    
    async def search_customers(self, query: str, limit: int = 10) -> List[Customer]:
        """Search customers in HubSpot."""
        try:
            search_data = {
                "query": query,
                "limit": limit,
                "after": 0
            }
            
            endpoint = "crm/v3/objects/contacts/search"
            result = await self._make_api_request(endpoint, "POST", search_data)
            
            customers = []
            for contact in result.get("results", []):
                mapped_data = self.map_fields(contact.get("properties", {}))
                mapped_data["customer_id"] = contact.get("id")
                customer = Customer.from_provider_data(mapped_data, "hubspot")
                customers.append(customer)
            
            return customers
            
        except Exception as e:
            logger.error(f"Error searching HubSpot customers: {str(e)}")
            return []
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test HubSpot connection."""
        try:
            endpoint = "crm/v3/objects/contacts?limit=1"
            await self._make_api_request(endpoint)
            
            return {
                "status": "success",
                "provider": "hubspot",
                "message": "Connection successful"
            }
        except Exception as e:
            return {
                "status": "error",
                "provider": "hubspot",
                "error": str(e)
            }