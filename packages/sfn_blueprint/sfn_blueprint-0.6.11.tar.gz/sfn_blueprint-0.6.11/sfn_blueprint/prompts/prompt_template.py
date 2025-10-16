from string import Formatter
from typing import Any, Dict, Set, Tuple
from pydantic import BaseModel, model_validator, ConfigDict
import tiktoken
from sfn_llm_client.utils.logging import setup_logger
from langchain_core.utils.input import get_colored_text, get_bolded_text

logger, _ = setup_logger(logger_name="PromptTemplates")
fmt_msg = lambda msg, location, color="green": (
    f"{get_colored_text(f'[{location}]', color=color)} {get_bolded_text(msg)}"
)

class ReflectionPromptTemplates(BaseModel):
    model_config = ConfigDict(extra="allow")

    initial_system_prompt: str
    initial_user_prompt: str
    critique_system_prompt: str
    critique_user_prompt: str
    refine_system_prompt: str
    refine_user_prompt: str

    template_token_limit: int = 200
    input_token_limit: int = 200
    encoding_name: str = "o200k_base"
    
    partial_variables: Dict[str, Any] = {}

    @staticmethod
    def _get_variables(template: str) -> Set[str]:
        return {v for _, v, _, _ in Formatter().parse(template) if v is not None}

    @model_validator(mode="after")
    def _setup_and_validate(self) -> "ReflectionPromptTemplates":
        encoder = tiktoken.get_encoding(self.encoding_name)

        for name, template in self.model_dump().items():
            if isinstance(template, str):
                token_count = len(encoder.encode(template))
                if token_count > self.template_token_limit:
                    msg = fmt_msg(f"Template '{name}' has {token_count} tokens, which exceeds the limit of {self.template_token_limit}.", "reflection/PromptTemplates", color="yellow")
                    logger.warning(msg)

        del encoder
        initial_vars = self._get_variables(self.initial_user_prompt)
        critique_vars = self._get_variables(self.critique_user_prompt)
        refine_vars = self._get_variables(self.refine_user_prompt)
        
        allowed_critique_vars = initial_vars | {"assistant_response"}
        if not critique_vars.issubset(allowed_critique_vars):
            unexpected = critique_vars - allowed_critique_vars
            msg = fmt_msg(f"critique_user_prompt contains unexpected variables {unexpected} that are not in initial_user_prompt.", "reflection/PromptTemplates", color="red")
            logger.error(msg)
            raise ValueError(msg)


        allowed_refine_vars = initial_vars | {"previous_response", "critique"}
        if not refine_vars.issubset(allowed_refine_vars):
            unexpected = refine_vars - allowed_refine_vars
            msg = fmt_msg(f"refine_user_prompt contains unexpected variables {unexpected} that are not in initial_user_prompt.", "reflection/PromptTemplates", color="red")
            logger.error(msg)
            raise ValueError(f"refine_user_prompt contains unexpected variables {unexpected} that are not in initial_user_prompt.")
            
        return self

    def format_initial(self, **kwargs: Any) -> Tuple[str, str]:
        if self.partial_variables:
            msg = fmt_msg("This prompt session has already been initialized.", "reflection/PromptTemplates", color="red") 
            logger.error(msg)
            raise ValueError("This prompt session has already been initialized.")

        initial_vars = self._get_variables(self.initial_user_prompt)
        if not initial_vars == set(kwargs.keys()):
            missing = initial_vars - set(kwargs.keys())
            extra = set(kwargs.keys()) - initial_vars
            msg = "Provided arguments do not match variables in 'initial_user_prompt'."
            if missing: msg += f" Missing: {missing}."
            if extra: msg += f" Extra: {extra}."
            fmsg = fmt_msg(msg, "reflection/PromptTemplates", color="red")
            logger.error(fmsg)
            raise ValueError(msg)
        
        encoder = tiktoken.get_encoding(self.encoding_name)
        total_input_tokens = sum(len(encoder.encode(str(v))) for v in kwargs.values())
        del encoder
        if total_input_tokens > self.input_token_limit:
            msg = fmt_msg(f"The combined token count of your inputs is {total_input_tokens}, which exceeds the limit of {self.input_token_limit}.", "reflection/PromptTemplates", color="yellow")
            logger.warning(msg)

        self.partial_variables = kwargs
        return self.initial_system_prompt, self.initial_user_prompt.format(**kwargs)

    def format_critique(self, assistant_response: str) -> Tuple[str, str]:
        if not self.partial_variables:
            msg = fmt_msg("You must call format_initial() first to bind user input. before format_critique", "reflection/PromptTemplates", color="red")
            logger.error(msg)
            raise ValueError("You must call format_initial() first to bind user input. before format_critique")
        
        all_kwargs = {**self.partial_variables, "assistant_response": assistant_response}
        return self.critique_system_prompt, self.critique_user_prompt.format(**all_kwargs)

    def format_refine(self, previous_response: str, critique: str) -> Tuple[str, str]:
        if not self.partial_variables:
            msg = fmt_msg("You must call format_initial() first to bind user input. before format_refine", "reflection/PromptTemplates", color="red")
            logger.error(msg)
            raise ValueError("You must call format_initial() first to bind user input. before format_refine")
            
        all_kwargs = {**self.partial_variables, "previous_response": previous_response, "critique": critique}
        return self.refine_system_prompt, self.refine_user_prompt.format(**all_kwargs)