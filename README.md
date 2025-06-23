# ADK Customer Service Ecosystem

A sophisticated multi-agent customer service system built with **Google's Agent Development Kit (ADK)**, demonstrating proper ADK patterns, agent orchestration, and intelligent workflow management.

## 🎯 Overview

This project implements a comprehensive customer service ecosystem using Google ADK's native patterns:

- **🎯 Reception Agent**: AI-powered request categorization and priority assessment
- **📚 Knowledge Agent**: Intelligent knowledge base search and solution retrieval
- **🔧 Technical Agent**: Specialized technical troubleshooting with structured procedures
- **⬆️ Escalation Agent**: Smart routing to human specialists with comprehensive summaries
- **✅ Follow-up Agent**: Customer satisfaction verification and case closure
- **🧠 Learning Agent**: Continuous improvement through interaction analysis

## 🏗️ ADK Architecture

Built using proper Google ADK patterns:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Customer      │──▶│  ADK Coordinator │───▶│   Specialized   │
│   Request       │    │     Agent        │    │   Sub-Agents    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   ADK Tools &    │
                       │   Workflows      │
                       └──────────────────┘
```

### ADK Components Used

1. **LlmAgent**: Core agents powered by Gemini models
2. **SequentialAgent**: Workflow orchestration for multi-step processes
3. **FunctionTool**: Tool integration for specialized capabilities
4. **Session State**: Shared context and data management
5. **Callbacks**: Lifecycle management and monitoring

## 🚀 Key ADK Features

### Proper Agent Patterns
- **Native ADK Agent instantiation** using `google.adk.Agent`
- **Configuration-driven setup** with Pydantic settings
- **Tool-based architecture** instead of custom methods
- **Workflow orchestration** using ADK workflow agents

### Multi-Agent Coordination
- **LLM-Driven Delegation** for dynamic agent routing
- **Shared Session State** for context preservation
- **Agent Hierarchy** with proper parent-child relationships
- **Callback System** for lifecycle management

### Tool Integration
- **FunctionTool** wrappers for all capabilities
- **Knowledge base search** and content retrieval
- **Technical troubleshooting** procedures
- **Escalation management** and specialist routing
- **Analytics and learning** tools

## 📋 Prerequisites

- Python 3.8+
- Google Cloud Project with ADK enabled
- Gemini API access
- Google ADK SDK installed

## 🛠️ Installation

1. **Install Google ADK**
   ```bash
   pip install google-adk
   ```

2. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd adk-customer-service
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Google Cloud and ADK configuration
   ```

## 🔧 Configuration

### Environment Variables

```env
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_API_KEY=your-api-key
```

### Agent Configuration

```python
from config import Config

configs = Config()
# Automatically loads agent settings, models, and tools
```

## 🚀 Usage

### Direct ADK Integration (deprecated)

```python
from agents.customer_service_agents import root_agent

# Use the root agent directly with ADK
response = await root_agent.run_async(user_message="I need help with my account")
```

### FastAPI Server

```bash
python -m api
```

Access the API at `http://localhost:8000` with full OpenAPI documentation.

### Demo Scenarios (deprecated)

```bash
python -m examples.demo_adk_ecosystem
```

## 📊 API Endpoints

### Core Endpoints

```bash
# Create support request
POST /support/request
{
  "customer_id": "customer_123",
  "message": "My application keeps crashing",
  "channel": "chat",
  "priority": "high"
}

# Follow-up message
POST /support/request/{request_id}/followup
{
  "message": "The solution worked! Thank you!"
}

# System metrics
GET /support/metrics

# Agent information
GET /agents
```

## 🧪 ADK Patterns Demonstrated

### Agent Hierarchy
```python
coordinator_agent = LlmAgent(
    name="coordinator",
    sub_agents=[
        reception_agent,
        knowledge_agent,
        technical_agent,
        escalation_agent,
        followup_agent,
        learning_agent
    ]
)
```

### Tool Integration
```python
search_tool = FunctionTool(func=search_knowledge_base)
categorize_tool = FunctionTool(func=categorize_request)

knowledge_agent = LlmAgent(
    name="knowledge_agent",
    tools=[search_tool, categorize_tool],
    output_key="knowledge_response"
)
```

### Workflow Orchestration
```python
support_workflow = SequentialAgent(
    name="support_workflow",
    sub_agents=[
        reception_agent,
        knowledge_agent,
        followup_agent,
        learning_agent
    ]
)
```

### Session State Management
```python
# Agents automatically share state through ADK session
# Reception agent saves assessment
context.session.state['reception_assessment'] = assessment

# Knowledge agent reads assessment
assessment = context.session.state.get('reception_assessment')
```

## 🔄 Agent Workflows

### Standard Support Flow
1. **Reception** → Categorize and prioritize request
2. **Knowledge** → Search for documented solutions
3. **Follow-up** → Verify resolution and satisfaction
4. **Learning** → Analyze for continuous improvement

### Technical Support Flow
1. **Reception** → Assess technical complexity
2. **Technical** → Provide troubleshooting steps
3. **Follow-up** → Check resolution status
4. **Learning** → Capture technical patterns

### Escalation Flow
1. **Reception** → Identify critical/complex issues
2. **Escalation** → Route to human specialists
3. **Follow-up** → Monitor specialist progress
4. **Learning** → Analyze escalation patterns


## 📈 Monitoring & Analytics

### ADK Callbacks
- **before_agent**: Track agent execution start
- **after_agent**: Measure execution time
- **before_tool**: Log tool usage
- **after_tool**: Capture tool results

### Session Analytics
- Agent execution paths
- Tool usage patterns
- Resolution effectiveness
- Customer satisfaction metrics

## 🔒 Security & Best Practices

- **Secure credential management** with Google Cloud IAM
- **Input validation** and sanitization
- **Rate limiting** through ADK callbacks
- **Audit logging** for compliance
- **Error handling** and graceful degradation

## 🌟 Advanced ADK Features

### LLM-Driven Delegation
```python
# Agents can dynamically route to other agents
# LLM generates: transfer_to_agent(agent_name='technical_agent')
```

### Parallel Processing
```python
parallel_search = ParallelAgent(
    name="parallel_search",
    sub_agents=[faq_searcher, solution_searcher]
)
```

### Loop Workflows
```python
refinement_loop = LoopAgent(
    name="solution_refinement",
    max_iterations=3,
    sub_agents=[generator, reviewer, checker]
)
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For questions and support:
- Check the `/docs` endpoint for API documentation
- Review the demo scenarios for usage examples
- Consult Google ADK documentation for deployment guidance

---

**Built with ❤️ using Google's Agent Development Kit**

*This project demonstrates proper ADK patterns for building sophisticated multi-agent systems with native Google Cloud integration, intelligent workflows, and production-ready architecture.*

- N.B: Some of the implementations are incomplete, due to progressive project development, limited time to complete them and potential to build this into a full SaaS infrastructure.