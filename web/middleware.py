import time
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

# Define the path to templates
TEMPLATE_DIR = Path(__file__).parent.joinpath("templates/customer")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors in the customer interface."""
    
    async def dispatch(self, request: Request, call_next):
        try:
            # Process the request normally
            response = await call_next(request)
            return response
            
        except Exception as e:
            # Check if the request is for the customer interface
            if request.url.path.startswith("/customer"):
                # For API endpoints, return JSON error
                if request.url.path.startswith("/customer/api") or request.headers.get("accept") == "application/json":
                    return JSONResponse(
                        status_code=500,
                        content={"status": "error", "message": str(e)}
                    )
                
                # For HTML endpoints, return error page
                return templates.TemplateResponse(
                    "error.html",
                    {"request": request, "error": str(e)},
                    status_code=500
                )
            
            # For other interfaces, just re-raise the exception
            raise e

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process the request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log the request
        print(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
        
        return response

class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    """Middleware for maintenance mode."""
    
    def __init__(self, app, maintenance_mode=False, completion_time=None):
        super().__init__(app)
        self.maintenance_mode = maintenance_mode
        self.completion_time = completion_time
    
    async def dispatch(self, request: Request, call_next):
        # Check if maintenance mode is active
        if self.maintenance_mode:
            # Only apply to customer interface
            if request.url.path.startswith("/customer"):
                # For API endpoints, return JSON error
                if request.url.path.startswith("/customer/api") or request.headers.get("accept") == "application/json":
                    return JSONResponse(
                        status_code=503,
                        content={
                            "status": "error", 
                            "message": "System is under maintenance. Please try again later.",
                            "completion_time": self.completion_time
                        }
                    )
                
                # For HTML endpoints, return maintenance page
                return templates.TemplateResponse(
                    "maintenance.html",
                    {"request": request, "completion_time": self.completion_time},
                    status_code=503
                )
        
        # Process the request normally if not in maintenance mode
        return await call_next(request)