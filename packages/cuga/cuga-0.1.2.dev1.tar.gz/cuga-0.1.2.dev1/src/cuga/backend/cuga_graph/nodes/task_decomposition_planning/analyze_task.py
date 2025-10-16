import json
from typing import Literal, List, Optional, Tuple

import httpx
from pydantic import BaseModel
from cuga.backend.activity_tracker.tracker import ActivityTracker, Step
from cuga.backend.tools_env.registry.utils.types import AppDefinition
from cuga.backend.cuga_graph.nodes.shared.base_agent import create_partial
from cuga.backend.cuga_graph.nodes.shared.base_node import BaseNode
from cuga.backend.cuga_graph.state.agent_state import AgentState, AnalyzeTaskAppsOutput
from cuga.backend.cuga_graph.nodes.task_decomposition_planning.task_analyzer_agent.task_analyzer_agent import (
    TaskAnalyzerAgent,
    AnalyzeTaskOutput,
)
from cuga.backend.cuga_graph.nodes.task_decomposition_planning.task_analyzer_agent.tasks.app_matcher import (
    AppMatch,
)
from cuga.config import settings
from langgraph.types import Command
from loguru import logger
from cuga.backend.tools_env.registry.utils.api_utils import get_apps
from langchain_core.messages import AIMessage
from cuga.backend.cuga_graph.nodes.api.variables_manager.manager import VariablesManager

var_manager = VariablesManager()

tracker = ActivityTracker()


class TaskAnalyzer(BaseNode):
    def __init__(self, task_analyzer_agent: TaskAnalyzerAgent):
        super().__init__()
        self.name = task_analyzer_agent.name
        self.agent = task_analyzer_agent
        self.node = create_partial(
            TaskAnalyzer.node_handler,
            agent=self.agent,
            name=self.name,
        )

    @staticmethod
    def find_by_attribute(items: List[BaseModel], attr_name: str, attr_value) -> Optional[BaseModel]:
        """Find a Pydantic object by attribute value."""
        try:
            return next(item for item in items if getattr(item, attr_name) == attr_value)
        except StopIteration:
            return None

    @staticmethod
    async def match_apps(
        agent: TaskAnalyzerAgent,
        intent: str,
        mode: Literal['api', 'web', 'hybrid'],
        web_app_name: Optional[str] = "N/A",
        web_description: Optional[str] = "N/A",
    ) -> Tuple[Optional[List[AnalyzeTaskAppsOutput]], AppMatch]:
        """
        Match apps based on user intent and specified mode.

        Args:
            state: Current agent state
            intent: User intent to match against apps
            mode: Operation mode - 'api', 'web', or 'hybrid'

        Returns:
            Matched applications based on mode and intent
        """
        # Common initialization
        if mode == 'api' or mode == 'hybrid':
            apps = await get_apps()
            if mode == 'api' and len(apps) == 1:
                return [
                    AnalyzeTaskAppsOutput(
                        name=apps[0].name, description=apps[0].description, url=apps[0].url, type='api'
                    )
                ], AppMatch(relevant_apps=[apps[0].name], thoughts=[])
            if mode == 'hybrid' and len(apps) == 1:
                return [
                    AnalyzeTaskAppsOutput(
                        name=apps[0].name, description=apps[0].description, url=apps[0].url, type='api'
                    ),
                    AnalyzeTaskAppsOutput(name=web_app_name, description=web_description, url="", type='web'),
                ], AppMatch(relevant_apps=[apps[0].name, web_app_name], thoughts=[])
            logger.debug(f"All available apps: {[p for p in apps]}")
            if len(settings.features.forced_apps) == 0:
                res: AppMatch = await agent.match_apps_task.ainvoke(
                    input={
                        "inp": {
                            "intent": intent,
                            "available_apps": [{"name": p.name, "description": p.description} for p in apps],
                        }
                    }
                )
            else:
                res = AppMatch(thoughts=[], relevant_apps=settings.features.forced_apps)
            logger.debug(f"Matched apps: {res.relevant_apps}")
            result = []
            for p in res.relevant_apps:
                app: AppDefinition = TaskAnalyzer.find_by_attribute(apps, 'name', p)
                result.append(
                    AnalyzeTaskAppsOutput(name=p, description=app.description, url=app.url, type='api')
                )
            if mode == 'hybrid':
                result.append(
                    AnalyzeTaskAppsOutput(name=web_app_name, description=web_description, url="", type='web')
                )
            return result, res
        elif mode == 'web':
            return [
                AnalyzeTaskAppsOutput(name=web_app_name, description=web_description, url="", type='web')
            ], AppMatch(relevant_apps=[web_app_name], thoughts=[])

    @staticmethod
    async def call_authenticate_apps(apps: List[str]):
        payload = {"apps": apps}  # JSON body
        async with httpx.AsyncClient() as client:
            from cuga.config import settings

            response = await client.post(  # Changed from GET to POST
                f"http://127.0.0.1:{settings.server_ports.registry}/api/authenticate_apps",
                json=payload,  # Send as JSON body
            )
            print(response.status_code)
            print(response.json())

    @staticmethod
    async def node_handler(
        state: AgentState, agent: TaskAnalyzerAgent, name: str
    ) -> Command[Literal['TaskDecompositionAgent']]:
        if not settings.features.chat:
            var_manager.reset()
        if not state.sender or state.sender == "ChatAgent":
            state.api_intent_relevant_apps, app_matches = await TaskAnalyzer.match_apps(
                agent,
                state.input,
                settings.advanced_features.mode,
                state.current_app,
                state.current_app_description,
            )
            logger.debug(f"all apps are: {state.api_intent_relevant_apps}")
            data_representation = json.dumps([p.model_dump() for p in state.api_intent_relevant_apps])
            try:
                if settings.advanced_features.benchmark == "appworld":
                    await TaskAnalyzer.call_authenticate_apps(app_matches.relevant_apps)
            except Exception as e:
                logger.warning("Failed to authenticate upfront all apps")
                logger.warning(e)
            state.messages.append(AIMessage(content=data_representation))
            tracker.collect_step(Step(name=name, data=data_representation))
            res = await agent.run(state)
            task_analyzer_output = AnalyzeTaskOutput(**json.loads(res.content))

            state.task_analyzer_output = task_analyzer_output
            if state.task_analyzer_output.paraphrased_intent:
                state.input = state.task_analyzer_output.paraphrased_intent
            if (
                settings.advanced_features.use_location_resolver
                and state.task_analyzer_output.attrs.requires_location_search
                and state.current_app == "map"
                and (state.sites and len(state.sites) == 1)
            ):
                logger.debug("Intent has implicit locations")
                return Command(update=state.model_dump(), goto="LocationResolver")
            return Command(update=state.model_dump(), goto="TaskDecompositionAgent")
        # We arrived from LocationResolver
        if state.sender == "LocationResolver" and state.task_analyzer_output.resolved_intent:
            state.input = state.task_analyzer_output.resolved_intent
            return Command(update=state.model_dump(), goto="TaskDecompositionAgent")
        return Command(update=state.model_dump(), goto="TaskDecompositionAgent")
