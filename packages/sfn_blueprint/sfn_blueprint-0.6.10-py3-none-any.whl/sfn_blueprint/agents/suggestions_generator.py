import json
from typing import List, Dict, Any
from .base_agent import SFNAgent
from sfn_blueprint.tasks.task import Task
from sfn_blueprint.utils.prompt_manager import SFNPromptManager
from sfn_blueprint.config.model_config import MODEL_CONFIG
from sfn_blueprint.utils.llm_handler import SFNAIHandler
from sfn_blueprint.utils.logging import setup_logger

class SFNSuggestionsGeneratorAgent(SFNAgent):
    def __init__(self, llm_provider: str):
        super().__init__(name="Suggestions Generator", role="Generic Suggestions Generator")
        self.logger, _ = setup_logger(logger_name="SFNSuggestionsGeneratorAgent")
        
        self.llm_provider = llm_provider
        self.model_config = MODEL_CONFIG["suggestions_generator"]
        self.prompt_manager = SFNPromptManager()
        self.ai_handler = SFNAIHandler()

    def execute_task(self, task: Task) -> List[str]:
        """
        Execute the suggestion generation task.
        
        :param task: Task object containing the data, task_type and category
        :return: List of suggestions
        """
        self.logger.info(f"Executing task with provider {self.llm_provider} and task_type {task.task_type}")
        
        if not isinstance(task.data, dict) or 'df' not in task.data:
            self.logger.error("Task data must be a dictionary containing 'df' key")
            raise ValueError("Task data must be a dictionary containing 'df' key")
        
        df = task.data['df']
        task_type = task.task_type or 'feature_suggestion'
        category = task.category

        # Handle empty DataFrame case
        if df.empty:
            self.logger.warning("Empty DataFrame provided")
            return []
        
        self.logger.debug(f"Task category: {category}, Task type: {task_type}")
        
        columns = list(df.columns)  # Use list() to ensure it's not a pandas Index
        sample_records = df.head(3).to_dict(orient='records')
        
        # Handle describe() for empty or single-row DataFrames
        describe_dict = df.describe().to_dict() if len(df) > 1 else {}

        self.logger.info(f"Dataframe columns: {columns}")

        suggestions = self._generate_suggestions(
            columns=columns,
            sample_records=sample_records,
            describe_dict=describe_dict,
            task_type=task_type,
            category=category,
            llm_provider=self.llm_provider 
        )
        
        self.logger.info(f"Generated {len(suggestions)} suggestions")
        return suggestions

    def _generate_suggestions(self, columns: List[str], sample_records: List[Dict[str, Any]], 
                              describe_dict: Dict[str, Dict[str, float]], 
                              task_type: str,
                              category: str,
                              llm_provider: str) -> List[str]:
        """
        Generate suggestions based on the data, task type and category.
        """
        self.logger.info("Generating suggestions based on the provided data and model configuration")
        
        system_prompt, user_prompt = self.prompt_manager.get_prompt(
            agent_type='suggestions_generator',
            llm_provider=llm_provider,
            columns=columns,
            sample_records=sample_records,
            describe_dict=describe_dict,
            task_type=task_type,
            category=category
        )

        self.logger.debug(f"System Prompt: {system_prompt}")
        self.logger.debug(f"User Prompt: {user_prompt}")
        # Route to the correct LLM client via the handler
        configuration = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.model_config[llm_provider]["temperature"],
            "max_tokens": self.model_config[llm_provider]["max_tokens"]
        }

        self.logger.info(f"Routing API call to {llm_provider} with model {self.model_config[llm_provider]['model']}")
        
        try:
            suggestions_text, token_cost_summary = self.ai_handler.route_to(llm_provider, configuration, self.model_config[llm_provider]["model"])
            self.logger.info(f"token consumption cost:{token_cost_summary}")
        except Exception as e:
            self.logger.error(f"Error during API call to {llm_provider}: {str(e)}")
            raise

        self.logger.debug(f"Suggestions received: {suggestions_text[:100]}...")  # Log first 100 chars of response
        return self._parse_suggestions(suggestions_text)
    
    def _parse_suggestions(self, suggestions_text: str) -> List[str]:
        """
        Parse the suggestions text into a list of individual suggestions.
        
        :param suggestions_text: Raw text of suggestions from the LLM
        :return: List of individual suggestions
        """
        self.logger.info("Parsing suggestions from text")
        
        # If suggestions_text is empty, return an empty list
        if not suggestions_text:
            return []
        
        # Split the text by newlines and remove any empty lines
        suggestions = [line.strip() for line in suggestions_text.split('\n') if line.strip()]
        
        # Remove numbering from each suggestion, handling various formats
        parsed_suggestions = []
        for suggestion in suggestions:
            # Remove leading numbers, letters, or symbols followed by a period or parenthesis
            cleaned_suggestion = suggestion.split('. ', 1)[-1]
            cleaned_suggestion = cleaned_suggestion.split(') ', 1)[-1]
            cleaned_suggestion = cleaned_suggestion.split('] ', 1)[-1]
            parsed_suggestions.append(cleaned_suggestion)
        
        self.logger.info(f"Parsed {len(parsed_suggestions)} suggestions")
        return parsed_suggestions