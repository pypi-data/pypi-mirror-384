import pandas as pd
import numpy as np
import textblob
import sklearn
import nltk
import spacy
from .base_agent import SFNAgent
from sfn_blueprint.utils.logging import setup_logger
class SFNCodeExecutorAgent(SFNAgent):
    def __init__(self):
        super().__init__(name="Code Executor", role="Python Code Executor")
        self.logger, _ = setup_logger(logger_name="SFNCodeExecutorAgent")

    def execute_task(self, task) -> pd.DataFrame:
        """
        Executes the provided Python code in a controlled environment.

        :param task: Task object that contains the Python code and data (in the form of a DataFrame)
        :return: DataFrame after the code execution
        """
        self.logger.info(f"Executing task with provided code: {task.code[:100]}...")  # Log first 100 characters of the code
        local_env = {
            'pd': pd,
            'np': np,
            'textblob': textblob,
            'sklearn': sklearn,
            'nltk': nltk,
            'spacy': spacy,
            'df': task.data
        }
        
        try:
            self.logger.info("Executing code...")
            exec(task.code, local_env)
            self.logger.info("Code execution successful")
        except Exception as e:
            self.logger.error(f"Error during code execution: {str(e)}")
            raise e  # Optionally re-raise the error after logging

        if 'df' in local_env:
            self.logger.info("Returning modified DataFrame")
            return local_env['df']
        else:
            self.logger.error("'df' key DataFrame not found in local environment after code execution")
            raise KeyError("'df' key DataFrame not  found in the local environment after code execution")