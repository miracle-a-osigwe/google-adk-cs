"""Callback functions for the ADK customer service ecosystem."""

import logging
import asyncio
import time
from typing import Any, Dict
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

logger = logging.getLogger(__name__)

async def rate_limit_callback(context: InvocationContext) -> None:
    """
    Rate limiting callback to prevent excessive API calls.
    
    Args:
        context: The invocation context
    """
    # Simple rate limiting - add delay between requests
    await asyncio.sleep(0.1)
    logger.debug("Rate limit callback executed")

async def before_agent(context: InvocationContext) -> None:
    """
    Callback executed before agent processing.
    
    Args:
        context: The invocation context
    """
    agent_name = getattr(context, 'agent_name', 'unknown')
    logger.info(f"Starting agent: {agent_name}")
    
    # Save agent start time for performance tracking
    if not hasattr(context.session.state, 'agent_timings'):
        context.session.state['agent_timings'] = {}
    
    context.session.state['agent_timings'][agent_name] = {
        'start_time': time.time()
    }
    
    # Track agent execution order
    if 'agent_history' not in context.session.state:
        context.session.state['agent_history'] = []
    
    context.session.state['agent_history'].append(agent_name)

async def before_tool(context: InvocationContext, tool_name: str, tool_args: Dict[str, Any]) -> None:
    """
    Callback executed before tool execution.
    
    Args:
        context: The invocation context
        tool_name: Name of the tool being executed
        tool_args: Arguments passed to the tool
    """
    logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
    
    # Track tool usage for analytics
    if 'tool_usage' not in context.session.state:
        context.session.state['tool_usage'] = []
    
    context.session.state['tool_usage'].append({
        'tool_name': tool_name,
        'timestamp': time.time(),
        'args': tool_args
    })

async def after_tool(context: InvocationContext, tool_name: str, tool_result: Any) -> None:
    """
    Callback executed after tool execution.
    
    Args:
        context: The invocation context
        tool_name: Name of the tool that was executed
        tool_result: Result returned by the tool
    """
    logger.info(f"Tool {tool_name} completed with result type: {type(tool_result)}")
    
    # Update tool usage tracking with results
    if 'tool_usage' in context.session.state:
        # Find the most recent tool execution and update it
        for tool_record in reversed(context.session.state['tool_usage']):
            if tool_record['tool_name'] == tool_name and 'result' not in tool_record:
                tool_record['result'] = str(tool_result)[:200]  # Truncate for storage
                tool_record['success'] = True
                break

async def after_agent(context: InvocationContext) -> None:
    """
    Callback executed after agent processing.
    
    Args:
        context: The invocation context
    """
    agent_name = getattr(context, 'agent_name', 'unknown')
    logger.info(f"Completed agent: {agent_name}")
    
    # Calculate agent execution time
    if hasattr(context.session.state, 'agent_timings') and agent_name in context.session.state['agent_timings']:
        start_time = context.session.state['agent_timings'][agent_name]['start_time']
        execution_time = time.time() - start_time
        context.session.state['agent_timings'][agent_name]['execution_time'] = execution_time
        logger.info(f"Agent {agent_name} execution time: {execution_time:.2f} seconds")

async def on_error(context: InvocationContext, error: Exception) -> None:
    """
    Callback executed when an error occurs.
    
    Args:
        context: The invocation context
        error: The exception that occurred
    """
    logger.error(f"Error in customer service system: {str(error)}")
    
    # Track errors for analysis
    if 'errors' not in context.session.state:
        context.session.state['errors'] = []
    
    context.session.state['errors'].append({
        'error_type': type(error).__name__,
        'error_message': str(error),
        'timestamp': time.time(),
        'agent_context': getattr(context, 'agent_name', 'unknown')
    })

async def on_escalation(context: InvocationContext, escalation_reason: str) -> None:
    """
    Callback executed when an issue is escalated.
    
    Args:
        context: The invocation context
        escalation_reason: Reason for escalation
    """
    logger.info(f"Issue escalated: {escalation_reason}")
    
    # Track escalations for metrics
    if 'escalations' not in context.session.state:
        context.session.state['escalations'] = []
    
    context.session.state['escalations'].append({
        'reason': escalation_reason,
        'timestamp': time.time(),
        'agent_path': context.session.state.get('agent_history', [])
    })

async def on_resolution(context: InvocationContext, resolution_details: Dict[str, Any]) -> None:
    """
    Callback executed when an issue is resolved.
    
    Args:
        context: The invocation context
        resolution_details: Details about the resolution
    """
    logger.info(f"Issue resolved: {resolution_details}")
    
    # Track successful resolutions
    if 'resolutions' not in context.session.state:
        context.session.state['resolutions'] = []
    
    context.session.state['resolutions'].append({
        'details': resolution_details,
        'timestamp': time.time(),
        'agent_path': context.session.state.get('agent_history', []),
        'total_execution_time': sum(
            timing.get('execution_time', 0) 
            for timing in context.session.state.get('agent_timings', {}).values()
        )
    })