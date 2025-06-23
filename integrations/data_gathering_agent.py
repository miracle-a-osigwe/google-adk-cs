"""Data gathering agent for collecting missing customer information."""

import logging
from typing import Dict, Any, List, Optional
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from config import Config
from entities.customer import Customer
from models.business_config import BusinessConfig, IndustryTemplate

logger = logging.getLogger(__name__)
configs = Config()


class DataGatheringAgent:
    """Agent responsible for gathering missing customer information."""
    
    def __init__(self, business_config: BusinessConfig):
        self.business_config = business_config
        self.industry_template = self._get_industry_template()
        self.required_fields = self._get_required_fields()
        self.optional_fields = self._get_optional_fields()
        
        # Create LLM agent for intelligent data gathering
        self.llm_agent = LlmAgent(
            model=configs.coordinator_agent.model,
            instruction=self._get_agent_instruction(),
            name="data_gathering_agent",
            description="Gathers missing customer information intelligently",
            tools=[
                FunctionTool(func=self.analyze_missing_data),
                FunctionTool(func=self.generate_questions),
                FunctionTool(func=self.validate_collected_data)
            ],
            output_key="data_gathering_response"
        )
    
    def _get_industry_template(self) -> IndustryTemplate:
        """Get industry-specific template for data requirements."""
        industry_templates = {
            "ecommerce": IndustryTemplate(
                name="E-commerce",
                required_fields=["name", "email"],
                optional_fields=["phone", "shipping_address", "billing_address", "preferred_payment_method"],
                custom_fields=["customer_since", "total_orders", "loyalty_tier", "preferred_categories"],
                compliance_requirements=["gdpr_consent", "marketing_consent"],
                data_retention_days=2555  # 7 years
            ),
            "saas": IndustryTemplate(
                name="SaaS",
                required_fields=["name", "email", "company"],
                optional_fields=["phone", "job_title", "company_size"],
                custom_fields=["subscription_plan", "usage_tier", "account_type", "integration_needs"],
                compliance_requirements=["data_processing_consent"],
                data_retention_days=2190  # 6 years
            ),
            "healthcare": IndustryTemplate(
                name="Healthcare",
                required_fields=["name", "email", "phone", "date_of_birth"],
                optional_fields=["address", "emergency_contact", "insurance_provider"],
                custom_fields=["patient_id", "medical_record_number", "preferred_provider"],
                compliance_requirements=["hipaa_consent", "medical_data_consent"],
                data_retention_days=2555  # 7 years
            ),
            "financial": IndustryTemplate(
                name="Financial Services",
                required_fields=["name", "email", "phone", "address"],
                optional_fields=["ssn_last_four", "account_type", "preferred_contact_method"],
                custom_fields=["account_number", "risk_profile", "investment_goals"],
                compliance_requirements=["kyc_verification", "aml_consent", "privacy_notice"],
                data_retention_days=2555  # 7 years
            ),
            "retail": IndustryTemplate(
                name="Retail",
                required_fields=["name", "email"],
                optional_fields=["phone", "address", "preferred_store_location"],
                custom_fields=["loyalty_number", "preferred_brands", "size_preferences"],
                compliance_requirements=["marketing_consent"],
                data_retention_days=1095  # 3 years
            )
        }
        
        return industry_templates.get(
            self.business_config.industry, 
            industry_templates["saas"]  # Default template
        )
    
    def _get_required_fields(self) -> List[str]:
        """Get required fields for the business."""
        base_required = ["name", "email"]
        industry_required = self.industry_template.required_fields
        
        # Combine and deduplicate
        all_required = list(set(base_required + industry_required))
        return all_required
    
    def _get_optional_fields(self) -> List[str]:
        """Get optional fields for the business."""
        return self.industry_template.optional_fields
    
    def _get_agent_instruction(self) -> str:
        """Get instruction for the data gathering agent."""
        return f"""
        You are a Data Gathering Agent for {self.business_config.business_name}, a {self.industry_template.name} business.
        
        Your role is to intelligently gather missing customer information while providing excellent customer service.
        
        **Industry Context: {self.industry_template.name}**
        
        **Required Information:**
        {', '.join(self.required_fields)}
        
        **Optional Information:**
        {', '.join(self.optional_fields)}
        
        **Custom Fields:**
        {', '.join(self.industry_template.custom_fields)}
        
        **Guidelines:**
        1. Always be polite and explain why you need the information
        2. Gather required information first, then optional information
        3. Use natural conversation flow - don't ask for everything at once
        4. Respect customer privacy and explain data usage
        5. Offer alternatives if customers are hesitant to provide information
        6. Validate information as you collect it
        
        **Compliance Requirements:**
        {', '.join(self.industry_template.compliance_requirements)}
        
        Always prioritize customer experience while gathering necessary information.
        """
    
    async def analyze_customer_data_completeness(self, customer: Customer) -> Dict[str, Any]:
        """Analyze what data is missing for a customer."""
        missing_required = []
        missing_optional = []
        
        # Check required fields
        for field in self.required_fields:
            if not self._has_field_value(customer, field):
                missing_required.append(field)
        
        # Check optional fields
        for field in self.optional_fields:
            if not self._has_field_value(customer, field):
                missing_optional.append(field)
        
        # Check custom fields
        missing_custom = []
        for field in self.industry_template.custom_fields:
            if field not in customer.custom_fields or not customer.custom_fields[field]:
                missing_custom.append(field)
        
        completeness_score = self._calculate_completeness_score(
            customer, missing_required, missing_optional, missing_custom
        )
        
        return {
            "completeness_score": completeness_score,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "missing_custom": missing_custom,
            "is_complete": len(missing_required) == 0,
            "priority_fields": missing_required[:3],  # Top 3 priority fields
            "data_quality": self._assess_data_quality(customer)
        }
    
    def _has_field_value(self, customer: Customer, field: str) -> bool:
        """Check if customer has a value for the specified field."""
        field_mapping = {
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "company": customer.custom_fields.get("company"),
            "address": customer.custom_fields.get("address"),
            "date_of_birth": customer.custom_fields.get("date_of_birth")
        }
        
        value = field_mapping.get(field)
        return value is not None and str(value).strip() != ""
    
    def _calculate_completeness_score(
        self, 
        customer: Customer, 
        missing_required: List[str], 
        missing_optional: List[str], 
        missing_custom: List[str]
    ) -> float:
        """Calculate data completeness score (0-1)."""
        total_fields = len(self.required_fields) + len(self.optional_fields) + len(self.industry_template.custom_fields)
        missing_fields = len(missing_required) + len(missing_optional) + len(missing_custom)
        
        if total_fields == 0:
            return 1.0
        
        # Weight required fields more heavily
        required_weight = 0.6
        optional_weight = 0.3
        custom_weight = 0.1
        
        required_score = 1.0 - (len(missing_required) / len(self.required_fields)) if self.required_fields else 1.0
        optional_score = 1.0 - (len(missing_optional) / len(self.optional_fields)) if self.optional_fields else 1.0
        custom_score = 1.0 - (len(missing_custom) / len(self.industry_template.custom_fields)) if self.industry_template.custom_fields else 1.0
        
        weighted_score = (
            required_score * required_weight +
            optional_score * optional_weight +
            custom_score * custom_weight
        )
        
        return round(weighted_score, 2)
    
    def _assess_data_quality(self, customer: Customer) -> Dict[str, Any]:
        """Assess the quality of existing customer data."""
        quality_issues = []
        
        # Check email format
        if customer.email and "@" not in customer.email:
            quality_issues.append("Invalid email format")
        
        # Check phone format (basic check)
        if customer.phone and len(customer.phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")) < 10:
            quality_issues.append("Phone number appears incomplete")
        
        # Check name completeness
        if customer.name and len(customer.name.split()) < 2:
            quality_issues.append("Name appears incomplete (missing first or last name)")
        
        quality_score = 1.0 - (len(quality_issues) * 0.2)  # Deduct 0.2 for each issue
        quality_score = max(0.0, quality_score)
        
        return {
            "quality_score": quality_score,
            "issues": quality_issues,
            "suggestions": self._generate_quality_suggestions(quality_issues)
        }
    
    def _generate_quality_suggestions(self, issues: List[str]) -> List[str]:
        """Generate suggestions for improving data quality."""
        suggestions = []
        
        for issue in issues:
            if "email" in issue.lower():
                suggestions.append("Verify email address format with customer")
            elif "phone" in issue.lower():
                suggestions.append("Request complete phone number including area code")
            elif "name" in issue.lower():
                suggestions.append("Ask for both first and last name")
        
        return suggestions
    
    async def generate_data_gathering_questions(
        self, 
        customer: Customer, 
        context: str = "",
        max_questions: int = 3
    ) -> Dict[str, Any]:
        """Generate intelligent questions to gather missing data."""
        analysis = await self.analyze_customer_data_completeness(customer)
        
        if analysis["is_complete"]:
            return {
                "questions": [],
                "message": "Customer profile is complete!",
                "next_action": "proceed_with_service"
            }
        
        # Prioritize questions
        priority_fields = analysis["priority_fields"]
        questions = []
        
        for field in priority_fields[:max_questions]:
            question = self._generate_field_question(field, customer, context)
            if question:
                questions.append(question)
        
        return {
            "questions": questions,
            "missing_data_summary": analysis,
            "next_action": "collect_information",
            "completion_after": analysis["completeness_score"] + (len(questions) * 0.1)
        }
    
    def _generate_field_question(self, field: str, customer: Customer, context: str) -> Optional[Dict[str, Any]]:
        """Generate a natural question for a specific field."""
        questions_map = {
            "name": {
                "question": "To better assist you, could you please provide your full name?",
                "type": "text",
                "required": True,
                "validation": "name"
            },
            "email": {
                "question": "What's the best email address to reach you at?",
                "type": "email",
                "required": True,
                "validation": "email"
            },
            "phone": {
                "question": "Could you provide a phone number where we can reach you if needed?",
                "type": "phone",
                "required": False,
                "validation": "phone"
            },
            "company": {
                "question": "What company are you with?",
                "type": "text",
                "required": False,
                "validation": "text"
            },
            "address": {
                "question": "What's your mailing address?",
                "type": "address",
                "required": False,
                "validation": "address"
            }
        }
        
        base_question = questions_map.get(field)
        if not base_question:
            return None
        
        # Customize question based on context
        if context and "urgent" in context.lower():
            base_question["question"] = f"For urgent matters, {base_question['question'].lower()}"
        
        return {
            "field": field,
            **base_question
        }
    
    async def validate_and_store_collected_data(
        self, 
        customer: Customer, 
        collected_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and store newly collected customer data."""
        validation_results = {}
        updated_fields = []
        
        for field, value in collected_data.items():
            validation_result = self._validate_field_value(field, value)
            validation_results[field] = validation_result
            
            if validation_result["valid"]:
                # Update customer object
                if field == "name":
                    customer.name = value
                    # Try to split into first/last name
                    name_parts = value.split()
                    if len(name_parts) >= 2:
                        customer.first_name = name_parts[0]
                        customer.last_name = " ".join(name_parts[1:])
                elif field == "email":
                    customer.email = value
                elif field == "phone":
                    customer.phone = value
                else:
                    # Store in custom fields
                    customer.custom_fields[field] = value
                
                updated_fields.append(field)
        
        # Update completeness score
        new_analysis = await self.analyze_customer_data_completeness(customer)
        
        return {
            "validation_results": validation_results,
            "updated_fields": updated_fields,
            "new_completeness_score": new_analysis["completeness_score"],
            "is_now_complete": new_analysis["is_complete"],
            "customer": customer
        }
    
    def _validate_field_value(self, field: str, value: str) -> Dict[str, Any]:
        """Validate a field value."""
        if not value or not value.strip():
            return {"valid": False, "error": "Value is required"}
        
        value = value.strip()
        
        if field == "email":
            if "@" not in value or "." not in value.split("@")[-1]:
                return {"valid": False, "error": "Invalid email format"}
        
        elif field == "phone":
            # Basic phone validation
            digits = "".join(filter(str.isdigit, value))
            if len(digits) < 10:
                return {"valid": False, "error": "Phone number must have at least 10 digits"}
        
        elif field == "name":
            if len(value.split()) < 2:
                return {"valid": False, "error": "Please provide both first and last name"}
        
        return {"valid": True, "cleaned_value": value}
    
    def get_data_gathering_strategy(self, customer: Customer, urgency: str = "normal") -> Dict[str, Any]:
        """Get data gathering strategy based on customer and urgency."""
        analysis = self.analyze_customer_data_completeness(customer)
        
        if urgency == "high" or urgency == "critical":
            # For urgent cases, only gather essential information
            strategy = {
                "approach": "minimal",
                "max_questions": 1,
                "focus_fields": analysis["missing_required"][:1],
                "defer_optional": True
            }
        elif analysis["completeness_score"] < 0.3:
            # Very incomplete profile
            strategy = {
                "approach": "progressive",
                "max_questions": 2,
                "focus_fields": analysis["missing_required"][:2],
                "defer_optional": False
            }
        else:
            # Mostly complete profile
            strategy = {
                "approach": "opportunistic",
                "max_questions": 1,
                "focus_fields": analysis["missing_required"] + analysis["missing_optional"][:1],
                "defer_optional": False
            }
        
        return strategy
    
    # Tool functions for LLM agent
    def analyze_missing_data(self, customer_data: str) -> str:
        """Tool function to analyze missing customer data."""
        try:
            # This would be called by the LLM agent
            # Parse customer data and return analysis
            return "Data analysis completed"
        except Exception as e:
            return f"Error analyzing data: {str(e)}"
    
    def generate_questions(self, missing_fields: str, context: str = "") -> str:
        """Tool function to generate data gathering questions."""
        try:
            # This would be called by the LLM agent
            return "Questions generated"
        except Exception as e:
            return f"Error generating questions: {str(e)}"
    
    def validate_collected_data(self, field_name: str, field_value: str) -> str:
        """Tool function to validate collected data."""
        try:
            result = self._validate_field_value(field_name, field_value)
            return f"Validation result: {result}"
        except Exception as e:
            return f"Error validating data: {str(e)}"