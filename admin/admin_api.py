"""Admin web interface for configuring the customer service system."""

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json

from .config_manager import ConfigManager
from models.business_config import BusinessConfig
from integrations.base_provider import IntegrationConfig
from integrations.customer_data_manager import CustomerDataManager

# Create admin FastAPI app
admin_app = FastAPI(
    title="Customer Service Admin",
    description="Admin interface for customer service configuration",
    version="1.0.0"
)

# Initialize templates
templates = Jinja2Templates(directory="adk_customer_service/admin/templates")

# Initialize config manager
config_manager = ConfigManager()

# API Models
class BusinessConfigModel(BaseModel):
    business_name: str
    industry: str
    business_description: Optional[str] = None

class IntegrationConfigModel(BaseModel):
    provider_type: str
    provider_name: str
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database_url: Optional[str] = None
    custom_config: Dict[str, Any] = {}
    enabled: bool = True

# Admin Routes
@admin_app.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Admin dashboard."""
    try:
        business_config = config_manager.get_business_config()
        provider_status = await config_manager.test_all_providers()
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "business_config": business_config,
            "provider_status": provider_status,
            "total_providers": len(business_config.data_providers) if business_config else 0
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@admin_app.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request):
    """Initial setup page."""
    return templates.TemplateResponse("setup.html", {
        "request": request,
        "industries": ["ecommerce", "saas", "healthcare", "financial", "retail"]
    })

@admin_app.post("/setup")
async def create_business_config(
    business_name: str = Form(...),
    industry: str = Form(...),
    business_description: str = Form("")
):
    """Create initial business configuration."""
    try:
        business_config = BusinessConfig.create_default_config(business_name, industry)
        business_config.business_description = business_description
        
        config_manager.save_business_config(business_config)
        
        return RedirectResponse(url="/admin/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_app.get("/integrations", response_class=HTMLResponse)
async def integrations_page(request: Request):
    """Integrations management page."""
    try:
        business_config = config_manager.get_business_config()
        if not business_config:
            return RedirectResponse(url="/admin/setup")
        
        provider_status = await config_manager.test_all_providers()
        
        return templates.TemplateResponse("integrations.html", {
            "request": request,
            "business_config": business_config,
            "provider_status": provider_status,
            "provider_types": ["salesforce", "hubspot", "zendesk", "shopify", "postgresql"]
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@admin_app.post("/integrations/add")
async def add_integration(
    provider_type: str = Form(...),
    provider_name: str = Form(...),
    api_key: str = Form(""),
    api_secret: str = Form(""),
    username: str = Form(""),
    password: str = Form(""),
    api_endpoint: str = Form(""),
    database_url: str = Form(""),
    custom_config_json: str = Form("{}")
):
    """Add new integration."""
    try:
        business_config = config_manager.get_business_config()
        if not business_config:
            raise HTTPException(status_code=400, detail="Business config not found")
        
        # Parse custom config
        try:
            custom_config = json.loads(custom_config_json) if custom_config_json else {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid custom config JSON")
        
        # Create integration config
        integration_config = IntegrationConfig(
            provider_type=provider_type,
            provider_name=provider_name,
            api_key=api_key if api_key else None,
            api_secret=api_secret if api_secret else None,
            username=username if username else None,
            password=password if password else None,
            api_endpoint=api_endpoint if api_endpoint else None,
            database_url=database_url if database_url else None,
            custom_config=custom_config,
            enabled=True
        )
        
        # Add to business config
        business_config.add_data_provider(integration_config)
        
        # Set as primary if it's the first one
        if len(business_config.data_providers) == 1:
            business_config.primary_data_provider = provider_name
        
        config_manager.save_business_config(business_config)
        
        return RedirectResponse(url="/admin/integrations", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_app.post("/integrations/{provider_name}/test")
async def test_integration(provider_name: str):
    """Test specific integration."""
    try:
        result = await config_manager.test_provider(provider_name)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@admin_app.post("/integrations/{provider_name}/toggle")
async def toggle_integration(provider_name: str):
    """Enable/disable integration."""
    try:
        business_config = config_manager.get_business_config()
        if not business_config:
            raise HTTPException(status_code=400, detail="Business config not found")
        
        # Find and toggle the provider
        for provider in business_config.data_providers:
            if provider.provider_name == provider_name:
                provider.enabled = not provider.enabled
                break
        
        config_manager.save_business_config(business_config)
        
        return {"status": "success", "enabled": provider.enabled}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@admin_app.get("/customers", response_class=HTMLResponse)
async def customers_page(request: Request):
    """Customer data management page."""
    try:
        business_config = config_manager.get_business_config()
        if not business_config:
            return RedirectResponse(url="/admin/setup")
        
        # Get sample customers
        data_manager = CustomerDataManager(business_config)
        sample_customers = await data_manager.search_customers("", limit=10)
        
        return templates.TemplateResponse("customers.html", {
            "request": request,
            "business_config": business_config,
            "customers": sample_customers,
            "provider_info": data_manager.get_provider_info()
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@admin_app.get("/customers/search")
async def search_customers(query: str = "", limit: int = 10):
    """Search customers API."""
    try:
        business_config = config_manager.get_business_config()
        if not business_config:
            return {"customers": [], "error": "Business config not found"}
        
        data_manager = CustomerDataManager(business_config)
        customers = await data_manager.search_customers(query, limit)
        
        return {
            "customers": [customer.model_dump() for customer in customers],
            "total": len(customers)
        }
    except Exception as e:
        return {"customers": [], "error": str(e)}

@admin_app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """System settings page."""
    try:
        business_config = config_manager.get_business_config()
        if not business_config:
            return RedirectResponse(url="/admin/setup")
        
        return templates.TemplateResponse("settings.html", {
            "request": request,
            "business_config": business_config
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@admin_app.post("/settings/update")
async def update_settings(
    max_conversation_turns: int = Form(10),
    escalation_threshold: int = Form(3),
    data_retention_days: int = Form(1095),
    default_timezone: str = Form("UTC"),
    supported_languages: str = Form("en")
):
    """Update system settings."""
    try:
        business_config = config_manager.get_business_config()
        if not business_config:
            raise HTTPException(status_code=400, detail="Business config not found")
        
        # Update settings
        business_config.max_conversation_turns = max_conversation_turns
        business_config.escalation_threshold = escalation_threshold
        business_config.data_retention_days = data_retention_days
        business_config.default_timezone = default_timezone
        business_config.supported_languages = [lang.strip() for lang in supported_languages.split(",")]
        
        config_manager.save_business_config(business_config)
        
        return RedirectResponse(url="/admin/settings", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_app.get("/api/status")
async def system_status():
    """Get system status API."""
    try:
        business_config = config_manager.get_business_config()
        if not business_config:
            return {"status": "not_configured"}
        
        provider_status = await config_manager.test_all_providers()
        
        return {
            "status": "configured",
            "business_name": business_config.business_name,
            "industry": business_config.industry,
            "total_providers": len(business_config.data_providers),
            "active_providers": len([p for p in business_config.data_providers if p.enabled]),
            "provider_status": provider_status
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Error handlers
@admin_app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse("error.html", {
        "request": request,
        "error": "Page not found"
    }, status_code=404)

@admin_app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    return templates.TemplateResponse("error.html", {
        "request": request,
        "error": "Internal server error"
    }, status_code=500)