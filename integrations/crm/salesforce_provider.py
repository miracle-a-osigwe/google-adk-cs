"""Salesforce CRM integration provider."""

import logging
from typing import Dict, Any, List, Optional
import aiohttp
import base64
from datetime import datetime

from ..base_provider import CustomerDataProvider, IntegrationConfig, ProviderConnectionError
from entities.customer import Customer

logger = logging.getLogger(__name__)


class SalesforceProvider(CustomerDataProvider):
    """Salesforce CRM data provider."""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.instance_url = config.custom_config.get("instance_url")
        self.client_id = config.api_key
        self.client_secret = config.api_secret
        self.username = config.username
        self.password = config.password
        self.security_token = config.custom_config.get("security_token", "")
        self.access_token = None
        self.token_expires_at = None
    
    async def _get_access_token(self) -> str:
        """Get OAuth access token for Salesforce API."""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
        
        auth_url = f"{self.instance_url}/services/oauth2/token"
        
        data = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": f"{self.password}{self.security_token}"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(auth_url, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        self.access_token = token_data["access_token"]
                        # Tokens typically expire in 2 hours
                        self.token_expires_at = datetime.now().timestamp() + 7200
                        return self.access_token
                    else:
                        error_text = await response.text()
                        raise ProviderConnectionError(f"Salesforce auth failed: {error_text}")
        except Exception as e:
            raise ProviderConnectionError(f"Salesforce connection error: {str(e)}")
    
    async def _make_api_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """Make authenticated API request to Salesforce."""
        access_token = await self._get_access_token()
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.instance_url}/services/data/v58.0/{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                if method == "GET":
                    async with session.get(url, headers=headers) as response:
                        return await response.json()
                elif method == "POST":
                    async with session.post(url, headers=headers, json=data) as response:
                        return await response.json()
                elif method == "PATCH":
                    async with session.patch(url, headers=headers, json=data) as response:
                        return await response.json()
        except Exception as e:
            raise ProviderConnectionError(f"Salesforce API error: {str(e)}")
    
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by Salesforce Contact ID."""
        try:
            endpoint = f"sobjects/Contact/{customer_id}"
            contact_data = await self._make_api_request(endpoint)
            
            if contact_data:
                mapped_data = self.map_fields(contact_data)
                return Customer.from_provider_data(mapped_data, "salesforce")
            
            return None
        except Exception as e:
            logger.error(f"Error getting Salesforce customer {customer_id}: {str(e)}")
            return None
    
    async def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email address."""
        try:
            query = f"SELECT Id, FirstName, LastName, Email, Phone, Account.Name FROM Contact WHERE Email = '{email}' LIMIT 1"
            endpoint = f"query/?q={query}"
            
            result = await self._make_api_request(endpoint)
            
            if result.get("records"):
                contact_data = result["records"][0]
                mapped_data = self.map_fields(contact_data)
                return Customer.from_provider_data(mapped_data, "salesforce")
            
            return None
        except Exception as e:
            logger.error(f"Error getting Salesforce customer by email {email}: {str(e)}")
            return None
    
    async def get_customer_by_phone(self, phone: str) -> Optional[Customer]:
        """Get customer by phone number."""
        try:
            query = f"SELECT Id, FirstName, LastName, Email, Phone, Account.Name FROM Contact WHERE Phone = '{phone}' LIMIT 1"
            endpoint = f"query/?q={query}"
            
            result = await self._make_api_request(endpoint)
            
            if result.get("records"):
                contact_data = result["records"][0]
                mapped_data = self.map_fields(contact_data)
                return Customer.from_provider_data(mapped_data, "salesforce")
            
            return None
        except Exception as e:
            logger.error(f"Error getting Salesforce customer by phone {phone}: {str(e)}")
            return None
    
    async def create_customer(self, customer_data: Dict[str, Any]) -> Customer:
        """Create new customer in Salesforce."""
        try:
            # Map standard fields to Salesforce fields
            sf_data = {
                "FirstName": customer_data.get("first_name", ""),
                "LastName": customer_data.get("last_name", customer_data.get("name", "Unknown")),
                "Email": customer_data.get("email"),
                "Phone": customer_data.get("phone"),
                "LeadSource": "Customer Service"
            }
            
            # Add custom fields
            for key, value in customer_data.get("custom_fields", {}).items():
                if key.endswith("__c"):  # Salesforce custom field format
                    sf_data[key] = value
            
            endpoint = "sobjects/Contact"
            result = await self._make_api_request(endpoint, "POST", sf_data)
            
            if result.get("success"):
                # Get the created customer
                return await self.get_customer(result["id"])
            else:
                raise Exception(f"Failed to create customer: {result}")
                
        except Exception as e:
            logger.error(f"Error creating Salesforce customer: {str(e)}")
            raise
    
    async def update_customer(self, customer: Customer) -> bool:
        """Update existing customer in Salesforce."""
        try:
            sf_data = {
                "FirstName": customer.first_name,
                "LastName": customer.last_name,
                "Email": customer.email,
                "Phone": customer.phone
            }
            
            # Add custom fields
            for key, value in customer.custom_fields.items():
                if key.endswith("__c"):
                    sf_data[key] = value
            
            endpoint = f"sobjects/Contact/{customer.customer_id}"
            result = await self._make_api_request(endpoint, "PATCH", sf_data)
            
            return not result.get("errors")
            
        except Exception as e:
            logger.error(f"Error updating Salesforce customer {customer.customer_id}: {str(e)}")
            return False
    
    async def get_customer_history(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get customer interaction history from Salesforce."""
        try:
            # Get Cases associated with the Contact
            query = f"SELECT Id, Subject, Description, Status, CreatedDate, Priority FROM Case WHERE ContactId = '{customer_id}' ORDER BY CreatedDate DESC"
            endpoint = f"query/?q={query}"
            
            result = await self._make_api_request(endpoint)
            
            history = []
            for case in result.get("records", []):
                history.append({
                    "id": case["Id"],
                    "type": "case",
                    "subject": case.get("Subject", ""),
                    "description": case.get("Description", ""),
                    "status": case.get("Status", ""),
                    "priority": case.get("Priority", ""),
                    "created_date": case.get("CreatedDate", ""),
                    "source": "salesforce"
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting Salesforce customer history {customer_id}: {str(e)}")
            return []
    
    async def search_customers(self, query: str, limit: int = 10) -> List[Customer]:
        """Search customers in Salesforce."""
        try:
            # Use SOSL for full-text search
            sosl_query = f"FIND {{*{query}*}} IN ALL FIELDS RETURNING Contact(Id, FirstName, LastName, Email, Phone) LIMIT {limit}"
            endpoint = f"search/?q={sosl_query}"
            
            result = await self._make_api_request(endpoint)
            
            customers = []
            for record in result.get("searchRecords", []):
                mapped_data = self.map_fields(record)
                customer = Customer.from_provider_data(mapped_data, "salesforce")
                customers.append(customer)
            
            return customers
            
        except Exception as e:
            logger.error(f"Error searching Salesforce customers: {str(e)}")
            return []
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Salesforce connection."""
        try:
            await self._get_access_token()
            
            # Test with a simple query
            endpoint = "query/?q=SELECT Id FROM Contact LIMIT 1"
            await self._make_api_request(endpoint)
            
            return {
                "status": "success",
                "provider": "salesforce",
                "message": "Connection successful"
            }
        except Exception as e:
            return {
                "status": "error",
                "provider": "salesforce",
                "error": str(e)
            }