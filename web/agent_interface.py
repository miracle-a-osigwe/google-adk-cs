"""Agent interface for human customer service representatives."""
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from pathlib import Path

from fastapi import FastAPI, Request, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from agents.customer_service_agents import root_agent, coordinator_agent, reception_agent, knowledge_agent, technical_agent, escalation_agent, followup_agent, learning_agent
from config import config

# Create agent app
agent_app = FastAPI(
    title="Agent Dashboard",
    description="Interface for human customer service agents",
    version="1.0.0"
)


# 2. Define the path to this file
current_file_path = Path(__file__)
static_dir = current_file_path.parent.joinpath("static")
TEMPLATE_DIR = current_file_path.parent.joinpath("templates/agent")

# This is the corrected initialization
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# 4. Mount the static files using the absolute path
#    Make sure the static directory actually exists!
if not static_dir.exists():
    print(f"Warning: Static directory not found at {static_dir}. Creating it.")
    static_dir.mkdir(parents=True, exist_ok=True)


# Initialize templates
# templates = Jinja2Templates(directory="adk_customer_service/web/templates/agent")

# Mount static files
agent_app.mount("/static", StaticFiles(directory=static_dir), name="static")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections.copy():
            try:
                await connection.send_json(message)
            except:
                self.active_connections.discard(connection)

manager = ConnectionManager()

# Get available agents from the coordinator
def get_available_agents():
    """Get available agents from the coordinator agent."""
    agents = {
        "reception_agent": {
            "id": f"agent_{uuid.uuid4().hex[:8]}",
            "name": reception_agent.name,
            "team": config.reception_agent.team,
            "description": "Categorizes and prioritizes customer requests",
            "icon": "sitemap"
        },
        "knowledge_agent": {
            "id": f"agent_{uuid.uuid4().hex[:8]}",
            "name": knowledge_agent.name,
            "team": config.knowledge_agent.team,
            "description": "Searches knowledge base and provides documented solutions",
            "icon": "book"
        },
        "technical_agent": {
            "id": f"agent_{uuid.uuid4().hex[:8]}",
            "name": technical_agent.name,
            "team": config.technical_agent.team,
            "description": "Provides technical troubleshooting and problem-solving",
            "icon": "cogs"
        },
        "escalation_agent": {
            "id": f"agent_{uuid.uuid4().hex[:8]}",
            "name": escalation_agent.name,
            "team": config.escalation_agent.team,
            "description": "Manages escalation to human specialists",
            "icon": "users"
        },
        "followup_agent": {
            "id": f"agent_{uuid.uuid4().hex[:8]}",
            "name": followup_agent.name,
            "team": config.followup_agent.team,
            "description": "Ensures customer satisfaction and proper issue resolution",
            "icon": "check-circle"
        },
        "learning_agent": {
            "id": f"agent_{uuid.uuid4().hex[:8]}",
            "name": learning_agent.name,
            "team": config.learning_agent.team,
            "description": "Analyzes interactions for continuous system improvement",
            "icon": "brain"
        }
    }
    return agents


@agent_app.get("/", response_class=HTMLResponse)
async def agent_dashboard(request: Request, agent_id: Optional[str] = None):
    """Main agent dashboard."""
    # Get available agents
    available_agents = get_available_agents()
    
    # Mock queue data
    queue_data = {
        "waiting": 0,
        "in_progress": 0,
        "escalated": 0,
        "avg_wait_time": "0 min"
    }
    active_conversations = []
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "agent": agent_data,
        "queue": queue_data,
        "page_title": "Agent Dashboard",
        "available_agents": available_agents,
        "active_conversations": active_conversations
    })

@agent_app.get("/queue", response_class=HTMLResponse)
async def ticket_queue(request: Request, agent_id: Optional[str] = None):
    """Ticket queue management."""
    
    # Mock queue tickets
    tickets = [
        {
            "id": "TICK-001",
            "customer": "John Doe",
            "subject": "API Integration Issue",
            "priority": "high",
            "category": "technical",
            "wait_time": "5 min",
            "customer_tier": "enterprise"
        },
        {
            "id": "TICK-002",
            "customer": "Jane Smith", 
            "subject": "Billing Question",
            "priority": "medium",
            "category": "billing",
            "wait_time": "12 min",
            "customer_tier": "premium"
        },
        {
            "id": "TICK-003",
            "customer": "Mike Johnson",
            "subject": "Password Reset Help",
            "priority": "low",
            "category": "account",
            "wait_time": "8 min",
            "customer_tier": "standard"
        }
    ]
    
    return templates.TemplateResponse("queue.html", {
        "request": request,
        "tickets": tickets,
        "agent_id": agent_id,
        "page_title": "Ticket Queue"
    })

@agent_app.get("/chat/{conversation_id}", response_class=HTMLResponse)
async def agent_chat(request: Request, conversation_id: str, agent_id: Optional[str] = None):
    """Agent chat interface for specific conversation."""
    
    # Mock conversation data
    conversation = {
        "id": conversation_id,
        "customer": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "tier": "enterprise",
            "previous_tickets": 3
        },
        "context": {
            "category": "technical",
            "priority": "high",
            "ai_summary": "Customer experiencing API authentication issues with Salesforce integration",
            "suggested_actions": [
                "Check API credentials",
                "Verify endpoint configuration",
                "Test with minimal payload"
            ]
        },
        "messages": [
            {
                "sender": "customer",
                "text": "I'm getting 401 errors when trying to authenticate with your API",
                "timestamp": "2024-01-15T10:30:00"
            },
            {
                "sender": "ai",
                "text": "I understand you're experiencing authentication issues. Let me connect you with a technical specialist.",
                "timestamp": "2024-01-15T10:30:30"
            }
        ]
    }
    
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "conversation": conversation,
        "agent_id": agent_id,
        "page_title": f"Chat - {conversation['customer']['name']}"
    })

@agent_app.get("/customer/{customer_id}", response_class=HTMLResponse)
async def customer_profile(request: Request, customer_id: str):
    """Customer profile and history."""
    
    # Mock customer data
    customer = {
        "id": customer_id,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "company": "TechCorp Inc",
        "tier": "enterprise",
        "since": "2022-03-15",
        "total_tickets": 12,
        "satisfaction_score": 4.2,
        "recent_activity": [
            {"date": "2024-01-15", "type": "ticket", "description": "API Integration Issue"},
            {"date": "2024-01-10", "type": "login", "description": "Account access"},
            {"date": "2024-01-08", "type": "ticket", "description": "Billing inquiry"}
        ],
        "preferences": {
            "contact_method": "email",
            "language": "English",
            "timezone": "PST"
        }
    }
    
    return templates.TemplateResponse("customer_profile.html", {
        "request": request,
        "customer": customer,
        "page_title": f"Customer Profile - {customer['name']}"
    })

@agent_app.get("/knowledge", response_class=HTMLResponse)
async def agent_knowledge_base(request: Request):
    """Agent knowledge base and resources."""
    
    # Mock knowledge sections
    knowledge_sections = [
        {
            "title": "Technical Troubleshooting",
            "articles": [
                "API Authentication Guide",
                "Common Integration Issues",
                "Error Code Reference"
            ]
        },
        {
            "title": "Billing Procedures",
            "articles": [
                "Refund Process",
                "Subscription Changes",
                "Payment Method Updates"
            ]
        },
        {
            "title": "Escalation Guidelines",
            "articles": [
                "When to Escalate",
                "Specialist Teams",
                "Handoff Procedures"
            ]
        }
    ]
    
    return templates.TemplateResponse("knowledge.html", {
        "request": request,
        "knowledge_sections": knowledge_sections,
        "page_title": "Knowledge Base"
    })

@agent_app.get("/agent-metrics", response_class=HTMLResponse)
async def agent_metrics(request: Request):
    """View metrics about AI agent performance."""
    
    # Get available agents
    available_agents = get_available_agents()
    
    # In a real implementation, this would fetch metrics from a database
    # For now, we'll use mock data
    agent_metrics = {
        "reception_agent": {
            "total_requests": 1250,
            "accuracy": 0.94,
            "avg_processing_time": "1.2s",
            "success_rate": 0.96
        },
        "knowledge_agent": {
            "total_searches": 980,
            "hit_rate": 0.78,
            "avg_processing_time": "0.8s",
            "relevance_score": 0.85
        },
        "technical_agent": {
            "total_cases": 456,
            "resolution_rate": 0.82,
            "avg_processing_time": "3.5s",
            "escalation_rate": 0.18
        },
        "escalation_agent": {
            "total_escalations": 163,
            "routing_accuracy": 0.91,
            "avg_processing_time": "2.1s",
            "specialist_satisfaction": 0.88
        }
    }
    
    return templates.TemplateResponse("agent_metrics.html", {
        "request": request,
        "agent_metrics": agent_metrics,
        "available_agents": available_agents,
        "page_title": "Agent Metrics"
    })

@agent_app.post("/ticket/{ticket_id}/assign")
async def assign_ticket(ticket_id: str, agent_id: str = Form(...)):
    """Assign ticket to agent."""
    
    try:
        # Mock ticket assignment
        assignment_data = {
            "ticket_id": ticket_id,
            "agent_id": agent_id,
            "assigned_at": datetime.now().isoformat(),
            "status": "assigned"
        }
        
        # Broadcast update to connected agents
        await manager.broadcast({
            "type": "ticket_assigned",
            "data": assignment_data
        })
        
        return JSONResponse({
            "status": "success",
            "message": f"Ticket {ticket_id} assigned successfully"
        })
        
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)

@agent_app.post("/chat/{conversation_id}/message")
async def send_agent_message(
    conversation_id: str,
    agent_id: str = Form(...),
    message: str = Form(...),
    action: Optional[str] = Form(None)
):
    """Send message from agent to customer."""
    
    try:
        message_data = {
            "conversation_id": conversation_id,
            "agent_id": agent_id,
            "message": message,
            "action": action,
            "timestamp": datetime.now().isoformat()
        }
        
        # Broadcast to customer interface
        await manager.broadcast({
            "type": "agent_message",
            "data": message_data
        })
        
        return JSONResponse({
            "status": "success",
            "message": "Message sent successfully"
        })
        
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)

@agent_app.websocket("/ws/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message["type"] == "status_update":
                await manager.broadcast({
                    "type": "agent_status",
                    "agent_id": agent_id,
                    "status": message["status"]
                })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)