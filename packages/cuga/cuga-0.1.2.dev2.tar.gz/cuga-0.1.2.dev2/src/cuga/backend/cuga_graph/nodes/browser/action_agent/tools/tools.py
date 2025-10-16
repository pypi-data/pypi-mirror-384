import inspect
from typing import Dict, List, Literal, Optional

from langchain_core.messages import ToolCall
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, tool
from cuga.backend.browser_env.tools.providers import BrowserToolImplProvider
from cuga.backend.cuga_graph.nodes.browser.action_agent.tools.alert import Alert


# ----------------------------------------------------------------------------
# Original public API (tool functions)
# ----------------------------------------------------------------------------


def get_params_and_values_except(func, exclude_param, *args, **kwargs):
    # Retrieve the signature of the function
    sig = inspect.signature(func)
    # Bind the provided arguments to the function's parameters
    bound_args = sig.bind(*args, **kwargs)
    # Apply default values for missing arguments
    bound_args.apply_defaults()
    # Create a dictionary of parameter names and their values, excluding the specified one
    params_and_values = {k: v for k, v in bound_args.arguments.items() if k != exclude_param}
    return params_and_values


# ----------------------------------------------------------
# Delegation helper – choose implementation set at import time
# ----------------------------------------------------------


def _retrieve_impl(config: RunnableConfig, tool_name: str):
    impl: BrowserToolImplProvider = config['configurable']['tool_impl']
    tool_impl = impl.implementations()[tool_name]
    return tool_impl


@tool
async def go_back(config: RunnableConfig | None = None):
    """
    Go back to previous page.

    Examples:
    """
    _go_back = _retrieve_impl(config, 'go_back')
    await _go_back(config)


@tool
async def open_app(
    app_name: Literal[
        "wikipedia",
        "map",
        "reddit",
        "gitlab",
        "shopping",
        "shopping_admin",
    ],
    config: RunnableConfig = None,
):
    """
    Open an application

    Examples:
        open_app('reddit')
    """
    _open_app = _retrieve_impl(config, 'open_app')
    return await _open_app(app_name=app_name, config=config)


@tool
async def click(
    bid: str,
    button: Literal["left", "middle", "right"] = "left",
    modifiers: Optional[List[Literal["Alt", "Control", "Meta", "Shift"]]] = [],
    config: RunnableConfig = None,
) -> Optional[Alert]:
    """
    Click an element.

    Examples:
        click('a51')
        click('b22', button="right")
        click('48', button="middle", modifiers=["Shift"])
    """
    _click = _retrieve_impl(config, 'click')
    return await _click(bid=bid, button=button, modifiers=modifiers or [], config=config)


@tool
async def select_option(bid: str, options: str | list[str], config: RunnableConfig = None) -> Optional[Alert]:
    """
    Select one or more options in a dropdown – delegate to implementation.
    """
    _select_option = _retrieve_impl(config, 'select_option')
    return await _select_option(bid=bid, options=options, config=config)


@tool
async def type(bid: str, value: str, press_enter: bool, config: RunnableConfig) -> Optional[Alert]:
    """
    Fill out a form field. It focuses the element and triggers an input event with the entered text.
    It works for <input>, <textarea> and [contenteditable] elements.
    use press_enter true when the search input field requires pressing enter after filling the element.
    Examples:
        type('237', 'example value')
        type('45', "multi-line\\nexample")
        type('a12', "example with \\"quotes\\"")
        type('a12', "example search value", True)
    """
    _type = _retrieve_impl(config, 'type')
    return await _type(bid=bid, value=value, press_enter=press_enter, config=config)


def format_tools(tools: List[ToolCall]):
    res = []
    for t in tools:
        desc = "{}({})".format(t.get("name"), ", ".join(f"{k}={v}" for k, v in t.get("args").items()))
        res.append(desc)
    return "\n".join(res)


@tool
async def memorize(information: str):
    """
    Memorize key information for later!

    Examples:
        memorize('Order 1 cost is 24 dollars')
        memorize('Previous route is 34km away')
    """
    return information


@tool
def human_in_the_loop(state, message: str) -> str:
    """
    Facilitates communication between the agent and the user, allowing the agent to seek input or permission
    based on environment policies or complex decision-making scenarios.

    Parameters:
    - text (str): The content of the message to be sent to the user

    Guidelines:
    1. Use this function when environment policies require user confirmation before taking certain actions.
    2. Construct clear, concise messages that explain the situation and request specific input from the user.
    3. Respect organizational and user-defined policies when deciding to initiate communication.

    Examples:
        human_in_the_loop("I'm about to create a new project. Do you give permission to proceed? (Yes/No)")
        human_in_the_loop("I'm ready to invite a new member. Please confirm if I should continue. (Confirm/Cancel)")

    Note:
    - This function should be used judiciously, only when required by policies or for critical decisions.
    - This function helps maintain compliance with organizational rules and user preferences.
    """
    pass


@tool
def scroll(state) -> str:
    """
    Scroll the page
    """
    page = state.get("page")
    scroll_args = state["prediction"]["args"]
    # if scroll_args is None or len(scroll_args) != 1:
    #     return "Failed to scroll due to incorrect arguments."
    direction = scroll_args[0]
    if direction not in ["up", "down"]:
        return f"Failed to scroll due to incorrect direction: {direction}."
    page.scroll(direction)
    return f'Scrolled {direction}'


# ----------------------------------------------------------------------------
# Setup Tools Function (placed at end to avoid name collision with type function)
# ----------------------------------------------------------------------------


def setup_tools() -> Dict[str, BaseTool]:
    """
    Set up and return all available tools for the action agent.
    This function is placed at the end of the file to ensure all tool functions
    are defined before being referenced, avoiding the name collision with Python's
    built-in 'type' function.
    """
    return {
        "click": click,
        "type": type,  # Now refers to the @tool decorated function, not builtin type
        "go_back": go_back,
        "select_option": select_option,
    }
