import json
from typing import Any, Literal, Union

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

from cuga.backend.cuga_graph.nodes.api.variables_manager.manager import VariablesManager
from cuga.backend.cuga_graph.nodes.shared.base_agent import BaseAgent
from cuga.backend.cuga_graph.nodes.answer.final_answer_agent.prompts.load_prompt import (
    FinalAnswerOutput,
    FinalAnswerAppworldOutput,
    parser,
)
from cuga.backend.cuga_graph.state.agent_state import AgentState
from cuga.backend.llm.models import LLMManager
from cuga.backend.llm.utils.helpers import load_prompt_simple
from cuga.config import settings
from cuga.backend.activity_tracker.tracker import ActivityTracker
from cuga.configurations.instructions_manager import InstructionsManager

instructions_manager = InstructionsManager()
llm_manager = LLMManager()
tracker = ActivityTracker()
var_manager = VariablesManager()


class FinalAnswerAgent(BaseAgent):
    def __init__(
        self,
        prompt_template: ChatPromptTemplate,
        llm: BaseChatModel,
        mode: Literal['default', 'appworld'] = 'default',
        tools: Any = None,
    ):
        super().__init__()
        self.name = "FinalAnswerAgent"
        parser = RunnableLambda(FinalAnswerAgent.output_parser)
        parser_default = RunnableLambda(FinalAnswerAgent.default_answer_parser)
        if mode == "default":
            self.chain = BaseAgent.get_chain(prompt_template, llm, wx_json_mode="no_format") | (
                parser_default.bind(name=self.name)
            )
        else:
            self.chain = BaseAgent.get_chain(prompt_template, llm, FinalAnswerAppworldOutput) | (
                parser.bind(name=self.name)
            )

    @staticmethod
    def default_answer_parser(result: AIMessage, name):
        result = AIMessage(
            content=FinalAnswerOutput(thoughts=[], final_answer=result.content).model_dump_json(), name=name
        )
        return result

    @staticmethod
    def output_parser(result: Union[FinalAnswerOutput, FinalAnswerAppworldOutput], name) -> Any:
        result = AIMessage(content=json.dumps(result.model_dump()), name=name)
        return result

    async def run(self, input_variables: AgentState) -> AIMessage:
        if settings.features.final_answer:
            data = input_variables.model_dump()
            data["variable_summary"] = var_manager.get_variables_summary(last_n=2)
            data["instructions"] = instructions_manager.get_instructions(self.name)
            return await self.chain.ainvoke(data)
        else:
            last_variable_name, last_variable = var_manager.get_last_variable()
            return AIMessage(
                content=json.dumps(
                    FinalAnswerOutput(
                        final_answer=input_variables.last_planner_answer
                        + (
                            f"\n\n{last_variable.description}\n\n---\n\n{var_manager.present_variable(last_variable_name)}"
                            if last_variable_name
                            else ""
                        ),
                        thoughts=["Skipping final answer, using last agent answer"],
                    ).model_dump()
                )
            )

    @staticmethod
    def create():
        dyna_model = settings.agent.final_answer.model
        if settings.advanced_features.benchmark == "appworld":
            return FinalAnswerAgent(
                prompt_template=load_prompt_simple(
                    "./prompts/system_appworld.jinja2",
                    "./prompts/user_msg_appworld.jinja2",
                    model_config=dyna_model,
                ),
                mode="appworld",
                llm=llm_manager.get_model(dyna_model),
            )
        else:
            return FinalAnswerAgent(
                prompt_template=load_prompt_simple(
                    "./prompts/system.jinja2",
                    "./prompts/user_msg.jinja2",
                    model_config=dyna_model,
                    format_instructions=BaseAgent.get_format_instructions(parser),
                ),
                llm=llm_manager.get_model(dyna_model),
            )
