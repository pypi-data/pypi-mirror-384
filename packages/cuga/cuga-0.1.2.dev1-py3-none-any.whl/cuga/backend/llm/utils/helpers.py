from datetime import datetime
import os.path

from langchain_core.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
)
from langchain_core.prompts.image import ImagePromptTemplate

from cuga.config import settings

import inspect

from pathlib import Path


def get_caller_directory_path():
    """
    Get the absolute directory path of the caller.
    Production-ready with proper error handling.

    Returns:
        str: Absolute directory path of caller file, or None if unable to determine
    """
    try:
        # Get the caller's frame (skip current function)
        frame = inspect.currentframe()
        if frame is None:
            return None

        caller_frame = frame.f_back
        if caller_frame is None:
            return None
        caller_frame = caller_frame.f_back
        if caller_frame is None:
            return None
        # Get the filename
        filename = caller_frame.f_code.co_filename

        # Convert to absolute path and get parent directory
        abs_path = Path(filename).resolve()
        directory_path = abs_path.parent

        return str(directory_path)

    except (AttributeError, OSError, RuntimeError):
        # Handle cases where frame inspection fails
        return None
    finally:
        # Clean up frame references to prevent memory leaks
        del frame
        if 'caller_frame' in locals():
            del caller_frame


def load_prompt_chat(system_path, relative_to_caller=True):
    if relative_to_caller:
        parent_dir = get_caller_directory_path()
        system_path = os.path.join(parent_dir, system_path)

    pmt_system = PromptTemplate.from_file(
        system_path,
        input_variables=["variables_history"],
        template_format="jinja2",
    )
    prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate(prompt=pmt_system),
            MessagesPlaceholder(variable_name="conversation", optional=True),
        ]
    )
    return prompt


def load_prompt_with_image(
    system_path, user_path, model_config=None, format_instructions=None, relative_to_caller=True
):
    if relative_to_caller:
        parent_dir = get_caller_directory_path()
        user_path = os.path.join(parent_dir, user_path)
        system_path = os.path.join(parent_dir, system_path)

    # here = pathlib.Path(__file__).parent.parent.parent
    # sitemap_path = here / "knowledge" / "shopping_admin" / "sitemap.txt"

    pmt_system = PromptTemplate.from_file(
        system_path,
        partial_variables={
            "format_instructions": (
                format_instructions if model_config and model_config.enable_format else ""
            ),
            "current_date": datetime.now().strftime("%m/%d/%Y"),
            # "sitemap": open("cuga/backend/knowledge/shopping_admin/sitemap.txt").read(),
        },
        template_format="jinja2",
    )

    pmt_user = PromptTemplate.from_file(user_path, template_format="jinja2")
    pmt_image = ImagePromptTemplate(input_variables=['img'], template={"url": '{img}'})
    pmt_with_vision = [pmt_image, pmt_user] if settings.advanced_features.use_vision else pmt_user
    prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate(prompt=pmt_system),
            HumanMessagePromptTemplate(prompt=pmt_with_vision),
        ]
    )
    return prompt


def load_one_prompt(pmt_path, relative_to_caller=True) -> PromptTemplate:
    if relative_to_caller:
        parent_dir = get_caller_directory_path()
        pmt_path = os.path.join(parent_dir, pmt_path)
    pmt_system = PromptTemplate.from_file(pmt_path, template_format="jinja2")
    return pmt_system


def load_prompt_simple(
    system_path, user_path, model_config=None, format_instructions=None, relative_to_caller=True
):
    if relative_to_caller:
        parent_dir = get_caller_directory_path()
        user_path = os.path.join(parent_dir, user_path)
        system_path = os.path.join(parent_dir, system_path)

    pmt_system = PromptTemplate.from_file(
        system_path,
        template_format="jinja2",
        partial_variables={
            "format_instructions": format_instructions if model_config and model_config.enable_format else "",
        },
        encoding='utf-8',
    )
    pmt_user = PromptTemplate.from_file(user_path, template_format="jinja2")
    prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate(prompt=pmt_system),
            HumanMessagePromptTemplate(prompt=pmt_user),
        ]
    )
    return prompt
