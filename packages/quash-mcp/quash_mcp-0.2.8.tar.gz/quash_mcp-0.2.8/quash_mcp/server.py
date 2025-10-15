#!/usr/bin/env python3
"""
Quash MCP Server
A Model Context Protocol server for mobile automation testing with Quash.
"""

import asyncio
import logging
from typing import Any
from pathlib import Path
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Load .env file from project root
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"
load_dotenv(env_file)

from .tools.build import build
from .tools.connect import connect
from .tools.configure import configure
from .tools.execute import execute
from .tools.runsuite import runsuite
from .tools.usage import usage
from .state import get_state

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("quash-mcp")

# Create MCP server instance
app = Server("quash-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available Quash tools with dynamic state information."""

    # Get current state
    state = get_state()

    # Build dynamic descriptions

    # CONNECT tool description
    connect_desc = ("Connect to an Android device or emulator. "
                   "Auto-detects single device or allows selection from multiple devices. "
                   "Verifies connectivity and checks/installs Quash Portal accessibility service.")

    if state.is_device_connected():
        connect_desc += f"\n\n📱 CURRENT DEVICE:\n"
        connect_desc += f"  • Serial: {state.device_serial}\n"
        if state.device_info:
            connect_desc += f"  • Model: {state.device_info.get('model', 'Unknown')}\n"
            connect_desc += f"  • Android: {state.device_info.get('android_version', 'Unknown')}\n"
        connect_desc += f"  • Portal: {'✓ Ready' if state.portal_ready else '✗ Not Ready'}"
    else:
        connect_desc += "\n\n📱 CURRENT DEVICE: Not connected"

    # CONFIGURE tool description
    configure_desc = ("Configure Quash agent execution parameters. "
                     "Set API key, model, temperature, max steps, and enable/disable vision, reasoning, and reflection features. "
                     "Only updates parameters that are provided.")

    # Mask API key for display (show first 10 and last 6 chars)
    api_key = state.config.get('api_key')
    if api_key:
        if len(api_key) < 20:
            masked_key = api_key[:4] + "..." + api_key[-4:]
        else:
            masked_key = api_key[:10] + "..." + api_key[-6:]
        api_key_display = masked_key
    else:
        api_key_display = "✗ Not Set"

    configure_desc += f"\n\n⚙️  CURRENT CONFIGURATION:\n"
    configure_desc += f"  • API Key: {api_key_display}\n"
    configure_desc += f"  • Model: {state.config.get('model', 'anthropic/claude-sonnet-4')}\n"
    configure_desc += f"  • Temperature: {state.config.get('temperature', 0.2)}\n"
    configure_desc += f"  • Max Steps: {state.config.get('max_steps', 15)}\n"
    configure_desc += f"  • Vision: {'✓ Enabled' if state.config.get('vision') else '✗ Disabled'}\n"
    configure_desc += f"  • Reasoning: {'✓ Enabled' if state.config.get('reasoning') else '✗ Disabled'}\n"
    configure_desc += f"  • Reflection: {'✓ Enabled' if state.config.get('reflection') else '✗ Disabled'}\n"
    configure_desc += f"  • Debug: {'✓ Enabled' if state.config.get('debug') else '✗ Disabled'}"

    # RUNSUITE tool description with latest execution
    runsuite_desc = ("Execute a suite of tasks in sequence. "
                     "Runs multiple tasks with support for retries, failure handling, and wait times. "
                     "Provides detailed execution summary with pass rates and task-by-task results. "
                     "Requires device to be connected and configuration to be set.")

    # Show latest suite execution if available
    if state.latest_suite:
        suite = state.latest_suite
        runsuite_desc += f"\n\n📋 LATEST SUITE: {suite['suite_name']}\n"
        runsuite_desc += f"  • Status: {suite['status'].upper()}\n"
        runsuite_desc += f"  • Pass Rate: {suite['pass_rate']}%\n"
        runsuite_desc += f"  • Duration: {suite['duration_seconds']}s\n"
        runsuite_desc += f"  • Tasks: {suite['completed_tasks']}/{suite['total_tasks']} completed\n"

        # Show individual task results
        runsuite_desc += "\n  Task Results:\n"
        for task_result in suite.get('task_results', []):
            task_num = task_result['task_number']
            task_status = task_result['status']
            task_prompt = task_result.get('prompt', 'No prompt')[:40]

            # Status indicator
            if task_status == 'completed':
                indicator = "✅"
            elif task_status == 'failed':
                indicator = "❌"
            else:
                indicator = "⏭️"

            runsuite_desc += f"    {indicator} Task {task_num}: {task_prompt}... - {task_status.upper()}\n"
    else:
        runsuite_desc += "\n\n📋 LATEST SUITE: No suites executed yet"

    # USAGE tool description
    usage_desc = ("View usage statistics and costs for your Quash executions. "
                 "All usage tracking happens on the backend for security. "
                 "Directs you to the web dashboard for detailed statistics.")

    return [
        Tool(
            name="build",
            description="Setup and verify all dependencies required for Quash mobile automation. "
                       "Checks Python version, ADB installation, Quash package, and Portal APK. "
                       "Attempts to auto-install missing dependencies where possible.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="connect",
            description=connect_desc,
            inputSchema={
                "type": "object",
                "properties": {
                    "device_serial": {
                        "type": "string",
                        "description": "Device serial number (optional - auto-detects if only one device)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="configure",
            description=configure_desc,
            inputSchema={
                "type": "object",
                "properties": {
                    "quash_api_key": {
                        "type": "string",
                        "description": "Quash API key for authentication and access"
                    },
                    "model": {
                        "type": "string",
                        "description": "LLM model name (e.g., 'openai/gpt-4o', 'anthropic/claude-3.5-sonnet')"
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Temperature for LLM sampling (0-2, default 0.2)"
                    },
                    "max_steps": {
                        "type": "integer",
                        "description": "Maximum number of execution steps (default 15)"
                    },
                    "vision": {
                        "type": "boolean",
                        "description": "Enable vision capabilities using screenshots (default false)"
                    },
                    "reasoning": {
                        "type": "boolean",
                        "description": "Enable planning with reasoning for complex tasks (default false)"
                    },
                    "reflection": {
                        "type": "boolean",
                        "description": "Enable reflection for self-improvement (default false)"
                    },
                    "debug": {
                        "type": "boolean",
                        "description": "Enable verbose debug logging (default false)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="execute",
            description="Execute a mobile automation task on the connected Android device. "
                       "Takes natural language instructions and performs the task using AI agents. "
                       "Provides live progress updates during execution. "
                       "Requires device to be connected and configuration to be set.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "Natural language description of the task to perform (e.g., 'Open Settings and navigate to WiFi')"
                    }
                },
                "required": ["task"]
            }
        ),
        Tool(
            name="runsuite",
            description=runsuite_desc,
            inputSchema={
                "type": "object",
                "properties": {
                    "suite_name": {
                        "type": "string",
                        "description": "Name of the test suite being executed"
                    },
                    "tasks": {
                        "type": "array",
                        "description": "Array of task definitions to execute in sequence",
                        "items": {
                            "type": "object",
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "description": "Task instruction (required)"
                                },
                                "type": {
                                    "type": "string",
                                    "description": "Task type: 'setup', 'test', or 'teardown' (optional, default 'test')",
                                    "enum": ["setup", "test", "teardown"]
                                },
                                "retries": {
                                    "type": "integer",
                                    "description": "Number of retry attempts on failure (optional, default 0)"
                                },
                                "continueOnFailure": {
                                    "type": "boolean",
                                    "description": "Continue suite execution if this task fails (optional, default false)"
                                },
                                "waitBefore": {
                                    "type": "integer",
                                    "description": "Seconds to wait before executing task (optional, default 0)"
                                }
                            },
                            "required": ["prompt"]
                        }
                    }
                },
                "required": ["suite_name", "tasks"]
            }
        ),
        Tool(
            name="usage",
            description=usage_desc,
            inputSchema={
                "type": "object",
                "properties": {
                    "api_key": {
                        "type": "string",
                        "description": "Specific API key to query (optional - shows all if not provided)"
                    },
                    "show_recent": {
                        "type": "integer",
                        "description": "Number of recent executions to show (default: 5)"
                    }
                },
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool execution."""

    try:
        if name == "build":
            result = await build()

        elif name == "connect":
            device_serial = arguments.get("device_serial")
            result = await connect(device_serial=device_serial)

        elif name == "configure":
            result = await configure(
                quash_api_key=arguments.get("quash_api_key"),
                model=arguments.get("model"),
                temperature=arguments.get("temperature"),
                max_steps=arguments.get("max_steps"),
                vision=arguments.get("vision"),
                reasoning=arguments.get("reasoning"),
                reflection=arguments.get("reflection"),
                debug=arguments.get("debug")
            )

        elif name == "execute":
            task = arguments.get("task")
            if not task:
                return [TextContent(
                    type="text",
                    text="❌ Error: 'task' parameter is required"
                )]

            # Collect progress messages
            progress_messages = []

            def progress_callback(message: str):
                progress_messages.append(message)

            result = await execute(task=task, progress_callback=progress_callback)

            # Combine progress messages with result
            if progress_messages:
                result["execution_log"] = "\n".join(progress_messages)

        elif name == "runsuite":
            suite_name = arguments.get("suite_name")
            tasks = arguments.get("tasks")

            if not suite_name:
                return [TextContent(
                    type="text",
                    text="❌ Error: 'suite_name' parameter is required"
                )]

            if not tasks or not isinstance(tasks, list) or len(tasks) == 0:
                return [TextContent(
                    type="text",
                    text="❌ Error: 'tasks' must be a non-empty array"
                )]

            # Collect progress messages
            progress_messages = []

            def progress_callback(message: str):
                progress_messages.append(message)

            result = await runsuite(
                suite_name=suite_name,
                tasks=tasks,
                progress_callback=progress_callback
            )

            # Combine progress messages with result
            if progress_messages:
                result["execution_log"] = "\n".join(progress_messages)

        elif name == "usage":
            result = await usage(
                api_key=arguments.get("api_key"),
                show_recent=arguments.get("show_recent", 5)
            )

        else:
            return [TextContent(
                type="text",
                text=f"❌ Unknown tool: {name}"
            )]

        # Format result as text
        import json
        result_text = json.dumps(result, indent=2)

        return [TextContent(
            type="text",
            text=result_text
        )]

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"❌ Error executing {name}: {str(e)}"
        )]


async def async_main():
    """Run the MCP server (async)."""
    async with stdio_server() as (read_stream, write_stream):
        logger.info("🚀 Quash MCP Server started")
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def main():
    """Entry point for the quash-mcp command."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()