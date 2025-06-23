"""ADK Customer Service Agents using proper Google ADK patterns."""

import logging
import warnings

from google.adk import Agent
from google.adk.runners import Runner
from google.adk.cli.utils import create_empty_state
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent
from google.adk.tools import FunctionTool
from google.adk.sessions import InMemorySessionService
from google.adk.sessions import DatabaseSessionService

from config import Config
from prompts import (
    GLOBAL_INSTRUCTION,
    COORDINATOR_INSTRUCTION,
    TRIAGE_INSTRUCTION,
    KNOWLEDGE_INSTRUCTION,
    TECHNICAL_INSTRUCTION,
    ESCALATION_INSTRUCTION,
    FOLLOWUP_INSTRUCTION,
    LEARNING_INSTRUCTION
)
from tools.customer_service_tools import (
    search_knowledge_base,
    categorize_request,
    assess_priority,
    get_troubleshooting_steps,
    identify_issue_type,
    select_specialist_team,
    create_escalation_summary,
    assess_customer_satisfaction,
    determine_next_action,
    analyze_interaction_patterns,
    generate_improvement_suggestions,
    save_to_session_state,
    get_from_session_state
)

warnings.filterwarnings("ignore", category=UserWarning, module=".*pydantic.*")

configs = Config()
logger = logging.getLogger(__name__)

# Create an instance. That's it.
# session_service = InMemorySessionService()
db_url = "sqlite:///./my_agent_data.db"
session_service = DatabaseSessionService(db_url=db_url)

# Create function tools for each capability
search_kb_tool = FunctionTool(func=search_knowledge_base)
categorize_tool = FunctionTool(func=categorize_request)
priority_tool = FunctionTool(func=assess_priority)
troubleshooting_tool = FunctionTool(func=get_troubleshooting_steps)
issue_type_tool = FunctionTool(func=identify_issue_type)
specialist_tool = FunctionTool(func=select_specialist_team)
escalation_summary_tool = FunctionTool(func=create_escalation_summary)
satisfaction_tool = FunctionTool(func=assess_customer_satisfaction)
next_action_tool = FunctionTool(func=determine_next_action)
analysis_tool = FunctionTool(func=analyze_interaction_patterns)
suggestions_tool = FunctionTool(func=generate_improvement_suggestions)
save_state_tool = FunctionTool(func=save_to_session_state)
get_state_tool = FunctionTool(func=get_from_session_state)

# Reception Agent - Initial categorization and routing
reception_agent = LlmAgent(
    model=configs.reception_agent.model,
    global_instruction=GLOBAL_INSTRUCTION,
    instruction=TRIAGE_INSTRUCTION,
    name=configs.reception_agent.name,
    description="Categorizes and prioritizes customer requests for proper routing",
    tools=[
        categorize_tool,
        priority_tool,
        save_state_tool
    ],
    output_key="reception_assessment"
)

# Knowledge Agent - Search knowledge base and provide solutions
knowledge_agent = LlmAgent(
    model=configs.knowledge_agent.model,
    global_instruction=GLOBAL_INSTRUCTION,
    instruction=KNOWLEDGE_INSTRUCTION,
    name=configs.knowledge_agent.name,
    description="Searches knowledge base and provides documented solutions",
    tools=[
        search_kb_tool,
        get_state_tool,
        save_state_tool
    ],
    output_key="knowledge_response"
)

# Technical Agent - Complex troubleshooting and technical support
technical_agent = LlmAgent(
    model=configs.technical_agent.model,
    global_instruction=GLOBAL_INSTRUCTION,
    instruction=TECHNICAL_INSTRUCTION,
    name=configs.technical_agent.name,
    description="Provides specialized technical troubleshooting and problem-solving",
    tools=[
        issue_type_tool,
        troubleshooting_tool,
        get_state_tool,
        save_state_tool
    ],
    output_key="technical_response"
)

# Escalation Agent - Route to human specialists
escalation_agent = LlmAgent(
    model=configs.escalation_agent.model,
    global_instruction=GLOBAL_INSTRUCTION,
    instruction=ESCALATION_INSTRUCTION,
    name=configs.escalation_agent.name,
    description="Manages escalation to human specialists with comprehensive summaries",
    tools=[
        specialist_tool,
        escalation_summary_tool,
        get_state_tool,
        save_state_tool
    ],
    output_key="escalation_response"
)

# Follow-up Agent - Check satisfaction and ensure resolution
followup_agent = LlmAgent(
    model=configs.followup_agent.model,
    global_instruction=GLOBAL_INSTRUCTION,
    instruction=FOLLOWUP_INSTRUCTION,
    name=configs.followup_agent.name,
    description="Ensures customer satisfaction and proper issue resolution",
    tools=[
        satisfaction_tool,
        next_action_tool,
        get_state_tool,
        save_state_tool
    ],
    output_key="followup_response"
)

# Learning Agent - Analyze interactions for continuous improvement
learning_agent = LlmAgent(
    model=configs.learning_agent.model,
    global_instruction=GLOBAL_INSTRUCTION,
    instruction=LEARNING_INSTRUCTION,
    name=configs.learning_agent.name,
    description="Analyzes interactions for continuous system improvement",
    tools=[
        analysis_tool,
        suggestions_tool,
        get_state_tool,
        save_state_tool
    ],
    output_key="learning_insights"
)

# Main Coordinator Agent - Routes to appropriate workflows
coordinator_agent = LlmAgent(
    model=configs.coordinator_agent.model,
    global_instruction=GLOBAL_INSTRUCTION,
    instruction=COORDINATOR_INSTRUCTION,
    name=configs.coordinator_agent.name,
    description="Main coordinator for customer service requests",
    sub_agents=[
        reception_agent,
        knowledge_agent,
        technical_agent,
        escalation_agent,
        followup_agent,
        learning_agent
    ],
    tools=[
        categorize_tool,
        priority_tool,
        get_state_tool,
        save_state_tool
    ],
    # after_model_callback=simple_after_model_modifier # Assign the function here
    
)

# Export the main agent for use in applications
root_agent = coordinator_agent
runner = Runner(
    app_name="customer-service",
    agent=root_agent,
    session_service=session_service
)
logger.info("ADK Customer Service Agents initialized successfully")

def create_new_state():
    return create_empty_state(root_agent)