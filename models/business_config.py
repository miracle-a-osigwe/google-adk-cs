"""Business configuration models."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from core.base import IntegrationConfig


class IndustryTemplate(BaseModel):
    """Industry-specific template for customer data requirements."""
    name: str
    required_fields: List[str] = Field(default_factory=list)
    optional_fields: List[str] = Field(default_factory=list)
    custom_fields: List[str] = Field(default_factory=list)
    compliance_requirements: List[str] = Field(default_factory=list)
    data_retention_days: int = 1095  # 3 years default
    
    # Industry-specific settings
    escalation_rules: Dict[str, Any] = Field(default_factory=dict)
    business_hours: Dict[str, str] = Field(default_factory=dict)
    sla_targets: Dict[str, str] = Field(default_factory=dict)


class BusinessConfig(BaseModel):
    """Complete business configuration for the customer service system."""
    
    # Basic business information
    business_name: str
    industry: str  # "ecommerce", "saas", "healthcare", "financial", "retail"
    business_description: Optional[str] = None
    
    # Data provider configuration
    data_providers: List[IntegrationConfig] = Field(default_factory=list)
    primary_data_provider: str
    
    # Customer data requirements
    required_customer_fields: List[str] = Field(default_factory=list)
    optional_customer_fields: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, str] = Field(default_factory=dict)  # field_name: field_type
    
    # Business rules
    escalation_rules: Dict[str, Any] = Field(default_factory=dict)
    business_hours: Dict[str, str] = Field(default_factory=dict)
    supported_languages: List[str] = Field(default=["en"])
    default_timezone: str = "UTC"
    
    # Compliance and privacy
    data_retention_days: int = 1095  # 3 years default
    privacy_settings: Dict[str, bool] = Field(default_factory=dict)
    compliance_requirements: List[str] = Field(default_factory=list)
    
    # Service level agreements
    sla_targets: Dict[str, str] = Field(default_factory=dict)
    
    # System settings
    max_conversation_turns: int = 10
    escalation_threshold: int = 3
    auto_escalate_keywords: List[str] = Field(default_factory=list)
    
    # Integration settings
    webhook_urls: Dict[str, str] = Field(default_factory=dict)
    notification_settings: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"
    
    @classmethod
    def create_default_config(cls, business_name: str, industry: str) -> "BusinessConfig":
        """Create default configuration for a business."""
        
        industry_defaults = {
            "ecommerce": {
                "required_fields": ["name", "email"],
                "optional_fields": ["phone", "shipping_address", "billing_address"],
                "custom_fields": {
                    "customer_since": "date",
                    "total_orders": "integer",
                    "loyalty_tier": "string",
                    "preferred_categories": "array"
                },
                "compliance": ["gdpr_consent", "marketing_consent"],
                "sla_targets": {
                    "first_response": "2 hours",
                    "resolution": "24 hours"
                }
            },
            "saas": {
                "required_fields": ["name", "email", "company"],
                "optional_fields": ["phone", "job_title", "company_size"],
                "custom_fields": {
                    "subscription_plan": "string",
                    "usage_tier": "string",
                    "account_type": "string",
                    "integration_needs": "array"
                },
                "compliance": ["data_processing_consent"],
                "sla_targets": {
                    "first_response": "1 hour",
                    "resolution": "8 hours"
                }
            },
            "healthcare": {
                "required_fields": ["name", "email", "phone", "date_of_birth"],
                "optional_fields": ["address", "emergency_contact", "insurance_provider"],
                "custom_fields": {
                    "patient_id": "string",
                    "medical_record_number": "string",
                    "preferred_provider": "string"
                },
                "compliance": ["hipaa_consent", "medical_data_consent"],
                "sla_targets": {
                    "first_response": "30 minutes",
                    "resolution": "4 hours"
                }
            },
            "financial": {
                "required_fields": ["name", "email", "phone", "address"],
                "optional_fields": ["ssn_last_four", "account_type", "preferred_contact_method"],
                "custom_fields": {
                    "account_number": "string",
                    "risk_profile": "string",
                    "investment_goals": "array"
                },
                "compliance": ["kyc_verification", "aml_consent", "privacy_notice"],
                "sla_targets": {
                    "first_response": "15 minutes",
                    "resolution": "2 hours"
                }
            },
            "retail": {
                "required_fields": ["name", "email"],
                "optional_fields": ["phone", "address", "preferred_store_location"],
                "custom_fields": {
                    "loyalty_number": "string",
                    "preferred_brands": "array",
                    "size_preferences": "object"
                },
                "compliance": ["marketing_consent"],
                "sla_targets": {
                    "first_response": "4 hours",
                    "resolution": "24 hours"
                }
            }
        }
        
        defaults = industry_defaults.get(industry, industry_defaults["saas"])
        
        return cls(
            business_name=business_name,
            industry=industry,
            primary_data_provider="database",  # Default to database
            required_customer_fields=defaults["required_fields"],
            optional_customer_fields=defaults["optional_fields"],
            custom_fields=defaults["custom_fields"],
            compliance_requirements=defaults["compliance"],
            sla_targets=defaults["sla_targets"],
            business_hours={
                "monday": "9:00-17:00",
                "tuesday": "9:00-17:00",
                "wednesday": "9:00-17:00",
                "thursday": "9:00-17:00",
                "friday": "9:00-17:00",
                "saturday": "closed",
                "sunday": "closed"
            },
            escalation_rules={
                "critical_keywords": ["urgent", "critical", "emergency", "down", "outage"],
                "auto_escalate_after_hours": True,
                "vip_customer_auto_escalate": True
            },
            privacy_settings={
                "collect_analytics": True,
                "share_with_partners": False,
                "marketing_communications": True
            }
        )
    
    def add_data_provider(self, provider_config: IntegrationConfig):
        """Add a data provider configuration."""
        self.data_providers.append(provider_config)
        self.updated_at = datetime.now()
    
    def update_field_requirements(
        self, 
        required_fields: List[str] = None,
        optional_fields: List[str] = None,
        custom_fields: Dict[str, str] = None
    ):
        """Update field requirements."""
        if required_fields is not None:
            self.required_customer_fields = required_fields
        if optional_fields is not None:
            self.optional_customer_fields = optional_fields
        if custom_fields is not None:
            self.custom_fields.update(custom_fields)
        
        self.updated_at = datetime.now()
    
    def get_industry_template(self) -> IndustryTemplate:
        """Get industry template based on current configuration."""
        return IndustryTemplate(
            name=self.industry.title(),
            required_fields=self.required_customer_fields,
            optional_fields=self.optional_customer_fields,
            custom_fields=list(self.custom_fields.keys()),
            compliance_requirements=self.compliance_requirements,
            data_retention_days=self.data_retention_days,
            escalation_rules=self.escalation_rules,
            business_hours=self.business_hours,
            sla_targets=self.sla_targets
        )