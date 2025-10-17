import json

from langchain_core.messages import AIMessage
from loguru import logger
from cuga.backend.activity_tracker.tracker import ActivityTracker, Step
from cuga.backend.cuga_graph.nodes.shared.base_agent import create_partial
from cuga.backend.cuga_graph.nodes.shared.base_node import BaseNode
from cuga.backend.cuga_graph.state.agent_state import AgentState
from cuga.backend.cuga_graph.nodes.task_decomposition_planning.task_decomposition_agent.prompts.load_prompt import (
    TaskDecompositionPlan,
    DecomposedTask,
)
from cuga.backend.cuga_graph.nodes.task_decomposition_planning.task_decomposition_agent.task_decomposition_agent import (
    TaskDecompositionAgent,
)
from cuga.config import settings

tracker = ActivityTracker()


class TaskDecompositionNode(BaseNode):
    def __init__(self, task_decomposition_agent: TaskDecompositionAgent):
        super().__init__()
        self.task_decomposition_agent = task_decomposition_agent
        self.node = create_partial(
            TaskDecompositionNode.node_handler,
            agent=self.task_decomposition_agent,
            name=self.task_decomposition_agent.name,
        )

    @staticmethod
    async def node_handler(state: AgentState, agent: TaskDecompositionAgent, name: str) -> AgentState:
        # task1, app_name, web
        # task2, app_name, web
        # Add few shots presenting the 3 types, only api, only web, and hybrid.
        state.sender = name
        # logger.debug(state.api_intent_relevant_apps)
        # logger.debug(state.api_intent_relevant_apps_current)

        if not settings.features.task_decomposition:
            logger.debug("Task decomposition is disabled")
            task_decomposition_plan = TaskDecompositionPlan(
                thoughts="",
                task_decomposition=[
                    DecomposedTask(
                        task=state.input,
                        app=state.api_intent_relevant_apps[0].name,
                        type=state.api_intent_relevant_apps[0].type,
                    )
                ],
            )
            state.task_decomposition = task_decomposition_plan
            state.messages.append(AIMessage(content=task_decomposition_plan.model_dump_json()))
            return state

        result: AIMessage = await agent.run(state)
        result.name = name
        state.messages.append(result)
        state.task_decomposition = TaskDecompositionPlan(**json.loads(result.content))
        if settings.advanced_features.benchmark == "appworld":
            for k in state.task_decomposition.task_decomposition:
                if k.type == "web":
                    k.type = "api"
        logger.debug(state.task_decomposition.model_dump_json(indent=2))
        tracker.collect_step(step=Step(name=name, data=state.task_decomposition.model_dump_json()))
        return state
