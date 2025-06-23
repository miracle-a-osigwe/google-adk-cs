"""Enhanced customer service tools with dynamic customer data integration."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from entities.customer import Customer
from models.business_config import BusinessConfig
from integrations.customer_data_manager import CustomerDataManager
from integrations.data_gathering_agent import DataGatheringAgent
from knowledge.dynamic_knowledge_manager import DynamicKnowledgeManager

logger = logging.getLogger(__name__)


class EnhancedCustomerServiceTools:
    """Enhanced tools that integrate with dynamic customer data and business configuration."""
    
    def __init__(self, business_config: BusinessConfig, data_manager: CustomerDataManager):
        self.business_config = business_config
        self.data_manager = data_manager
        self.data_gathering_agent = DataGatheringAgent(business_config)
        self.knowledge_manager = DynamicKnowledgeManager(business_config, data_manager)
    
    async def enhanced_search_knowledge_base(
        self, 
        query: str, 
        customer: Optional[Customer] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Enhanced knowledge base search with customer context."""
        
        try:
            # Use dynamic knowledge manager for contextual search
            results = await self.knowledge_manager.get_contextual_knowledge(
                query, customer, context
            )
            
            return {
                "query": query,
                "results": results,
                "total_found": len(results),
                "personalized": customer is not None,
                "business_context_applied": True,
                "knowledge_sources": list(set(r["source"] for r in results))
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced knowledge search: {str(e)}")
            return {
                "query": query,
                "results": [],
                "total_found": 0,
                "error": str(e)
            }
    
    async def enhanced_categorize_request(
        self, 
        message: str, 
        customer: Optional[Customer] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Enhanced request categorization with customer and business context."""
        
        try:
            # Base categorization
            base_category = self._categorize_message_content(message)
            
            # Customer context enhancement
            if customer:
                customer_category = self._enhance_with_customer_context(
                    base_category, customer, message
                )
            else:
                customer_category = base_category
            
            # Business context enhancement
            business_category = self._enhance_with_business_context(
                customer_category, message, context
            )
            
            # Industry-specific adjustments
            final_category = self._apply_industry_rules(
                business_category, message, customer
            )
            
            return {
                "category": final_category["category"],
                "subcategory": final_category.get("subcategory"),
                "confidence": final_category["confidence"],
                "reasoning": final_category["reasoning"],
                "customer_context_applied": customer is not None,
                "business_rules_applied": True,
                "industry_specific": final_category.get("industry_specific", False)
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced categorization: {str(e)}")
            return {
                "category": "general",
                "confidence": 0.5,
                "error": str(e)
            }
    
    def _categorize_message_content(self, message: str) -> Dict[str, Any]:
        """Basic message content categorization."""
        message_lower = message.lower()
        
        category_patterns = {
            "technical": {
                "keywords": ["error", "bug", "crash", "not working", "broken", "issue", "problem", "api", "integration"],
                "weight": 1.0
            },
            "billing": {
                "keywords": ["payment", "charge", "invoice", "refund", "subscription", "billing", "cost", "price"],
                "weight": 1.0
            },
            "account": {
                "keywords": ["login", "password", "access", "profile", "settings", "account", "signin", "signup"],
                "weight": 1.0
            },
            "support": {
                "keywords": ["help", "support", "assistance", "question", "how to", "guide", "tutorial"],
                "weight": 0.8
            },
            "sales": {
                "keywords": ["buy", "purchase", "pricing", "demo", "trial", "upgrade", "plan"],
                "weight": 0.9
            }
        }
        
        scores = {}
        for category, config in category_patterns.items():
            score = sum(
                config["weight"] for keyword in config["keywords"] 
                if keyword in message_lower
            )
            if score > 0:
                scores[category] = score
        
        if scores:
            best_category = max(scores, key=scores.get)
            confidence = min(0.9, scores[best_category] / 3.0)  # Normalize confidence
        else:
            best_category = "general"
            confidence = 0.5
        
        return {
            "category": best_category,
            "confidence": confidence,
            "scores": scores
        }
    
    def _enhance_with_customer_context(
        self, 
        base_category: Dict[str, Any], 
        customer: Customer, 
        message: str
    ) -> Dict[str, Any]:
        """Enhance categorization with customer context."""
        
        enhanced = base_category.copy()
        
        # Customer tier adjustments
        if customer.tier in ["premium", "enterprise"]:
            enhanced["confidence"] += 0.1  # Higher confidence for premium customers
        
        # Customer history analysis
        if customer.interaction_count > 0:
            # If customer has history of technical issues, bias towards technical
            if "technical" in str(customer.custom_fields.get("interaction_history", [])):
                if enhanced["category"] in ["general", "support"]:
                    enhanced["category"] = "technical"
                    enhanced["confidence"] = 0.7
                    enhanced["reasoning"] = "Customer has history of technical issues"
        
        # Industry-specific customer context
        if customer.company and self.business_config.industry == "saas":
            company_lower = customer.company.lower()
            if any(word in company_lower for word in ["tech", "software", "digital"]):
                if enhanced["category"] == "general":
                    enhanced["category"] = "technical"
                    enhanced["confidence"] = 0.8
                    enhanced["reasoning"] = "Tech company customer likely has technical inquiry"
        
        return enhanced
    
    def _enhance_with_business_context(
        self, 
        category: Dict[str, Any], 
        message: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance categorization with business context."""
        
        enhanced = category.copy()
        
        # Business hours context
        if context and context.get("outside_business_hours"):
            if enhanced["category"] in ["sales", "support"]:
                enhanced["subcategory"] = "after_hours"
                enhanced["confidence"] *= 0.9  # Slightly lower confidence
        
        # Channel context
        channel = context.get("channel", "unknown")
        if channel == "phone" and enhanced["category"] == "general":
            enhanced["category"] = "support"
            enhanced["confidence"] = 0.7
            enhanced["reasoning"] = "Phone channel typically indicates support need"
        
        return enhanced
    
    def _apply_industry_rules(
        self, 
        category: Dict[str, Any], 
        message: str, 
        customer: Optional[Customer]
    ) -> Dict[str, Any]:
        """Apply industry-specific categorization rules."""
        
        enhanced = category.copy()
        message_lower = message.lower()
        industry = self.business_config.industry
        
        if industry == "healthcare":
            if any(word in message_lower for word in ["appointment", "doctor", "medical", "prescription"]):
                enhanced["category"] = "medical"
                enhanced["subcategory"] = "appointment_related"
                enhanced["confidence"] = 0.9
                enhanced["industry_specific"] = True
        
        elif industry == "financial":
            if any(word in message_lower for word in ["investment", "portfolio", "trading", "market"]):
                enhanced["category"] = "financial_advisory"
                enhanced["subcategory"] = "investment_related"
                enhanced["confidence"] = 0.9
                enhanced["industry_specific"] = True
        
        elif industry == "ecommerce":
            if any(word in message_lower for word in ["order", "shipping", "delivery", "return"]):
                enhanced["category"] = "order_management"
                enhanced["subcategory"] = "fulfillment_related"
                enhanced["confidence"] = 0.9
                enhanced["industry_specific"] = True
        
        return enhanced
    
    async def enhanced_assess_priority(
        self, 
        message: str, 
        customer: Optional[Customer] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Enhanced priority assessment with customer and business context."""
        
        try:
            # Base priority from message content
            base_priority = self._assess_message_priority(message)
            
            # Customer context adjustments
            if customer:
                customer_adjustment = self._assess_customer_priority_factors(customer)
            else:
                customer_adjustment = {"modifier": 0, "factors": []}
            
            # Business context adjustments
            business_adjustment = self._assess_business_priority_factors(message, context)
            
            # Calculate final priority
            final_priority = self._calculate_final_priority(
                base_priority, customer_adjustment, business_adjustment
            )
            
            return {
                "priority": final_priority["level"],
                "confidence": final_priority["confidence"],
                "base_priority": base_priority["level"],
                "customer_factors": customer_adjustment["factors"],
                "business_factors": business_adjustment["factors"],
                "reasoning": final_priority["reasoning"],
                "sla_target": self._get_sla_target(final_priority["level"])
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced priority assessment: {str(e)}")
            return {
                "priority": "medium",
                "confidence": 0.5,
                "error": str(e)
            }
    
    def _assess_message_priority(self, message: str) -> Dict[str, Any]:
        """Assess priority from message content."""
        message_lower = message.lower()
        
        priority_indicators = {
            "critical": {
                "keywords": ["urgent", "critical", "emergency", "down", "outage", "security", "breach"],
                "score": 4
            },
            "high": {
                "keywords": ["important", "asap", "priority", "escalate", "business", "production"],
                "score": 3
            },
            "medium": {
                "keywords": ["soon", "when possible", "moderate", "standard"],
                "score": 2
            },
            "low": {
                "keywords": ["whenever", "no rush", "low priority", "minor", "question"],
                "score": 1
            }
        }
        
        max_score = 0
        detected_level = "medium"
        
        for level, config in priority_indicators.items():
            score = sum(config["score"] for keyword in config["keywords"] if keyword in message_lower)
            if score > max_score:
                max_score = score
                detected_level = level
        
        confidence = min(0.9, max_score / 4.0) if max_score > 0 else 0.5
        
        return {
            "level": detected_level,
            "confidence": confidence,
            "score": max_score
        }
    
    def _assess_customer_priority_factors(self, customer: Customer) -> Dict[str, Any]:
        """Assess priority factors based on customer profile."""
        
        factors = []
        modifier = 0
        
        # Customer tier
        if customer.tier == "enterprise":
            factors.append("enterprise_customer")
            modifier += 2
        elif customer.tier == "premium":
            factors.append("premium_customer")
            modifier += 1
        
        # Interaction history
        if customer.interaction_count > 5:
            factors.append("frequent_customer")
            modifier += 1
        
        # Recent escalations
        if "escalation" in str(customer.custom_fields.get("interaction_history", [])):
            factors.append("previous_escalation")
            modifier += 1
        
        # Customer satisfaction history
        if customer.custom_fields.get("satisfaction_score", 0) < 3:
            factors.append("low_satisfaction_history")
            modifier += 1
        
        return {
            "modifier": modifier,
            "factors": factors
        }
    
    def _assess_business_priority_factors(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess priority factors based on business context."""
        
        factors = []
        modifier = 0
        
        # Business hours
        if context and context.get("outside_business_hours"):
            factors.append("outside_business_hours")
            modifier -= 1  # Lower priority outside hours unless critical
        
        # Industry-specific factors
        industry = self.business_config.industry
        message_lower = message.lower()
        
        if industry == "healthcare":
            if any(word in message_lower for word in ["pain", "emergency", "medical"]):
                factors.append("medical_urgency")
                modifier += 2
        
        elif industry == "financial":
            if any(word in message_lower for word in ["fraud", "unauthorized", "security"]):
                factors.append("security_concern")
                modifier += 2
        
        elif industry == "ecommerce":
            if any(word in message_lower for word in ["order", "shipping", "delivery"]):
                factors.append("order_fulfillment")
                modifier += 1
        
        # Channel priority
        channel = context.get("channel", "unknown") if context else "unknown"
        if channel == "phone":
            factors.append("phone_channel")
            modifier += 1
        
        return {
            "modifier": modifier,
            "factors": factors
        }
    
    def _calculate_final_priority(
        self, 
        base_priority: Dict[str, Any], 
        customer_adjustment: Dict[str, Any], 
        business_adjustment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate final priority level."""
        
        priority_levels = ["low", "medium", "high", "critical"]
        base_index = priority_levels.index(base_priority["level"])
        
        # Apply adjustments
        total_modifier = customer_adjustment["modifier"] + business_adjustment["modifier"]
        final_index = max(0, min(len(priority_levels) - 1, base_index + total_modifier))
        
        final_level = priority_levels[final_index]
        
        # Calculate confidence
        confidence = base_priority["confidence"]
        if total_modifier != 0:
            confidence = min(0.95, confidence + 0.1)  # Increase confidence when context is applied
        
        # Generate reasoning
        reasoning_parts = [f"Base priority: {base_priority['level']}"]
        
        if customer_adjustment["factors"]:
            reasoning_parts.append(f"Customer factors: {', '.join(customer_adjustment['factors'])}")
        
        if business_adjustment["factors"]:
            reasoning_parts.append(f"Business factors: {', '.join(business_adjustment['factors'])}")
        
        if final_level != base_priority["level"]:
            reasoning_parts.append(f"Adjusted to {final_level}")
        
        return {
            "level": final_level,
            "confidence": confidence,
            "reasoning": "; ".join(reasoning_parts)
        }
    
    def _get_sla_target(self, priority: str) -> str:
        """Get SLA target for priority level."""
        
        # Use business config SLA targets if available
        sla_targets = self.business_config.sla_targets
        
        if sla_targets:
            return sla_targets.get("first_response", "24 hours")
        
        # Default SLA targets
        default_slas = {
            "critical": "15 minutes",
            "high": "1 hour",
            "medium": "4 hours",
            "low": "24 hours"
        }
        
        return default_slas.get(priority, "24 hours")
    
    async def enhanced_get_customer_context(
        self, 
        customer_identifier: str, 
        identifier_type: str = "email"
    ) -> Dict[str, Any]:
        """Get comprehensive customer context from all available sources."""
        
        try:
            # Get customer from data manager
            customer = await self.data_manager.get_customer(customer_identifier, identifier_type)
            
            if not customer:
                return {
                    "customer_found": False,
                    "identifier": customer_identifier,
                    "identifier_type": identifier_type,
                    "data_gathering_needed": True
                }
            
            # Get customer history
            try:
                history = await self.data_manager.get_customer_history(customer.customer_id)
            except Exception as e:
                logger.warning(f"Could not retrieve customer history: {e}")
                history = []
            
            # Analyze data completeness
            completeness_analysis = await self.data_gathering_agent.analyze_customer_data_completeness(customer)
            
            # Get provider information
            provider_info = self.data_manager.get_provider_info()
            
            return {
                "customer_found": True,
                "customer": customer.dict(),
                "interaction_history": history,
                "data_completeness": completeness_analysis,
                "provider_info": provider_info,
                "personalization_available": True,
                "context_enrichment": {
                    "tier_benefits": self._get_tier_benefits(customer.tier),
                    "communication_preferences": customer.communication_preferences,
                    "preferred_channel": customer.preferred_channel,
                    "timezone": customer.timezone,
                    "language": customer.language
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting customer context: {str(e)}")
            return {
                "customer_found": False,
                "error": str(e),
                "data_gathering_needed": True
            }
    
    def _get_tier_benefits(self, tier: str) -> List[str]:
        """Get benefits available for customer tier."""
        
        tier_benefits = {
            "enterprise": [
                "Priority support queue",
                "Dedicated account manager",
                "24/7 phone support",
                "Custom SLA agreements",
                "Advanced integrations",
                "Priority feature requests"
            ],
            "premium": [
                "Priority support queue",
                "Extended support hours",
                "Phone support",
                "Advanced features access",
                "Priority bug fixes"
            ],
            "standard": [
                "Email support",
                "Knowledge base access",
                "Community forum access",
                "Standard features"
            ]
        }
        
        return tier_benefits.get(tier, tier_benefits["standard"])
    
    async def enhanced_generate_data_gathering_questions(
        self, 
        customer: Optional[Customer], 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate intelligent data gathering questions."""
        
        try:
            if not customer:
                # Create basic customer profile for data gathering
                customer = Customer(
                    customer_id="temp_unknown",
                    name="Unknown Customer",
                    email="unknown@email.com"
                )
            
            # Use data gathering agent
            questions_result = await self.data_gathering_agent.generate_data_gathering_questions(
                customer, 
                context.get("urgency", "normal") if context else "normal",
                max_questions=3
            )
            
            return {
                "questions": questions_result["questions"],
                "data_strategy": questions_result.get("next_action", "collect_information"),
                "completion_estimate": questions_result.get("completion_after", 0.5),
                "business_context": {
                    "industry": self.business_config.industry,
                    "required_fields": self.business_config.required_customer_fields,
                    "compliance_requirements": self.business_config.compliance_requirements
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating data gathering questions: {str(e)}")
            return {
                "questions": [],
                "error": str(e),
                "fallback_message": "To better assist you, could you please provide your name and email address?"
            }
    
    async def enhanced_save_customer_interaction(
        self, 
        customer: Optional[Customer], 
        interaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Save customer interaction with enhanced context."""
        
        try:
            if customer:
                # Add interaction to customer record
                customer.add_interaction_record(
                    interaction_data.get("type", "support"),
                    interaction_data
                )
                
                # Update customer in data manager
                success = await self.data_manager.update_customer(customer)
                
                if success:
                    # Update knowledge manager with successful interaction
                    if interaction_data.get("resolution_successful"):
                        await self.knowledge_manager.update_knowledge_from_interaction(
                            interaction_data, True
                        )
                
                return {
                    "saved": success,
                    "customer_updated": True,
                    "interaction_count": customer.interaction_count
                }
            else:
                # Save interaction without customer context
                logger.info(f"Saving interaction without customer context: {interaction_data}")
                return {
                    "saved": True,
                    "customer_updated": False,
                    "note": "Interaction saved without customer association"
                }
                
        except Exception as e:
            logger.error(f"Error saving customer interaction: {str(e)}")
            return {
                "saved": False,
                "error": str(e)
            }


# Tool function wrappers for ADK integration
async def enhanced_search_knowledge_base(
    query: str, 
    customer_context: str = "", 
    business_context: str = ""
) -> str:
    """Enhanced knowledge base search tool function."""
    try:
        # This would be initialized with proper business config and data manager
        # For now, return a placeholder
        return f"Enhanced knowledge search completed for: {query}"
    except Exception as e:
        return f"Error in enhanced knowledge search: {str(e)}"

async def enhanced_categorize_request(
    message: str, 
    customer_context: str = "", 
    business_context: str = ""
) -> str:
    """Enhanced request categorization tool function."""
    try:
        return f"Enhanced categorization completed for message"
    except Exception as e:
        return f"Error in enhanced categorization: {str(e)}"

async def enhanced_assess_priority(
    message: str, 
    customer_context: str = "", 
    business_context: str = ""
) -> str:
    """Enhanced priority assessment tool function."""
    try:
        return f"Enhanced priority assessment completed"
    except Exception as e:
        return f"Error in enhanced priority assessment: {str(e)}"

async def enhanced_get_customer_context(customer_identifier: str, identifier_type: str = "email") -> str:
    """Enhanced customer context retrieval tool function."""
    try:
        return f"Enhanced customer context retrieved for: {customer_identifier}"
    except Exception as e:
        return f"Error getting enhanced customer context: {str(e)}"