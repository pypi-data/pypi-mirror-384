import logging
from dataclasses import dataclass
from typing import Optional, List, Annotated, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, create_model

from langgraph.graph.message import add_messages
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, AnyMessage

from sfn_llm_client import LLMConfig

class CritiqueStructureOutput(BaseModel):
    is_sufficient: bool = Field(
        ...,
        description="A boolean flag indicating if the response is good enough to be considered final.",
    )
    critique: str = Field(
        ...,
        description="Constructive feedback and detailed critique of the response.",
    )

@dataclass
class ReflectionPromptTemplates:
    critique_system: str
    reflector_system: str
    initial_system: str
    critique: str
    refine: str
    initial_user: str

class ReflectionState(BaseModel):

    user_query: Dict[str, Any] = Field( 
        description="Original user question or request that started the refinement process."
    )
    current_response: Optional[BaseModel]= Field(
        default=None,
        description="Current response version being evaluated or awaiting critique."
    )

    critique: Optional[CritiqueStructureOutput] = Field(
        default=None,
        description="Structured feedback containing both strengths and improvement suggestions."
    )
    reflections_count: int = Field(
        default=0,
        description="Safety limit preventing infinite refinement loops (typically 3-5).",
        gt=0
    )
    max_reflections: int = Field(
        default=3,
        description="Safety limit preventing infinite refinement loops (typically 3-5).",
        gt=0
    )
    messages: Annotated[List[AnyMessage], add_messages] =  Field(
        default_factory=list,
        description="Full conversation transcript including all prompts, responses, and metadata."
    )

class MultiAgentConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_runnable_config(
        cls,
        runnable_settings: RunnableConfig,
        required_agents: list[str],
    ) -> "MultiAgentConfig":
  
        if not runnable_settings or "configurable" not in runnable_settings:
            raise ValueError("Invalid or empty runnable_settings provided. It must contain a 'configurable' key.")
        
        config_values = runnable_settings.get("configurable", {})
        if not config_values:
            raise ValueError("The 'configurable' key in runnable_settings is empty.")

        if required_agents:
            missing = [name for name in required_agents if name not in config_values]
            if missing:
                raise ValueError(f"Missing required agent configurations: {', '.join(missing)}")

        field_definitions: Dict[str, Any] = {}
        init_data: Dict[str, LLMConfig] = {}

        for agent_name, raw_config in config_values.items():
            if not isinstance(raw_config, dict):
                raise TypeError(f"Configuration for agent '{agent_name}' must be a dictionary.")
            
            required_fields = ["model_name"]
            for field in required_fields:
                if field not in raw_config:
                    raise ValueError(f"'{field}' must be provided for agent '{agent_name}'")

            processed_config = raw_config.copy()

            field_definitions[agent_name] = (LLMConfig, Field(
                description=f"Configuration for the '{agent_name}' agent's LLM."
            ))
            
            init_data[agent_name] = LLMConfig(**processed_config)

        DynamicModel = create_model(
            'DynamicAgentConfiguration',
            __base__=cls,
            **field_definitions
        )

        return DynamicModel(**init_data)



class ChatState(BaseModel):
    messages: Annotated[List[AnyMessage], add_messages] =  Field(
        default_factory=list,
        description="Full conversation transcript including all prompts, responses, and metadata."
    )
    user_query: str = Field(
        ...,
        description="User's input message to the chat agent."
    )
    output_message: Optional[str] = Field(
        default= None,
        description="Agent's response message to the user."
    )