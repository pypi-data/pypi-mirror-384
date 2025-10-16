import asyncio
import subprocess
import traceback
import shutil

import httpx
import json
import os
import signal
import unittest
from typing import List, Dict, Any, Optional, Tuple
import psutil

from cuga.backend.cuga_graph.nodes.human_in_the_loop.followup_model import ActionResponse
from cuga.config import settings

# Define server and registry commands
DEMO_COMMAND = ["uv", "run", "demo"]  # Assuming demo runs on port 8005 as per main.py
REGISTRY_COMMAND = ["uv", "run", "registry"]  # Assuming default port for registry
DIGITAL_SALES_MCP_COMMAND = ["uv", "run", "digital_sales_openapi"]  # Digital sales MCP server

# Server URL
SERVER_URL = f"http://localhost:{settings.server_ports.demo}"
STREAM_ENDPOINT = f"{SERVER_URL}/stream"
STOP_ENDPOINT = f"{SERVER_URL}/stop"
os.environ["MCP_SERVERS_FILE"] = os.path.join(os.path.dirname(__file__), "config", "mcp_servers.yaml")
os.environ["CUGA_TEST_ENV"] = "true"
os.environ["DYNACONF_ADVANCED_FEATURES__TRACKER_ENABLED"] = "true"


class BaseTestServerStream(unittest.IsolatedAsyncioTestCase):
    """
    Base test class for FastAPI server's streaming endpoint.
    Contains shared functionality and setup/teardown logic.
    """

    # Override this in subclasses to set specific environment variables
    test_env_vars = {}

    def _kill_process_by_port(self, port: int, service_name: str = "service") -> bool:
        """
        Kill processes listening on a specific port.

        Args:
            port: The port number to check
            service_name: Name of the service for logging purposes

        Returns:
            True if any processes were killed, False otherwise
        """
        killed_any = False
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    connections = proc.net_connections()
                    if connections:
                        for conn in connections:
                            if (
                                hasattr(conn, 'laddr')
                                and conn.laddr
                                and conn.laddr.port == port
                                and conn.status == 'LISTEN'
                            ):
                                print(
                                    f"Killing {service_name} process {proc.info['pid']} ({proc.info['name']}) on port {port}"
                                )
                                proc.terminate()
                                try:
                                    proc.wait(timeout=5)
                                    print(f"{service_name} process {proc.info['pid']} terminated gracefully")
                                except psutil.TimeoutExpired:
                                    print(
                                        f"{service_name} process {proc.info['pid']} did not terminate gracefully, killing..."
                                    )
                                    proc.kill()
                                    proc.wait()
                                killed_any = True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Process might have already terminated or we don't have permission
                    continue
        except Exception as e:
            print(f"Error while trying to kill {service_name} processes on port {port}: {e}")

        return killed_any

    def _create_log_files(self):
        """Create log files for demo and registry processes per test method in separate folders."""
        # Create logs directory within e2e folder
        e2e_dir = os.path.dirname(__file__)
        base_log_dir = os.path.join(e2e_dir, "logs")

        # Get test class and method names for folder naming
        test_class_name = self.__class__.__name__
        test_method_name = getattr(self, '_testMethodName', 'unknown_test')

        # Create a unique folder for this specific test
        test_folder_name = f"{test_class_name}_{test_method_name}"
        self.test_log_dir = os.path.join(base_log_dir, test_folder_name)
        os.environ["CUGA_LOGGING_DIR"] = os.path.join(self.test_log_dir, "logging")

        # Remove existing test folder if it exists (to reset for rerun)
        if os.path.exists(self.test_log_dir):
            shutil.rmtree(self.test_log_dir)
            print(f"Removed existing test folder: {self.test_log_dir}")

        # Create the test-specific folder
        os.makedirs(self.test_log_dir, exist_ok=True)
        print(f"Created test folder: {self.test_log_dir}")

        # Create log file paths within the test folder
        self.demo_log_file = os.path.join(self.test_log_dir, "demo_server.log")
        self.registry_log_file = os.path.join(self.test_log_dir, "registry_server.log")
        self.digital_sales_mcp_log_file = os.path.join(self.test_log_dir, "digital_sales_mcp.log")

        # Clear/truncate log files to ensure they start fresh for each test
        for log_file in [self.demo_log_file, self.registry_log_file, self.digital_sales_mcp_log_file]:
            with open(log_file, 'w') as f:
                f.write('')  # Clear the file
            print(f"Cleared log file: {log_file}")

        print(f"Demo server logs will be saved to: {self.demo_log_file}")
        print(f"Registry server logs will be saved to: {self.registry_log_file}")
        print(f"Digital sales MCP logs will be saved to: {self.digital_sales_mcp_log_file}")

    async def asyncSetUp(self):
        """
        Sets up the test environment before each test method.
        Starts the demo server, registry, and digital sales MCP processes with configured environment.
        """
        print(f"\n--- Setting up test environment for {self.__class__.__name__} ---")
        self.demo_process = None
        self.registry_process = None
        self.digital_sales_mcp_process = None
        self.demo_log_handle = None
        self.registry_log_handle = None
        self.digital_sales_mcp_log_handle = None

        # Create log files (this will also clear any existing ones)
        self._create_log_files()

        # Clean up any existing processes on our ports before starting
        print("Cleaning up any existing processes on target ports...")
        self._kill_process_by_port(settings.server_ports.digital_sales_api, "digital sales MCP")
        self._kill_process_by_port(settings.server_ports.demo, "demo server")
        self._kill_process_by_port(settings.server_ports.registry, "registry")
        if hasattr(settings.server_ports, 'saved_flows'):
            self._kill_process_by_port(settings.server_ports.saved_flows, "saved flows")

        # Wait a moment for ports to be freed
        await asyncio.sleep(2)

        # Set environment variables for this test class
        print(f"Configuring environment variables: {self.test_env_vars}")
        for key, value in self.test_env_vars.items():
            if value is None:
                os.environ.pop(key, None)
                print(f"  Removed {key}")
            else:
                os.environ[key] = value
                print(f"  Set {key} = {value}")

        # Open log files for writing
        self.registry_log_handle = open(self.registry_log_file, 'w', buffering=1)  # Line buffered
        self.demo_log_handle = open(self.demo_log_file, 'w', buffering=1)  # Line buffered
        self.digital_sales_mcp_log_handle = open(
            self.digital_sales_mcp_log_file, 'w', buffering=1
        )  # Line buffered
        print("Starting digital sales MCP process...")
        self.digital_sales_mcp_process = subprocess.Popen(
            DIGITAL_SALES_MCP_COMMAND,
            stdout=self.digital_sales_mcp_log_handle,
            stderr=subprocess.STDOUT,  # Redirect stderr to stdout (and thus to log file)
            text=True,
            env=os.environ.copy(),  # Pass the updated environment
            preexec_fn=os.setsid,  # For proper process group management
        )
        await asyncio.sleep(3)
        print("Starting registry process...")
        self.registry_process = subprocess.Popen(
            REGISTRY_COMMAND,
            stdout=self.registry_log_handle,
            stderr=subprocess.STDOUT,  # Redirect stderr to stdout (and thus to log file)
            text=True,
            env=os.environ.copy(),  # Pass the updated environment
            preexec_fn=os.setsid,  # For proper process group management
        )
        print(f"Registry process started with PID: {self.registry_process.pid}")

        print("Starting demo server process...")
        self.demo_process = subprocess.Popen(
            DEMO_COMMAND,
            stdout=self.demo_log_handle,
            stderr=subprocess.STDOUT,  # Redirect stderr to stdout (and thus to log file)
            text=True,
            env=os.environ.copy(),  # Pass the updated environment
            preexec_fn=os.setsid,  # For proper process group management
        )
        print(f"Demo server process started with PID: {self.demo_process.pid}")

        # Give processes some time to start up
        print("Waiting for servers to initialize (20 seconds)...")
        await asyncio.sleep(20)
        print("Server initialization wait complete.")
        print("--- Test environment setup complete ---")

    async def asyncTearDown(self):
        """
        Cleans up the test environment after each test method.
        Stops the demo server, registry, and digital sales MCP processes by port and PID.
        """
        print(f"\n--- Tearing down test environment for {self.__class__.__name__} ---")
        print("Stopping processes...")

        # First, try to terminate processes gracefully by PID if they still exist
        if self.demo_process:
            try:
                if self.demo_process.poll() is None:  # Process is still running
                    # Send SIGTERM to the process group
                    os.killpg(os.getpgid(self.demo_process.pid), signal.SIGTERM)
                    self.demo_process.wait(timeout=5)
                    print("Demo server process terminated gracefully.")
                else:
                    print("Demo server process already terminated.")
            except (subprocess.TimeoutExpired, ProcessLookupError, OSError):
                print("Demo server process did not terminate gracefully or was already gone.")
                try:
                    if self.demo_process.poll() is None:
                        os.killpg(os.getpgid(self.demo_process.pid), signal.SIGKILL)
                        self.demo_process.wait()
                except (ProcessLookupError, OSError):
                    pass  # Process was already gone
            self.demo_process = None

        if self.registry_process:
            try:
                if self.registry_process.poll() is None:  # Process is still running
                    # Send SIGTERM to the process group
                    os.killpg(os.getpgid(self.registry_process.pid), signal.SIGTERM)
                    self.registry_process.wait(timeout=5)
                    print("Registry process terminated gracefully.")
                else:
                    print("Registry process already terminated.")
            except (subprocess.TimeoutExpired, ProcessLookupError, OSError):
                print("Registry process did not terminate gracefully or was already gone.")
                try:
                    if self.registry_process.poll() is None:
                        os.killpg(os.getpgid(self.registry_process.pid), signal.SIGKILL)
                        self.registry_process.wait()
                except (ProcessLookupError, OSError):
                    pass  # Process was already gone
            self.registry_process = None

        if self.digital_sales_mcp_process:
            try:
                if self.digital_sales_mcp_process.poll() is None:  # Process is still running
                    # Send SIGTERM to the process group
                    os.killpg(os.getpgid(self.digital_sales_mcp_process.pid), signal.SIGTERM)
                    self.digital_sales_mcp_process.wait(timeout=5)
                    print("Digital sales MCP process terminated gracefully.")
                else:
                    print("Digital sales MCP process already terminated.")
            except (subprocess.TimeoutExpired, ProcessLookupError, OSError):
                print("Digital sales MCP process did not terminate gracefully or was already gone.")
                try:
                    if self.digital_sales_mcp_process.poll() is None:
                        os.killpg(os.getpgid(self.digital_sales_mcp_process.pid), signal.SIGKILL)
                        self.digital_sales_mcp_process.wait()
                except (ProcessLookupError, OSError):
                    pass  # Process was already gone
            self.digital_sales_mcp_process = None

        # Close log file handles
        if self.demo_log_handle:
            self.demo_log_handle.close()
            self.demo_log_handle = None
            print(f"Demo server log file closed: {self.demo_log_file}")

        if self.registry_log_handle:
            self.registry_log_handle.close()
            self.registry_log_handle = None
            print(f"Registry server log file closed: {self.registry_log_file}")

        if self.digital_sales_mcp_log_handle:
            self.digital_sales_mcp_log_handle.close()
            self.digital_sales_mcp_log_handle = None
            print(f"Digital sales MCP log file closed: {self.digital_sales_mcp_log_file}")

        # Then, kill any remaining processes by port as a backup
        print("Cleaning up any remaining processes on target ports...")
        demo_killed = self._kill_process_by_port(settings.server_ports.demo, "demo server")
        registry_killed = self._kill_process_by_port(settings.server_ports.registry, "registry")

        saved_flows_killed = False
        if hasattr(settings.server_ports, 'saved_flows'):
            saved_flows_killed = self._kill_process_by_port(settings.server_ports.saved_flows, "saved flows")

        if not (demo_killed or registry_killed or saved_flows_killed):
            print("No additional processes found on target ports.")

        print("All processes stopped.")
        print("--- Test environment teardown complete ---")

    def _parse_event_data(self, data_str: str) -> Any:
        """
        Parse event data which can be:
        1. Plain string
        2. JSON string
        3. JSON object with "data" key containing the actual content
        """
        try:
            # First, try to parse as JSON
            parsed_json = json.loads(data_str)

            # If it's a dict with "data" key, extract the content
            if isinstance(parsed_json, dict) and "data" in parsed_json:
                return parsed_json["data"]

            # Otherwise, return the parsed JSON as-is
            return parsed_json

        except json.JSONDecodeError:
            # If JSON parsing fails, return as plain string
            return data_str

    def get_event_at(self, all_data: List[Dict[str, Any]], n: int) -> Tuple[str, str]:
        last_event = all_data[n]
        last_event_key = last_event['event']
        last_event_value = last_event.get('data', 'N/A')
        return last_event_key, last_event_value

    async def run_task(
        self,
        query: str,
        followup_response: Optional[ActionResponse] = None,
        stop_on_answer: bool = True,
        timeout: Optional[float] = None,
        verbose: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Helper function to run a streaming task and return all events.

        Args:
            query: The query string to send to the stream endpoint
            stop_on_answer: Whether to stop streaming when "Answer" event is received
            timeout: Optional timeout for the entire operation
            verbose: Whether to print event details during streaming

        Returns:
            List of event dictionaries with 'event' and 'data' keys
        """
        all_events = []

        if verbose:
            print(f"\n--- Running task for query: '{query}' ---")

        try:
            if verbose:
                print(f"Sending POST request to {STREAM_ENDPOINT} with query: '{query}'")

            client_timeout = httpx.Timeout(timeout) if timeout else None

            async with httpx.AsyncClient(timeout=client_timeout) as client:
                async with client.stream(
                    "POST",
                    STREAM_ENDPOINT,
                    json={"query": query} if query and query != "" else followup_response.model_dump(),
                    headers={"Accept": "text/event-stream"},
                ) as response:
                    response.raise_for_status()

                    # Ensure content-type is correct for SSE
                    content_type = response.headers.get("content-type", "")
                    if "text/event-stream" not in content_type and verbose:
                        print(f"Warning: Expected 'text/event-stream', got '{content_type}'")

                    buffer = b""
                    async for chunk in response.aiter_bytes():
                        buffer += chunk

                        # Process complete events (delimited by double newlines)
                        while b"\n\n" in buffer:
                            event_block, buffer = buffer.split(b"\n\n", 1)
                            event_lines = event_block.split(b"\n")

                            event_data = {}
                            for line in event_lines:
                                line = line.strip()
                                if not line:
                                    continue

                                if line.startswith(b"event: "):
                                    event_data["event"] = line[len(b"event: ") :].decode("utf-8").strip()
                                elif line.startswith(b"data: "):
                                    try:
                                        data_str = line[len(b"data: ") :].decode("utf-8").strip()
                                        event_data["data"] = self._parse_event_data(data_str)
                                    except UnicodeDecodeError:
                                        event_data["data"] = line[len(b"data: ") :].strip()
                                else:
                                    # Handle cases where the format might be just "<key>\n<value>"
                                    try:
                                        line_str = line.decode("utf-8").strip()
                                        if ":" not in line_str and not event_data.get("event"):
                                            # This might be an event type on its own line
                                            event_data["event"] = line_str
                                        elif ":" not in line_str and not event_data.get("data"):
                                            # This might be data on its own line
                                            event_data["data"] = self._parse_event_data(line_str)
                                    except UnicodeDecodeError:
                                        continue

                            # Only add events that have at least an event type or data
                            if event_data and (event_data.get("event") or event_data.get("data")):
                                all_events.append(event_data)

                                if verbose:
                                    print(f"Received Event: {event_data.get('event', 'N/A')}")
                                    print(f"  Data: {event_data.get('data', 'N/A')}\n")

                                # Stop early if Answer event is received and stop_on_answer is True
                                if stop_on_answer and event_data.get("event") == "Answer":
                                    if verbose:
                                        print("--- 'Answer' event received, stopping stream. ---")

                                    # # Send a stop signal to the agent if it's still running
                                    # try:
                                    #     await client.post(STOP_ENDPOINT)
                                    #     if verbose:
                                    #         print("Stop signal sent to agent.")
                                    # except httpx.HTTPStatusError as e:
                                    #     if verbose:
                                    #         print(f"Failed to send stop signal: {e}")
                                    # break

        except httpx.RequestError as exc:
            print(f"Request URL: {exc.request.url!r}")
            print(f"Request Method: {exc.request.method}")
            print(f"Exception Type: {type(exc).__name__}")
            print(f"Exception Message: {exc}")
            print("Full Traceback:")
            traceback.print_exc()
            print("--- End HTTP Request Error ---\n")
        except Exception as e:
            print("\n--- Unexpected Error Occurred ---")
            print(f"Exception Type: {type(e).__name__}")
            print(f"Exception Message: {e}")
            print("Full Traceback:")
            raise Exception(f"An unexpected error occurred during stream processing: {e}")

        if verbose:
            print(f"\n--- Task completed. Total events received: {len(all_events)} ---")

        return all_events

    def _assert_answer_event(self, all_events: List[Dict[str, Any]], expected_keywords: List[str] = None):
        """
        Common assertion logic for answer events.

        Args:
            all_events: List of events from the stream
            expected_keywords: Optional list of keywords that should be in the answer
        """
        print("\n--- Performing assertions ---")

        # Basic assertions
        self.assertGreater(len(all_events), 0, "No events were received from the stream.")

        # Find the 'Answer' event
        answer_event = next((e for e in all_events if e.get("event") == "Answer"), None)

        self.assertIsNotNone(answer_event, "The 'Answer' event was not found in the stream.")
        print("Assertion Passed: 'Answer' event found.")

        answer_data = answer_event.get("data")
        self.assertIsNotNone(answer_data, "The 'Answer' event has no data.")
        self.assertNotEqual(answer_data, "", "The 'Answer' event data is empty.")
        print("Assertion Passed: 'Answer' data is not empty.")

        # Keyword validation if provided
        if expected_keywords:
            answer_str = str(answer_data).lower()
            for keyword in expected_keywords:
                self.assertIn(keyword.lower(), answer_str, f"Answer does not contain '{keyword}'.")
            print(f"Assertion Passed: Answer contains expected keywords: {expected_keywords}")

        print("\n--- All assertions passed! ---")
