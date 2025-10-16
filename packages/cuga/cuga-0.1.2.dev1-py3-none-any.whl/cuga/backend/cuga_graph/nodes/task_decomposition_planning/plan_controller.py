import json
import uuid
from typing import Literal

from langchain_core.messages import AIMessage
from langgraph.types import Command
from loguru import logger
from langchain_core.runnables.config import RunnableConfig
from cuga.backend.activity_tracker.tracker import ActivityTracker, Step
from cuga.backend.tools_env.registry.utils.api_utils import get_apis
from cuga.backend.cuga_graph.nodes.api.variables_manager.manager import VariablesManager
from cuga.backend.cuga_graph.nodes.shared.base_agent import create_partial
from cuga.backend.cuga_graph.nodes.shared.base_node import BaseNode
from cuga.backend.cuga_graph.state.agent_state import AgentState, SubTaskHistory
from cuga.backend.cuga_graph.nodes.task_decomposition_planning.plan_controller_agent.plan_controller_agent import (
    PlanControllerAgent,
)
from cuga.backend.cuga_graph.nodes.task_decomposition_planning.plan_controller_agent.prompts.load_prompt import (
    PlanControllerOutput,
)

tracker = ActivityTracker()
var_manager = VariablesManager()


def find_substring(string_array, target_string):
    """
    Check if any string from string_array is contained within target_string.
    Returns the first matching string found, or None if no matches.

    Args:
        string_array (list): List of strings to search for
        target_string (str): String to search within

    Returns:
        str or None: First matching string found, or None if no matches
    """
    for substring in string_array:
        if substring in target_string:
            return substring
    return None


class PlanControllerNode(BaseNode):
    def __init__(self, plan_controller_agent: PlanControllerAgent):
        super().__init__()
        self.plan_controller_agent = plan_controller_agent
        self.node = create_partial(
            PlanControllerNode.node_handler,
            agent=self.plan_controller_agent,
            name=self.plan_controller_agent.name,
        )

    @staticmethod
    async def node_handler(
        state: AgentState, agent: PlanControllerAgent, name: str, config: RunnableConfig
    ) -> Command[
        Literal[
            "BrowserPlannerAgent",
            "APIPlannerAgent",
            "FinalAnswerAgent",
            "PlanControllerAgent",
            "InterruptToolNode",
        ]
    ]:
        ignore_controller = (
            len(state.task_decomposition.task_decomposition) == 1
            or len(state.task_decomposition.task_decomposition) == 0
        )
        # API Agent must return list of natural language progress, summarize the plan relative to the output of code
        # Examples for 3 modes
        # Final answer ifs

        if state.sender == "TaskDecompositionAgent":
            if ignore_controller:
                state.sub_task = state.task_decomposition.task_decomposition[0].task
                state.sub_task_app = state.task_decomposition.task_decomposition[0].app
                state.sub_task_type = state.task_decomposition.task_decomposition[0].type
                if state.sub_task_type == "api":
                    state.api_intent_relevant_apps_current = [
                        app
                        for app in state.api_intent_relevant_apps
                        if app.name == state.task_decomposition.task_decomposition[0].app
                    ]
                    if state.api_shortlister_all_filtered_apis is None:
                        state.api_shortlister_all_filtered_apis = {}
                    state.api_shortlister_all_filtered_apis[
                        state.api_intent_relevant_apps_current[0].name
                    ] = await get_apis(state.api_intent_relevant_apps_current[0].name)
                state.messages.append(
                    AIMessage(
                        content=PlanControllerOutput(
                            thoughts=[],
                            next_subtask=state.sub_task,
                            subtasks_progress=[],
                            conclude_task=False,
                            conclude_final_answer="",
                            next_subtask_app=state.sub_task_app,
                            next_subtask_type=state.sub_task_type,
                        ).model_dump_json()
                    )
                )
                if state.sub_task_type == 'web':
                    return Command(update=state.model_dump(), goto="BrowserPlannerAgent")
                else:
                    state.api_planner_history = []
                    return Command(update=state.model_dump(), goto="APIPlannerAgent")
        state.sender = name

        # Else is loop return
        logger.debug("returning from planner or api agent")
        if ignore_controller and state.last_planner_answer:
            state.messages.append(
                AIMessage(
                    content=PlanControllerOutput(
                        thoughts=[],
                        next_subtask=state.sub_task,
                        subtasks_progress=[],
                        conclude_task=True,
                        conclude_final_answer=state.last_planner_answer or "",
                        next_subtask_app=state.sub_task_app,
                        next_subtask_type=state.sub_task_type,
                    ).model_dump_json()
                )
            )
            logger.debug("ignore controller use last planner or api answer")
            return Command(update=state.model_dump(), goto="FinalAnswerAgent")

        result: AIMessage = await agent.run(state)
        plan_controller_output = PlanControllerOutput(**json.loads(result.content))
        tracker.collect_step(step=Step(name=name, data=plan_controller_output.model_dump_json()))
        state.messages.append(result)
        if plan_controller_output.conclude_task and not plan_controller_output.next_subtask:
            state.last_planner_answer = plan_controller_output.conclude_final_answer
            return Command(update=state.model_dump(), goto="FinalAnswerAgent")
        else:
            if "open application" in plan_controller_output.next_subtask:
                app = find_substring(
                    ["reddit", "map", "wikipedia", "gitlab", "shopping", "shopping_admin"],
                    plan_controller_output.next_subtask.lower(),
                )
                state.tool_call = {"name": "open_app", "args": {"app_name": app}, "id": str(uuid.uuid4())}
                state.stm_all_history.append(
                    SubTaskHistory(
                        sub_task=plan_controller_output.next_subtask,
                        steps=[f"Navigated to {app}"],
                        final_answer="The application opened successfully",
                    )
                )
                return Command(update=state.model_dump(), goto="InterruptToolNode")
            # Updates current sub task for UI, API Planners
            state.sub_task = plan_controller_output.next_subtask
            state.sub_task_app = plan_controller_output.next_subtask_app
            state.sub_task_type = plan_controller_output.next_subtask_type
            if plan_controller_output.next_subtask_type == "api":
                state.api_intent_relevant_apps_current = [
                    app
                    for app in state.api_intent_relevant_apps
                    if app.name == plan_controller_output.next_subtask_app
                ]
                state.api_shortlister_all_filtered_apis = {}
                state.api_shortlister_all_filtered_apis[
                    state.api_intent_relevant_apps_current[0].name
                ] = await get_apis(state.api_intent_relevant_apps_current[0].name)

            state.previous_steps = []
            if state.sites and len(state.sites) > 0:
                pass
            else:
                state.stm_steps_history = []

            if plan_controller_output.next_subtask_type == 'web':
                return Command(update=state.model_dump(), goto="BrowserPlannerAgent")
            else:
                state.api_planner_history = []
                return Command(update=state.model_dump(), goto="APIPlannerAgent")
