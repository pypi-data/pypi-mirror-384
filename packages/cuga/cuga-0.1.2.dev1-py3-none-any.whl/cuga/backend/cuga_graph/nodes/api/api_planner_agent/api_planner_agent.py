from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel
from cuga.backend.activity_tracker.tracker import ActivityTracker
from cuga.backend.cuga_graph.nodes.api.variables_manager.manager import VariablesManager
from cuga.backend.cuga_graph.nodes.shared.base_agent import BaseAgent
from cuga.backend.cuga_graph.state.agent_state import AgentState
from cuga.backend.cuga_graph.nodes.api.api_planner_agent.prompts.load_prompt import (
    APIPlannerOutput,
    APIPlannerOutputLite,
    APIPlannerOutputNoHITL,
    APIPlannerOutputLiteNoHITL,
)
from cuga.backend.llm.models import LLMManager
from cuga.backend.llm.utils.helpers import load_prompt_simple
from cuga.config import settings
from cuga.configurations.instructions_manager import InstructionsManager

instructions_manager = InstructionsManager()
tracker = ActivityTracker()
llm_manager = LLMManager()
var_manager = VariablesManager()


class APIPlannerAgent(BaseAgent):
    def __init__(self, prompt_template: ChatPromptTemplate, llm: BaseChatModel, tools: Any = None):
        super().__init__()
        self.name = "APIPlannerAgent"

        if settings.advanced_features.api_planner_hitl:
            schema = APIPlannerOutputLite if not settings.features.thoughts else APIPlannerOutput
        else:
            schema = APIPlannerOutputLiteNoHITL if not settings.features.thoughts else APIPlannerOutputNoHITL

        self.chain = BaseAgent.get_chain(prompt_template=prompt_template, llm=llm, schema=schema)

    def output_parser(result: AIMessage, name) -> Any:
        result = AIMessage(content=result.content, name=name)
        return result

    async def run(self, input_variables: AgentState) -> AIMessage:
        data = input_variables.model_dump()
        data['variables_summary'] = var_manager.get_variables_summary()
        data["instructions"] = instructions_manager.get_instructions(self.name)
        res = await self.chain.ainvoke(data)

        if not settings.features.thoughts:
            lite_res = res
            if settings.advanced_features.api_planner_hitl:
                full_res = APIPlannerOutput(
                    thoughts=[],
                    action=lite_res.action,
                    action_input_shortlisting_agent=lite_res.action_input_shortlisting_agent,
                    action_input_coder_agent=lite_res.action_input_coder_agent,
                    action_input_conclude_task=lite_res.action_input_conclude_task,
                    action_input_consult_with_human=lite_res.action_input_consult_with_human,
                )
            else:
                full_res = APIPlannerOutput(
                    thoughts=[],
                    action=lite_res.action,
                    action_input_shortlisting_agent=lite_res.action_input_shortlisting_agent,
                    action_input_coder_agent=lite_res.action_input_coder_agent,
                    action_input_conclude_task=lite_res.action_input_conclude_task,
                    action_input_consult_with_human=None,
                )
            return AIMessage(content=full_res.model_dump_json())
        else:
            if not settings.advanced_features.api_planner_hitl:
                if hasattr(res, 'action_input_consult_with_human'):
                    res_dict = res.model_dump()
                    res_dict['action_input_consult_with_human'] = None
                    full_res = APIPlannerOutput(**res_dict)
                    return AIMessage(content=full_res.model_dump_json())
            return AIMessage(content=res.model_dump_json())

    @staticmethod
    def create():
        dyna_model = settings.agent.planner.model

        if settings.advanced_features.api_planner_hitl:
            system_prompt = "./prompts/system_hitl.jinja2"
            user_prompt = "./prompts/user_hitl.jinja2"
        else:
            system_prompt = "./prompts/system.jinja2"
            user_prompt = "./prompts/user.jinja2"

        return APIPlannerAgent(
            prompt_template=load_prompt_simple(
                system_prompt,
                user_prompt,
                model_config=dyna_model,
            ),
            llm=llm_manager.get_model(dyna_model),
        )
