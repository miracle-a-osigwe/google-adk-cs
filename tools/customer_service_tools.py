"""Tools for the ADK customer service ecosystem."""

import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from google.adk.agents.callback_context import CallbackContext
from typing import Optional
from google.genai import types
from google.adk.models import LlmResponse

logger = logging.getLogger(__name__)


# --- Define the Callback Function ---
def simple_after_model_modifier(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Inspects/modifies the LLM response after it's received."""
    agent_name = callback_context.agent_name
    print(f"[Callback] After model call for agent: {agent_name}")

    # --- Inspection ---
    original_text = ""
    if llm_response.content and llm_response.content.parts:
        # Assuming simple text response for this example
        if llm_response.content.parts[0].text:
            original_text = llm_response.content.parts[0].text
            print(f"[Callback] Inspected original response text: '{original_text[:100]}...'") # Log snippet
        elif llm_response.content.parts[0].function_call:
            print(f"[Callback] Inspected response: Contains function call '{llm_response.content.parts[0].function_call.name}'. No text modification.")
            return None # Don't modify tool calls in this example
        else:
            print("[Callback] Inspected response: No text content found.")
            return None
    elif llm_response.error_message:
        print(f"[Callback] Inspected response: Contains error '{llm_response.error_message}'. No modification.")
        return None
    else:
        print("[Callback] Inspected response: Empty LlmResponse.")
        return None # Nothing to modify

    # --- Modification Example ---
    # Replace "joke" with "funny story" (case-insensitive)
    search_term = "joke"
    replace_term = "funny story"
    if search_term in original_text.lower():
        print(f"[Callback] Found '{search_term}'. Modifying response.")
        modified_text = original_text.replace(search_term, replace_term)
        modified_text = modified_text.replace(search_term.capitalize(), replace_term.capitalize()) # Handle capitalization

        # Create a NEW LlmResponse with the modified content
        # Deep copy parts to avoid modifying original if other callbacks exist
        modified_parts = [copy.deepcopy(part) for part in llm_response.content.parts]
        modified_parts[0].text = modified_text # Update the text in the copied part

        new_response = LlmResponse(
            content=types.Content(role="model", parts=modified_parts),
            # Copy other relevant fields if necessary, e.g., grounding_metadata
            grounding_metadata=llm_response.grounding_metadata
            )
        print(f"[Callback] Returning modified response.")
        return new_response # Return the modified response
    else:
        print(f"[Callback] '{search_term}' not found. Passing original response through.")
        # Return None to use the original llm_response
        return None


# Knowledge Base Tools
def search_knowledge_base(query: str, category: str = "") -> Dict[str, Any]:
    """
    Search the knowledge base for relevant information.
    
    Args:
        query (str): The search query
        category (str): Optional category filter (technical, billing, account, general)
    
    Returns:
        Dict containing search results with relevance scores
    """
    logger.info(f"Searching knowledge base for: {query}, category: {category}")
    
    # Mock knowledge base data
    knowledge_base = {
        "faqs": [
            {
                "id": "faq_001",
                "question": "How do I reset my password?",
                "answer": "To reset your password, go to the login page and click 'Forgot Password'. Enter your email address and follow the instructions sent to your email.",
                "category": "account",
                "keywords": ["password", "reset", "login", "forgot", "access"]
            },
            {
                "id": "faq_002",
                "question": "Why is my payment failing?",
                "answer": "Payment failures can occur due to insufficient funds, expired cards, or incorrect billing information. Please check your payment method and try again.",
                "category": "billing",
                "keywords": ["payment", "failing", "declined", "billing", "card"]
            },
            {
                "id": "faq_003",
                "question": "How do I update my profile information?",
                "answer": "You can update your profile by logging into your account and navigating to 'Account Settings'. From there, you can modify your personal information, contact details, and preferences.",
                "category": "account",
                "keywords": ["profile", "update", "information", "settings", "account"]
            }
        ],
        "solutions": [
            {
                "id": "sol_001",
                "title": "Application Crash on Startup",
                "solution": "1. Clear application cache and temporary files\n2. Restart the application\n3. Update to the latest version\n4. Check system requirements\n5. Disable conflicting software\n6. Contact support if issue persists",
                "category": "technical",
                "keywords": ["crash", "startup", "error", "application", "launch"]
            },
            {
                "id": "sol_002",
                "title": "Slow Performance Issues",
                "solution": "1. Check available system memory and CPU usage\n2. Close unnecessary applications\n3. Clear browser cache and cookies\n4. Update your browser to the latest version\n5. Disable browser extensions temporarily\n6. Check internet connection speed",
                "category": "technical",
                "keywords": ["slow", "performance", "lag", "speed", "loading"]
            }
        ]
    }
    
    query_lower = query.lower()
    results = []
    
    # Search FAQs
    for faq in knowledge_base["faqs"]:
        if category and faq.get("category") != category:
            continue
        
        relevance = 0
        for keyword in faq.get("keywords", []):
            if keyword in query_lower:
                relevance += 1
        
        if relevance > 0:
            results.append({
                "type": "faq",
                "content": faq,
                "relevance_score": relevance / len(faq.get("keywords", [1]))
            })
    
    # Search Solutions
    for solution in knowledge_base["solutions"]:
        if category and solution.get("category") != category:
            continue
        
        relevance = 0
        for keyword in solution.get("keywords", []):
            if keyword in query_lower:
                relevance += 1
        
        if relevance > 0:
            results.append({
                "type": "solution",
                "content": solution,
                "relevance_score": relevance / len(solution.get("keywords", [1]))
            })
    
    # Sort by relevance
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    return {
        "query": query,
        "category": category,
        "results": results[:5],  # Top 5 results
        "total_found": len(results)
    }

def categorize_request(message: str) -> Dict[str, Any]:
    """
    Categorize a customer request using keyword analysis.
    
    Args:
        message (str): The customer message to categorize
    
    Returns:
        Dict containing category and confidence score
    """
    logger.info(f"Categorizing request: {message[:100]}...")
    
    category_keywords = {
        "technical": ["error", "bug", "crash", "not working", "broken", "issue", "slow", "performance"],
        "billing": ["payment", "charge", "invoice", "refund", "subscription", "billing", "cost"],
        "account": ["login", "password", "access", "profile", "settings", "account", "signin"],
        "general": ["question", "help", "how to", "information", "guide", "tutorial"]
    }
    
    message_lower = message.lower()
    category_scores = {}
    
    for category, keywords in category_keywords.items():
        score = sum(1 for keyword in keywords if keyword in message_lower)
        if score > 0:
            category_scores[category] = score
    
    if category_scores:
        best_category = max(category_scores, key=category_scores.get)
        confidence = category_scores[best_category] / len(category_keywords[best_category])
    else:
        best_category = "general"
        confidence = 0.5
    
    return {
        "category": best_category,
        "confidence": confidence,
        "all_scores": category_scores
    }

def assess_priority(message: str) -> Dict[str, Any]:
    """
    Assess the priority level of a customer request.
    
    Args:
        message (str): The customer message to assess
    
    Returns:
        Dict containing priority level and reasoning
    """
    logger.info(f"Assessing priority for: {message[:100]}...")
    
    priority_keywords = {
        "critical": ["urgent", "critical", "emergency", "down", "outage", "security", "breach", "data loss"],
        "high": ["important", "asap", "priority", "escalate", "business", "production", "broken"],
        "medium": ["soon", "when possible", "moderate", "standard", "issue"],
        "low": ["whenever", "no rush", "low priority", "minor", "question"]
    }
    
    message_lower = message.lower()
    
    for priority, keywords in priority_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            return {
                "priority": priority,
                "confidence": 0.8,
                "reasoning": f"Contains {priority}-priority keywords"
            }
    
    # Default priority based on message characteristics
    if any(word in message_lower for word in ["error", "crash", "not working"]):
        return {
            "priority": "high",
            "confidence": 0.6,
            "reasoning": "Contains error-related keywords"
        }
    
    return {
        "priority": "medium",
        "confidence": 0.5,
        "reasoning": "Default priority assignment"
    }

# Technical Support Tools
def get_troubleshooting_steps(issue_type: str) -> Dict[str, Any]:
    """
    Get structured troubleshooting steps for a specific issue type.
    
    Args:
        issue_type (str): The type of technical issue
    
    Returns:
        Dict containing troubleshooting steps and metadata
    """
    logger.info(f"Getting troubleshooting steps for: {issue_type}")
    
    troubleshooting_procedures = {
        "application_crash": {
            "title": "Application Crash Troubleshooting",
            "steps": [
                "Check system requirements and compatibility",
                "Clear application cache and temporary files",
                "Restart the application",
                "Update to the latest version",
                "Disable conflicting software or extensions",
                "Run application in safe mode",
                "Check system logs for error details",
                "Reinstall the application if necessary"
            ],
            "estimated_time": "15-30 minutes",
            "difficulty": "medium"
        },
        "login_issues": {
            "title": "Login Problem Resolution",
            "steps": [
                "Verify username and password accuracy",
                "Check for caps lock and special characters",
                "Clear browser cache and cookies",
                "Try incognito/private browsing mode",
                "Disable browser extensions",
                "Check network connectivity",
                "Reset password if necessary",
                "Contact support for account lockout"
            ],
            "estimated_time": "10-20 minutes",
            "difficulty": "easy"
        },
        "performance_issues": {
            "title": "Performance Optimization",
            "steps": [
                "Check system resource usage (CPU, RAM)",
                "Close unnecessary applications",
                "Clear cache and temporary files",
                "Update drivers and software",
                "Run system maintenance tools",
                "Check for malware or viruses",
                "Consider hardware limitations",
                "Optimize application settings"
            ],
            "estimated_time": "20-45 minutes",
            "difficulty": "medium"
        },
        "connectivity_issues": {
            "title": "Network Connectivity Troubleshooting",
            "steps": [
                "Check internet connection stability",
                "Restart router and modem",
                "Flush DNS cache",
                "Check firewall and antivirus settings",
                "Try different network or VPN",
                "Update network drivers",
                "Test with different device",
                "Contact ISP if issues persist"
            ],
            "estimated_time": "15-30 minutes",
            "difficulty": "medium"
        }
    }
    
    if issue_type in troubleshooting_procedures:
        return {
            "issue_type": issue_type,
            "found": True,
            **troubleshooting_procedures[issue_type]
        }
    else:
        return {
            "issue_type": issue_type,
            "found": False,
            "message": "No specific troubleshooting steps found for this issue type",
            "recommendation": "Please provide more details about the specific problem"
        }

def identify_issue_type(message: str) -> Dict[str, Any]:
    """
    Identify the type of technical issue from a customer message.
    
    Args:
        message (str): The customer message describing the issue
    
    Returns:
        Dict containing identified issue type and confidence
    """
    logger.info(f"Identifying issue type for: {message[:100]}...")
    
    issue_keywords = {
        "application_crash": ["crash", "freeze", "hang", "stop working", "error", "exception"],
        "login_issues": ["login", "sign in", "password", "authentication", "access", "signin"],
        "performance_issues": ["slow", "lag", "performance", "speed", "loading", "timeout"],
        "connectivity_issues": ["connection", "network", "internet", "offline", "timeout", "dns"]
    }
    
    message_lower = message.lower()
    
    for issue_type, keywords in issue_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            return {
                "issue_type": issue_type,
                "confidence": 0.8,
                "keywords_found": [kw for kw in keywords if kw in message_lower]
            }
    
    return {
        "issue_type": "general_technical",
        "confidence": 0.5,
        "keywords_found": [],
        "message": "Could not identify specific issue type"
    }

# Escalation Tools
def select_specialist_team(category: str, priority: str, issue_details: str) -> Dict[str, Any]:
    """
    Select the appropriate specialist team for escalation.
    
    Args:
        category (str): Issue category
        priority (str): Issue priority level
        issue_details (str): Detailed description of the issue
    
    Returns:
        Dict containing specialist team information
    """
    logger.info(f"Selecting specialist team for {category} issue with {priority} priority")
    
    specialist_teams = {
        "technical": {
            "name": "Technical Support Team",
            "availability": "24/7",
            "specialties": ["complex technical issues", "system integrations", "custom configurations"],
            "sla": "4 hours",
            "contact": "tech-support@company.com"
        },
        "billing": {
            "name": "Billing Support Team",
            "availability": "Business hours (9 AM - 6 PM EST)",
            "specialties": ["payment issues", "refunds", "subscription management"],
            "sla": "24 hours",
            "contact": "billing@company.com"
        },
        "account": {
            "name": "Account Management Team",
            "availability": "Business hours (9 AM - 6 PM EST)",
            "specialties": ["account access", "security issues", "data management"],
            "sla": "24 hours",
            "contact": "accounts@company.com"
        },
        "executive": {
            "name": "Executive Support Team",
            "availability": "24/7",
            "specialties": ["critical issues", "enterprise accounts", "escalated complaints"],
            "sla": "1 hour",
            "contact": "executive-support@company.com"
        }
    }
    
    # Critical priority goes to executive team
    if priority == "critical":
        return specialist_teams["executive"]
    
    # Route based on category
    team_key = category if category in specialist_teams else "technical"
    return specialist_teams[team_key]

def create_escalation_summary(customer_id: str, issue_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a comprehensive escalation summary for human specialists.
    
    Args:
        customer_id (str): Customer identifier
        issue_details (Dict): Complete issue context and history
    
    Returns:
        Dict containing formatted escalation summary
    """
    logger.info(f"Creating escalation summary for customer {customer_id}")
    
    escalation_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    summary = {
        "escalation_id": escalation_id,
        "timestamp": timestamp,
        "customer_id": customer_id,
        "issue_summary": issue_details.get("original_message", ""),
        "category": issue_details.get("category", "unknown"),
        "priority": issue_details.get("priority", "medium"),
        "agent_history": issue_details.get("agent_path", []),
        "troubleshooting_attempted": issue_details.get("troubleshooting_steps", []),
        "knowledge_base_searched": issue_details.get("knowledge_search_performed", False),
        "escalation_reason": issue_details.get("escalation_reason", "Issue complexity exceeds automated resolution"),
        "recommended_actions": [
            "Review customer history and previous interactions",
            "Assess technical complexity and resource requirements",
            "Provide personalized solution or workaround",
            f"Follow up within {issue_details.get('sla', '24 hours')}"
        ]
    }
    
    return summary

# Follow-up and Assessment Tools
def assess_customer_satisfaction(message: str) -> Dict[str, Any]:
    """
    Assess customer satisfaction from their response.
    
    Args:
        message (str): Customer's response message
    
    Returns:
        Dict containing satisfaction assessment
    """
    logger.info(f"Assessing customer satisfaction from: {message[:100]}...")
    
    satisfaction_keywords = {
        "high": ["excellent", "amazing", "perfect", "love", "fantastic", "outstanding", "great"],
        "medium": ["good", "okay", "fine", "decent", "satisfied", "helpful", "thanks"],
        "low": ["disappointed", "frustrated", "angry", "terrible", "awful", "poor", "bad"]
    }
    
    resolution_keywords = {
        "resolved": ["yes", "solved", "fixed", "working", "resolved", "thank you", "perfect"],
        "unresolved": ["no", "still", "not working", "problem", "issue", "help", "broken"],
        "partial": ["maybe", "partially", "somewhat", "kind of", "better"]
    }
    
    message_lower = message.lower()
    
    # Assess satisfaction level
    satisfaction = "unknown"
    for level, keywords in satisfaction_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            satisfaction = level
            break
    
    # Assess resolution status
    resolution_status = "unclear"
    for status, keywords in resolution_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            resolution_status = status
            break
    
    # Default assessment based on resolution status
    if satisfaction == "unknown":
        if resolution_status == "resolved":
            satisfaction = "medium"
        elif resolution_status == "unresolved":
            satisfaction = "low"
    
    return {
        "satisfaction_level": satisfaction,
        "resolution_status": resolution_status,
        "confidence": 0.7 if satisfaction != "unknown" else 0.4,
        "message_sentiment": "positive" if satisfaction == "high" else "negative" if satisfaction == "low" else "neutral"
    }

def determine_next_action(satisfaction_data: Dict[str, Any], interaction_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determine the next action based on satisfaction assessment and context.
    
    Args:
        satisfaction_data (Dict): Customer satisfaction assessment
        interaction_context (Dict): Complete interaction context
    
    Returns:
        Dict containing recommended next action
    """
    logger.info("Determining next action based on satisfaction and context")
    
    resolution_status = satisfaction_data.get("resolution_status", "unclear")
    satisfaction_level = satisfaction_data.get("satisfaction_level", "unknown")
    
    if resolution_status == "resolved" and satisfaction_level in ["high", "medium"]:
        return {
            "action": "close_case",
            "next_agent": "learning_agent",
            "reasoning": "Issue resolved and customer satisfied"
        }
    
    elif resolution_status == "unresolved":
        if interaction_context.get("escalated", False):
            return {
                "action": "check_escalation_status",
                "next_agent": "escalation_agent",
                "reasoning": "Issue was escalated but remains unresolved"
            }
        elif interaction_context.get("technical_analysis_performed", False):
            return {
                "action": "escalate_to_human",
                "next_agent": "escalation_agent",
                "reasoning": "Technical troubleshooting attempted but issue persists"
            }
        else:
            return {
                "action": "provide_technical_support",
                "next_agent": "technical_agent",
                "reasoning": "Issue unresolved, try technical troubleshooting"
            }
    
    elif resolution_status == "partial":
        return {
            "action": "continue_troubleshooting",
            "next_agent": "technical_agent",
            "reasoning": "Partial resolution achieved, continue with technical support"
        }
    
    else:  # unclear
        return {
            "action": "clarify_status",
            "next_agent": "followup_agent",
            "reasoning": "Need clarification on resolution status"
        }

# Learning and Analytics Tools
def analyze_interaction_patterns(interaction_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze interaction patterns for learning and improvement.
    
    Args:
        interaction_data (Dict): Complete interaction data
    
    Returns:
        Dict containing analysis results and recommendations
    """
    logger.info("Analyzing interaction patterns for learning")
    
    analysis = {
        "interaction_id": interaction_data.get("request_id", "unknown"),
        "category": interaction_data.get("category", "unknown"),
        "priority": interaction_data.get("priority", "medium"),
        "agent_path": interaction_data.get("agent_history", []),
        "resolution_outcome": interaction_data.get("resolution_status", "unknown"),
        "customer_satisfaction": interaction_data.get("satisfaction_level", "unknown"),
        "total_agent_hops": len(interaction_data.get("agent_history", [])),
        "escalated": interaction_data.get("escalated", False),
        "knowledge_base_helpful": interaction_data.get("relevant_content_found", False),
        "technical_support_provided": interaction_data.get("technical_analysis_performed", False)
    }
    
    # Calculate effectiveness score
    effectiveness_score = 0.5  # Base score
    
    if analysis["resolution_outcome"] == "resolved":
        effectiveness_score += 0.3
    elif analysis["escalated"]:
        effectiveness_score += 0.1  # Escalation can be appropriate
    
    if analysis["customer_satisfaction"] == "high":
        effectiveness_score += 0.2
    elif analysis["customer_satisfaction"] == "low":
        effectiveness_score -= 0.2
    
    if analysis["knowledge_base_helpful"]:
        effectiveness_score += 0.1
    
    # Ensure score is within valid range
    effectiveness_score = max(0.0, min(1.0, effectiveness_score))
    analysis["effectiveness_score"] = effectiveness_score
    
    return analysis

def generate_improvement_suggestions(analysis_data: Dict[str, Any]) -> List[str]:
    """
    Generate improvement suggestions based on interaction analysis.
    
    Args:
        analysis_data (Dict): Interaction analysis results
    
    Returns:
        List of improvement suggestions
    """
    logger.info("Generating improvement suggestions")
    
    suggestions = []
    
    # Knowledge base improvements
    if not analysis_data.get("knowledge_base_helpful", True) and analysis_data.get("category"):
        suggestions.append(f"Consider adding more content to knowledge base for '{analysis_data['category']}' category")
    
    # Technical support improvements
    if analysis_data.get("technical_support_provided") and analysis_data.get("resolution_outcome") == "unresolved":
        suggestions.append("Review technical troubleshooting procedures for this issue type")
    
    # Escalation pattern analysis
    if analysis_data.get("escalated") and analysis_data.get("effectiveness_score", 0) < 0.5:
        suggestions.append("Review escalation criteria - this case may have been escalated too early or too late")
    
    # Customer satisfaction improvements
    if analysis_data.get("customer_satisfaction") == "low":
        suggestions.append("Analyze communication style and response quality for this interaction")
    
    # Agent routing optimization
    agent_hops = analysis_data.get("total_agent_hops", 0)
    if agent_hops > 4 and analysis_data.get("resolution_outcome") != "resolved":
        suggestions.append("Consider streamlining agent handoff process to reduce complexity")
    
    return suggestions

# Simplified State Management Tools (without ToolContext)
def save_to_session_state(key: str, value: str) -> Dict[str, str]:
    """
    Save data to session state for sharing between agents.
    Note: This is a simplified version that returns status only.
    The actual state management is handled by the ADK framework.
    
    Args:
        key (str): State key
        value (str): Value to save (as string)
    
    Returns:
        Dict with operation status
    """
    try:
        logger.info(f"Saving to session state: {key}")
        # The actual saving is handled by the ADK framework through agent context
        return {"status": "success", "message": f"Saved {key} to session state"}
    except Exception as e:
        logger.error(f"Error saving to session state: {e}")
        return {"status": "error", "message": str(e)}

def get_from_session_state(key: str) -> Dict[str, Any]:
    """
    Retrieve data from session state.
    Note: This is a simplified version that returns status only.
    The actual state retrieval is handled by the ADK framework.
    
    Args:
        key (str): State key to retrieve
    
    Returns:
        Dict with retrieved value or error
    """
    try:
        logger.info(f"Retrieving from session state: {key}")
        # The actual retrieval is handled by the ADK framework through agent context
        return {"status": "success", "key": key, "message": "State retrieval handled by ADK framework"}
    except Exception as e:
        logger.error(f"Error retrieving from session state: {e}")
        return {"status": "error", "message": str(e)}