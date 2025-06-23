"""Customer-facing web interface for self-service support."""
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import google.genai.types as types

from agents.customer_service_agents import runner, session_service, create_new_state
from integrations.customer_data_manager import CustomerDataManager
from models.business_config import BusinessConfig
from entities.customer import Customer
# Import the dependency we just created
from .dependencies import get_current_user

# Create customer app
customer_app = FastAPI(
    title="Customer Support Portal",
    description="Self-service customer support interface",
    version="1.0.0"
)

# 2. Define the path to this file
current_file_path = Path(__file__)
static_dir = current_file_path.parent.joinpath("static")
TEMPLATE_DIR = current_file_path.parent.joinpath("templates/customer")

# This is the corrected initialization
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# 4. Mount the static files using the absolute path
#    Make sure the static directory actually exists!
if not static_dir.exists():
    print(f"Warning: Static directory not found at {static_dir}. Creating it.")
    static_dir.mkdir(parents=True, exist_ok=True)


# Initialize templates
# templates = Jinja2Templates(directory="adk_customer_service/web/templates/customer")

# Mount static files
customer_app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Store active conversation sessions
CONVERSATION_SESSIONS: Dict[str, Dict[str, Any]] = {}

@customer_app.get("/", response_class=HTMLResponse)
async def customer_portal_home(request: Request):
    """Customer portal home page."""
    return templates.TemplateResponse("home.html", {
        "request": request,
        "page_title": "Customer Support Portal"
    })

# Add these new routes to serve the HTML pages
@customer_app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serves the login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@customer_app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Serves the signup page."""
    return templates.TemplateResponse("signup.html", {"request": request})

@customer_app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, user: Dict = Depends(get_current_user)):
    """User profile page."""
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user,
        "page_title": "My Profile"
    })

@customer_app.get("/support", response_class=HTMLResponse)
async def support_center(request: Request):
    """Support center with knowledge base and contact options."""
    
    # Mock knowledge base categories
    knowledge_categories = [
        {
            "name": "Getting Started",
            "icon": "play-circle",
            "articles": 12,
            "popular_articles": [
                "Account Setup Guide",
                "First Steps Tutorial",
                "Basic Configuration"
            ]
        },
        {
            "name": "Account Management",
            "icon": "user",
            "articles": 8,
            "popular_articles": [
                "Password Reset",
                "Profile Updates",
                "Security Settings"
            ]
        },
        {
            "name": "Billing & Payments",
            "icon": "credit-card",
            "articles": 6,
            "popular_articles": [
                "Payment Methods",
                "Billing Cycles",
                "Refund Policy"
            ]
        },
        {
            "name": "Technical Support",
            "icon": "settings",
            "articles": 15,
            "popular_articles": [
                "API Integration",
                "Troubleshooting Guide",
                "System Requirements"
            ]
        }
    ]
    
    return templates.TemplateResponse("support_center.html", {
        "request": request,
        "knowledge_categories": knowledge_categories,
        "page_title": "Support Center"
    })

@customer_app.get("/chat", response_class=HTMLResponse)
async def live_chat(request: Request, customer_id: Optional[str] = None):
    """Live chat interface."""

    # Generate session ID if not provided
    if not customer_id:
        customer_id = f"guest_{uuid.uuid4().hex[:8]}"
    
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "customer_id": customer_id,
        "page_title": "Live Chat Support"
    })

@customer_app.post("/chat/message")
async def send_chat_message(
    customer_id: str = Form(...),
    message: str = Form(...),
    conversation_id: Optional[str] = Form(None)
):
    """Handle chat message from customer."""
    
    try:
        # Generate conversation ID if not provided
        if not conversation_id:
            conversation_id = f"chat_{uuid.uuid4().hex[:8]}"

        # Get or create session data for this conversation
        # session_data = CONVERSATION_SESSIONS.setdefault(conversation_id, {})
        app_name = "customer-service"
        # Process the message through the root agent
        session = await session_service.get_session(
            app_name=app_name, user_id=customer_id, session_id=conversation_id
        )
        if session is None and not session:
            state = create_new_state()
            print("New session created")
            session = await session_service.create_session(
                app_name=app_name, user_id=customer_id, state=state, session_id=conversation_id
            )

        try:
            message = types.Content(role="user", parts=[types.Part(text=message)])
            events = [
                event
                async for event in runner.run_async(
                    user_id=customer_id,
                    session_id=session.id,
                    new_message=message,
                )
            ]
            # response_text = events[0].content.parts[0].text
            # Extract response text from events
            response_text = events[0].content.parts[0].text if events and events[0].content and events[0].content.parts else "I'm sorry, I couldn't process your request."
            # agent_response.get("output", "I'm sorry, I couldn't process your request.")
            
        except Exception as e:
            print(f"Agent processing error: {str(e)}")
            response_text = "I apologize, but I encountered an issue while processing your request. Please try again."

        return JSONResponse({
            "status": "success",
            "conversation_id": conversation_id,
            "response": {
                "text": response_text,
                "timestamp": datetime.now().isoformat(),
                "agent": "AI Assistant"
            }
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse({
            "status": "error",
            "error": f"Sorry, there was an internal error: {str(e.__class__.__name__)}. Please try again later"
        }, status_code=500)

@customer_app.get("/tickets", response_class=HTMLResponse)
async def customer_tickets(request: Request, customer: Dict = Depends(get_current_user)):
    """Customer ticket history and status."""
    customer_id = customer.get("sub") # 'sub' is the standard claim for user ID in a JWT
    if not customer_id:
        print(customer_id)
        return templates.TemplateResponse("login_required.html", {
            "request": request,
            "page_title": "Login Required"
        })
    
    # Mock ticket data
    tickets = [
        {
            "id": "TICK-001",
            "subject": "API Integration Help",
            "status": "resolved",
            "priority": "medium",
            "created": "2024-01-10",
            "last_update": "2024-01-12"
        },
        {
            "id": "TICK-002", 
            "subject": "Billing Question",
            "status": "in_progress",
            "priority": "low",
            "created": "2024-01-15",
            "last_update": "2024-01-15"
        }
    ]
    
    return templates.TemplateResponse("tickets.html", {
        "request": request,
        "customer_id": customer_id,
        "tickets": tickets,
        "page_title": "My Support Tickets"
    })

@customer_app.get("/me", response_class=JSONResponse)
async def get_my_profile(current_user: Dict = Depends(get_current_user)):
    """A protected API endpoint to get the current user's details."""
    # This is a good way to check if a user's session is still valid from the client.
    # Connect to managed session if agent_engine_id is set.
    user_id = current_user.get("sub")
    return {
        "message": "User is authenticated.",
        "user_id": user_id,
        "email": current_user.get("email"),
        "role": current_user.get("role"),
        "token_issued_at": datetime.fromtimestamp(current_user.get("iat")).isoformat()
    }

@customer_app.get("/knowledge/{category}")
async def knowledge_category(request: Request, category: str):
    """Knowledge base category page."""
    
    # Mock articles for category
    articles = {
        "getting-started": [
            {"title": "Account Setup Guide", "summary": "Complete guide to setting up your account"},
            {"title": "First Steps Tutorial", "summary": "Learn the basics in 5 minutes"},
            {"title": "Basic Configuration", "summary": "Essential settings for new users"}
        ],
        "account": [
            {"title": "Password Reset", "summary": "How to reset your password"},
            {"title": "Profile Updates", "summary": "Managing your profile information"},
            {"title": "Security Settings", "summary": "Keeping your account secure"}
        ]
    }
    
    category_articles = articles.get(category, [])
    
    return templates.TemplateResponse("knowledge_category.html", {
        "request": request,
        "category": category.replace("-", " ").title(),
        "articles": category_articles,
        "page_title": f"{category.replace('-', ' ').title()} - Knowledge Base"
    })

@customer_app.get("/feedback", response_class=HTMLResponse)
async def feedback_form(request: Request):
    """Customer feedback form."""
    return templates.TemplateResponse("feedback.html", {
        "request": request,
        "page_title": "Feedback"
    })

@customer_app.post("/feedback/submit")
async def submit_feedback(
    customer_id: str = Form(...),
    rating: int = Form(...),
    category: str = Form(...),
    message: str = Form(...),
    email: Optional[str] = Form(None)
):
    """Submit customer feedback."""
    
    try:
        feedback_data = {
            "customer_id": customer_id,
            "rating": rating,
            "category": category,
            "message": message,
            "email": email,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store feedback (mock)
        print(f"Feedback received: {feedback_data}")
        
        return JSONResponse({
            "status": "success",
            "message": "Thank you for your feedback!"
        })
        
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)

# Add error handling routes
@customer_app.exception_handler(404)
async def not_found_error(request: Request, exc):
    """Handle 404 errors."""
    return templates.TemplateResponse("error.html", {
        "request": request,
        "error": "The page you're looking for doesn't exist.",
        "page_title": "Page Not Found"
    }, status_code=404)

@customer_app.exception_handler(500)
async def server_error(request: Request, exc):
    """Handle 500 errors."""
    return templates.TemplateResponse("error.html", {
        "request": request,
        "error": "An internal server error occurred. Please try again later.",
        "page_title": "Server Error"
    }, status_code=500)

@customer_app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc):
    """Handle all other exceptions."""
    return templates.TemplateResponse("error.html", {
        "request": request,
        "error": f"An error occurred: {str(exc)}",
        "page_title": "Error"
    }, status_code=500)