import requests
from typing import Dict, Any, List
import json
import aiohttp
from cuga.config import PACKAGE_ROOT
import os

from mcp.types import TextContent

try:
    from fastmcp import Client as FastMCPClient
except ImportError:
    FastMCPClient = None

from cuga.backend.tools_env.registry.config.config_loader import Auth
from cuga.backend.tools_env.registry.config.config_loader import ServiceConfig, Service
from cuga.backend.tools_env.registry.mcp_manager.openapi_parser import SimpleOpenAPIParser
from cuga.backend.tools_env.registry.mcp_manager.adapter import new_mcp_from_custom_parser
import threading
from collections import defaultdict
from urllib.parse import urlparse

from cuga.backend.tools_env.registry.mcp_manager.openapi_parser_v0 import OpenAPITransformer
from cuga.backend.tools_env.registry.mcp_manager.response_schema import extract_response_schema
import yaml
from cuga.backend.utils.consts import ServiceType, LOCAL_ORCHESTRATE_URL, LOCAL_TRM_URL


class MCPManager:
    def __init__(self, config: Dict[str, ServiceConfig]):
        self.schema_urls: Dict[str, ServiceConfig] = config
        self.servers = {}
        self.threads = {}
        self.tools_by_server = defaultdict(list)
        self.server_by_tool = {}
        self.server_ports = {}
        self.auth_config = {}
        self.schemas = {}
        self.trm_tools = {}
        self.mcp_clients = {}  # Store MCP client connections
        self.fastmcp_client = None  # FastMCP client for standard MCP servers

    @staticmethod
    def _get_response_schema_from_tool(
        tool_dict: dict, openapi_spec: Dict[str, Any], prefix: str
    ) -> Dict[str, Any]:
        """
        Given a tool_dict and OpenAPI spec, extract and resolve the response schema.

        Args:
            tool_dict: Tool definition as provided to a language model
            openapi_spec: OpenAPI specification as a dictionary

        Returns:
                Fully resolved response schema
        """

        def _extract_operation_id_from_tool(tool_name: str, prefix: str) -> str:
            """
            Recover the original operationId from a sanitized tool name.
            this is based on the tool naming convention in adapter.py
            """
            if tool_name.startswith(prefix.lower() + "_"):
                return tool_name[len(prefix) + 1 :]  # Remove prefix and underscore
            return tool_name

        operation_id = _extract_operation_id_from_tool(tool_dict['name'], prefix)
        return extract_response_schema(openapi_spec, operation_id)

    @staticmethod
    def _extract_base_url(full_url: str):
        parsed = urlparse(full_url)

        # Base URL: scheme://netloc
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        return base_url

    @staticmethod
    def _get_free_port():
        import socket
        import random

        for _ in range(100):  # Try up to 100 times
            port = random.randint(49152, 65535)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('', port))
                    return port
                except OSError:
                    continue
        raise RuntimeError("No free port found in safe range.")

    @staticmethod
    def _fetch_and_parse_schema(url_or_path):
        parsed = urlparse(url_or_path)
        is_url = parsed.scheme in ('http', 'https')
        if is_url:
            # Handle HTTP/HTTPS URLs
            r = requests.get(url_or_path.split('&')[0])
            r.raise_for_status()
            ct = r.headers.get("Content-Type", "").lower()
            raw = r.text
        else:
            # Handle local file paths
            if os.path.isabs(url_or_path):
                file_path = url_or_path
            else:
                file_path = os.path.join(PACKAGE_ROOT, url_or_path)

            with open(file_path, 'r', encoding='utf-8') as f:
                raw = f.read()
            # Determine content type from file extension
            ct = 'json' if file_path.lower().endswith('.json') else 'yaml'

        # Parse based on content type
        if 'json' in ct:
            parser = SimpleOpenAPIParser.from_json(raw)
            schema_data = json.loads(raw)
        else:
            parser = SimpleOpenAPIParser.from_yaml(raw)
            schema_data = yaml.safe_load(raw)

        return schema_data, parser, is_url

    def _create_mcp_server(self, base_url, parser, name):
        return new_mcp_from_custom_parser(base_url, parser, name, self.schema_urls)

    def _remove_parameter_from_body_schema(
        self, body_schema: Dict[str, Any], parameter_name: str
    ) -> Dict[str, Any]:
        """
        Remove a specific parameter from the request body schema.

        Args:
            body_schema: The request body schema
            parameter_name: Name of the parameter to remove

        Returns:
            Modified body schema with the parameter removed
        """
        if not body_schema or not isinstance(body_schema, dict):
            return body_schema

        modified_schema = body_schema.copy()

        # Handle schema with properties (typical JSON schema structure)
        if 'properties' in modified_schema and isinstance(modified_schema['properties'], dict):
            properties = modified_schema['properties'].copy()
            if parameter_name in properties:
                del properties[parameter_name]
                modified_schema['properties'] = properties

                # Also remove from required array if present
                if 'required' in modified_schema and isinstance(modified_schema['required'], list):
                    required = [req for req in modified_schema['required'] if req != parameter_name]
                    modified_schema['required'] = required

        # Handle allOf, anyOf, oneOf structures
        for schema_type in ['allOf', 'anyOf', 'oneOf']:
            if schema_type in modified_schema and isinstance(modified_schema[schema_type], list):
                modified_schemas = []
                for sub_schema in modified_schema[schema_type]:
                    modified_sub_schema = self._remove_parameter_from_body_schema(sub_schema, parameter_name)
                    modified_schemas.append(modified_sub_schema)
                modified_schema[schema_type] = modified_schemas

        return modified_schema

    from typing import Dict

    def _filter_and_override_schema(
        self, schema_data: Dict[str, Any], config: ServiceConfig
    ) -> Dict[str, Any]:
        """
        Filter the OpenAPI schema to include only specified operations and override descriptions, request body schemas, and query parameters.

        Args:
            schema_data: The original OpenAPI schema
            config: ServiceConfig containing include list and api_overrides

        Returns:
            Modified schema with filtered operations, overridden descriptions, modified request body schemas, and filtered query parameters
        """
        if not config.include and not config.api_overrides:
            return schema_data

        # Create a copy of the schema to modify
        modified_schema = schema_data.copy()

        # Filter operations if include list is provided
        if config.include:
            if 'paths' in modified_schema:
                filtered_paths = {}
                for path, path_item in modified_schema['paths'].items():
                    filtered_path_item = {}
                    for method, operation in path_item.items():
                        if method.lower() in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                            operation_id = operation.get('operationId')
                            if operation_id and operation_id in config.include:
                                filtered_path_item[method] = operation
                        else:
                            # Keep non-operation items (like parameters, servers, etc.)
                            filtered_path_item[method] = operation

                    if filtered_path_item:
                        filtered_paths[path] = filtered_path_item

                modified_schema['paths'] = filtered_paths

        # Override descriptions if api_overrides is provided
        if config.api_overrides:
            override_map = {override.operation_id: override for override in config.api_overrides}

            if 'paths' in modified_schema:
                for path, path_item in modified_schema['paths'].items():
                    for method, operation in path_item.items():
                        if method.lower() in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                            operation_id = operation.get('operationId')
                            if operation_id and operation_id in override_map:
                                override = override_map[operation_id]
                                if override.description is not None:
                                    operation['description'] = override.description

        # Override request body schemas and query parameters if api_overrides contains them
        if config.api_overrides:
            # Create maps for both body and query parameter overrides
            body_override_map = {}
            query_override_map = {}

            for override in config.api_overrides:
                if override.drop_request_body_parameters:
                    body_override_map[override.operation_id] = override.drop_request_body_parameters
                if override.drop_query_parameters:
                    query_override_map[override.operation_id] = override.drop_query_parameters

            if (body_override_map or query_override_map) and 'paths' in modified_schema:
                for path, path_item in modified_schema['paths'].items():
                    for method, operation in path_item.items():
                        if method.lower() in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                            operation_id = operation.get('operationId')
                            if not operation_id:
                                continue

                            # Handle request body parameter removal
                            if operation_id in body_override_map:
                                if 'requestBody' in operation:
                                    request_body = operation['requestBody']
                                    if 'content' in request_body:
                                        for content_type, content_schema in request_body['content'].items():
                                            if 'schema' in content_schema:
                                                schema_ref = content_schema['schema']

                                                # Handle $ref schemas by resolving them first
                                                if '$ref' in schema_ref:
                                                    # Extract the reference path (e.g., "#/components/schemas/UserRequest")
                                                    ref_path = schema_ref['$ref']
                                                    if ref_path.startswith('#/'):
                                                        # Navigate to the referenced schema in the OpenAPI spec
                                                        ref_parts = ref_path[2:].split(
                                                            '/'
                                                        )  # Remove '#/' and split
                                                        resolved_schema = modified_schema
                                                        for part in ref_parts:
                                                            if part in resolved_schema:
                                                                resolved_schema = resolved_schema[part]
                                                            else:
                                                                # Reference not found, skip modification
                                                                resolved_schema = None
                                                                break

                                                        if resolved_schema:
                                                            # Create a copy of the resolved schema and modify it
                                                            modified_body_schema = resolved_schema.copy()

                                                            # Drop each specified parameter
                                                            for param_to_drop in body_override_map[
                                                                operation_id
                                                            ]:
                                                                modified_body_schema = (
                                                                    self._remove_parameter_from_body_schema(
                                                                        modified_body_schema, param_to_drop
                                                                    )
                                                                )

                                                            # Replace the $ref with the modified inline schema
                                                            content_schema['schema'] = modified_body_schema
                                                else:
                                                    # Handle inline schemas (existing logic)
                                                    original_schema = schema_ref
                                                    modified_body_schema = original_schema.copy()

                                                    # Drop each specified parameter
                                                    for param_to_drop in body_override_map[operation_id]:
                                                        modified_body_schema = (
                                                            self._remove_parameter_from_body_schema(
                                                                modified_body_schema, param_to_drop
                                                            )
                                                        )

                                                    content_schema['schema'] = modified_body_schema

                            # Handle query parameter removal
                            if operation_id in query_override_map:
                                if 'parameters' in operation:
                                    # Filter out the query parameters that should be dropped
                                    filtered_parameters = []
                                    for param in operation['parameters']:
                                        # Check if this is a query parameter that should be dropped
                                        if (
                                            param.get('in') == 'query'
                                            and param.get('name') in query_override_map[operation_id]
                                        ):
                                            continue  # Skip this parameter (drop it)
                                        filtered_parameters.append(param)

                                    operation['parameters'] = filtered_parameters

        return modified_schema

    def _convert_mcp_parameters_to_openapi_format(self, mcp_parameters: dict) -> List[dict]:
        """
        Convert MCP tool parameters to OpenAPI-style parameter list format.

        Args:
            mcp_parameters: MCP tool parameters schema

        Returns:
            List of parameter dictionaries in OpenAPI format
        """
        if not isinstance(mcp_parameters, dict):
            return []

        parameters = []
        properties = mcp_parameters.get('properties', {})
        required_fields = mcp_parameters.get('required', [])

        for param_name, param_schema in properties.items():
            if isinstance(param_schema, dict):
                param_info = {
                    "name": param_name,
                    "type": param_schema.get('type', 'string'),
                    "required": param_name in required_fields,
                    "description": param_schema.get('description', ''),
                    "default": param_schema.get('default'),
                    "constraints": [],
                }

                # Add enum constraints if present
                if 'enum' in param_schema:
                    enum_values_str = ", ".join(map(str, param_schema['enum']))
                    param_info['constraints'].append(f"must be one of: [{enum_values_str}]")

                parameters.append(param_info)

        return parameters

    def _convert_trm_parameters_to_openapi_format(self, trm_input_schema: dict) -> List[dict]:
        """
        Convert TRM tool input schema to OpenAPI-style parameter list format.

        Args:
            trm_input_schema: TRM tool input schema

        Returns:
            List of parameter dictionaries in OpenAPI format
        """
        if not isinstance(trm_input_schema, dict):
            return []

        parameters = []
        properties = trm_input_schema.get('properties', {})
        required_fields = trm_input_schema.get('required', [])

        for param_name, param_schema in properties.items():
            if isinstance(param_schema, dict):
                param_info = {
                    "name": param_name,
                    "type": param_schema.get('type', 'string'),
                    "required": param_name in required_fields,
                    "description": param_schema.get('description', ''),
                    "default": param_schema.get('default'),
                    "constraints": [],
                }

                # Add enum constraints if present
                if 'enum' in param_schema:
                    enum_values_str = ", ".join(map(str, param_schema['enum']))
                    param_info['constraints'].append(f"must be one of: [{enum_values_str}]")

                parameters.append(param_info)

        return parameters

    def _convert_trm_response_schema(self, trm_output_schema: dict) -> dict:
        """
        Convert TRM tool output schema to OpenAPI-style response schema format.

        Args:
            trm_output_schema: TRM tool output schema

        Returns:
            Dictionary with success/failure response schemas
        """
        if not isinstance(trm_output_schema, dict):
            return {}

        # TRM tools typically have a simple output schema
        # Convert it to a success response format
        return {"success": trm_output_schema, "failure": {"error": "string"}}

    async def _get_trm_tools(self, app_name: str, url: str, app_tools: List[str], auth: Auth):
        tools = (requests.get(url + '/api/v1/tools/', headers={auth.type: auth.value})).json()
        for tool in tools:
            if tool['name'] in app_tools:
                self.trm_tools[app_name + '_' + tool['name']] = {
                    "name": tool["name"],
                    "description": tool["description"],
                    "input_schema": tool["input_schema"],
                    "output_schema": tool["output_schema"],
                    "id": tool["id"],
                    "binding": tool['binding'],
                }

    async def call_tool(self, tool_name: str, args: dict, headers: dict = None):
        if not headers:
            headers = {}
        trm_tool = next((item for item in list(self.trm_tools.keys())), None)
        if trm_tool:
            auth = self.auth_config[trm_tool.split("_")[0]]
            tool = self.trm_tools[trm_tool]
            tool_type = next(iter(tool['binding']))
            response = (
                requests.post(
                    LOCAL_TRM_URL + f"/api/v1/runtime/tools/{tool['id']}/run?tool_type={tool_type}",
                    json={
                        "args": args,
                        "type": tool_type,
                        "function": f"{tool['binding'][tool_type]['function']}",
                    },
                    headers={auth.type: auth.value},
                )
            ).json()
            return [TextContent(text=response['data']['tool_output'], type='text')]

        server = self.server_by_tool.get(tool_name)
        if not args:
            args = {}
        if not server:
            raise Exception(f"[Tool {tool_name} not found in any server]")

        # Check if this is an MCP server tool
        if isinstance(server, str) and server in self.mcp_clients:
            return await self._call_mcp_server_tool(server, tool_name, args)
        else:
            # Traditional MCP server call
            return await server.call_tool(tool_name, {"params": args, "headers": headers})

    def get_server_names(self):
        return list(self.tools_by_server.keys())

    def get_apps(self) -> List[ServiceConfig]:
        return list(self.schema_urls.values())

    def get_all_apis(self, include_response_schema=False):
        app_names = list(self.tools_by_server.keys())
        tools = {app: self.get_apis_for_application(app, include_response_schema) for app in app_names}
        return tools

    def get_apis_for_application(self, app_name, include_response_schema=False):
        if "default" in app_name:
            return self.schemas[app_name]
        is_trm_app = any(app_name in item for item in list(self.trm_tools.keys()))
        if is_trm_app:
            result = {}
            for s in self.schemas[app_name]:
                s_copy = s.copy()  # Create a copy to avoid modifying the original
                tool_name = s.get('name')
                prefixed_tool_name = f"{app_name}_{tool_name}"
                s_copy['api_name'] = prefixed_tool_name
                s_copy['description'] = s.get('description')
                s_copy['app_name'] = app_name
                s_copy['secure'] = False
                # Add missing fields for consistency with OpenAPI format
                s_copy['path'] = f"/{tool_name}"
                s_copy['method'] = "POST"
                s_copy['parameters'] = self._convert_trm_parameters_to_openapi_format(
                    s.get('input_schema', {})
                )
                if include_response_schema:
                    s_copy['response_schemas'] = self._convert_trm_response_schema(s.get('output_schema', {}))
                else:
                    s_copy['response_schemas'] = {}
                result[prefixed_tool_name] = s_copy
            return result

        # Check if it's an MCP server
        if app_name in self.mcp_clients:
            # Convert MCP tools to the same format as OpenAPITransformer
            result = {}
            mcp_tools = self.tools_by_server.get(app_name, [])
            for tool in mcp_tools:
                if isinstance(tool, dict) and 'function' in tool:
                    func = tool['function']
                    tool_name = func.get('name', '')
                    # Create the standardized API format

                    api_info = {
                        "app_name": app_name,
                        "secure": False,  # MCP servers are generally not secure by default
                        "api_name": tool_name,
                        "path": f"/{tool_name.replace(f'{app_name}_', '')}",  # Remove app prefix for path
                        "method": "POST",  # MCP tools are typically POST operations
                        "description": func.get('description', ''),
                        "parameters": self._convert_mcp_parameters_to_openapi_format(
                            func.get('parameters', {})
                        ),
                        "response_schemas": func.get(
                            'outputSchema', ""
                        ),  # MCP tools don't typically have response schemas defined
                    }

                    if include_response_schema:
                        # Add empty response schema structure for consistency
                        api_info["response_schemas"] = {
                            "success": {"result": "string"},
                            "failure": {"error": "string"},
                        }

                    result[tool_name] = api_info

            return result

        self.schemas[app_name]['x-app-name'] = app_name
        trans = OpenAPITransformer(self.schemas[app_name])
        res = trans.transform()
        return res

    async def _initialize_fastmcp_client(self, mcp_servers: List[tuple]):
        """Initialize FastMCP client with all MCP servers"""
        if not FastMCPClient or not mcp_servers:
            return

        try:
            # Build FastMCP config
            fastmcp_config = {"mcpServers": {}}

            for name, config in mcp_servers:
                server_config = {"url": config.url}
                if config.command:
                    server_config["command"] = config.command
                    if config.args:
                        server_config["args"] = config.args

                fastmcp_config["mcpServers"][name] = server_config

            print(f"Initializing FastMCP client with config: {fastmcp_config}")

            # Create FastMCP client
            self.fastmcp_client = FastMCPClient(fastmcp_config)

            # Connect to all servers and get tools
            async with self.fastmcp_client:
                # Get all tools from all connected servers
                tools = await self.fastmcp_client.list_tools()
                print(f"Retrieved {len(tools)} tools from FastMCP client: {[tool.name for tool in tools]}")

                for name, config in mcp_servers:
                    try:
                        # For single server, all tools belong to this server
                        # We need to prefix them manually since FastMCP doesn't do it automatically
                        server_tools = tools  # All tools from the single server

                        self.schemas[name] = {
                            "tools": [
                                {
                                    "name": tool.name,
                                    "description": tool.description,
                                    "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else {},
                                    "outputSchema": tool.outputSchema
                                    if hasattr(tool, 'outputSchema')
                                    else {},
                                }
                                for tool in server_tools
                            ]
                        }

                        # Register tools with server prefix and flatten parameters
                        for tool in server_tools:
                            prefixed_name = f"{name}_{tool.name}"

                            # Flatten parameters by resolving $defs and simplifying structures
                            input_schema = tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                            flattened_params = self._flatten_tool_parameters(input_schema)

                            tool_dict = {
                                "type": "function",
                                "function": {
                                    "name": prefixed_name,
                                    "description": tool.description,
                                    "parameters": flattened_params,
                                },
                            }
                            self.tools_by_server[name].append(tool_dict)
                            self.server_by_tool[prefixed_name] = name

                        print(f"Connected to MCP server {name} with {len(server_tools)} tools")
                        self.mcp_clients[name] = config.url

                    except Exception as e:
                        print(f"Error connecting to MCP server {name}: {e}")

        except Exception as e:
            print(f"Error initializing FastMCP client: {e}")
            # Fallback to mock implementation
            await self._fallback_mcp_connection(mcp_servers)

    def _flatten_tool_parameters(self, input_schema: dict) -> dict:
        """Flatten tool parameters by resolving $defs and simplifying complex structures"""
        try:
            if not input_schema:
                return {}

            # Create a flattened version of the schema
            flattened = self._flatten_schema_recursive(input_schema, input_schema.get('$defs', {}))

            # Remove $defs from the final result as they're no longer needed
            if '$defs' in flattened:
                del flattened['$defs']

            return flattened

        except Exception as e:
            print(f"Warning: Failed to flatten parameters: {e}")
            # Return original schema as fallback
            return input_schema

    def _flatten_schema_recursive(self, schema: dict, defs: dict) -> dict:
        """Recursively flatten a schema by resolving references and simplifying structures"""
        if not isinstance(schema, dict):
            return schema

        flattened = {}

        for key, value in schema.items():
            if key == '$defs':
                # Skip $defs in the final output, but keep them for reference resolution
                continue
            elif isinstance(value, dict):
                if '$ref' in value:
                    # Resolve the reference
                    ref_path = value['$ref']
                    if ref_path.startswith('#/$defs/'):
                        ref_name = ref_path.replace('#/$defs/', '')
                        if ref_name in defs:
                            # Recursively flatten the referenced schema
                            flattened[key] = self._flatten_schema_recursive(defs[ref_name], defs)
                        else:
                            # If reference can't be resolved, create a simple string parameter
                            flattened[key] = {"type": "string", "description": f"Reference to {ref_name}"}
                    else:
                        # Unknown reference format, treat as string
                        flattened[key] = {"type": "string", "description": f"Reference: {ref_path}"}
                elif value.get('type') == 'array' and 'items' in value:
                    # Handle arrays
                    items = value['items']
                    if isinstance(items, dict) and '$ref' in items:
                        # Array of referenced objects - simplify to array of strings
                        ref_path = items['$ref']
                        ref_name = (
                            ref_path.replace('#/$defs/', '') if ref_path.startswith('#/$defs/') else ref_path
                        )
                        flattened[key] = {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": f"Array of {ref_name} objects (simplified to strings)",
                        }
                    else:
                        # Regular array, flatten recursively
                        flattened[key] = {
                            "type": "array",
                            "items": self._flatten_schema_recursive(items, defs)
                            if isinstance(items, dict)
                            else items,
                        }
                        if 'title' in value:
                            flattened[key]['description'] = value['title']
                elif value.get('type') == 'object' and 'properties' in value:
                    # Nested object - flatten its properties into the parent level with prefixes
                    nested_props = self._flatten_schema_recursive(value, defs)
                    if 'properties' in nested_props:
                        for prop_name, prop_schema in nested_props['properties'].items():
                            prefixed_name = f"{key}_{prop_name}"
                            flattened[prefixed_name] = prop_schema
                    else:
                        # If can't flatten, treat as generic object (string)
                        flattened[key] = {"type": "string", "description": f"Object: {key}"}
                else:
                    # Regular nested dict, flatten recursively
                    flattened[key] = self._flatten_schema_recursive(value, defs)
            elif isinstance(value, list):
                # Handle lists recursively
                flattened[key] = [
                    self._flatten_schema_recursive(item, defs) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                # Primitive value, keep as-is
                flattened[key] = value

        return flattened

    async def _fallback_mcp_connection(self, mcp_servers: List[tuple]):
        """Fallback mock implementation when FastMCP is not available"""
        print("Using fallback mock MCP implementation")

        for name, config in mcp_servers:
            try:
                print(f"Mock connecting to MCP server {name} at {config.url}")

                # Mock tools for demonstration
                mock_tools = [
                    {
                        "name": "get_my_accounts",
                        "description": "Get my territory accounts",
                        "inputSchema": {"type": "object", "properties": {}, "required": []},
                    },
                    {
                        "name": "get_accounts_tpp",
                        "description": "Retrieve accounts from TPP",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "client_status": {"type": "string"},
                                "coverage_id": {"type": "string"},
                                "product_name": {"type": "string"},
                            },
                            "required": [],
                        },
                    },
                ]

                self.schemas[name] = {"tools": mock_tools}

                # Register tools with server prefix and flatten parameters
                for tool in mock_tools:
                    prefixed_name = f"{name}_{tool['name']}"

                    # Use OpenAPITransformer to flatten parameters
                    input_schema = tool.get('inputSchema', {})
                    flattened_params = self._flatten_tool_parameters(input_schema)

                    tool_dict = {
                        "type": "function",
                        "function": {
                            "name": prefixed_name,
                            "description": tool.get('description', ''),
                            "parameters": flattened_params,
                        },
                    }
                    self.tools_by_server[name].append(tool_dict)
                    self.server_by_tool[prefixed_name] = name

                print(f"Mock connected to MCP server {name} with {len(mock_tools)} tools")
                self.mcp_clients[name] = config.url

            except Exception as e:
                print(f"Error in fallback connection to MCP server {name}: {e}")

    async def _call_mcp_server_tool(self, server_name: str, tool_name: str, args: dict):
        """Call a tool on an external MCP server using FastMCP client"""
        try:
            if self.fastmcp_client:
                # Use FastMCP client for proper MCP communication
                async with self.fastmcp_client:
                    # Remove server prefix from tool name for FastMCP call
                    original_tool_name = tool_name.replace(f"{server_name}_", "")
                    result = await self.fastmcp_client.call_tool(original_tool_name, args)
                    result = result.content[0].text
                    return [TextContent(text=str(result), type='text')]
            else:
                # Fallback to direct HTTP calls
                url = self.mcp_clients[server_name]
                base_url = url.replace('/sse', '')

                # Remove server prefix from tool name
                original_tool_name = tool_name.replace(f"{server_name}_", "")

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{base_url}/call_tool", json={"name": original_tool_name, "arguments": args}
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return [TextContent(text=str(result), type='text')]
                        else:
                            error_msg = f"MCP server call failed with status {response.status}"
                            return [TextContent(text=error_msg, type='text')]

        except Exception as e:
            error_msg = f"Error calling MCP server tool: {e}"
            return [TextContent(text=error_msg, type='text')]

    async def load_tools(self):
        openapi = []
        trm = []
        mcp_servers = []
        trm_urls = {}

        for name, config in self.schema_urls.items():
            if config.type == ServiceType.OPENAPI:
                openapi.append((name, config))
            elif config.type == ServiceType.TRM:
                trm.append((name, config))
                trm_urls[name] = {
                    "url": config.url if config.url != "local" else LOCAL_ORCHESTRATE_URL,
                    "tools": config.tools,
                    "auth": config.auth,
                }
            elif config.type == ServiceType.MCP_SERVER:
                mcp_servers.append((name, config))

        await self.initialize_servers(openapi)
        await self.run_all_servers()

        # Initialize FastMCP client for all MCP servers
        if mcp_servers:
            await self._initialize_fastmcp_client(mcp_servers)

        if len(trm_urls) > 0:
            for name, data in trm_urls.items():
                await self._get_trm_tools(name, data["url"], data["tools"], data["auth"])
        self.add_trm_tools(trm)

    def add_trm_tools(self, services: List[Service]):
        for name, config in services:
            self.auth_config[name] = config.auth
            schemas = []
            for tool_name in config.tools:
                schema_data = self.trm_tools[name + '_' + tool_name]
                schemas.append(schema_data)
            self.schemas[name] = schemas

    async def initialize_servers(self, services: List[Service]):
        for name, config in services:
            try:
                schema_data, parser, is_url = self._fetch_and_parse_schema(config.url)
                if not is_url:
                    # this is a path
                    config.url = schema_data['servers'][0]['url']

                # Apply filtering and overrides
                modified_schema = self._filter_and_override_schema(schema_data, config)

                self.schemas[name] = modified_schema
                self.auth_config[name] = config.auth
                base_url = self._extract_base_url(config.url)

                # Create parser from modified schema
                has_body_overrides = any(
                    override.drop_request_body_parameters for override in (config.api_overrides or [])
                )
                has_query_overrides = any(
                    override.drop_query_parameters for override in (config.api_overrides or [])
                )

                if config.include or config.api_overrides or has_body_overrides or has_query_overrides:
                    # Re-create parser with modified schema
                    schema_json = (
                        yaml.dump(modified_schema)
                        if isinstance(modified_schema, dict)
                        else str(modified_schema)
                    )
                    parser = SimpleOpenAPIParser.from_yaml(schema_json)
                mcp_server = self._create_mcp_server(base_url, parser, name)
                self.servers[name] = mcp_server
                await self._register_tools(mcp_server)
            except Exception as e:
                print(f"Failed to initialize server for {config.url}: {e}")

    async def _register_tools(self, mcp_server):
        response = await mcp_server.list_tools()
        for tool in response:
            tool_dict = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            self.tools_by_server[mcp_server.name].append(tool_dict)
            self.server_by_tool[tool.name] = mcp_server

    async def run_all_servers(self):
        for name, server in self.servers.items():
            port = self._get_free_port()
            self.server_ports[server.name] = port
            server.settings.port = port
            thread = threading.Thread(target=server.run, kwargs={"transport": "sse"}, daemon=True)
            thread.start()
            self.threads[name] = thread
            print(f"Started MCP SSE server for {name} on port {port}")
