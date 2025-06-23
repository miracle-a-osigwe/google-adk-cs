from typing import Optional, Dict, Any
from pydantic import BaseModel


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
