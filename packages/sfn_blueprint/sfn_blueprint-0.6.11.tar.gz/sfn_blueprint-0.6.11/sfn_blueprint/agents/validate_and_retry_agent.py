import time
from typing import Any
from .base_agent import SFNAgent
from sfn_blueprint.config.model_config import MODEL_CONFIG
from sfn_blueprint.utils.llm_handler import SFNAIHandler
from sfn_blueprint.utils.logging import setup_logger

class SFNValidateAndRetryAgent(SFNAgent):
    def __init__(self, llm_provider: str, for_agent: str):
        super().__init__(name="Validation Agent", role="Validator")
        # here for_agent name should be exact same, agent name specified in prompt_config.json file
        self.for_agent = for_agent
        self.logger, _ = setup_logger(f"SFNValidationAgent for -{for_agent}-")
        self.model_config = MODEL_CONFIG["validator"]
        self.llm_provider = llm_provider
        self.ai_handler = SFNAIHandler()

    def complete(self, agent_to_validate: Any, task: Any, validation_task: Any,
                             method_name: str, get_validation_params: str, max_retries: int = 3, retry_delay: float = 3.0):
        """
        Execute a task with validation and retry logic.
        
        Args:
            agent_to_validate: The agent object to execute the task
            task: The primary task to execute
            validation_task: Task object containing validation context
            method_name: Name of the method to execute on agent
            get_validation_params: Name of method to get validation parameters
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        for attempt in range(max_retries):
            self.logger.info(f"Attempt {attempt + 1}: Executing {method_name}")
            
            # Execute the primary task
            method_to_call = getattr(agent_to_validate, method_name)
            response = method_to_call(task)
            self.logger.info(f'Executed primary task of agent:{agent_to_validate}')

            # Get validation parameters
            get_validation_method = getattr(agent_to_validate, get_validation_params)
            validation_prompts = get_validation_method(response, validation_task)
            self.logger.info(f'Received validation prompts:{validation_prompts}')

            # Validate the response
            is_valid, message = self.validate(validation_prompts)
            
            if is_valid:
                self.logger.info("Validation successful")
                return response, message, True
            
            self.logger.warning(f"Validation failed: {message}")
            if attempt == max_retries - 1:
                message = 'Validation failed:' + message
                return response, message, False
                
            time.sleep(retry_delay)

    def validate(self, validation_prompts: dict) -> tuple:
        """
        Validate the response using the provided prompts.
        
        Returns:
            Tuple of (is_valid: bool, message: str)
        """
        configuration = {
            "messages": [
                {"role": "system", "content": validation_prompts["system_prompt"]},
                {"role": "user", "content": validation_prompts["user_prompt"]}
            ],
            "temperature": self.model_config[self.llm_provider]["temperature"],
            "max_tokens": self.model_config[self.llm_provider]["max_tokens"]
        }

        try:
            validation_result, _ = self.ai_handler.route_to(
                self.llm_provider,
                configuration,
                self.model_config[self.llm_provider]["model"]
            )
            
            return self._parse_validation_result(validation_result)
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return False, str(e)

    def _parse_validation_result(self, result: str) -> tuple:
        """
        Parse the validation result into a boolean and message.
        
        Returns:
            Tuple of (is_valid: bool, message: str)
        """
        try:
            parts = result.strip().split('\n', 1)
            is_valid = parts[0].upper() == "TRUE"
            message = parts[1] if len(parts) > 1 else ""
            return is_valid, message.strip()
        except Exception as e:
            return False, f"Error parsing validation result: {e}"
