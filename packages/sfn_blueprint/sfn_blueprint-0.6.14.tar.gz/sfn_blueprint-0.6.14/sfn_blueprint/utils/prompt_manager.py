import os
import json
from typing import Dict, Tuple, Union
from sfn_blueprint.utils.logging import setup_logger
from sfn_blueprint.config.model_config import SFN_SUPPORTED_LLM_PROVIDERS

class SFNPromptManager:
    def __init__(self, prompts_config_path: str = None):
        self.logger, _ = setup_logger(logger_name="SFNPromptManager")
        
        # If no path provided, use the default path relative to the package
        if prompts_config_path is None:
            # Get the directory where this file is located
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up to the sfn_blueprint package root and then to config
            package_root = os.path.dirname(os.path.dirname(current_dir))
            prompts_config_path = os.path.join(package_root, "config", "prompts_config.json")
        
        try:
            self.prompts_config = self._load_prompts_config(prompts_config_path)
            self.logger.info(f"Prompt Manager initialized with config from: {prompts_config_path}")
            self.logger.debug(f"Loaded prompt config: {self.prompts_config}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Prompt Manager: {str(e)}")
            raise RuntimeError(f"Prompt Manager initialization failed: {str(e)}") from e

    def _load_prompts_config(self, path: str) -> Dict:
        if not os.path.exists(path):
            self.logger.error(f"Prompts config file not found at: {path}")
            raise FileNotFoundError(f"Prompts config file not found at: {path}")
            
        try:
            with open(path, 'r') as f:
                config = json.load(f)
            if not isinstance(config, dict):
                self.logger.error("Config file must contain a JSON object")
                raise ValueError("Config file must contain a JSON object")
            self.logger.info(f"Prompts config loaded successfully from {path}")
            return config
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in config file: {str(e)}")
            raise ValueError(f"Invalid JSON in config file: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error loading prompts config: {str(e)}")
            raise Exception(f"Error loading prompts config: {str(e)}")

    def get_prompt(self, agent_type: str, llm_provider: str, prompt_type: str = 'main', **kwargs) -> Union[Tuple[str, str], Dict[str, str]]:
        """
        Get formatted prompts for specific agent and LLM provider
        
        Args:
            agent_type: Type of agent (e.g., 'feature_suggester', 'code_generator')
            llm_provider: LLM provider (e.g., 'openai', 'anthropic')
            prompt_type: Type of prompt to retrieve ('main' or 'validation')
            **kwargs: Variables for formatting the prompt template
            
        Returns:
            Union[Tuple[str, str], Dict[str, str]]: Either (system_prompt, formatted_user_prompt) 
            or {'system_prompt': str, 'user_prompt': str}
        """
        if agent_type not in self.prompts_config:
            error_msg = f"Unknown agent type, please specify this agent in prompt config file: {agent_type}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        if llm_provider not in self.prompts_config[agent_type]:
            error_msg = f"Unknown LLM provider{', please add configuration of this llm provider in prompt config file' if llm_provider in SFN_SUPPORTED_LLM_PROVIDERS else ''}: {llm_provider}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        prompts = self.prompts_config[agent_type][llm_provider]
        
        if prompt_type not in prompts:
            self.logger.error(f"Unknown prompt type: {prompt_type}")
            raise ValueError(f"Unknown prompt type: {prompt_type}")

        prompt_config = prompts[prompt_type]
        system_prompt = prompt_config["system_prompt"]
        user_prompt = prompt_config["user_prompt_template"].format(**kwargs)

        if prompt_type == 'validation':
            # For validation prompts, return a dict format
            return {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt
            }
        
        # For main prompts, return tuple format
        return system_prompt, user_prompt