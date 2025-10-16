from langchain_core.runnables import Runnable
from cuga.backend.cuga_graph.nodes.shared.base_agent import BaseAgent
from cuga.backend.llm.models import LLMManager
from cuga.backend.llm.utils.helpers import load_prompt_simple

llm_manager = LLMManager()


def summarize_steps(llm, enable_format=False) -> Runnable:
    prompt_template = load_prompt_simple(
        "./prompts/summary_system.jinja2",
        "./prompts/summary_user.jinja2",
    )
    return BaseAgent.get_chain(prompt_template, llm, wx_json_mode="no_format")
