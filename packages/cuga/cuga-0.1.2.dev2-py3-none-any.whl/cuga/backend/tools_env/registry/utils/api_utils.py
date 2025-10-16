import json
from typing import List

import aiohttp

from cuga.backend.tools_env.registry.utils.types import AppDefinition
from cuga.config import settings
from loguru import logger
from cuga.backend.activity_tracker.tracker import ActivityTracker

tracker = ActivityTracker()


async def get_apis(app_name: str):
    """
    Execute an asynchronous GET request to retrieve Petstore APIs from localhost:8001
    and return the result as formatted JSON.

    Returns:
        dict: The JSON response data as a Python dictionary

    Raises:
        Exception: If the request fails or the response is not valid JSON
    """
    all_tools = {}

    # Get tools from tracker
    try:
        logger.debug("calling get_apis")
        tools = tracker.get_tools_by_server(app_name)
        if not settings.advanced_features.registry:
            logger.debug("Registry is not enabled, using external tools")
            return tools
        if tools:
            return tools
    except Exception as e:
        logger.warning(e)

    # Get tools from API
    url = f'http://127.0.0.1:{settings.server_ports.registry}/applications/{app_name}/apis?include_response_schema=true'
    headers = {'accept': 'application/json'}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                # Check if the request was successful
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Request failed with status {response.status}: {error_text}")

                # Parse JSON response
                json_data = await response.json()
                if json_data:
                    all_tools.update(json_data)
                return all_tools

    except Exception as e:
        if len(all_tools) > 0:
            logger.warning("registry is not running, using external apps")
            return all_tools
        else:
            logger.error("Error while calling registry to get apps")
            raise e


async def get_apps() -> List[AppDefinition]:
    """
    Execute an asynchronous GET request to retrieve Petstore APIs from localhost:8001
    and return the result as formatted JSON.

    Returns:
        dict: The JSON response data as a Python dictionary

    Raises:
        Exception: If the request fails or the response is not valid JSON
    """
    logger.debug("Calling get apps")

    url = f'http://127.0.0.1:{settings.server_ports.registry}/applications'
    headers = {'accept': 'application/json'}
    external_apps = tracker.apps
    if not settings.advanced_features.registry:
        logger.debug("Registry is not enabled, using external apps")
        return external_apps
    logger.debug(f"External apps are {external_apps}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                logger.debug("Recieved responses")
                # Check if the request was successful
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Request failed with status {response.status}: {error_text}")

                # Parse JSON response
                json_data = await response.json()
                result = [AppDefinition(**p) for p in json_data]
                for e in external_apps:
                    result.append(e)

                return result
    except Exception as e:
        if len(external_apps) > 0:
            logger.warning("registry is not running, using external apps")
            return external_apps
        else:
            logger.error("Error while calling registry to get apps")
            raise e


def read_json_file(file_path):
    """
    Read and parse a JSON file from the specified path.

    Args:
        file_path (str): Path to the JSON file

    Returns:
        dict: The parsed JSON data
    """
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {file_path}")
    except Exception as e:
        print(f"Error reading file: {e}")
