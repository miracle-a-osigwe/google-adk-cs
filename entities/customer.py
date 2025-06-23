"""Enhanced Customer entity with provider integration support."""

import json
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class Customer(BaseModel):
    """Enhanced Customer entity model with provider integration support."""
    
    # Core identifiers
    customer_id: str = Field(..., description="Unique customer identifier")
    external_ids: Dict[str, str] = Field(default_factory=dict, description="External system IDs")
    
    # Basic information
    name: Optional[str] = Field(default=None, description="Full customer name")
    first_name: Optional[str] = Field(default=None, description="First name")
    last_name: Optional[str] = Field(default=None, description="Last name")
    email: Optional[str] = Field(default=None, description="Primary email address")
    phone: Optional[str] = Field(default=None, description="Primary phone number")
    
    # Location and contact
    address: Optional[Dict[str, str]] = Field(default=None, description="Address information")
    timezone: Optional[str] = Field(default=None, description="Customer timezone")
    language: Optional[str] = Field(default="en", description="Preferred language")
    
    # Business relationship
    company: Optional[str] = Field(default=None, description="Company name")
    job_title: Optional[str] = Field(default=None, description="Job title")
    tier: str = Field(default="standard", description="Customer tier (standard, premium, enterprise)")
    account_status: str = Field(default="active", description="Account status")
    
    # Interaction preferences
    preferred_channel: Optional[str] = Field(default=None, description="Preferred communication channel")
    communication_preferences: Dict[str, bool] = Field(default_factory=dict, description="Communication preferences")
    
    # Historical data
    customer_since: Optional[datetime] = Field(default=None, description="Customer since date")
    last_interaction: Optional[datetime] = Field(default=None, description="Last interaction date")
    interaction_count: int = Field(default=0, description="Total interaction count")
    
    # Business-specific data
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom business fields")
    tags: List[str] = Field(default_factory=list, description="Customer tags")
    
    # System metadata
    data_source: Optional[str] = Field(default=None, description="Primary data source")
    data_sources: List[str] = Field(default_factory=list, description="All data sources")
    data_quality_score: float = Field(default=0.0, description="Data quality score (0-1)")
    completeness_score: float = Field(default=0.0, description="Data completeness score (0-1)")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    # Compliance and privacy
    consent_status: Dict[str, bool] = Field(default_factory=dict, description="Consent status")
    data_retention_until: Optional[datetime] = Field(default=None, description="Data retention date")
    
    @classmethod
    def from_provider_data(cls, provider_data: Dict[str, Any], provider_name: str) -> "Customer":
        """Create Customer instance from provider data."""
        
        # Extract standard fields
        customer_data = {
            "customer_id": str(provider_data.get("id", provider_data.get("customer_id", ""))),
            "data_source": provider_name,
            "data_sources": [provider_name]
        }
        
        # Map common fields
        field_mappings = {
            # Salesforce mappings
            "FirstName": "first_name",
            "LastName": "last_name",
            "Email": "email",
            "Phone": "phone",
            "Account.Name": "company",
            
            # HubSpot mappings
            "firstname": "first_name",
            "lastname": "last_name",
            "email": "email",
            "phone": "phone",
            "company": "company",
            
            # Zendesk mappings
            "name": "name",
            "email": "email",
            "phone": "phone",
            
            # Shopify mappings
            "first_name": "first_name",
            "last_name": "last_name",
            "email": "email",
            "phone": "phone",
            
            # Database mappings
            "first_name": "first_name",
            "last_name": "last_name",
            "email": "email",
            "phone": "phone",
            "company": "company"
        }
        
        # Apply field mappings
        for provider_field, standard_field in field_mappings.items():
            if provider_field in provider_data and provider_data[provider_field]:
                customer_data[standard_field] = provider_data[provider_field]
        
        # Handle nested fields (like Account.Name in Salesforce)
        for provider_field, standard_field in field_mappings.items():
            if "." in provider_field:
                parts = provider_field.split(".")
                nested_data = provider_data
                for part in parts:
                    if isinstance(nested_data, dict) and part in nested_data:
                        nested_data = nested_data[part]
                    else:
                        nested_data = None
                        break
                
                if nested_data:
                    customer_data[standard_field] = nested_data
        
        # Construct full name if not provided
        if not customer_data.get("name") and (customer_data.get("first_name") or customer_data.get("last_name")):
            name_parts = []
            if customer_data.get("first_name"):
                name_parts.append(customer_data["first_name"])
            if customer_data.get("last_name"):
                name_parts.append(customer_data["last_name"])
            customer_data["name"] = " ".join(name_parts)
        
        # Store unmapped fields in custom_fields
        custom_fields = {}
        for key, value in provider_data.items():
            if key not in field_mappings and key not in ["id", "customer_id"]:
                custom_fields[key] = value
        
        if custom_fields:
            customer_data["custom_fields"] = custom_fields
        
        # Set external ID
        if customer_data["customer_id"]:
            customer_data["external_ids"] = {provider_name: customer_data["customer_id"]}
        
        return cls(**customer_data)
    
    @classmethod
    def create_from_gathered_data(
        cls, 
        gathered_data: Dict[str, Any], 
        business_config: Optional[Dict[str, Any]] = None
    ) -> "Customer":
        """Create Customer instance from gathered data during conversation."""
        
        # Generate temporary customer ID
        import uuid
        customer_id = f"temp_{str(uuid.uuid4())[:8]}"
        
        customer_data = {
            "customer_id": customer_id,
            "data_source": "conversation",
            "data_sources": ["conversation"]
        }
        
        # Map gathered data to customer fields
        for key, value in gathered_data.items():
            if hasattr(cls, key):
                customer_data[key] = value
            else:
                # Store in custom fields
                if "custom_fields" not in customer_data:
                    customer_data["custom_fields"] = {}
                customer_data["custom_fields"][key] = value
        
        return cls(**customer_data)
    
    def merge_with_provider_data(self, provider_data: Dict[str, Any], provider_name: str) -> "Customer":
        """Merge current customer data with data from another provider."""
        
        # Create customer from provider data
        provider_customer = self.from_provider_data(provider_data, provider_name)
        
        # Merge data, preferring non-empty values
        merged_data = self.dict()
        
        # Update basic fields if they're empty or provider has better data
        for field in ["first_name", "last_name", "name", "email", "phone", "company"]:
            provider_value = getattr(provider_customer, field)
            current_value = getattr(self, field)
            
            if provider_value and (not current_value or len(str(provider_value)) > len(str(current_value))):
                merged_data[field] = provider_value
        
        # Merge custom fields
        merged_data["custom_fields"].update(provider_customer.custom_fields)
        
        # Add to data sources
        if provider_name not in merged_data["data_sources"]:
            merged_data["data_sources"].append(provider_name)
        
        # Update external IDs
        merged_data["external_ids"].update(provider_customer.external_ids)
        
        # Update timestamp
        merged_data["updated_at"] = datetime.now()
        
        return Customer(**merged_data)
    
    def calculate_completeness_score(self, required_fields: List[str], optional_fields: List[str] = None) -> float:
        """Calculate data completeness score based on required and optional fields."""
        if optional_fields is None:
            optional_fields = []
        
        total_fields = len(required_fields) + len(optional_fields)
        if total_fields == 0:
            return 1.0
        
        completed_fields = 0
        
        # Check required fields (weighted more heavily)
        for field in required_fields:
            if self._has_field_value(field):
                completed_fields += 1.5  # Weight required fields more
        
        # Check optional fields
        for field in optional_fields:
            if self._has_field_value(field):
                completed_fields += 1
        
        # Calculate score
        max_possible = len(required_fields) * 1.5 + len(optional_fields)
        score = completed_fields / max_possible if max_possible > 0 else 1.0
        
        return min(1.0, score)
    
    def _has_field_value(self, field: str) -> bool:
        """Check if a field has a meaningful value."""
        value = getattr(self, field, None)
        
        if value is None:
            # Check in custom fields
            value = self.custom_fields.get(field)
        
        if value is None:
            return False
        
        if isinstance(value, str):
            return value.strip() != ""
        elif isinstance(value, (list, dict)):
            return len(value) > 0
        else:
            return True
    
    def get_display_name(self) -> str:
        """Get display name for the customer."""
        if self.name:
            return self.name
        elif self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.email:
            return self.email.split("@")[0]
        else:
            return f"Customer {self.customer_id}"
    
    def get_contact_info(self) -> Dict[str, str]:
        """Get available contact information."""
        contact_info = {}
        
        if self.email:
            contact_info["email"] = self.email
        if self.phone:
            contact_info["phone"] = self.phone
        if self.address:
            contact_info["address"] = self.address
        
        return contact_info
    
    def add_interaction_record(self, interaction_type: str, details: Dict[str, Any] = None):
        """Add interaction record to customer."""
        self.interaction_count += 1
        self.last_interaction = datetime.now()
        self.updated_at = datetime.now()
        
        # Store interaction in custom fields for now
        if "interaction_history" not in self.custom_fields:
            self.custom_fields["interaction_history"] = []
        
        interaction_record = {
            "type": interaction_type,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        self.custom_fields["interaction_history"].append(interaction_record)
        
        # Keep only last 10 interactions
        if len(self.custom_fields["interaction_history"]) > 10:
            self.custom_fields["interaction_history"] = self.custom_fields["interaction_history"][-10:]
    
    def update_data_quality_score(self):
        """Update data quality score based on current data."""
        quality_factors = []
        
        # Email format
        if self.email:
            if "@" in self.email and "." in self.email.split("@")[-1]:
                quality_factors.append(1.0)
            else:
                quality_factors.append(0.0)
        
        # Phone format
        if self.phone:
            digits = "".join(filter(str.isdigit, self.phone))
            if len(digits) >= 10:
                quality_factors.append(1.0)
            else:
                quality_factors.append(0.5)
        
        # Name completeness
        if self.name or (self.first_name and self.last_name):
            quality_factors.append(1.0)
        elif self.first_name or self.last_name:
            quality_factors.append(0.7)
        else:
            quality_factors.append(0.0)
        
        # Calculate average
        if quality_factors:
            self.data_quality_score = sum(quality_factors) / len(quality_factors)
        else:
            self.data_quality_score = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert customer to dictionary."""
        return self.dict()
    
    def to_json(self) -> str:
        """Convert customer to JSON string."""
        return json.dumps(self.dict(), indent=2, default=str)
    
    @classmethod
    def get_customer(cls, customer_id: str) -> "Customer":
        """Get customer by ID - now redirects to CustomerDataManager."""
        # This method is kept for backward compatibility
        # In practice, CustomerDataManager should be used
        return cls(
            customer_id=customer_id,
            name="Unknown Customer",
            email="unknown@email.com",
            data_source="legacy"
        )