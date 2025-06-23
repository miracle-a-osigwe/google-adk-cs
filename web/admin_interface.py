"""Admin web interface for system configuration and monitoring."""
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from admin.admin_api import admin_app as base_admin_app
from admin.config_manager import ConfigManager
from models.business_config import BusinessConfig
from integrations.base_provider import IntegrationConfig
from integrations.customer_data_manager import CustomerDataManager

# Create enhanced admin app
admin_app = FastAPI(
    title="Customer Service Admin Interface",
    description="Complete admin interface for customer service system",
    version="1.0.0"
)

# 2. Define the path to this file
current_file_path = Path(__file__)
static_dir = current_file_path.parent.joinpath("static")
TEMPLATE_DIR = current_file_path.parent.joinpath("templates/admin")

# This is the corrected initialization
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# 4. Mount the static files using the absolute path
#    Make sure the static directory actually exists!
if not static_dir.exists():
    print(f"Warning: Static directory not found at {static_dir}. Creating it.")
    static_dir.mkdir(parents=True, exist_ok=True)

# Mount the base admin app
admin_app.mount("/api", base_admin_app)

# Initialize templates
# templates = Jinja2Templates(directory="adk_customer_service/web/templates/admin")

# Mount static files
admin_app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Initialize config manager
config_manager = ConfigManager()

@admin_app.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Enhanced admin dashboard with comprehensive metrics."""
    try:
        business_config = config_manager.get_business_config()
        provider_status = await config_manager.test_all_providers()
        
        # Get system metrics
        system_metrics = {
            "total_requests": 1250,
            "resolution_rate": 0.87,
            "escalation_rate": 0.13,
            "avg_response_time": "2.3 minutes",
            "customer_satisfaction": 4.2,
            "active_conversations": 23
        }
        
        # Get recent activity
        recent_activity = [
            {"time": "2 min ago", "event": "New customer registered", "type": "info"},
            {"time": "5 min ago", "event": "Integration test successful", "type": "success"},
            {"time": "10 min ago", "event": "High priority ticket escalated", "type": "warning"},
            {"time": "15 min ago", "event": "Knowledge base updated", "type": "info"}
        ]

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "business_config": business_config,
            "provider_status": provider_status,
            "system_metrics": system_metrics,
            "recent_activity": recent_activity,
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

@admin_app.get("/analytics", response_class=HTMLResponse)
async def analytics_dashboard(request: Request):
    """Analytics and reporting dashboard."""
    try:
        business_config = config_manager.get_business_config()
        
        # Mock analytics data
        analytics_data = {
            "request_volume": {
                "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                "data": [120, 150, 180, 140, 200, 90, 70]
            },
            "category_breakdown": {
                "technical": 45,
                "billing": 25,
                "account": 20,
                "general": 10
            },
            "resolution_trends": {
                "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
                "resolved": [85, 87, 89, 91],
                "escalated": [15, 13, 11, 9]
            },
            "customer_satisfaction": {
                "excellent": 60,
                "good": 25,
                "fair": 10,
                "poor": 5
            }
        }
        
        return templates.TemplateResponse("analytics.html", {
            "request": request,
            "business_config": business_config,
            "analytics_data": analytics_data
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@admin_app.get("/knowledge-management", response_class=HTMLResponse)
async def knowledge_management(request: Request):
    """Knowledge base management interface."""
    try:
        business_config = config_manager.get_business_config()
        
        # Mock knowledge base data
        knowledge_stats = {
            "total_articles": 156,
            "categories": 8,
            "last_updated": "2 hours ago",
            "search_accuracy": 0.89,
            "most_accessed": [
                {"title": "Password Reset Guide", "views": 245},
                {"title": "API Integration Setup", "views": 189},
                {"title": "Billing FAQ", "views": 167}
            ]
        }
        
        return templates.TemplateResponse("knowledge_management.html", {
            "request": request,
            "business_config": business_config,
            "knowledge_stats": knowledge_stats
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@admin_app.get("/agent-performance", response_class=HTMLResponse)
async def agent_performance(request: Request):
    """Agent performance monitoring dashboard."""
    try:
        business_config = config_manager.get_business_config()
        
        # Mock agent performance data
        agent_metrics = {
            "reception_agent": {
                "accuracy": 0.94,
                "avg_processing_time": "1.2s",
                "total_requests": 1250,
                "success_rate": 0.96
            },
            "knowledge_agent": {
                "hit_rate": 0.78,
                "avg_processing_time": "0.8s",
                "total_searches": 980,
                "relevance_score": 0.85
            },
            "technical_agent": {
                "resolution_rate": 0.82,
                "avg_processing_time": "3.5s",
                "total_cases": 456,
                "escalation_rate": 0.18
            },
            "escalation_agent": {
                "routing_accuracy": 0.91,
                "avg_processing_time": "2.1s",
                "total_escalations": 163,
                "specialist_satisfaction": 0.88
            }
        }
        
        return templates.TemplateResponse("agent_performance.html", {
            "request": request,
            "business_config": business_config,
            "agent_metrics": agent_metrics
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

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

@admin_app.get("/integrations-old", response_class=HTMLResponse)
async def integrations_page(request: Request):
    """Integrations management page."""
    # Mock integrations data
    integrations = [
        {"name": "Salesforce", "type": "CRM", "enabled": True, "icon": "cloud", "color": "blue"},
        {"name": "Zendesk", "type": "Support", "enabled": True, "icon": "headset", "color": "green"},
        {"name": "Shopify", "type": "E-commerce", "enabled": False, "icon": "shopping-cart", "color": "purple"},
    ]
    return templates.TemplateResponse("integrations.html", {
        "request": request,
        "integrations": integrations
    })

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

@admin_app.get("/customers-old", response_class=HTMLResponse)
async def customers_page(request: Request):
    """Customer list page."""
    # Mock customer data
    customers = [
        {"name": "Alice Johnson", "email": "alice@example.com", "last_interaction": "2 hours ago", "total_requests": 5, "satisfaction": 4.8, "avatar": "https://i.pravatar.cc/150?u=alice"},
        {"name": "Bob Williams", "email": "bob@example.com", "last_interaction": "1 day ago", "total_requests": 2, "satisfaction": 4.2, "avatar": "https://i.pravatar.cc/150?u=bob"},
        {"name": "Charlie Brown", "email": "charlie@example.com", "last_interaction": "3 days ago", "total_requests": 8, "satisfaction": 3.5, "avatar": "https://i.pravatar.cc/150?u=charlie"},
        {"name": "Diana Prince", "email": "diana@example.com", "last_interaction": "1 week ago", "total_requests": 1, "satisfaction": 5.0, "avatar": "https://i.pravatar.cc/150?u=diana"},
    ]
    return templates.TemplateResponse("customers.html", {
        "request": request,
        "customers": customers
    })

@admin_app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """System settings page."""
    try:
        # Fetch existing config or use a default if not found
        business_config = config_manager.get_business_config()
        if not business_config:
            # Create a default mock config for the template if none exists
            business_config = {
                "business_name": "My Awesome Company",
                "industry": "Technology"
            }
        
        return templates.TemplateResponse("settings.html", {
            "request": request,
            "business_config": business_config
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {"request": request, "error": str(e)})