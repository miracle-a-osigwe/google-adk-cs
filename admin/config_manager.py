"""Configuration manager for the admin interface."""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

from models.business_config import BusinessConfig
from integrations.customer_data_manager import CustomerDataManager


class ConfigManager:
    """Manages business configuration and integration settings."""
    
    def __init__(self, config_file: str = "business_config.json"):
        self.config_file = config_file
        self.business_config: Optional[BusinessConfig] = None
        self.data_manager: Optional[CustomerDataManager] = None
        self._load_config()
    
    def _load_config(self):
        """Load business configuration from file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    self.business_config = BusinessConfig(**config_data)
                    
                # Initialize data manager if config exists
                if self.business_config:
                    self.data_manager = CustomerDataManager(self.business_config)
                    
            except Exception as e:
                print(f"Error loading config: {e}")
                self.business_config = None
    
    def save_business_config(self, business_config: BusinessConfig):
        """Save business configuration to file."""
        try:
            business_config.updated_at = datetime.now()
            
            with open(self.config_file, 'w') as f:
                json.dump(business_config.dict(), f, indent=2, default=str)
            
            self.business_config = business_config
            
            # Reinitialize data manager
            self.data_manager = CustomerDataManager(business_config)
            
        except Exception as e:
            raise Exception(f"Error saving config: {e}")
    
    def get_business_config(self) -> Optional[BusinessConfig]:
        """Get current business configuration."""
        return self.business_config
    
    def get_data_manager(self) -> Optional[CustomerDataManager]:
        """Get customer data manager."""
        return self.data_manager
    
    async def test_all_providers(self) -> Dict[str, Dict[str, Any]]:
        """Test all configured providers."""
        if not self.data_manager:
            return {}
        
        return await self.data_manager.test_all_connections()
    
    async def test_provider(self, provider_name: str) -> Dict[str, Any]:
        """Test specific provider."""
        if not self.data_manager:
            return {"status": "error", "error": "No data manager available"}
        
        if provider_name not in self.data_manager.providers:
            return {"status": "error", "error": "Provider not found"}
        
        provider = self.data_manager.providers[provider_name]
        return await provider.test_connection()
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about configured providers."""
        if not self.data_manager:
            return {
                "total_providers": 0,
                "primary_provider": None,
                "available_providers": []
            }
        
        return self.data_manager.get_provider_info()
    
    def create_default_config(self, business_name: str, industry: str) -> BusinessConfig:
        """Create and save default configuration."""
        business_config = BusinessConfig.create_default_config(business_name, industry)
        self.save_business_config(business_config)
        return business_config
    
    def update_provider_status(self, provider_name: str, enabled: bool):
        """Update provider enabled status."""
        if not self.business_config:
            raise Exception("No business config available")
        
        for provider in self.business_config.data_providers:
            if provider.provider_name == provider_name:
                provider.enabled = enabled
                break
        
        self.save_business_config(self.business_config)
    
    def set_primary_provider(self, provider_name: str):
        """Set primary data provider."""
        if not self.business_config:
            raise Exception("No business config available")
        
        # Check if provider exists
        provider_exists = any(
            p.provider_name == provider_name 
            for p in self.business_config.data_providers
        )
        
        if not provider_exists:
            raise Exception(f"Provider {provider_name} not found")
        
        self.business_config.primary_data_provider = provider_name
        self.save_business_config(self.business_config)
    
    def get_industry_template(self) -> Dict[str, Any]:
        """Get industry template for current business."""
        if not self.business_config:
            return {}
        
        template = self.business_config.get_industry_template()
        return template.dict()
    
    def export_config(self) -> Dict[str, Any]:
        """Export configuration for backup."""
        if not self.business_config:
            return {}
        
        return {
            "business_config": self.business_config.dict(),
            "export_timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    
    def import_config(self, config_data: Dict[str, Any]):
        """Import configuration from backup."""
        try:
            if "business_config" in config_data:
                business_config = BusinessConfig(**config_data["business_config"])
                self.save_business_config(business_config)
            else:
                raise Exception("Invalid config format")
        except Exception as e:
            raise Exception(f"Error importing config: {e}")
    
    def reset_config(self):
        """Reset configuration to default state."""
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        
        self.business_config = None
        self.data_manager = None
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration."""
        if not self.business_config:
            return {
                "valid": False,
                "errors": ["No business configuration found"],
                "warnings": []
            }
        
        errors = []
        warnings = []
        
        # Check required fields
        if not self.business_config.business_name:
            errors.append("Business name is required")
        
        if not self.business_config.industry:
            errors.append("Industry is required")
        
        # Check data providers
        if not self.business_config.data_providers:
            warnings.append("No data providers configured")
        
        if not self.business_config.primary_data_provider:
            warnings.append("No primary data provider set")
        
        # Check if primary provider exists
        if self.business_config.primary_data_provider:
            primary_exists = any(
                p.provider_name == self.business_config.primary_data_provider
                for p in self.business_config.data_providers
            )
            if not primary_exists:
                errors.append("Primary data provider not found in configured providers")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }