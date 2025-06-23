"""PostgreSQL database integration provider."""

import logging
from typing import Dict, Any, List, Optional
import asyncpg
from datetime import datetime

from ..base_provider import CustomerDataProvider, IntegrationConfig, ProviderConnectionError
from entities.customer import Customer


logger = logging.getLogger(__name__)


class PostgreSQLProvider(CustomerDataProvider):
    """PostgreSQL database data provider."""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.database_url = config.database_url
        self.table_name = config.custom_config.get("table_name", "customers")
        self.connection_pool = None
        self.config = config
    
    async def _get_connection_pool(self):
        """Get or create connection pool."""
        if not self.connection_pool:
            try:
                self.connection_pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=1,
                    max_size=10
                )
            except Exception as e:
                raise ProviderConnectionError(f"PostgreSQL connection error: {str(e)}")
        
        return self.connection_pool
    
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID."""
        try:
            pool = await self._get_connection_pool()
            
            async with pool.acquire() as connection:
                query = f"SELECT * FROM {self.table_name} WHERE id = $1"
                row = await connection.fetchrow(query, customer_id)
                
                if row:
                    customer_data = dict(row)
                    mapped_data = self.map_fields(customer_data)
                    return Customer.from_provider_data(mapped_data, "postgresql")
                
                return None
        except Exception as e:
            logger.error(f"Error getting PostgreSQL customer {customer_id}: {str(e)}")
            return None
    
    async def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email address."""
        try:
            pool = await self._get_connection_pool()
            
            async with pool.acquire() as connection:
                query = f"SELECT * FROM {self.table_name} WHERE email = $1"
                row = await connection.fetchrow(query, email)
                
                if row:
                    customer_data = dict(row)
                    mapped_data = self.map_fields(customer_data)
                    return Customer.from_provider_data(mapped_data, "postgresql")
                
                return None
        except Exception as e:
            logger.error(f"Error getting PostgreSQL customer by email {email}: {str(e)}")
            return None
    
    async def get_customer_by_phone(self, phone: str) -> Optional[Customer]:
        """Get customer by phone number."""
        try:
            pool = await self._get_connection_pool()
            
            async with pool.acquire() as connection:
                query = f"SELECT * FROM {self.table_name} WHERE phone = $1"
                row = await connection.fetchrow(query, phone)
                
                if row:
                    customer_data = dict(row)
                    mapped_data = self.map_fields(customer_data)
                    return Customer.from_provider_data(mapped_data, "postgresql")
                
                return None
        except Exception as e:
            logger.error(f"Error getting PostgreSQL customer by phone {phone}: {str(e)}")
            return None
    
    async def create_customer(self, customer_data: Dict[str, Any]) -> Customer:
        """Create new customer in PostgreSQL."""
        try:
            pool = await self._get_connection_pool()
            
            # Prepare data for insertion
            fields = ["first_name", "last_name", "email", "phone", "created_at"]
            values = [
                customer_data.get("first_name", ""),
                customer_data.get("last_name", customer_data.get("name", "Unknown")),
                customer_data.get("email"),
                customer_data.get("phone"),
                datetime.now()
            ]
            
            # Add custom fields if they exist as columns
            for key, value in customer_data.get("custom_fields", {}).items():
                fields.append(key)
                values.append(value)
            
            placeholders = ", ".join([f"${i+1}" for i in range(len(values))])
            fields_str = ", ".join(fields)
            
            async with pool.acquire() as connection:
                query = f"INSERT INTO {self.table_name} ({fields_str}) VALUES ({placeholders}) RETURNING id"
                customer_id = await connection.fetchval(query, *values)
                
                return await self.get_customer(str(customer_id))
                
        except Exception as e:
            logger.error(f"Error creating PostgreSQL customer: {str(e)}")
            raise
    
    async def update_customer(self, customer: Customer) -> bool:
        """Update existing customer in PostgreSQL."""
        try:
            pool = await self._get_connection_pool()
            
            async with pool.acquire() as connection:
                query = f"""
                UPDATE {self.table_name} 
                SET first_name = $1, last_name = $2, email = $3, phone = $4, updated_at = $5
                WHERE id = $6
                """
                
                result = await connection.execute(
                    query,
                    customer.first_name,
                    customer.last_name,
                    customer.email,
                    customer.phone,
                    datetime.now(),
                    customer.customer_id
                )
                
                return "UPDATE 1" in result
                
        except Exception as e:
            logger.error(f"Error updating PostgreSQL customer {customer.customer_id}: {str(e)}")
            return False
    
    async def get_customer_history(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get customer interaction history from PostgreSQL."""
        try:
            pool = await self._get_connection_pool()
            
            # Assuming there's an interactions table
            interactions_table = self.config.custom_config.get("interactions_table", "customer_interactions")
            
            async with pool.acquire() as connection:
                query = f"""
                SELECT * FROM {interactions_table} 
                WHERE customer_id = $1 
                ORDER BY created_at DESC
                """
                rows = await connection.fetch(query, customer_id)
                
                history = []
                for row in rows:
                    history.append({
                        "id": row["id"],
                        "type": row.get("interaction_type", "interaction"),
                        "subject": row.get("subject", ""),
                        "content": row.get("content", ""),
                        "status": row.get("status", ""),
                        "created_date": row.get("created_at", ""),
                        "source": "postgresql"
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Error getting PostgreSQL customer history {customer_id}: {str(e)}")
            return []
    
    async def search_customers(self, query: str, limit: int = 10) -> List[Customer]:
        """Search customers in PostgreSQL."""
        try:
            pool = await self._get_connection_pool()
            
            async with pool.acquire() as connection:
                search_query = f"""
                SELECT * FROM {self.table_name} 
                WHERE first_name ILIKE $1 OR last_name ILIKE $1 OR email ILIKE $1
                LIMIT $2
                """
                
                rows = await connection.fetch(search_query, f"%{query}%", limit)
                
                customers = []
                for row in rows:
                    customer_data = dict(row)
                    mapped_data = self.map_fields(customer_data)
                    customer = Customer.from_provider_data(mapped_data, "postgresql")
                    customers.append(customer)
                
                return customers
                
        except Exception as e:
            logger.error(f"Error searching PostgreSQL customers: {str(e)}")
            return []
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test PostgreSQL connection."""
        try:
            pool = await self._get_connection_pool()
            
            async with pool.acquire() as connection:
                await connection.fetchval("SELECT 1")
            
            return {
                "status": "success",
                "provider": "postgresql",
                "message": "Connection successful"
            }
        except Exception as e:
            return {
                "status": "error",
                "provider": "postgresql",
                "error": str(e)
            }
    
    async def close(self):
        """Close connection pool."""
        if self.connection_pool:
            await self.connection_pool.close()