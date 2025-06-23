"""Shopify e-commerce integration provider."""

import logging
from typing import Dict, Any, List, Optional
import aiohttp
from datetime import datetime

from ..base_provider import CustomerDataProvider, IntegrationConfig, ProviderConnectionError
from entities.customer import Customer

logger = logging.getLogger(__name__)


class ShopifyProvider(CustomerDataProvider):
    """Shopify e-commerce data provider."""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.shop_domain = config.custom_config.get("shop_domain")
        self.access_token = config.api_key
        self.base_url = ""
    
    async def _make_api_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """Make authenticated API request to Shopify."""
        headers = {
            "X-Shopify-Access-Token": self.access_token,
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
                            raise ProviderConnectionError(f"Shopify API error: {error_text}")
                elif method == "POST":
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status in [200, 201]:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            raise ProviderConnectionError(f"Shopify API error: {error_text}")
                elif method == "PUT":
                    async with session.put(url, headers=headers, json=data) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            raise ProviderConnectionError(f"Shopify API error: {error_text}")
        except Exception as e:
            raise ProviderConnectionError(f"Shopify connection error: {str(e)}")
    
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by Shopify Customer ID."""
        try:
            endpoint = f"customers/{customer_id}.json"
            customer_data = await self._make_api_request(endpoint)
            
            if customer_data.get("customer"):
                mapped_data = self.map_fields(customer_data["customer"])
                return Customer.from_provider_data(mapped_data, "shopify")
            
            return None
        except Exception as e:
            logger.error(f"Error getting Shopify customer {customer_id}: {str(e)}")
            return None
    
    async def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email address."""
        try:
            endpoint = f"customers/search.json?query=email:{email}"
            result = await self._make_api_request(endpoint)
            
            if result.get("customers") and len(result["customers"]) > 0:
                customer_data = result["customers"][0]
                mapped_data = self.map_fields(customer_data)
                return Customer.from_provider_data(mapped_data, "shopify")
            
            return None
        except Exception as e:
            logger.error(f"Error getting Shopify customer by email {email}: {str(e)}")
            return None
    
    async def get_customer_by_phone(self, phone: str) -> Optional[Customer]:
        """Get customer by phone number."""
        try:
            endpoint = f"customers/search.json?query=phone:{phone}"
            result = await self._make_api_request(endpoint)
            
            if result.get("customers") and len(result["customers"]) > 0:
                customer_data = result["customers"][0]
                mapped_data = self.map_fields(customer_data)
                return Customer.from_provider_data(mapped_data, "shopify")
            
            return None
        except Exception as e:
            logger.error(f"Error getting Shopify customer by phone {phone}: {str(e)}")
            return None
    
    async def create_customer(self, customer_data: Dict[str, Any]) -> Customer:
        """Create new customer in Shopify."""
        try:
            # Map standard fields to Shopify customer fields
            shopify_data = {
                "customer": {
                    "first_name": customer_data.get("first_name", ""),
                    "last_name": customer_data.get("last_name", customer_data.get("name", "Unknown")),
                    "email": customer_data.get("email"),
                    "phone": customer_data.get("phone"),
                    "verified_email": False,
                    "send_email_welcome": False
                }
            }
            
            # Add custom fields as metafields
            if customer_data.get("custom_fields"):
                shopify_data["customer"]["metafields"] = []
                for key, value in customer_data["custom_fields"].items():
                    shopify_data["customer"]["metafields"].append({
                        "namespace": "custom",
                        "key": key,
                        "value": str(value),
                        "type": "single_line_text_field"
                    })
            
            endpoint = "customers.json"
            result = await self._make_api_request(endpoint, "POST", shopify_data)
            
            if result.get("customer"):
                mapped_data = self.map_fields(result["customer"])
                return Customer.from_provider_data(mapped_data, "shopify")
            else:
                raise Exception(f"Failed to create customer: {result}")
                
        except Exception as e:
            logger.error(f"Error creating Shopify customer: {str(e)}")
            raise
    
    async def update_customer(self, customer: Customer) -> bool:
        """Update existing customer in Shopify."""
        try:
            shopify_data = {
                "customer": {
                    "id": customer.customer_id,
                    "first_name": customer.first_name,
                    "last_name": customer.last_name,
                    "email": customer.email,
                    "phone": customer.phone
                }
            }
            
            endpoint = f"customers/{customer.customer_id}.json"
            result = await self._make_api_request(endpoint, "PUT", shopify_data)
            
            return result.get("customer") is not None
            
        except Exception as e:
            logger.error(f"Error updating Shopify customer {customer.customer_id}: {str(e)}")
            return False
    
    async def get_customer_history(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get customer interaction history from Shopify."""
        try:
            history = []
            
            # Get orders for the customer
            endpoint = f"customers/{customer_id}/orders.json"
            orders_result = await self._make_api_request(endpoint)
            
            for order in orders_result.get("orders", []):
                history.append({
                    "id": order.get("id"),
                    "type": "order",
                    "order_number": order.get("order_number"),
                    "total_price": order.get("total_price"),
                    "financial_status": order.get("financial_status"),
                    "fulfillment_status": order.get("fulfillment_status"),
                    "created_date": order.get("created_at"),
                    "source": "shopify"
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting Shopify customer history {customer_id}: {str(e)}")
            return []
    
    async def search_customers(self, query: str, limit: int = 10) -> List[Customer]:
        """Search customers in Shopify."""
        try:
            endpoint = f"customers/search.json?query={query}&limit={limit}"
            result = await self._make_api_request(endpoint)
            
            customers = []
            for customer_data in result.get("customers", []):
                mapped_data = self.map_fields(customer_data)
                customer = Customer.from_provider_data(mapped_data, "shopify")
                customers.append(customer)
            
            return customers
            
        except Exception as e:
            logger.error(f"Error searching Shopify customers: {str(e)}")
            return []
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Shopify connection."""
        try:
            endpoint = "shop.json"
            await self._make_api_request(endpoint)
            
            return {
                "status": "success",
                "provider": "shopify",
                "message": "Connection successful"
            }
        except Exception as e:
            return {
                "status": "error",
                "provider": "shopify",
                "error": str(e)
            }