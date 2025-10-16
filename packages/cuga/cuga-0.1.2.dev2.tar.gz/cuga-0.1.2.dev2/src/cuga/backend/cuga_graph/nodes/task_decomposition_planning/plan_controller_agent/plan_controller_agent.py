import json
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

from cuga.backend.activity_tracker.tracker import ActivityTracker
from cuga.backend.cuga_graph.nodes.api.variables_manager.manager import VariablesManager
from cuga.backend.cuga_graph.nodes.shared.base_agent import BaseAgent
from cuga.backend.cuga_graph.state.agent_state import AgentState
from cuga.backend.cuga_graph.nodes.task_decomposition_planning.plan_controller_agent.prompts.load_prompt import (
    PlanControllerOutput,
    parser,
)
from cuga.backend.llm.models import LLMManager
from cuga.backend.llm.utils.helpers import load_prompt_simple
from cuga.config import settings
from cuga.configurations.instructions_manager import InstructionsManager

instructions_manager = InstructionsManager()
tracker = ActivityTracker()
var_manager = VariablesManager()
llm_manager = LLMManager()


class PlanControllerAgent(BaseAgent):
    def __init__(self, prompt_template: ChatPromptTemplate, llm: BaseChatModel, tools: Any = None):
        super().__init__()
        self.name = "PlanControllerAgent"
        parser = RunnableLambda(PlanControllerAgent.output_parser)
        # if not enable_format:
        self.chain = BaseAgent.get_chain(prompt_template, llm, PlanControllerOutput) | (
            parser.bind(name=self.name)
        )

        # else:
        # self.chain = prompt_template | llm | controller_step_parser | (parser.bind(name=self.name))

    @staticmethod
    def output_parser(result: PlanControllerOutput, name) -> Any:
        result = AIMessage(content=json.dumps(result.model_dump()), name=name)
        return result

    async def run(self, input_variables: AgentState) -> AIMessage:
        task_input = {
            "task_decomposition": input_variables.task_decomposition.format_as_list(),
            "stm_all_history": input_variables.stm_all_history,
        }
        data = input_variables.model_dump()
        if tracker.images and len(tracker.images) > 0:
            data["img"] = tracker.images[-1]
        data["task_decomposition"] = task_input["task_decomposition"]
        data["stm_all_history"] = task_input["stm_all_history"]
        data["variables_history"] = var_manager.get_variables_summary(last_n=6)
        data["instructions"] = instructions_manager.get_instructions(self.name)
        return await self.chain.ainvoke(data)

    @staticmethod
    def create():
        dyna_model = settings.agent.plan_controller.model
        return PlanControllerAgent(
            prompt_template=load_prompt_simple(
                "./prompts/system.jinja2",
                "./prompts/user.jinja2",
                model_config=dyna_model,
                format_instructions=BaseAgent.get_format_instructions(parser),
            ),
            llm=llm_manager.get_model(dyna_model),
        )
