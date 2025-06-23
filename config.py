"""Configuration module for the ADK customer service ecosystem."""

import os
import logging
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AgentModel(BaseModel):
    """Agent model settings."""
    name: str = Field(default="customer_service_agent")
    team: str = Field(default="Customer Support")
    model: str = Field(default="gemini-2.0-flash-001")

class ReceptionAgentModel(BaseModel):
    """Reception agent settings."""
    name: str = Field(default="reception_agent")
    team: str = Field(default="General Support")
    model: str = Field(default="gemini-2.0-flash-001")

class KnowledgeAgentModel(BaseModel):
    """Knowledge agent settings."""
    name: str = Field(default="knowledge_agent")
    team: str = Field(default="Knowledge Base Support")
    model: str = Field(default="gemini-2.0-flash-001")

class TechnicalAgentModel(BaseModel):
    """Technical agent settings."""
    name: str = Field(default="technical_agent")
    team: str = Field(default="Technical Support")
    model: str = Field(default="gemini-2.0-flash-001")

class EscalationAgentModel(BaseModel):
    """Escalation agent settings."""
    name: str = Field(default="escalation_agent")
    team: str = Field(default="Escalation Team")
    model: str = Field(default="gemini-2.0-flash-001")

class FollowupAgentModel(BaseModel):
    """Follow-up agent settings."""
    name: str = Field(default="followup_agent")
    team: str = Field(default="Followup Team")
    model: str = Field(default="gemini-2.0-flash-001")

class LearningAgentModel(BaseModel):
    """Learning agent settings."""
    name: str = Field(default="learning_agent")
    team: str = Field(default="R & D Team")
    model: str = Field(default="gemini-2.0-flash-001")

class Config(BaseSettings):
    """Configuration settings for the customer service ecosystem."""

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            ), ".env"
        ),
        env_prefix="GOOGLE_",
        case_sensitive=True,
    )
    # print(model_config)
    
    # Main coordinator agent
    coordinator_agent: AgentModel = Field(default=AgentModel(name="customer_service_coordinator"))
    
    # Specialized agents
    reception_agent: ReceptionAgentModel = Field(default=ReceptionAgentModel())
    knowledge_agent: KnowledgeAgentModel = Field(default=KnowledgeAgentModel())
    technical_agent: TechnicalAgentModel = Field(default=TechnicalAgentModel())
    escalation_agent: EscalationAgentModel = Field(default=EscalationAgentModel())
    followup_agent: FollowupAgentModel = Field(default=FollowupAgentModel())
    learning_agent: LearningAgentModel = Field(default=LearningAgentModel())
    
    # Application settings
    app_name: str = "customer_service_ecosystem"
    CLOUD_PROJECT: str = Field(default="my_project")
    CLOUD_LOCATION: str = Field(default="us-central1")
    GENAI_USE_VERTEXAI: str = Field(default="1")
    API_KEY: Optional[str] = Field(default="")
    
    # Knowledge base settings
    knowledge_base_path: str = "data/knowledge_base"
    max_conversation_turns: int = 10
    escalation_threshold: int = 3
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8008)
    log_level: str = Field(default="DEBUG")

config = Config()
