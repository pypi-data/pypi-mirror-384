"""
Context Utilities for SFN Blueprint Agents

This module provides utilities for agents to extract, analyze, and utilize
enriched context data from the problem orchestrator for intelligent decision making.
Uses AI intelligence to provide context-aware recommendations without hardcoding.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime

# Import existing sfn_blueprint utilities
from .llm_handler import SFNAIHandler
from .prompt_manager import SFNPromptManager
from .logging import setup_logger
from ..config.config_manager import SFNConfigManager
from ..config.model_config import SFN_SUPPORTED_LLM_PROVIDERS

logger = logging.getLogger(__name__)


@dataclass
class ContextInfo:
    """Structured context information for agents"""
    domain: str
    business_context: Dict[str, Any]
    workflow_goal: str
    data_sensitivity: str
    compliance_requirements: List[str]
    optimization_hints: List[str]
    risk_factors: List[str]
    data_files: List[str]
    constraints: Dict[str, Any]
    stakeholders: List[str]
    workflow_complexity: str
    risk_level: str
    current_step: Dict[str, Any]
    execution_progress: Dict[str, Any]


@dataclass
class ContextRecommendations:
    """Context-aware recommendations for agents"""
    data_processing: List[str]
    quality_checks: List[str]
    optimization_strategies: List[str]
    risk_mitigation: List[str]
    compliance_measures: List[str]
    performance_tuning: List[str]


class ContextAnalyzer:
    """Analyzes enriched context and provides intelligent recommendations"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ContextAnalyzer")
    
    def extract_context_info(self, task_data: Dict[str, Any]) -> Optional[ContextInfo]:
        """
        Extract structured context information from enriched task data.
        
        Args:
            task_data: Enriched task data from problem orchestrator
            
        Returns:
            ContextInfo object or None if context extraction fails
        """
        try:
            # Check if we have enriched context
            if 'enriched_context' not in task_data:
                self.logger.warning("No enriched_context found in task_data")
                return None
            
            enriched_context = task_data['enriched_context']
            
            # Extract domain knowledge
            domain_knowledge = enriched_context.get('domain_knowledge', {})
            domain = domain_knowledge.get('domain', 'unknown')
            business_context = domain_knowledge.get('business_context', {})
            data_files = domain_knowledge.get('data_files', [])
            constraints = domain_knowledge.get('constraints', {})
            stakeholders = domain_knowledge.get('stakeholders', [])
            
            # Extract workflow context
            workflow_context = enriched_context.get('workflow_context', {})
            workflow_goal = workflow_context.get('goal', 'No specific goal provided')
            workflow_complexity = workflow_context.get('complexity', 'moderate')
            risk_level = workflow_context.get('risk_level', 'medium')
            
            # Extract execution context
            execution_context = enriched_context.get('execution_context', {})
            current_step = execution_context.get('current_step', {})
            execution_progress = execution_context.get('execution_progress', {})
            
            # Extract compliance and sensitivity from business context
            compliance_requirements = []
            if 'compliance' in business_context:
                compliance_requirements.append(business_context['compliance'])
            if 'regulations' in business_context:
                compliance_requirements.extend(business_context['regulations'])
            
            # Extract data sensitivity
            data_sensitivity = business_context.get('data_sensitivity', 'medium')
            if 'privacy' in constraints:
                data_sensitivity = constraints['privacy']
            
            # Extract optimization hints
            optimization_hints = []
            if 'optimization_requirements' in workflow_context:
                optimization_hints = workflow_context['optimization_requirements']
            
            # Extract risk factors
            risk_factors = []
            if 'risk_factors' in workflow_context:
                risk_factors = workflow_context['risk_factors']
            if 'safety_requirements' in workflow_context:
                risk_factors.extend(workflow_context['safety_requirements'])
            
            return ContextInfo(
                domain=domain,
                business_context=business_context,
                workflow_goal=workflow_goal,
                data_sensitivity=data_sensitivity,
                compliance_requirements=compliance_requirements,
                optimization_hints=optimization_hints,
                risk_factors=risk_factors,
                data_files=data_files,
                constraints=constraints,
                stakeholders=stakeholders,
                workflow_complexity=workflow_complexity,
                risk_level=risk_level,
                current_step=current_step,
                execution_progress=execution_progress
            )
            
        except Exception as e:
            self.logger.error(f"Failed to extract context info: {e}")
            return None
    
    def get_context_aware_recommendations(self, context: ContextInfo, agent_type: str) -> ContextRecommendations:
        """
        Generate context-aware recommendations for a specific agent type using AI intelligence.
        
        Args:
            context: Extracted context information
            agent_type: Type of agent (e.g., 'cleaning_agent', 'model_selection_agent')
            
        Returns:
            ContextRecommendations object with AI-generated recommendations
        """
        try:
            # Initialize AI handler and prompt manager
            ai_handler = SFNAIHandler()
            prompt_manager = SFNPromptManager()
            
            # Get the appropriate prompt for context analysis
            prompt_config = prompt_manager.prompts_config.get('context_analyzer', {})
            
            # Use supported LLM providers from config
            available_providers = [provider for provider in SFN_SUPPORTED_LLM_PROVIDERS if provider in prompt_config]
            if not available_providers:
                error_msg = f"No supported LLM providers found in prompt config. Available: {list(prompt_config.keys())}, Supported: {SFN_SUPPORTED_LLM_PROVIDERS}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            llm_provider = available_providers[0]  # Use first available supported provider
            
            # Prepare context data for AI analysis
            context_data = {
                'agent_type': agent_type,
                'domain': context.domain,
                'workflow_goal': context.workflow_goal,
                'data_sensitivity': context.data_sensitivity,
                'compliance_requirements': json.dumps(context.compliance_requirements),
                'business_context': json.dumps(context.business_context),
                'workflow_complexity': context.workflow_complexity,
                'risk_level': context.risk_level,
                'data_files': json.dumps(context.data_files),
                'constraints': json.dumps(context.constraints),
                'stakeholders': json.dumps(context.stakeholders)
            }
            
            # Get prompts for the selected provider
            provider_prompts = prompt_config.get(llm_provider, {})
            main_prompts = provider_prompts.get('main', {})
            
            system_prompt = main_prompts.get('system_prompt', '')
            user_prompt_template = main_prompts.get('user_prompt_template', '')
            
            # Format the user prompt with context data
            user_prompt = user_prompt_template.format(**context_data)
            
            # Prepare messages for LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Call LLM for intelligent recommendations - let the AI handler use its defaults
            configuration = {
                "messages": messages
            }
            
            # Let the AI handler determine the appropriate model for each provider
            # No hardcoded model selection - let the handler use its defaults
            model = None
            
            # Make LLM call
            response = ai_handler.route_to(
                llm_provider=llm_provider,
                configuration=configuration,
                model=model
            )
            
            # Parse AI response
            if response and hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
                
                # Try to parse JSON response
                try:
                    ai_recommendations = json.loads(content)
                    
                    # Validate and structure the response
                    recommendations = ContextRecommendations(
                        data_processing=ai_recommendations.get('data_processing', []),
                        quality_checks=ai_recommendations.get('quality_checks', []),
                        optimization_strategies=ai_recommendations.get('optimization_strategies', []),
                        risk_mitigation=ai_recommendations.get('risk_mitigation', []),
                        compliance_measures=ai_recommendations.get('compliance_measures', []),
                        performance_tuning=ai_recommendations.get('performance_tuning', [])
                    )
                    
                    self.logger.info(f"AI-generated {len(recommendations.data_processing)} data processing recommendations")
                    self.logger.info(f"AI-generated {len(recommendations.compliance_measures)} compliance recommendations")
                    
                    return recommendations
                    
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Failed to parse AI response as JSON: {e}")
                    self.logger.debug(f"Raw AI response: {content}")
            
            # AI call failed - throw error instead of fallback
            error_msg = "AI recommendation generation failed - no fallback available"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        except Exception as e:
            self.logger.error(f"Error generating AI-powered recommendations: {e}")
            # Re-raise the exception instead of fallback
            raise
    


    
    def validate_required_context(self, context: ContextInfo, required_fields: List[str]) -> Dict[str, Any]:
        """
        Validate that required context fields are present and meaningful.
        
        Args:
            context: Extracted context information
            required_fields: List of required field names
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'is_valid': True,
            'missing_fields': [],
            'empty_fields': [],
            'quality_score': 0.0,
            'recommendations': []
        }
        
        missing_count = 0
        empty_count = 0
        total_fields = len(required_fields)
        
        for field in required_fields:
            if not hasattr(context, field):
                validation_result['missing_fields'].append(field)
                missing_count += 1
            else:
                value = getattr(context, field)
                if self._is_empty_value(value):
                    validation_result['empty_fields'].append(field)
                    empty_count += 1
        
        # Calculate quality score
        validation_result['quality_score'] = max(0.0, (total_fields - missing_count - empty_count) / total_fields)
        
        # Determine overall validity
        validation_result['is_valid'] = missing_count == 0 and validation_result['quality_score'] >= 0.7
        
        # Generate recommendations
        if missing_count > 0:
            validation_result['recommendations'].append(
                f"Missing {missing_count} required context fields: {', '.join(validation_result['missing_fields'])}"
            )
        
        if empty_count > 0:
            validation_result['recommendations'].append(
                f"{empty_count} context fields are empty: {', '.join(validation_result['empty_fields'])}"
            )
        
        if validation_result['quality_score'] < 0.7:
            validation_result['recommendations'].append(
                "Context quality is below recommended threshold. Consider enriching context data."
            )
        
        return validation_result
    
    def _is_empty_value(self, value: Any) -> bool:
        """Check if a value is considered empty for context validation."""
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == '':
            return True
        if isinstance(value, (list, dict)) and len(value) == 0:
            return True
        return False
    
    def log_context_usage(self, context: ContextInfo, agent_type: str, field_usage: List[str]):
        """
        Log context usage for transparency and debugging.
        
        Args:
            context: Extracted context information
            agent_type: Type of agent using the context
            field_usage: List of context fields being used
        """
        self.logger.info(f"Agent {agent_type} using context:")
        self.logger.info(f"  Domain: {context.domain}")
        self.logger.info(f"  Workflow Goal: {context.workflow_goal}")
        self.logger.info(f"  Data Sensitivity: {context.data_sensitivity}")
        self.logger.info(f"  Compliance Requirements: {context.compliance_requirements}")
        self.logger.info(f"  Context Fields Used: {', '.join(field_usage)}")
        
        if context.optimization_hints:
            self.logger.info(f"  Optimization Hints: {context.optimization_hints}")
        if context.risk_factors:
            self.logger.info(f"  Risk Factors: {context.risk_factors}")


# Convenience functions for easy import
def extract_context_info(task_data: Dict[str, Any]) -> Optional[ContextInfo]:
    """Extract structured context from enriched task data."""
    analyzer = ContextAnalyzer()
    return analyzer.extract_context_info(task_data)


def get_context_recommendations(context: ContextInfo, agent_type: str) -> ContextRecommendations:
    """Get context-aware recommendations for an agent type."""
    analyzer = ContextAnalyzer()
    return analyzer.get_context_aware_recommendations(context, agent_type)


def validate_context(context: ContextInfo, required_fields: List[str]) -> Dict[str, Any]:
    """Validate required context fields."""
    analyzer = ContextAnalyzer()
    return analyzer.validate_required_context(context, required_fields)


def log_context_usage(context: ContextInfo, agent_type: str, field_usage: List[str]):
    """Log context usage for transparency."""
    analyzer = ContextAnalyzer()
    analyzer.log_context_usage(context, agent_type, field_usage)
