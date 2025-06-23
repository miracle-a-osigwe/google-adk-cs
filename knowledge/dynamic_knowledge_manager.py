"""Dynamic knowledge management system that adapts to customer data and business context."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from models.business_config import BusinessConfig
from entities.customer import Customer
from integrations.customer_data_manager import CustomerDataManager

logger = logging.getLogger(__name__)


class DynamicKnowledgeManager:
    """Manages knowledge base content that adapts to customer context and business data."""
    
    def __init__(self, business_config: BusinessConfig, data_manager: CustomerDataManager):
        self.business_config = business_config
        self.data_manager = data_manager
        self.static_knowledge = self._load_static_knowledge()
        self.dynamic_templates = self._load_dynamic_templates()
        self.customer_specific_cache = {}
    
    def _load_static_knowledge(self) -> Dict[str, Any]:
        """Load static knowledge base content."""
        # This would load from files or database
        return {
            "general_faqs": [
                {
                    "id": "general_001",
                    "question": "How do I contact support?",
                    "answer_template": "You can contact our support team through {channels}. Our business hours are {business_hours}.",
                    "category": "general",
                    "dynamic_fields": ["channels", "business_hours"]
                }
            ],
            "industry_specific": {},
            "provider_specific": {}
        }
    
    def _load_dynamic_templates(self) -> Dict[str, Any]:
        """Load templates for dynamic content generation."""
        return {
            "customer_greeting": {
                "new_customer": "Welcome to {business_name}! I'm here to help you get started.",
                "returning_customer": "Welcome back, {customer_name}! How can I assist you today?",
                "vip_customer": "Hello {customer_name}, thank you for being a valued {tier} customer. How may I help you?"
            },
            "escalation_messages": {
                "ecommerce": "I'm connecting you with our e-commerce specialist who can help with orders, shipping, and product questions.",
                "saas": "I'm routing you to our technical team who specializes in {product_name} integrations and account management.",
                "healthcare": "I'm connecting you with our patient care team who can assist with appointments and medical inquiries.",
                "financial": "I'm transferring you to our financial advisor who can help with your account and investment questions."
            },
            "data_collection": {
                "ecommerce": "To better assist you with your order, could you provide your order number or email address?",
                "saas": "To help troubleshoot your account, what's the company email domain you're using with our service?",
                "healthcare": "For your privacy and security, could you verify your date of birth and phone number?",
                "financial": "For security purposes, please provide the last four digits of your account number."
            }
        }
    
    async def get_contextual_knowledge(
        self, 
        query: str, 
        customer: Optional[Customer] = None,
        interaction_context: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Get knowledge base results adapted to customer and business context."""
        
        # Start with static knowledge search
        base_results = self._search_static_knowledge(query)
        
        # Enhance with dynamic content
        enhanced_results = []
        for result in base_results:
            enhanced_result = await self._enhance_with_dynamic_content(
                result, customer, interaction_context
            )
            enhanced_results.append(enhanced_result)
        
        # Add customer-specific knowledge
        if customer:
            customer_specific = await self._get_customer_specific_knowledge(
                customer, query, interaction_context
            )
            enhanced_results.extend(customer_specific)
        
        # Add business-specific knowledge
        business_specific = await self._get_business_specific_knowledge(
            query, interaction_context
        )
        enhanced_results.extend(business_specific)
        
        return enhanced_results
    
    def _search_static_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Search static knowledge base."""
        query_lower = query.lower()
        results = []
        
        # Search general FAQs
        for faq in self.static_knowledge["general_faqs"]:
            if any(keyword in query_lower for keyword in faq.get("keywords", [])):
                results.append({
                    "type": "faq",
                    "content": faq,
                    "relevance_score": 0.8,
                    "source": "static"
                })
        
        return results
    
    async def _enhance_with_dynamic_content(
        self, 
        result: Dict[str, Any], 
        customer: Optional[Customer],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance static content with dynamic, contextual information."""
        
        content = result["content"]
        
        if "answer_template" in content and "dynamic_fields" in content:
            # Replace dynamic fields with actual values
            template = content["answer_template"]
            dynamic_values = {}
            
            for field in content["dynamic_fields"]:
                value = await self._get_dynamic_field_value(field, customer, context)
                dynamic_values[field] = value
            
            # Replace template variables
            enhanced_answer = template.format(**dynamic_values)
            
            # Update the result
            enhanced_content = content.copy()
            enhanced_content["answer"] = enhanced_answer
            enhanced_content["dynamic_values"] = dynamic_values
            
            result["content"] = enhanced_content
        
        return result
    
    async def _get_dynamic_field_value(
        self, 
        field: str, 
        customer: Optional[Customer],
        context: Dict[str, Any]
    ) -> str:
        """Get value for a dynamic field based on business config and customer data."""
        
        field_handlers = {
            "business_name": lambda: self.business_config.business_name,
            "business_hours": lambda: self._format_business_hours(),
            "channels": lambda: self._get_support_channels(),
            "customer_name": lambda: customer.get_display_name() if customer else "valued customer",
            "customer_tier": lambda: customer.tier if customer else "standard",
            "industry": lambda: self.business_config.industry,
            "company_name": lambda: customer.company if customer and customer.company else self.business_config.business_name
        }
        
        handler = field_handlers.get(field)
        if handler:
            return handler()
        
        # Check customer custom fields
        if customer and field in customer.custom_fields:
            return str(customer.custom_fields[field])
        
        # Check business config
        if hasattr(self.business_config, field):
            return str(getattr(self.business_config, field))
        
        return f"[{field}]"  # Placeholder if not found
    
    def _format_business_hours(self) -> str:
        """Format business hours for display."""
        hours = self.business_config.business_hours
        if not hours:
            return "24/7"
        
        formatted = []
        for day, time in hours.items():
            if time.lower() != "closed":
                formatted.append(f"{day.title()}: {time}")
        
        return ", ".join(formatted) if formatted else "Please check our website for current hours"
    
    def _get_support_channels(self) -> str:
        """Get available support channels."""
        channels = ["email", "chat"]
        
        # Add phone if business hours are defined
        if self.business_config.business_hours:
            channels.append("phone")
        
        # Add industry-specific channels
        if self.business_config.industry == "healthcare":
            channels.append("patient portal")
        elif self.business_config.industry == "financial":
            channels.append("secure messaging")
        
        return ", ".join(channels)
    
    async def _get_customer_specific_knowledge(
        self, 
        customer: Customer, 
        query: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get knowledge specific to the customer's history and profile."""
        
        customer_knowledge = []
        
        # Get customer history from providers
        try:
            history = await self.data_manager.get_customer_history(customer.customer_id)
            
            # Generate knowledge based on history
            if history:
                recent_issues = [h for h in history if h.get("status") == "resolved"]
                if recent_issues:
                    customer_knowledge.append({
                        "type": "customer_history",
                        "content": {
                            "title": "Your Recent Interactions",
                            "answer": f"I see you've contacted us {len(recent_issues)} times recently. Your last issue was resolved successfully. How can I help you today?",
                            "history_count": len(recent_issues)
                        },
                        "relevance_score": 0.9,
                        "source": "customer_history"
                    })
        except Exception as e:
            logger.warning(f"Could not retrieve customer history: {e}")
        
        # Add customer tier-specific knowledge
        if customer.tier in ["premium", "enterprise"]:
            customer_knowledge.append({
                "type": "tier_specific",
                "content": {
                    "title": f"{customer.tier.title()} Support",
                    "answer": f"As a {customer.tier} customer, you have access to priority support and dedicated assistance. Let me help you right away.",
                    "tier": customer.tier
                },
                "relevance_score": 0.8,
                "source": "customer_tier"
            })
        
        return customer_knowledge
    
    async def _get_business_specific_knowledge(
        self, 
        query: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get knowledge specific to the business configuration."""
        
        business_knowledge = []
        
        # Industry-specific responses
        industry_templates = self.dynamic_templates.get("escalation_messages", {})
        if self.business_config.industry in industry_templates:
            if any(word in query.lower() for word in ["escalate", "specialist", "expert", "manager"]):
                business_knowledge.append({
                    "type": "industry_escalation",
                    "content": {
                        "title": "Specialist Support",
                        "answer": industry_templates[self.business_config.industry],
                        "industry": self.business_config.industry
                    },
                    "relevance_score": 0.7,
                    "source": "business_config"
                })
        
        # SLA-specific information
        if self.business_config.sla_targets:
            if any(word in query.lower() for word in ["how long", "when", "time", "response"]):
                first_response = self.business_config.sla_targets.get("first_response", "within 24 hours")
                business_knowledge.append({
                    "type": "sla_info",
                    "content": {
                        "title": "Response Time",
                        "answer": f"We typically respond to inquiries {first_response}. For urgent matters, please mention 'urgent' in your message.",
                        "sla": first_response
                    },
                    "relevance_score": 0.6,
                    "source": "sla_config"
                })
        
        return business_knowledge
    
    async def generate_dynamic_greeting(self, customer: Optional[Customer]) -> str:
        """Generate a dynamic greeting based on customer context."""
        
        if not customer:
            return f"Hello! Welcome to {self.business_config.business_name}. How can I help you today?"
        
        templates = self.dynamic_templates["customer_greeting"]
        
        # Determine customer type
        if customer.tier in ["premium", "enterprise"]:
            template = templates["vip_customer"]
        elif customer.interaction_count > 0:
            template = templates["returning_customer"]
        else:
            template = templates["new_customer"]
        
        # Replace variables
        return template.format(
            business_name=self.business_config.business_name,
            customer_name=customer.get_display_name(),
            tier=customer.tier
        )
    
    async def generate_data_collection_prompt(
        self, 
        customer: Optional[Customer],
        missing_fields: List[str]
    ) -> str:
        """Generate appropriate data collection prompt based on industry and missing fields."""
        
        industry = self.business_config.industry
        base_template = self.dynamic_templates["data_collection"].get(
            industry, 
            "To better assist you, could you provide some additional information?"
        )
        
        # Customize based on missing fields
        if "email" in missing_fields:
            return "To send you updates and confirmations, what's the best email address to reach you?"
        elif "phone" in missing_fields and industry in ["healthcare", "financial"]:
            return "For security and urgent communications, could you provide a phone number?"
        elif "company" in missing_fields and industry == "saas":
            return "What company are you with? This helps us provide relevant support."
        
        return base_template
    
    async def update_knowledge_from_interaction(
        self, 
        interaction_data: Dict[str, Any],
        resolution_successful: bool
    ):
        """Update knowledge base based on successful interactions."""
        
        if not resolution_successful:
            return
        
        # Extract patterns for future knowledge updates
        query = interaction_data.get("original_query", "")
        resolution = interaction_data.get("resolution_text", "")
        category = interaction_data.get("category", "")
        
        # Store successful resolution patterns
        pattern_data = {
            "query_pattern": query,
            "resolution_pattern": resolution,
            "category": category,
            "customer_context": interaction_data.get("customer_context", {}),
            "timestamp": datetime.now().isoformat(),
            "success_score": 1.0
        }
        
        # This would be stored in a learning database
        logger.info(f"Storing successful resolution pattern: {pattern_data}")
    
    def get_knowledge_completeness_score(self) -> Dict[str, Any]:
        """Assess knowledge base completeness for the current business configuration."""
        
        industry = self.business_config.industry
        
        # Industry-specific knowledge requirements
        required_categories = {
            "ecommerce": ["orders", "shipping", "returns", "products", "payments"],
            "saas": ["account_setup", "integrations", "billing", "technical_support", "features"],
            "healthcare": ["appointments", "patient_records", "insurance", "prescriptions", "privacy"],
            "financial": ["account_management", "transactions", "security", "investments", "compliance"],
            "retail": ["products", "store_locations", "loyalty_program", "returns", "promotions"]
        }
        
        required_for_industry = required_categories.get(industry, ["general", "support", "billing"])
        
        # Check coverage
        covered_categories = set()
        for faq in self.static_knowledge.get("general_faqs", []):
            covered_categories.add(faq.get("category", "general"))
        
        coverage_score = len(covered_categories.intersection(required_for_industry)) / len(required_for_industry)
        
        return {
            "completeness_score": coverage_score,
            "required_categories": required_for_industry,
            "covered_categories": list(covered_categories),
            "missing_categories": list(set(required_for_industry) - covered_categories),
            "recommendations": self._generate_knowledge_recommendations(
                set(required_for_industry) - covered_categories
            )
        }
    
    def _generate_knowledge_recommendations(self, missing_categories: set) -> List[str]:
        """Generate recommendations for improving knowledge base."""
        
        recommendations = []
        
        category_suggestions = {
            "orders": "Add FAQs about order status, modification, and cancellation",
            "shipping": "Include shipping options, tracking, and delivery information",
            "returns": "Create return policy and process documentation",
            "account_setup": "Add account creation and configuration guides",
            "integrations": "Document API and third-party integration procedures",
            "appointments": "Include appointment scheduling and modification processes",
            "security": "Add security procedures and account protection information"
        }
        
        for category in missing_categories:
            suggestion = category_suggestions.get(category, f"Add content for {category} category")
            recommendations.append(suggestion)
        
        return recommendations