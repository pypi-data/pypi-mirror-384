import functools
import json
from typing import Literal, Dict, Callable

from langgraph.types import Command

from cuga.backend.activity_tracker.tracker import ActivityTracker, Step
from cuga.backend.cuga_graph.nodes.api.variables_manager.manager import VariablesManager
from cuga.backend.cuga_graph.nodes.answer.final_answer_agent.final_answer_agent import FinalAnswerAgent
from cuga.backend.cuga_graph.nodes.answer.final_answer_agent.prompts.load_prompt import FinalAnswerOutput
from cuga.backend.cuga_graph.nodes.shared.base_node import BaseNode
from cuga.backend.cuga_graph.nodes.human_in_the_loop.followup_model import (
    create_save_reuse_action,
    create_get_more_utterances,
)
from cuga.backend.cuga_graph.state.agent_state import AgentState
from cuga.config import settings
from cuga.backend.cuga_graph.utils.nodes_names import NodeNames, ActionIds, MessagePrefixes

var_manager = VariablesManager()
tracker = ActivityTracker()

# Feature flag for human-in-the-loop functionality
ENABLE_SAVE_REUSE = settings.features.save_reuse


class HumanInTheLoopHandler:
    """Simple handler for human-in-the-loop interactions"""

    def __init__(self):
        self._action_handlers: Dict[str, Callable] = {
            ActionIds.SAVE_REUSE: self._handle_save_reuse,
            ActionIds.SAVE_REUSE_INTENT: self._handle_save_reuse_intent,
        }

    def handle_human_response(self, state: AgentState, node_name: str) -> Command:
        """Handle any human response based on action_id"""
        action_id = state.hitl_response.action_id

        if action_id in self._action_handlers:
            return self._action_handlers[action_id](state, node_name)

        # Default fallback
        return Command(update=state.model_dump(), goto=NodeNames.END)

    def add_action_handler(self, action_id: str, handler: Callable):
        """Add a custom action handler"""
        self._action_handlers[action_id] = handler

    def _handle_save_reuse(self, state: AgentState, node_name: str) -> Command:
        """Handle save/reuse action - get more utterances"""
        state.hitl_action = create_get_more_utterances()
        state.sender = node_name
        return Command(update=state.model_dump(), goto=NodeNames.SUGGEST_HUMAN_ACTIONS)

    def _handle_save_reuse_intent(self, state: AgentState, node_name: str) -> Command:
        """Handle save/reuse intent - go to reuse agent"""
        state.sender = node_name
        return Command(update=state.model_dump(), goto=NodeNames.REUSE_AGENT)


class FinalAnswerNode(BaseNode):
    def __init__(self, final_answer_agent: FinalAnswerAgent):
        super().__init__()
        self.final_answer_agent = final_answer_agent
        self.hitl_handler = HumanInTheLoopHandler()

        self.node = functools.partial(
            FinalAnswerNode.node_handler,
            agent=self.final_answer_agent,
            name=self.final_answer_agent.name,
            hitl_handler=self.hitl_handler,
        )

    @staticmethod
    async def node_handler(
        state: AgentState, agent: FinalAnswerAgent, name: str, hitl_handler: HumanInTheLoopHandler
    ) -> Command[Literal["__end__", "SuggestHumanActions", "ReuseAgent"]]:
        # Handle human responses (only if HITL is enabled)
        if ENABLE_SAVE_REUSE and state.sender == NodeNames.WAIT_FOR_RESPONSE:
            return hitl_handler.handle_human_response(state, name)

        # Handle direct chat calls (no processing needed)
        if state.sender == NodeNames.CHAT_AGENT:
            state.sender = name
            state.final_answer = state.chat_messages[-1].content
            return Command(update=state.model_dump(), goto=NodeNames.END)

        # Main processing: generate final answer
        await FinalAnswerNode._generate_final_answer(state, agent, name)

        # Route based on sender (only suggest human actions if HITL is enabled)
        if ENABLE_SAVE_REUSE and state.sender == NodeNames.PLAN_CONTROLLER_AGENT:
            state.hitl_action = create_save_reuse_action()
            state.sender = name
            return Command(update=state.model_dump(), goto=NodeNames.SUGGEST_HUMAN_ACTIONS)
        else:
            return Command(update=state.model_dump(), goto=NodeNames.END)

    @staticmethod
    async def _generate_final_answer(state: AgentState, agent: FinalAnswerAgent, name: str):
        """Generate and process the final answer"""
        # Run the agent
        response = await agent.run(state)
        state.messages.append(response)

        # Parse and process output
        final_answer_output = FinalAnswerOutput(**json.loads(response.content))

        # Add to chat if enabled
        if settings.features.chat:
            chat_message = f"{MessagePrefixes.ANSWER_PREFIX}{final_answer_output.final_answer}"
            state.append_to_last_chat_message(chat_message)

        # Track the step
        tracker.collect_step(Step(name=name, data=final_answer_output.model_dump_json()))

        # Replace variables and update state
        final_answer_output.final_answer = var_manager.replace_variables_placeholders(
            final_answer_output.final_answer
        )
        state.final_answer = final_answer_output.final_answer
