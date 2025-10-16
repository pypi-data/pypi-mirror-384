import json
import os
from sfn_blueprint.agents.base_agent import SFNAgent
import re
from sfn_blueprint.utils.prompt_manager import SFNPromptManager
from sfn_blueprint.config.model_config import MODEL_CONFIG
from sfn_blueprint.utils.llm_handler import SFNAIHandler 
from sfn_blueprint.utils.logging import setup_logger
class SFNFeatureCodeGeneratorAgent(SFNAgent):
    def __init__(self, llm_provider: str):
        super().__init__(name="Feature Code Generator", role="Python Developer")
        self.logger, _ = setup_logger("SFNFeatureCodeGeneratorAgent")
        self.llm_provider = llm_provider
        self.model_config = MODEL_CONFIG["code_generator"]
        parent_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
        prompt_config_path = os.path.join(parent_path, 'config', 'prompts_config.json')
        self.prompt_manager = SFNPromptManager(prompt_config_path)
        self.ai_handler = SFNAIHandler(logger_name="AIHandler-FeatureCodeGenerator")

    def execute_task(self, task, error_message=None) -> str:
        self.logger.info(f"Executing task for LLM provider: {self.llm_provider }")
        prompt_kwargs = {
            'suggestion': task.data['suggestion'],
            'columns': task.data['columns'],
            'dtypes': task.data['dtypes'],
            'sample_records': task.data['sample_records'],
            'error_message': error_message
        }
        
        system_prompt, user_prompt = self.prompt_manager.get_prompt(
            agent_type='code_generator',
            llm_provider=self.llm_provider ,
            sfn_blueprint_prompt = True, 
            **prompt_kwargs
        )

        # Route to the correct LLM client via the handler
        configuration = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.model_config[self.llm_provider]["temperature"],
            "max_tokens": self.model_config[self.llm_provider]["max_tokens"]
        }

        try:
            code, token_cost_summary = self.ai_handler.route_to(self.llm_provider, configuration, self.model_config[self.llm_provider]["model"])
            self.logger.info(f"Generated code response: {code}")
            self.logger.info(f"token consumption cost:{token_cost_summary}")

        except Exception as e:
            self.logger.error(f"Error during task execution: {e}")
            raise e

        self.logger.debug(f"code received: {code}...")  # Log first 100 chars of response
        return self.clean_generated_code(code)
    
    @staticmethod
    def clean_generated_code(code: str) -> str:
        code = re.sub(r'```python\n|```', '', code)
        code = re.sub(r'print\(.*\)\n?', '', code)
        code = re.sub(r'#.*\n', '', code)
        code = '\n'.join(line for line in code.split('\n') if line.strip())
        print('>>code cleaned..', code)
        return code