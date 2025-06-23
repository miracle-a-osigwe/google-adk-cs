"""Main entry point for the Customer Service Ecosystem."""
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from web.admin_interface import admin_app
from web.customer_interface import customer_app
from web.agent_interface import agent_app
from web.api_interface import api_app as enhanced_api_app
from web.middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware
from config import config

# Create main application
app = FastAPI(
    title="Customer Service Ecosystem",
    description="Complete customer service system with admin, customer, and agent interfaces",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# 2. Define the path to this file
current_file_path = Path(__file__)
static_dir = current_file_path.parent.joinpath("web/static")

# 4. Mount the static files using the absolute path
#    Make sure the static directory actually exists!
if not static_dir.exists():
    print(f"Warning: Static directory not found at {static_dir}. Creating it.")
    static_dir.mkdir(parents=True, exist_ok=True)

TEMPLATE_DIR = current_file_path.parent.joinpath("web/templates")

# This is the corrected initialization
templates = Jinja2Templates(directory=TEMPLATE_DIR)


# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount sub-applications
app.mount("/api", enhanced_api_app)
app.mount("/admin", admin_app)
app.mount("/customer", customer_app)
app.mount("/agent", agent_app)

@app.get("/")
async def root(request: Request):
    """Redirect to customer portal by default."""
    # return RedirectResponse(url="/customer/")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "interfaces": {
            "api": "/api",
            "admin": "/admin",
            "customer": "/customer",
            "agent": "/agent"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.api_host,
        port=config.api_port,
        log_level=config.log_level.lower(),
        reload=True
    )