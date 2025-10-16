from langchain_core.tracers.stdout import elapsed, try_json_stringify
from langchain_core.utils.input import get_colored_text, get_bolded_text, get_color_mapping
from langchain_core.tracers.schemas import Run

import logging
from typing import Any


from langchain.callbacks.tracers.logging import LoggingCallbackHandler

class ConfigurableLoggingHandler(LoggingCallbackHandler):
    """
    https://python.langchain.com/api_reference/langchain/callbacks/langchain.callbacks.tracers.logging.LoggingCallbackHandler.html

    if you changing anything read this docs and 
    langcain clone fine LoggingCallbackHandler file written by langchain 
    now it present libs/langchain/langchain/callbacks/tracers/logging.py but it may be changes sof find LoggingCallbackHandler

    go to baseclasses now is (FunctionCallbackHandler) it may be change then you understand change the code
    
    Basically i override base class function

    An extension of LoggingCallbackHandler that allows selectively disabling
    logging and customizes the output format for readability.
    """
    def __init__(
        self,
        logger: logging.Logger,
        log_level: int = logging.INFO,
        **kwargs: Any,
    ):
        super().__init__(logger=logger, log_level=log_level, **kwargs)

    def _on_llm_end(self, run: Run) -> None:
        try:
            output_text = run.outputs['generations'][0][0]['text']
            crumbs = self.get_breadcrumbs(run)
            self.function_callback(
                f"{get_colored_text('[llm/end]', color='blue')} "
                + get_bolded_text(
                    f"[{crumbs}] [{elapsed(run)}] Exiting LLM run with output:\n"
                )
                + f"{try_json_stringify(output_text, '[response]')}"
            )
        except Exception:
            super()._on_llm_end(run)
        
        
        # self.function_callback(
        #     f"{get_colored_text('[llm/end]', color='blue')} "
        #     + get_bolded_text(
        #         f"[{crumbs}]  Exiting LLM run with output:\n"
        #     )
        #     + f"{try_json_stringify(output_text, '[response]')}"
        # )
