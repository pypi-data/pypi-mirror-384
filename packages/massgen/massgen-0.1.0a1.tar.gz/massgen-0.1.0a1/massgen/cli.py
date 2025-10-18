#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MassGen Command Line Interface

A clean CLI for MassGen with file-based configuration support.
Supports both interactive mode and single-question mode.

Usage examples:
    # Use YAML/JSON configuration file
    python -m massgen.cli --config config.yaml "What is the capital of France?"

    # Quick setup with backend and model
    python -m massgen.cli --backend openai --model gpt-4o-mini "What is 2+2?"

    # Interactive mode
    python -m massgen.cli --config config.yaml

    # Multiple agents from config
    python -m massgen.cli --config multi_agent.yaml "Compare different approaches to renewable energy"  # noqa
"""

import argparse
import asyncio
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .agent_config import AgentConfig, TimeoutConfig
from .backend.azure_openai import AzureOpenAIBackend
from .backend.chat_completions import ChatCompletionsBackend
from .backend.claude import ClaudeBackend
from .backend.claude_code import ClaudeCodeBackend
from .backend.gemini import GeminiBackend
from .backend.grok import GrokBackend
from .backend.inference import InferenceBackend
from .backend.lmstudio import LMStudioBackend
from .backend.response import ResponseBackend
from .chat_agent import ConfigurableAgent, SingleAgent
from .frontend.coordination_ui import CoordinationUI
from .logger_config import _DEBUG_MODE, logger, setup_logging
from .orchestrator import Orchestrator
from .utils import get_backend_type_from_model


# Load environment variables from .env files
def load_env_file():
    """Load environment variables from .env files.

    Search order (later files override earlier ones):
    1. MassGen package .env (development fallback)
    2. User home ~/.massgen/.env (global user config)
    3. Current directory .env (project-specific, highest priority)
    """
    # Load in priority order (later overrides earlier)
    load_dotenv(Path(__file__).parent / ".env")  # Package fallback
    load_dotenv(Path.home() / ".massgen" / ".env")  # User global
    load_dotenv()  # Current directory (highest priority)


# Load .env file at module import
load_env_file()

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Color constants for terminal output
BRIGHT_CYAN = "\033[96m"
BRIGHT_BLUE = "\033[94m"
BRIGHT_GREEN = "\033[92m"
BRIGHT_YELLOW = "\033[93m"
BRIGHT_MAGENTA = "\033[95m"
BRIGHT_RED = "\033[91m"
BRIGHT_WHITE = "\033[97m"
RESET = "\033[0m"
BOLD = "\033[1m"


class ConfigurationError(Exception):
    """Configuration error for CLI."""


def _substitute_variables(obj: Any, variables: Dict[str, str]) -> Any:
    """Recursively substitute ${var} references in config with actual values.

    Args:
        obj: Config object (dict, list, str, or other)
        variables: Dict of variable names to values

    Returns:
        Config object with variables substituted
    """
    if isinstance(obj, dict):
        return {k: _substitute_variables(v, variables) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_substitute_variables(item, variables) for item in obj]
    elif isinstance(obj, str):
        # Replace ${var} with value
        result = obj
        for var_name, var_value in variables.items():
            result = result.replace(f"${{{var_name}}}", var_value)
        return result
    else:
        return obj


def resolve_config_path(config_arg: Optional[str]) -> Optional[Path]:
    """Resolve config file with flexible syntax.

    Priority order:

    **If --config flag provided (highest priority):**
    1. @examples/NAME → Package examples (search configs directory)
    2. Absolute/relative paths (exact path as specified)
    3. Named configs in ~/.config/massgen/agents/

    **If NO --config flag (auto-discovery):**
    1. .massgen/config.yaml (project-level config in current directory)
    2. ~/.config/massgen/config.yaml (global default config)
    3. None → trigger config builder

    Args:
        config_arg: Config argument from --config flag (can be @examples/NAME, path, or None)

    Returns:
        Path to config file, or None if config builder should run

    Raises:
        ConfigurationError: If config file not found
    """
    # Check for default configs if no config_arg provided
    if not config_arg:
        # Priority 1: Project-level config (.massgen/config.yaml in current directory)
        project_config = Path.cwd() / ".massgen" / "config.yaml"
        if project_config.exists():
            return project_config

        # Priority 2: Global default config
        global_config = Path.home() / ".config/massgen/config.yaml"
        if global_config.exists():
            return global_config

        return None  # Trigger builder

    # Handle @examples/ prefix - search in package configs
    if config_arg.startswith("@examples/"):
        name = config_arg[10:]  # Remove '@examples/' prefix
        try:
            from importlib.resources import files

            configs_root = files("massgen") / "configs"

            # Search recursively for matching name
            # Try to find by filename stem match
            for config_file in configs_root.rglob("*.yaml"):
                # Check if name matches the file stem or is contained in the path
                if name in config_file.name or name in str(config_file):
                    return Path(str(config_file))

            raise ConfigurationError(
                f"Config '{config_arg}' not found in package.\n" f"Use --list-examples to see available configs.",
            )
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(f"Error loading package config: {e}")

    # Try as regular path (absolute or relative)
    path = Path(config_arg).expanduser()
    if path.exists():
        return path

    # Try in user config directory (~/.config/massgen/agents/)
    user_agents_dir = Path.home() / ".config/massgen/agents"
    user_config = user_agents_dir / f"{config_arg}.yaml"
    if user_config.exists():
        return user_config

    # Also try with .yaml extension if not provided
    if not config_arg.endswith((".yaml", ".yml")):
        user_config_with_ext = user_agents_dir / f"{config_arg}.yaml"
        if user_config_with_ext.exists():
            return user_config_with_ext

    # Config not found anywhere
    raise ConfigurationError(
        f"Configuration file not found: {config_arg}\n"
        f"Searched in:\n"
        f"  - Current directory: {Path.cwd() / config_arg}\n"
        f"  - User configs: {user_agents_dir / config_arg}.yaml\n"
        f"Use --list-examples to see available package configs.",
    )


def load_config_file(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML or JSON file.

    Search order:
    1. Exact path as provided (absolute or relative to CWD)
    2. If just a filename, search in package's configs/ directory
    3. If a relative path, also try within package's configs/ directory

    Supports variable substitution: ${cwd} in any string will be replaced with the agent's cwd value.
    """
    path = Path(config_path)

    # Try the path as-is first (handles absolute paths and relative to CWD)
    if path.exists():
        pass  # Use this path
    elif path.is_absolute():
        # Absolute path that doesn't exist
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    else:
        # Relative path or just filename - search in package configs
        package_configs_dir = Path(__file__).parent / "configs"

        # Try 1: Just the filename in package configs root
        candidate1 = package_configs_dir / path.name
        # Try 2: The full relative path within package configs
        candidate2 = package_configs_dir / path

        if candidate1.exists():
            path = candidate1
        elif candidate2.exists():
            path = candidate2
        else:
            raise ConfigurationError(
                f"Configuration file not found: {config_path}\n" f"Searched in:\n" f"  - {Path.cwd() / config_path}\n" f"  - {candidate1}\n" f"  - {candidate2}",
            )

    try:
        with open(path, "r", encoding="utf-8") as f:
            if path.suffix.lower() in [".yaml", ".yml"]:
                return yaml.safe_load(f)
            elif path.suffix.lower() == ".json":
                return json.load(f)
            else:
                raise ConfigurationError(f"Unsupported config file format: {path.suffix}")
    except Exception as e:
        raise ConfigurationError(f"Error reading config file: {e}")


def create_backend(backend_type: str, **kwargs) -> Any:
    """Create backend instance from type and parameters.

    Supported backend types:
    - openai: OpenAI API (requires OPENAI_API_KEY)
    - grok: xAI Grok (requires XAI_API_KEY)
    - sglang: SGLang inference server (local)
    - claude: Anthropic Claude (requires ANTHROPIC_API_KEY)
    - gemini: Google Gemini (requires GOOGLE_API_KEY or GEMINI_API_KEY)
    - chatcompletion: OpenAI-compatible providers (auto-detects API key based on base_url)

    Supported backend with external dependencies:
    - ag2/autogen: AG2 (AutoGen) framework agents

    For chatcompletion backend, the following providers are auto-detected:
    - Cerebras AI (cerebras.ai) -> CEREBRAS_API_KEY
    - Together AI (together.ai/together.xyz) -> TOGETHER_API_KEY
    - Fireworks AI (fireworks.ai) -> FIREWORKS_API_KEY
    - Groq (groq.com) -> GROQ_API_KEY
    - Nebius AI Studio (studio.nebius.ai) -> NEBIUS_API_KEY
    - OpenRouter (openrouter.ai) -> OPENROUTER_API_KEY
    - POE (poe.com) -> POE_API_KEY
    - Qwen (dashscope.aliyuncs.com) -> QWEN_API_KEY

    External agent frameworks are supported via the adapter registry.
    """
    backend_type = backend_type.lower()

    # Check if this is a framework/adapter type
    from massgen.adapters import adapter_registry

    if backend_type in adapter_registry:
        # Use ExternalAgentBackend for all registered adapter types
        from massgen.backend.external import ExternalAgentBackend

        return ExternalAgentBackend(adapter_type=backend_type, **kwargs)

    if backend_type == "openai":
        api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ConfigurationError("OpenAI API key not found. Set OPENAI_API_KEY or provide " "in config.")
        return ResponseBackend(api_key=api_key, **kwargs)

    elif backend_type == "grok":
        api_key = kwargs.get("api_key") or os.getenv("XAI_API_KEY")
        if not api_key:
            raise ConfigurationError("Grok API key not found. Set XAI_API_KEY or provide in config.")
        return GrokBackend(api_key=api_key, **kwargs)

    elif backend_type == "claude":
        api_key = kwargs.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ConfigurationError("Claude API key not found. Set ANTHROPIC_API_KEY or provide in config.")
        return ClaudeBackend(api_key=api_key, **kwargs)

    elif backend_type == "gemini":
        api_key = kwargs.get("api_key") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ConfigurationError("Gemini API key not found. Set GOOGLE_API_KEY or provide in config.")
        return GeminiBackend(api_key=api_key, **kwargs)

    elif backend_type == "chatcompletion":
        api_key = kwargs.get("api_key")
        base_url = kwargs.get("base_url")

        # Determine API key based on base URL if not explicitly provided
        if not api_key:
            if base_url and "cerebras.ai" in base_url:
                api_key = os.getenv("CEREBRAS_API_KEY")
                if not api_key:
                    raise ConfigurationError("Cerebras AI API key not found. Set CEREBRAS_API_KEY or provide in config.")
            elif base_url and "together.xyz" in base_url:
                api_key = os.getenv("TOGETHER_API_KEY")
                if not api_key:
                    raise ConfigurationError("Together AI API key not found. Set TOGETHER_API_KEY or provide in config.")
            elif base_url and "fireworks.ai" in base_url:
                api_key = os.getenv("FIREWORKS_API_KEY")
                if not api_key:
                    raise ConfigurationError("Fireworks AI API key not found. Set FIREWORKS_API_KEY or provide in config.")
            elif base_url and "groq.com" in base_url:
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key:
                    raise ConfigurationError("Groq API key not found. Set GROQ_API_KEY or provide in config.")
            elif base_url and "nebius.com" in base_url:
                api_key = os.getenv("NEBIUS_API_KEY")
                if not api_key:
                    raise ConfigurationError("Nebius AI Studio API key not found. Set NEBIUS_API_KEY or provide in config.")
            elif base_url and "openrouter.ai" in base_url:
                api_key = os.getenv("OPENROUTER_API_KEY")
                if not api_key:
                    raise ConfigurationError("OpenRouter API key not found. Set OPENROUTER_API_KEY or provide in config.")
            elif base_url and ("z.ai" in base_url or "bigmodel.cn" in base_url):
                api_key = os.getenv("ZAI_API_KEY")
                if not api_key:
                    raise ConfigurationError("ZAI API key not found. Set ZAI_API_KEY or provide in config.")
            elif base_url and ("moonshot.ai" in base_url or "moonshot.cn" in base_url):
                api_key = os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY")
                if not api_key:
                    raise ConfigurationError("Kimi/Moonshot API key not found. Set MOONSHOT_API_KEY or KIMI_API_KEY or provide in config.")
            elif base_url and "poe.com" in base_url:
                api_key = os.getenv("POE_API_KEY")
                if not api_key:
                    raise ConfigurationError("POE API key not found. Set POE_API_KEY or provide in config.")
            elif base_url and "aliyuncs.com" in base_url:
                api_key = os.getenv("QWEN_API_KEY")
                if not api_key:
                    raise ConfigurationError("Qwen API key not found. Set QWEN_API_KEY or provide in config.")

        return ChatCompletionsBackend(api_key=api_key, **kwargs)

    elif backend_type == "zai":
        # ZAI (Zhipu.ai) uses OpenAI-compatible Chat Completions at a custom base_url
        # Supports both global (z.ai) and China (bigmodel.cn) endpoints
        api_key = kwargs.get("api_key") or os.getenv("ZAI_API_KEY")
        if not api_key:
            raise ConfigurationError("ZAI API key not found. Set ZAI_API_KEY or provide in config.")
        return ChatCompletionsBackend(api_key=api_key, **kwargs)

    elif backend_type == "lmstudio":
        # LM Studio local server (OpenAI-compatible). Defaults handled by backend.
        return LMStudioBackend(**kwargs)

    elif backend_type == "vllm":
        # vLLM local server (OpenAI-compatible). Defaults handled by backend.
        return InferenceBackend(backend_type="vllm", **kwargs)

    elif backend_type == "sglang":
        # SGLang local server (OpenAI-compatible). Defaults handled by backend.
        return InferenceBackend(backend_type="sglang", **kwargs)

    elif backend_type == "claude_code":
        # ClaudeCodeBackend using claude-code-sdk-python
        # Authentication handled by backend (API key or subscription)

        # Validate claude-code-sdk availability
        try:
            pass
        except ImportError:
            raise ConfigurationError("claude-code-sdk not found. Install with: pip install claude-code-sdk")

        return ClaudeCodeBackend(**kwargs)

    elif backend_type == "azure_openai":
        api_key = kwargs.get("api_key") or os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = kwargs.get("base_url") or os.getenv("AZURE_OPENAI_ENDPOINT")
        if not api_key:
            raise ConfigurationError("Azure OpenAI API key not found. Set AZURE_OPENAI_API_KEY or provide in config.")
        if not endpoint:
            raise ConfigurationError("Azure OpenAI endpoint not found. Set AZURE_OPENAI_ENDPOINT or provide base_url in config.")
        return AzureOpenAIBackend(**kwargs)

    else:
        raise ConfigurationError(f"Unsupported backend type: {backend_type}")


def create_agents_from_config(config: Dict[str, Any], orchestrator_config: Optional[Dict[str, Any]] = None) -> Dict[str, ConfigurableAgent]:
    """Create agents from configuration."""
    agents = {}

    agent_entries = [config["agent"]] if "agent" in config else config.get("agents", None)

    if not agent_entries:
        raise ConfigurationError("Configuration must contain either 'agent' or 'agents' section")

    for i, agent_data in enumerate(agent_entries, start=1):
        backend_config = agent_data.get("backend", {})

        # Substitute variables like ${cwd} in backend config
        if "cwd" in backend_config:
            variables = {"cwd": backend_config["cwd"]}
            backend_config = _substitute_variables(backend_config, variables)

        # Infer backend type from model if not explicitly provided
        backend_type = backend_config.get("type") or (get_backend_type_from_model(backend_config["model"]) if "model" in backend_config else None)
        if not backend_type:
            raise ConfigurationError("Backend type must be specified or inferrable from model")

        # Add orchestrator context for filesystem setup if available
        if orchestrator_config:
            if "agent_temporary_workspace" in orchestrator_config:
                backend_config["agent_temporary_workspace"] = orchestrator_config["agent_temporary_workspace"]
            # Add orchestrator-level context_paths to all agents
            if "context_paths" in orchestrator_config:
                # Merge orchestrator context_paths with agent-specific ones
                agent_context_paths = backend_config.get("context_paths", [])
                orchestrator_context_paths = orchestrator_config["context_paths"]

                # Deduplicate paths - orchestrator paths take precedence
                merged_paths = orchestrator_context_paths.copy()
                orchestrator_paths_set = {path.get("path") for path in orchestrator_context_paths}

                for agent_path in agent_context_paths:
                    if agent_path.get("path") not in orchestrator_paths_set:
                        merged_paths.append(agent_path)

                backend_config["context_paths"] = merged_paths

        backend = create_backend(backend_type, **backend_config)
        backend_params = {k: v for k, v in backend_config.items() if k != "type"}

        backend_type_lower = backend_type.lower()
        if backend_type_lower == "openai":
            agent_config = AgentConfig.create_openai_config(**backend_params)
        elif backend_type_lower == "claude":
            agent_config = AgentConfig.create_claude_config(**backend_params)
        elif backend_type_lower == "grok":
            agent_config = AgentConfig.create_grok_config(**backend_params)
        elif backend_type_lower == "gemini":
            agent_config = AgentConfig.create_gemini_config(**backend_params)
        elif backend_type_lower == "zai":
            agent_config = AgentConfig.create_zai_config(**backend_params)
        elif backend_type_lower == "chatcompletion":
            agent_config = AgentConfig.create_chatcompletion_config(**backend_params)
        elif backend_type_lower == "lmstudio":
            agent_config = AgentConfig.create_lmstudio_config(**backend_params)
        elif backend_type_lower == "vllm":
            agent_config = AgentConfig.create_vllm_config(**backend_params)
        elif backend_type_lower == "sglang":
            agent_config = AgentConfig.create_sglang_config(**backend_params)
        else:
            agent_config = AgentConfig(backend_params=backend_config)

        agent_config.agent_id = agent_data.get("id", f"agent{i}")

        # Route system_message to backend-specific system prompt parameter
        system_msg = agent_data.get("system_message")
        if system_msg:
            if backend_type_lower == "claude_code":
                # For Claude Code, use append_system_prompt to preserve Claude Code capabilities
                agent_config.backend_params["append_system_prompt"] = system_msg
            else:
                # For other backends, fall back to deprecated custom_system_instruction
                # TODO: Add backend-specific routing for other backends
                agent_config.custom_system_instruction = system_msg

        # Timeout configuration will be applied to orchestrator instead of individual agents

        agent = ConfigurableAgent(config=agent_config, backend=backend)
        agents[agent.config.agent_id] = agent

    return agents


def create_simple_config(
    backend_type: str,
    model: str,
    system_message: Optional[str] = None,
    base_url: Optional[str] = None,
    ui_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a simple single-agent configuration."""
    backend_config = {"type": backend_type, "model": model}
    if base_url:
        backend_config["base_url"] = base_url

    # Add required workspace configuration for Claude Code backend
    if backend_type == "claude_code":
        backend_config["cwd"] = "workspace1"

    # Use provided UI config or default to rich_terminal for CLI usage
    if ui_config is None:
        ui_config = {"display_type": "rich_terminal", "logging_enabled": True}

    config = {
        "agent": {
            "id": "agent1",
            "backend": backend_config,
            "system_message": system_message or "You are a helpful AI assistant.",
        },
        "ui": ui_config,
    }

    # Add orchestrator config with .massgen/ structure for Claude Code
    if backend_type == "claude_code":
        config["orchestrator"] = {
            "snapshot_storage": ".massgen/snapshots",
            "agent_temporary_workspace": ".massgen/temp_workspaces",
            "session_storage": ".massgen/sessions",
        }

    return config


def validate_context_paths(config: Dict[str, Any]) -> None:
    """Validate that all context paths in the config exist.

    Context paths can be either files or directories.
    File-level context paths allow access to specific files without exposing sibling files.
    Raises ConfigurationError with clear message if any paths don't exist.
    """
    orchestrator_cfg = config.get("orchestrator", {})
    context_paths = orchestrator_cfg.get("context_paths", [])

    missing_paths = []

    for context_path_config in context_paths:
        if isinstance(context_path_config, dict):
            path = context_path_config.get("path")
        else:
            # Handle string format for backwards compatibility
            path = context_path_config

        if path:
            path_obj = Path(path)
            if not path_obj.exists():
                missing_paths.append(path)

    if missing_paths:
        errors = ["Context paths not found:"]
        for path in missing_paths:
            errors.append(f"  - {path}")
        errors.append("\nPlease update your configuration with valid paths.")
        raise ConfigurationError("\n".join(errors))


def relocate_filesystem_paths(config: Dict[str, Any]) -> None:
    """Relocate filesystem paths (orchestrator paths and agent workspaces) to be under .massgen/ directory.

    Modifies the config in-place to ensure all MassGen state is organized
    under .massgen/ for clean project structure.
    """
    massgen_dir = Path(".massgen")

    # Relocate orchestrator paths
    orchestrator_cfg = config.get("orchestrator", {})
    if orchestrator_cfg:
        path_fields = [
            "snapshot_storage",
            "agent_temporary_workspace",
            "session_storage",
        ]

        for field in path_fields:
            if field in orchestrator_cfg:
                user_path = orchestrator_cfg[field]
                # If user provided an absolute path or already starts with .massgen/, keep as-is
                if Path(user_path).is_absolute() or user_path.startswith(".massgen/"):
                    continue
                # Otherwise, relocate under .massgen/
                orchestrator_cfg[field] = str(massgen_dir / user_path)

    # Relocate agent workspaces (cwd fields)
    agent_entries = [config["agent"]] if "agent" in config else config.get("agents", [])
    for agent_data in agent_entries:
        backend_config = agent_data.get("backend", {})
        if "cwd" in backend_config:
            user_cwd = backend_config["cwd"]
            # If user provided an absolute path or already starts with .massgen/, keep as-is
            if Path(user_cwd).is_absolute() or user_cwd.startswith(".massgen/"):
                continue
            # Otherwise, relocate under .massgen/workspaces/
            backend_config["cwd"] = str(massgen_dir / "workspaces" / user_cwd)


def load_previous_turns(session_info: Dict[str, Any], session_storage: str) -> List[Dict[str, Any]]:
    """
    Load previous turns from session storage.

    Returns:
        List of previous turn metadata dicts
    """
    session_id = session_info.get("session_id")
    if not session_id:
        return []

    session_dir = Path(session_storage) / session_id
    if not session_dir.exists():
        return []

    previous_turns = []
    turn_num = 1

    while True:
        turn_dir = session_dir / f"turn_{turn_num}"
        if not turn_dir.exists():
            break

        metadata_file = turn_dir / "metadata.json"
        if metadata_file.exists():
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
            # Use absolute path for workspace
            workspace_path = (turn_dir / "workspace").resolve()
            previous_turns.append(
                {
                    "turn": turn_num,
                    "path": str(workspace_path),
                    "task": metadata.get("task", ""),
                    "winning_agent": metadata.get("winning_agent", ""),
                },
            )

        turn_num += 1

    return previous_turns


async def handle_session_persistence(
    orchestrator,
    question: str,
    session_info: Dict[str, Any],
    session_storage: str,
) -> tuple[Optional[str], int, Optional[str]]:
    """
    Handle session persistence after orchestrator completes.

    Returns:
        tuple: (session_id, updated_turn_number, normalized_answer)
    """
    # Get final result from orchestrator
    final_result = orchestrator.get_final_result()
    if not final_result:
        # No filesystem work to persist
        return (session_info.get("session_id"), session_info.get("current_turn", 0), None)

    # Initialize or reuse session ID
    session_id = session_info.get("session_id")
    if not session_id:
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Increment turn
    current_turn = session_info.get("current_turn", 0) + 1

    # Create turn directory
    session_dir = Path(session_storage) / session_id
    turn_dir = session_dir / f"turn_{current_turn}"
    turn_dir.mkdir(parents=True, exist_ok=True)

    # Normalize answer paths
    final_answer = final_result["final_answer"]
    workspace_path = final_result.get("workspace_path")
    turn_workspace_path = (turn_dir / "workspace").resolve()  # Make absolute

    if workspace_path:
        # Replace workspace paths in answer with absolute path
        normalized_answer = final_answer.replace(workspace_path, str(turn_workspace_path))
    else:
        normalized_answer = final_answer

    # Save normalized answer
    answer_file = turn_dir / "answer.txt"
    answer_file.write_text(normalized_answer, encoding="utf-8")

    # Save metadata
    metadata = {
        "turn": current_turn,
        "timestamp": datetime.now().isoformat(),
        "winning_agent": final_result["winning_agent_id"],
        "task": question,
        "session_id": session_id,
    }
    metadata_file = turn_dir / "metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    # Create/update session summary for easy viewing
    session_summary_file = session_dir / "SESSION_SUMMARY.txt"
    summary_lines = []

    if session_summary_file.exists():
        summary_lines = session_summary_file.read_text(encoding="utf-8").splitlines()
    else:
        summary_lines.append("=" * 80)
        summary_lines.append(f"Multi-Turn Session: {session_id}")
        summary_lines.append("=" * 80)
        summary_lines.append("")

    # Add turn separator and info
    summary_lines.append("")
    summary_lines.append("=" * 80)
    summary_lines.append(f"TURN {current_turn}")
    summary_lines.append("=" * 80)
    summary_lines.append(f"Timestamp: {metadata['timestamp']}")
    summary_lines.append(f"Winning Agent: {metadata['winning_agent']}")
    summary_lines.append(f"Task: {question}")
    summary_lines.append(f"Workspace: {turn_workspace_path}")
    summary_lines.append(f"Answer: See {(turn_dir / 'answer.txt').resolve()}")
    summary_lines.append("")

    session_summary_file.write_text("\n".join(summary_lines), encoding="utf-8")

    # Copy workspace if it exists
    if workspace_path and Path(workspace_path).exists():
        shutil.copytree(workspace_path, turn_workspace_path, dirs_exist_ok=True)

    return (session_id, current_turn, normalized_answer)


async def run_question_with_history(
    question: str,
    agents: Dict[str, SingleAgent],
    ui_config: Dict[str, Any],
    history: List[Dict[str, Any]],
    session_info: Dict[str, Any],
    **kwargs,
) -> tuple[str, Optional[str], int]:
    """Run MassGen with a question and conversation history.

    Returns:
        tuple: (response_text, session_id, turn_number)
    """
    # Build messages including history
    messages = history.copy()
    messages.append({"role": "user", "content": question})

    # Check if we should use orchestrator for single agents (default: False for backward compatibility)
    use_orchestrator_for_single = ui_config.get("use_orchestrator_for_single_agent", True)

    if len(agents) == 1 and not use_orchestrator_for_single:
        # Single agent mode with history
        agent = next(iter(agents.values()))
        print(f"\n🤖 {BRIGHT_CYAN}Single Agent Mode{RESET}", flush=True)
        print(f"Agent: {agent.agent_id}", flush=True)
        if history:
            print(f"History: {len(history)//2} previous exchanges", flush=True)
        print(f"Question: {question}", flush=True)
        print("\n" + "=" * 60, flush=True)

        response_content = ""

        async for chunk in agent.chat(messages):
            if chunk.type == "content" and chunk.content:
                response_content += chunk.content
                print(chunk.content, end="", flush=True)
            elif chunk.type == "builtin_tool_results":
                # Skip builtin_tool_results to avoid duplication with real-time streaming
                # The backends already show tool status during execution
                continue
            elif chunk.type == "error":
                print(f"\n❌ Error: {chunk.error}", flush=True)
                return ("", session_info.get("session_id"), session_info.get("current_turn", 0))

        print("\n" + "=" * 60, flush=True)
        # Single agent mode doesn't use session storage
        return (response_content, session_info.get("session_id"), session_info.get("current_turn", 0))

    else:
        # Multi-agent mode with history
        # Create orchestrator config with timeout settings
        timeout_config = kwargs.get("timeout_config")
        orchestrator_config = AgentConfig()
        if timeout_config:
            orchestrator_config.timeout_config = timeout_config

        # Get orchestrator parameters from config
        orchestrator_cfg = kwargs.get("orchestrator", {})

        # Get context sharing parameters
        snapshot_storage = orchestrator_cfg.get("snapshot_storage")
        agent_temporary_workspace = orchestrator_cfg.get("agent_temporary_workspace")
        session_storage = orchestrator_cfg.get("session_storage", "sessions")  # Default to "sessions"

        # Get debug/test parameters
        if orchestrator_cfg.get("skip_coordination_rounds", False):
            orchestrator_config.skip_coordination_rounds = True

        # Load previous turns from session storage for multi-turn conversations
        previous_turns = load_previous_turns(session_info, session_storage)

        orchestrator = Orchestrator(
            agents=agents,
            config=orchestrator_config,
            snapshot_storage=snapshot_storage,
            agent_temporary_workspace=agent_temporary_workspace,
            previous_turns=previous_turns,
        )
        # Create a fresh UI instance for each question to ensure clean state
        ui = CoordinationUI(
            display_type=ui_config.get("display_type", "rich_terminal"),
            logging_enabled=ui_config.get("logging_enabled", True),
            enable_final_presentation=True,  # Required for multi-turn: ensures final answer is saved
        )

        print(f"\n🤖 {BRIGHT_CYAN}Multi-Agent Mode{RESET}", flush=True)
        print(f"Agents: {', '.join(agents.keys())}", flush=True)
        if history:
            print(f"History: {len(history)//2} previous exchanges", flush=True)
        print(f"Question: {question}", flush=True)
        print("\n" + "=" * 60, flush=True)

        # For multi-agent with history, we need to use a different approach
        # that maintains coordination UI display while supporting conversation context

        if history and len(history) > 0:
            # Use coordination UI with conversation context
            # Extract current question from messages
            current_question = messages[-1].get("content", question) if messages else question

            # Pass the full message context to the UI coordination
            response_content = await ui.coordinate_with_context(orchestrator, current_question, messages)
        else:
            # Standard coordination for new conversations
            response_content = await ui.coordinate(orchestrator, question)

        # Handle session persistence if applicable
        session_id_to_use, updated_turn, normalized_response = await handle_session_persistence(
            orchestrator,
            question,
            session_info,
            session_storage,
        )

        # Return normalized response so conversation history has correct paths
        return (normalized_response or response_content, session_id_to_use, updated_turn)


async def run_single_question(question: str, agents: Dict[str, SingleAgent], ui_config: Dict[str, Any], **kwargs) -> str:
    """Run MassGen with a single question."""
    # Check if we should use orchestrator for single agents (default: False for backward compatibility)
    use_orchestrator_for_single = ui_config.get("use_orchestrator_for_single_agent", True)

    if len(agents) == 1 and not use_orchestrator_for_single:
        # Single agent mode with existing SimpleDisplay frontend
        agent = next(iter(agents.values()))

        print(f"\n🤖 {BRIGHT_CYAN}Single Agent Mode{RESET}", flush=True)
        print(f"Agent: {agent.agent_id}", flush=True)
        print(f"Question: {question}", flush=True)
        print("\n" + "=" * 60, flush=True)

        messages = [{"role": "user", "content": question}]
        response_content = ""

        async for chunk in agent.chat(messages):
            if chunk.type == "content" and chunk.content:
                response_content += chunk.content
                print(chunk.content, end="", flush=True)
            elif chunk.type == "builtin_tool_results":
                # Skip builtin_tool_results to avoid duplication with real-time streaming
                continue
            elif chunk.type == "error":
                print(f"\n❌ Error: {chunk.error}", flush=True)
                return ""

        print("\n" + "=" * 60, flush=True)
        return response_content

    else:
        # Multi-agent mode
        # Create orchestrator config with timeout settings
        timeout_config = kwargs.get("timeout_config")
        orchestrator_config = AgentConfig()
        if timeout_config:
            orchestrator_config.timeout_config = timeout_config

        # Get orchestrator parameters from config
        orchestrator_cfg = kwargs.get("orchestrator", {})

        # Get context sharing parameters
        snapshot_storage = orchestrator_cfg.get("snapshot_storage")
        agent_temporary_workspace = orchestrator_cfg.get("agent_temporary_workspace")

        # Get debug/test parameters
        if orchestrator_cfg.get("skip_coordination_rounds", False):
            orchestrator_config.skip_coordination_rounds = True

        orchestrator = Orchestrator(
            agents=agents,
            config=orchestrator_config,
            snapshot_storage=snapshot_storage,
            agent_temporary_workspace=agent_temporary_workspace,
        )
        # Create a fresh UI instance for each question to ensure clean state
        ui = CoordinationUI(
            display_type=ui_config.get("display_type", "rich_terminal"),
            logging_enabled=ui_config.get("logging_enabled", True),
            enable_final_presentation=True,  # Ensures final presentation is generated
        )

        print(f"\n🤖 {BRIGHT_CYAN}Multi-Agent Mode{RESET}", flush=True)
        print(f"Agents: {', '.join(agents.keys())}", flush=True)
        print(f"Question: {question}", flush=True)
        print("\n" + "=" * 60, flush=True)

        final_response = await ui.coordinate(orchestrator, question)
        return final_response


def prompt_for_context_paths(original_config: Dict[str, Any], orchestrator_cfg: Dict[str, Any]) -> bool:
    """Prompt user to add context paths in interactive mode.

    Returns True if config was modified, False otherwise.
    """
    # Check if filesystem is enabled (at least one agent has cwd)
    agent_entries = [original_config["agent"]] if "agent" in original_config else original_config.get("agents", [])
    has_filesystem = any("cwd" in agent.get("backend", {}) for agent in agent_entries)

    if not has_filesystem:
        return False

    # Show current context paths
    existing_paths = orchestrator_cfg.get("context_paths", [])
    cwd = Path.cwd()

    # Use Rich for better display
    from rich.console import Console as RichConsole
    from rich.panel import Panel as RichPanel

    rich_console = RichConsole()

    # Build context paths display
    context_content = []
    if existing_paths:
        for path_config in existing_paths:
            path = path_config.get("path") if isinstance(path_config, dict) else path_config
            permission = path_config.get("permission", "read") if isinstance(path_config, dict) else "read"
            context_content.append(f"  [green]✓[/green] {path} [dim]({permission})[/dim]")
    else:
        context_content.append("  [yellow]No context paths configured[/yellow]")

    context_panel = RichPanel(
        "\n".join(context_content),
        title="[bold bright_cyan]📂 Context Paths[/bold bright_cyan]",
        border_style="cyan",
        padding=(0, 2),
        width=80,
    )
    rich_console.print(context_panel)
    print()

    # Check if CWD is already in context paths
    cwd_str = str(cwd)
    cwd_already_added = any((path_config.get("path") if isinstance(path_config, dict) else path_config) == cwd_str for path_config in existing_paths)

    if not cwd_already_added:
        # Create prompt panel
        prompt_content = [
            "[bold cyan]Add current directory as context path?[/bold cyan]",
            f"  [yellow]{cwd}[/yellow]",
            "",
            "  [dim]Context paths give agents access to your project files.[/dim]",
            "  [dim]• Read-only during coordination (prevents conflicts)[/dim]",
            "  [dim]• Write permission for final agent to save results[/dim]",
            "",
            "  [dim]Options:[/dim]",
            "  [green]Y[/green] → Add with write permission (default)",
            "  [cyan]P[/cyan] → Add with protected paths (e.g., .env, secrets)",
            "  [yellow]N[/yellow] → Skip",
            "  [blue]C[/blue] → Add custom path",
        ]
        prompt_panel = RichPanel(
            "\n".join(prompt_content),
            border_style="cyan",
            padding=(1, 2),
            width=80,
        )
        rich_console.print(prompt_panel)
        print()
        try:
            response = input(f"   {BRIGHT_CYAN}Your choice [Y/P/N/C]:{RESET} ").strip().lower()

            if response in ["y", "yes", ""]:
                # Add CWD with write permission
                if "context_paths" not in orchestrator_cfg:
                    orchestrator_cfg["context_paths"] = []
                orchestrator_cfg["context_paths"].append({"path": cwd_str, "permission": "write"})
                print(f"   {BRIGHT_GREEN}✅ Added: {cwd} (write){RESET}", flush=True)
                return True
            elif response in ["p", "protected"]:
                # Add CWD with write permission and protected paths
                protected_paths = []
                print(f"\n   {BRIGHT_CYAN}Enter protected paths (one per line, empty to finish):{RESET}", flush=True)
                print(f"   {BRIGHT_YELLOW}Tip: Protected paths are relative to {cwd}{RESET}", flush=True)
                while True:
                    protected_input = input(f"   {BRIGHT_CYAN}→{RESET} ").strip()
                    if not protected_input:
                        break
                    protected_paths.append(protected_input)
                    print(f"     {BRIGHT_GREEN}✓ Added: {protected_input}{RESET}", flush=True)

                if "context_paths" not in orchestrator_cfg:
                    orchestrator_cfg["context_paths"] = []

                context_config = {"path": cwd_str, "permission": "write"}
                if protected_paths:
                    context_config["protected_paths"] = protected_paths

                orchestrator_cfg["context_paths"].append(context_config)
                print(f"\n   {BRIGHT_GREEN}✅ Added: {cwd} (write) with {len(protected_paths)} protected path(s){RESET}", flush=True)
                return True
            elif response in ["n", "no"]:
                # User explicitly declined
                return False
            elif response in ["c", "custom"]:
                # Loop until valid path or user cancels
                print()
                while True:
                    custom_path = input(f"   {BRIGHT_CYAN}Enter path (absolute or relative):{RESET} ").strip()
                    if not custom_path:
                        print(f"   {BRIGHT_YELLOW}⚠️  Cancelled{RESET}", flush=True)
                        return False

                    # Resolve to absolute path
                    abs_path = str(Path(custom_path).resolve())

                    # Check if path exists
                    if not Path(abs_path).exists():
                        print(f"   {BRIGHT_RED}✗ Path does not exist: {abs_path}{RESET}", flush=True)
                        retry = input(f"   {BRIGHT_CYAN}Try again? [Y/n]:{RESET} ").strip().lower()
                        if retry in ["n", "no"]:
                            return False
                        continue

                    # Valid path (file or directory), ask for permission
                    permission = input(f"   {BRIGHT_CYAN}Permission [read/write] (default: write):{RESET} ").strip().lower() or "write"
                    if permission not in ["read", "write"]:
                        permission = "write"

                    # Ask about protected paths if write permission
                    protected_paths = []
                    if permission == "write":
                        add_protected = input(f"   {BRIGHT_CYAN}Add protected paths? [y/N]:{RESET} ").strip().lower()
                        if add_protected in ["y", "yes"]:
                            print(f"   {BRIGHT_CYAN}Enter protected paths (one per line, empty to finish):{RESET}", flush=True)
                            while True:
                                protected_input = input(f"   {BRIGHT_CYAN}→{RESET} ").strip()
                                if not protected_input:
                                    break
                                protected_paths.append(protected_input)
                                print(f"     {BRIGHT_GREEN}✓ Added: {protected_input}{RESET}", flush=True)

                    if "context_paths" not in orchestrator_cfg:
                        orchestrator_cfg["context_paths"] = []

                    context_config = {"path": abs_path, "permission": permission}
                    if protected_paths:
                        context_config["protected_paths"] = protected_paths

                    orchestrator_cfg["context_paths"].append(context_config)
                    if protected_paths:
                        print(f"   {BRIGHT_GREEN}✅ Added: {abs_path} ({permission}) with {len(protected_paths)} protected path(s){RESET}", flush=True)
                    else:
                        print(f"   {BRIGHT_GREEN}✅ Added: {abs_path} ({permission}){RESET}", flush=True)
                    return True
            else:
                # Invalid response - clarify options
                print(f"\n   {BRIGHT_RED}✗ Invalid option: '{response}'{RESET}", flush=True)
                print(f"   {BRIGHT_YELLOW}Please choose: Y (yes), P (protected), N (no), or C (custom){RESET}", flush=True)
                return False
        except (KeyboardInterrupt, EOFError):
            print()  # New line after Ctrl+C
            return False

    return False


def show_available_examples():
    """Display available example configurations from package."""
    try:
        from importlib.resources import files

        configs_root = files("massgen") / "configs"

        print(f"\n{BRIGHT_CYAN}Available Example Configurations{RESET}")
        print("=" * 60)

        # Organize by category
        categories = {}
        for config_file in sorted(configs_root.rglob("*.yaml")):
            # Get relative path from configs root
            rel_path = str(config_file).replace(str(configs_root) + "/", "")
            # Extract category (first directory)
            parts = rel_path.split("/")
            category = parts[0] if len(parts) > 1 else "root"

            if category not in categories:
                categories[category] = []

            # Create a short name for @examples/
            # Use the path without .yaml extension
            short_name = rel_path.replace(".yaml", "").replace("/", "_")

            categories[category].append((short_name, rel_path))

        # Display categories
        for category, configs in sorted(categories.items()):
            print(f"\n{BRIGHT_YELLOW}{category.title()}:{RESET}")
            for short_name, rel_path in configs[:10]:  # Limit to avoid overwhelming
                print(f"  {BRIGHT_GREEN}@examples/{short_name:<40}{RESET} {rel_path}")

            if len(configs) > 10:
                print(f"  ... and {len(configs) - 10} more")

        print(f"\n{BRIGHT_BLUE}Usage:{RESET}")
        print('  massgen --config @examples/SHORTNAME "Your question"')
        print("  massgen --example SHORTNAME > my-config.yaml")
        print()

    except Exception as e:
        print(f"Error listing examples: {e}")
        print("Examples may not be available (development mode?)")


def print_example_config(name: str):
    """Print an example config to stdout.

    Args:
        name: Name of the example (can include or exclude @examples/ prefix)
    """
    try:
        # Remove @examples/ prefix if present
        if name.startswith("@examples/"):
            name = name[10:]

        # Try to resolve the config
        resolved = resolve_config_path(f"@examples/{name}")
        if resolved:
            with open(resolved, "r") as f:
                print(f.read())
        else:
            print(f"Error: Could not find example '{name}'", file=sys.stderr)
            print("Use --list-examples to see available configs", file=sys.stderr)
            sys.exit(1)

    except ConfigurationError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error printing example config: {e}", file=sys.stderr)
        sys.exit(1)


def should_run_builder() -> bool:
    """Check if config builder should run automatically.

    Returns True if:
    - No default config exists at ~/.config/massgen/config.yaml
    """
    default_config = Path.home() / ".config/massgen/config.yaml"
    return not default_config.exists()


def print_help_messages():
    """Display help messages using Rich for better formatting."""
    rich_console = Console()

    help_content = """[dim]💬  Type your questions below
💡  Use slash commands: [cyan]/help[/cyan], [cyan]/quit[/cyan], [cyan]/reset[/cyan], [cyan]/status[/cyan], [cyan]/config[/cyan]
⌨️   Press [cyan]Ctrl+C[/cyan] to exit[/dim]"""

    help_panel = Panel(
        help_content,
        border_style="dim",
        padding=(0, 2),
        width=80,
    )
    rich_console.print(help_panel)


async def run_interactive_mode(
    agents: Dict[str, SingleAgent],
    ui_config: Dict[str, Any],
    original_config: Dict[str, Any] = None,
    orchestrator_cfg: Dict[str, Any] = None,
    config_path: Optional[str] = None,
    **kwargs,
):
    """Run MassGen in interactive mode with conversation history."""

    # Use Rich console for better display
    rich_console = Console()

    # Clear screen
    rich_console.clear()

    # ASCII art for interactive multi-agent mode
    ascii_art = """[bold cyan]
     ███╗   ███╗ █████╗ ███████╗███████╗ ██████╗ ███████╗███╗   ██╗
     ████╗ ████║██╔══██╗██╔════╝██╔════╝██╔════╝ ██╔════╝████╗  ██║
     ██╔████╔██║███████║███████╗███████╗██║  ███╗█████╗  ██╔██╗ ██║
     ██║╚██╔╝██║██╔══██║╚════██║╚════██║██║   ██║██╔══╝  ██║╚██╗██║
     ██║ ╚═╝ ██║██║  ██║███████║███████║╚██████╔╝███████╗██║ ╚████║
     ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝[/bold cyan]

     [dim]     🤖 🤖 🤖  →  💬 collaborate  →  🎯 winner  →  📢 final[/dim]
"""

    # Wrap ASCII art in a panel
    ascii_panel = Panel(
        ascii_art,
        border_style="bold cyan",
        padding=(0, 2),
        width=80,
    )
    rich_console.print(ascii_panel)
    print()

    # Create configuration table
    config_table = Table(
        show_header=False,
        box=None,
        padding=(0, 2),
        show_edge=False,
    )
    config_table.add_column("Label", style="bold cyan", no_wrap=True)
    config_table.add_column("Value", style="white")

    # Determine mode
    ui_config.get("use_orchestrator_for_single_agent", True)
    if len(agents) == 1:
        mode = "Single Agent"
        mode_icon = "🤖"
    else:
        mode = f"Multi-Agent ({len(agents)} agents)"
        mode_icon = "🤝"

    config_table.add_row(f"{mode_icon} Mode:", f"[bold]{mode}[/bold]")

    # Add agents info
    if len(agents) <= 3:
        # Show all agents if 3 or fewer
        for agent_id, agent in agents.items():
            # Get model name from config
            model = agent.config.backend_params.get("model", "unknown")
            backend_name = agent.backend.__class__.__name__.replace("Backend", "")
            # Show model with backend in parentheses
            display = f"{model} [dim]({backend_name})[/dim]"
            config_table.add_row(f"  ├─ {agent_id}:", display)
    else:
        # Show count and first 2 agents
        agent_list = list(agents.items())
        for i, (agent_id, agent) in enumerate(agent_list[:2]):
            model = agent.config.backend_params.get("model", "unknown")
            backend_name = agent.backend.__class__.__name__.replace("Backend", "")
            display = f"{model} [dim]({backend_name})[/dim]"
            config_table.add_row(f"  ├─ {agent_id}:", display)
        config_table.add_row("  └─ ...", f"[dim]and {len(agents) - 2} more[/dim]")

    # Create main panel with configuration
    config_panel = Panel(
        config_table,
        title="[bold bright_yellow]⚙️  Session Configuration[/bold bright_yellow]",
        border_style="yellow",
        padding=(0, 2),
        width=80,
    )
    rich_console.print(config_panel)
    print()

    # Prompt for context paths if filesystem is enabled
    if original_config and orchestrator_cfg:
        config_modified = prompt_for_context_paths(original_config, orchestrator_cfg)
        if config_modified:
            # Recreate agents with updated context paths
            agents = create_agents_from_config(original_config, orchestrator_cfg)
            print(f"   {BRIGHT_GREEN}✓ Agents reloaded with updated context paths{RESET}", flush=True)
            print()

    print_help_messages()

    # Maintain conversation history
    conversation_history = []

    # Session management for multi-turn filesystem support
    session_id = None
    current_turn = 0
    session_storage = kwargs.get("orchestrator", {}).get("session_storage", "sessions")

    try:
        while True:
            try:
                # Recreate agents with previous turn as read-only context path.
                # This provides agents with BOTH:
                # 1. Read-only context path (original turn n-1 results) - for reference/comparison
                # 2. Writable workspace (copy of turn n-1 results, pre-populated by orchestrator) - for modification
                # This allows agents to compare "what I changed" vs "what was originally there".
                # TODO: We may want to avoid full recreation if possible in the future, conditioned on being able to easily reset MCPs.
                if current_turn > 0 and original_config and orchestrator_cfg:
                    # Get the most recent turn path (the one just completed)
                    session_dir = Path(session_storage) / session_id
                    latest_turn_dir = session_dir / f"turn_{current_turn}"
                    latest_turn_workspace = latest_turn_dir / "workspace"

                    if latest_turn_workspace.exists():
                        logger.info(f"[CLI] Recreating agents with turn {current_turn} workspace as read-only context path")

                        # Clean up existing agents' backends and filesystem managers
                        for agent_id, agent in agents.items():
                            # Cleanup filesystem manager (Docker containers, etc.)
                            if hasattr(agent, "backend") and hasattr(agent.backend, "filesystem_manager"):
                                if agent.backend.filesystem_manager:
                                    try:
                                        agent.backend.filesystem_manager.cleanup()
                                    except Exception as e:
                                        logger.warning(f"[CLI] Cleanup failed for agent {agent_id}: {e}")

                            # Cleanup backend itself
                            if hasattr(agent.backend, "__aexit__"):
                                await agent.backend.__aexit__(None, None, None)

                        # Inject previous turn path as read-only context
                        modified_config = original_config.copy()
                        agent_entries = [modified_config["agent"]] if "agent" in modified_config else modified_config.get("agents", [])

                        for agent_data in agent_entries:
                            backend_config = agent_data.get("backend", {})
                            if "cwd" in backend_config:  # Only inject if agent has filesystem support
                                existing_context_paths = backend_config.get("context_paths", [])
                                new_turn_config = {"path": str(latest_turn_workspace.resolve()), "permission": "read"}
                                backend_config["context_paths"] = existing_context_paths + [new_turn_config]

                        # Recreate agents from modified config
                        agents = create_agents_from_config(modified_config, orchestrator_cfg)
                        logger.info(f"[CLI] Successfully recreated {len(agents)} agents with turn {current_turn} path as read-only context")

                question = input(f"\n{BRIGHT_BLUE}👤 User:{RESET} ").strip()

                # Handle slash commands
                if question.startswith("/"):
                    command = question.lower()

                    if command in ["/quit", "/exit", "/q"]:
                        print("👋 Goodbye!", flush=True)
                        break
                    elif command in ["/reset", "/clear"]:
                        conversation_history = []
                        # Reset all agents
                        for agent in agents.values():
                            agent.reset()
                        print(
                            f"{BRIGHT_YELLOW}🔄 Conversation history cleared!{RESET}",
                            flush=True,
                        )
                        continue
                    elif command in ["/help", "/h"]:
                        print(f"\n{BRIGHT_CYAN}📚 Available Commands:{RESET}", flush=True)
                        print("   /quit, /exit, /q     - Exit the program", flush=True)
                        print(
                            "   /reset, /clear       - Clear conversation history",
                            flush=True,
                        )
                        print(
                            "   /help, /h            - Show this help message",
                            flush=True,
                        )
                        print("   /status              - Show current status", flush=True)
                        print("   /config              - Open config file in editor", flush=True)
                        continue
                    elif command == "/status":
                        print(f"\n{BRIGHT_CYAN}📊 Current Status:{RESET}", flush=True)
                        print(
                            f"   Agents: {len(agents)} ({', '.join(agents.keys())})",
                            flush=True,
                        )
                        use_orch_single = ui_config.get("use_orchestrator_for_single_agent", True)
                        if len(agents) == 1:
                            mode_display = "Single Agent (Orchestrator)" if use_orch_single else "Single Agent (Direct)"
                        else:
                            mode_display = "Multi-Agent"
                        print(f"   Mode: {mode_display}", flush=True)
                        print(
                            f"   History: {len(conversation_history)//2} exchanges",
                            flush=True,
                        )
                        if config_path:
                            print(f"   Config: {config_path}", flush=True)
                        continue
                    elif command == "/config":
                        if config_path:
                            import platform
                            import subprocess

                            try:
                                system = platform.system()
                                if system == "Darwin":  # macOS
                                    subprocess.run(["open", config_path])
                                elif system == "Windows":
                                    subprocess.run(["start", config_path], shell=True)
                                else:  # Linux and others
                                    subprocess.run(["xdg-open", config_path])
                                print(f"\n📝 Opening config file: {config_path}", flush=True)
                            except Exception as e:
                                print(f"\n❌ Error opening config file: {e}", flush=True)
                                print(f"   Config location: {config_path}", flush=True)
                        else:
                            print("\n❌ No config file available (using CLI arguments)", flush=True)
                        continue
                    else:
                        print(f"❓ Unknown command: {command}", flush=True)
                        print("💡 Type /help for available commands", flush=True)
                        continue

                # Handle legacy plain text commands for backwards compatibility
                if question.lower() in ["quit", "exit", "q"]:
                    print("👋 Goodbye!")
                    break

                if question.lower() in ["reset", "clear"]:
                    conversation_history = []
                    for agent in agents.values():
                        agent.reset()
                    print(f"{BRIGHT_YELLOW}🔄 Conversation history cleared!{RESET}")
                    continue

                if not question:
                    print(
                        "Please enter a question or type /help for commands.",
                        flush=True,
                    )
                    continue

                print(f"\n🔄 {BRIGHT_YELLOW}Processing...{RESET}", flush=True)

                # Increment turn counter BEFORE processing so logs go to correct turn_N directory
                next_turn = current_turn + 1

                # Initialize session ID on first turn
                if session_id is None:
                    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                # Reconfigure logging for the turn we're about to process
                setup_logging(debug=_DEBUG_MODE, turn=next_turn)
                logger.info(f"Starting turn {next_turn}")

                # Pass session state for multi-turn filesystem support
                session_info = {
                    "session_id": session_id,
                    "current_turn": current_turn,  # Pass CURRENT turn (for looking up previous turns)
                    "session_storage": session_storage,
                }
                response, updated_session_id, updated_turn = await run_question_with_history(
                    question,
                    agents,
                    ui_config,
                    conversation_history,
                    session_info,
                    **kwargs,
                )

                # Update session state after completion
                session_id = updated_session_id
                current_turn = updated_turn

                if response:
                    # Add to conversation history
                    conversation_history.append({"role": "user", "content": question})
                    conversation_history.append({"role": "assistant", "content": response})
                    print(f"\n{BRIGHT_GREEN}✅ Complete!{RESET}", flush=True)
                    print(
                        f"{BRIGHT_CYAN}💭 History: {len(conversation_history)//2} exchanges{RESET}",
                        flush=True,
                    )
                    print_help_messages()

                else:
                    print(f"\n{BRIGHT_RED}❌ No response generated{RESET}", flush=True)

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}", flush=True)
                print("Please try again or type /quit to exit.", flush=True)

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


async def main(args):
    """Main CLI entry point (async operations only)."""
    # Check if bare `massgen` with no args - use default config if it exists
    if not args.backend and not args.model and not args.config:
        # Use resolve_config_path to check project-level then global config
        resolved_default = resolve_config_path(None)
        if resolved_default:
            # Use discovered config for interactive mode (no question) or single query (with question)
            args.config = str(resolved_default)
        else:
            # No default config - this will be handled by wizard trigger in cli_main()
            if args.question:
                # User provided a question but no config exists - this is an error
                print("❌ Configuration error: No default configuration found.", flush=True)
                print("Run 'massgen --init' to create one, or use 'massgen --model MODEL \"question\"'", flush=True)
                sys.exit(1)
            # No question and no config - wizard will be triggered in cli_main()
            return

    # Validate arguments (only if we didn't auto-set config above)
    if not args.backend:
        if not args.model and not args.config:
            print("❌ Configuration error: Either --config, --model, or --backend must be specified", flush=True)
            sys.exit(1)

    try:
        # Load or create configuration
        if args.config:
            # Resolve config path (handles @examples/, paths, ~/.config/massgen/agents/)
            resolved_path = resolve_config_path(args.config)
            if resolved_path is None:
                # This shouldn't happen if we reached here, but handle it
                raise ConfigurationError("Could not resolve config path")
            config = load_config_file(str(resolved_path))
            if args.debug:
                logger.debug(f"Resolved config path: {resolved_path}")
                logger.debug(f"Config content: {json.dumps(config, indent=2)}")
        else:
            model = args.model
            if args.backend:
                backend = args.backend
            else:
                backend = get_backend_type_from_model(model=model)
            if args.system_message:
                system_message = args.system_message
            else:
                system_message = None
            config = create_simple_config(
                backend_type=backend,
                model=model,
                system_message=system_message,
                base_url=args.base_url,
            )
            if args.debug:
                logger.debug(f"Created simple config with backend: {backend}, model: {model}")
                logger.debug(f"Config content: {json.dumps(config, indent=2)}")

        # Validate that all context paths exist before proceeding
        validate_context_paths(config)

        # Relocate all filesystem paths to .massgen/ directory
        relocate_filesystem_paths(config)

        # Apply command-line overrides
        ui_config = config.get("ui", {})
        if args.no_display:
            ui_config["display_type"] = "simple"
        if args.no_logs:
            ui_config["logging_enabled"] = False
        if args.debug:
            ui_config["debug"] = True
            # Enable logging if debug is on
            ui_config["logging_enabled"] = True
            # # Force simple UI in debug mode
            # ui_config["display_type"] = "simple"

        # Apply timeout overrides from CLI arguments
        timeout_settings = config.get("timeout_settings", {})
        if args.orchestrator_timeout is not None:
            timeout_settings["orchestrator_timeout_seconds"] = args.orchestrator_timeout

        # Update config with timeout settings
        config["timeout_settings"] = timeout_settings

        # Create agents
        if args.debug:
            logger.debug("Creating agents from config...")
        # Extract orchestrator config for agent setup
        orchestrator_cfg = config.get("orchestrator", {})

        # Check if any agent has cwd (filesystem support) and validate orchestrator config
        agent_entries = [config["agent"]] if "agent" in config else config.get("agents", [])
        has_cwd = any("cwd" in agent.get("backend", {}) for agent in agent_entries)

        if has_cwd:
            if not orchestrator_cfg:
                raise ConfigurationError(
                    "Agents with 'cwd' (filesystem support) require orchestrator configuration.\n"
                    "Please add an 'orchestrator' section to your config file.\n\n"
                    "Example (customize paths as needed):\n"
                    "orchestrator:\n"
                    '  snapshot_storage: "your_snapshot_dir"\n'
                    '  agent_temporary_workspace: "your_temp_dir"',
                )

            # Check for required fields in orchestrator config
            if "snapshot_storage" not in orchestrator_cfg:
                raise ConfigurationError(
                    "Missing 'snapshot_storage' in orchestrator configuration.\n"
                    "This is required for agents with filesystem support (cwd).\n\n"
                    "Add to your orchestrator section:\n"
                    '  snapshot_storage: "your_snapshot_dir"  # Directory for workspace snapshots',
                )

            if "agent_temporary_workspace" not in orchestrator_cfg:
                raise ConfigurationError(
                    "Missing 'agent_temporary_workspace' in orchestrator configuration.\n"
                    "This is required for agents with filesystem support (cwd).\n\n"
                    "Add to your orchestrator section:\n"
                    '  agent_temporary_workspace: "your_temp_dir"  # Directory for temporary agent workspaces',
                )

        agents = create_agents_from_config(config, orchestrator_cfg)

        if not agents:
            raise ConfigurationError("No agents configured")

        if args.debug:
            logger.debug(f"Created {len(agents)} agent(s): {list(agents.keys())}")

        # Create timeout config from settings and put it in kwargs
        timeout_settings = config.get("timeout_settings", {})
        timeout_config = TimeoutConfig(**timeout_settings) if timeout_settings else TimeoutConfig()

        kwargs = {"timeout_config": timeout_config}

        # Add orchestrator configuration if present
        if "orchestrator" in config:
            kwargs["orchestrator"] = config["orchestrator"]

        # Run mode based on whether question was provided
        try:
            if args.question:
                await run_single_question(args.question, agents, ui_config, **kwargs)
                # if response:
                #     print(f"\n{BRIGHT_GREEN}Final Response:{RESET}", flush=True)
                #     print(f"{response}", flush=True)
            else:
                # Pass the config path to interactive mode
                config_file_path = str(resolved_path) if args.config and resolved_path else None
                await run_interactive_mode(agents, ui_config, original_config=config, orchestrator_cfg=orchestrator_cfg, config_path=config_file_path, **kwargs)
        finally:
            # Cleanup all agents' filesystem managers (including Docker containers)
            for agent_id, agent in agents.items():
                if hasattr(agent, "backend") and hasattr(agent.backend, "filesystem_manager"):
                    if agent.backend.filesystem_manager:
                        try:
                            agent.backend.filesystem_manager.cleanup()
                        except Exception as e:
                            logger.warning(f"[CLI] Cleanup failed for agent {agent_id}: {e}")

    except ConfigurationError as e:
        print(f"❌ Configuration error: {e}", flush=True)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!", flush=True)
    except Exception as e:
        print(f"❌ Error: {e}", flush=True)
        sys.exit(1)


def cli_main():
    """Synchronous wrapper for CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MassGen - Multi-Agent Coordination CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use configuration file
  python -m massgen.cli --config config.yaml "What is machine learning?"

  # Quick single agent setup
  python -m massgen.cli --backend openai --model gpt-4o-mini "Explain quantum computing"
  python -m massgen.cli --backend claude --model claude-sonnet-4-20250514 "Analyze this data"

  # Use ChatCompletion backend with custom base URL
  python -m massgen.cli --backend chatcompletion --model gpt-oss-120b --base-url https://api.cerebras.ai/v1/chat/completions "What is 2+2?"

  # Interactive mode
  python -m massgen.cli --config config.yaml

  # Timeout control examples
  python -m massgen.cli --config config.yaml --orchestrator-timeout 600 "Complex task"

  # Create sample configurations
  python -m massgen.cli --create-samples

Environment Variables:
    OPENAI_API_KEY      - Required for OpenAI backend
    XAI_API_KEY         - Required for Grok backend
    ANTHROPIC_API_KEY   - Required for Claude backend
    GOOGLE_API_KEY      - Required for Gemini backend (or GEMINI_API_KEY)
    ZAI_API_KEY         - Required for ZAI backend

    CEREBRAS_API_KEY    - For Cerebras AI (cerebras.ai)
    TOGETHER_API_KEY    - For Together AI (together.ai, together.xyz)
    FIREWORKS_API_KEY   - For Fireworks AI (fireworks.ai)
    GROQ_API_KEY        - For Groq (groq.com)
    NEBIUS_API_KEY      - For Nebius AI Studio (studio.nebius.ai)
    OPENROUTER_API_KEY  - For OpenRouter (openrouter.ai)
    POE_API_KEY         - For POE (poe.com)

  Note: The chatcompletion backend auto-detects the provider from the base_url
        and uses the appropriate environment variable for API key.
        """,
    )

    # Question (optional for interactive mode)
    parser.add_argument(
        "question",
        nargs="?",
        help="Question to ask (optional - if not provided, enters interactive mode)",
    )

    # Configuration options
    config_group = parser.add_mutually_exclusive_group()
    config_group.add_argument("--config", type=str, help="Path to YAML/JSON configuration file or @examples/NAME")
    config_group.add_argument(
        "--backend",
        type=str,
        choices=[
            "chatcompletion",
            "claude",
            "gemini",
            "grok",
            "openai",
            "azure_openai",
            "claude_code",
            "zai",
            "lmstudio",
            "vllm",
            "sglang",
        ],
        help="Backend type for quick setup",
    )

    # Quick setup options
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name for quick setup",
    )
    parser.add_argument("--system-message", type=str, help="System message for quick setup")
    parser.add_argument(
        "--base-url",
        type=str,
        help="Base URL for API endpoint (e.g., https://api.cerebras.ai/v1/chat/completions)",
    )

    # UI options
    parser.add_argument("--no-display", action="store_true", help="Disable visual coordination display")
    parser.add_argument("--no-logs", action="store_true", help="Disable logging")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with verbose logging")
    parser.add_argument(
        "--init",
        action="store_true",
        help="Launch interactive configuration builder to create config file",
    )
    parser.add_argument(
        "--list-examples",
        action="store_true",
        help="List available example configurations from package",
    )
    parser.add_argument(
        "--example",
        type=str,
        help="Print example config to stdout (e.g., --example basic_multi)",
    )
    parser.add_argument(
        "--show-schema",
        action="store_true",
        help="Display configuration schema and available parameters",
    )
    parser.add_argument(
        "--schema-backend",
        type=str,
        help="Show schema for specific backend (use with --show-schema)",
    )
    parser.add_argument(
        "--with-examples",
        action="store_true",
        help="Include example configurations in schema display",
    )

    # Timeout options
    timeout_group = parser.add_argument_group("timeout settings", "Override timeout settings from config")
    timeout_group.add_argument(
        "--orchestrator-timeout",
        type=int,
        help="Maximum time for orchestrator coordination in seconds (default: 1800)",
    )

    args = parser.parse_args()

    # Always setup logging (will save INFO to file, console output depends on debug flag)
    setup_logging(debug=args.debug)

    if args.debug:
        logger.info("Debug mode enabled")
        logger.debug(f"Command line arguments: {vars(args)}")

    # Handle special commands first
    if args.list_examples:
        show_available_examples()
        return

    if args.example:
        print_example_config(args.example)
        return

    if args.show_schema:
        from .schema_display import show_schema

        show_schema(backend=args.schema_backend, show_examples=args.with_examples)
        return

    # Launch interactive config builder if requested
    if args.init:
        from .config_builder import ConfigBuilder

        builder = ConfigBuilder()
        result = builder.run()

        if result and len(result) == 2:
            filepath, question = result
            if filepath and question:
                # Update args to use the newly created config
                args.config = filepath
                args.question = question
            elif filepath:
                # Config created but user chose not to run
                print(f"\n✅ Configuration saved to: {filepath}")
                print(f'Run with: python -m massgen.cli --config {filepath} "Your question"')
                return
            else:
                # User cancelled
                return
        else:
            # Builder returned None (cancelled or error)
            return

    # First-run detection: auto-trigger builder if no config specified and first run
    if not args.question and not args.config and not args.model and not args.backend:
        if should_run_builder():
            print()
            print()
            print(f"{BRIGHT_CYAN}{'=' * 60}{RESET}")
            print(f"{BRIGHT_CYAN}  👋  Welcome to MassGen!{RESET}")
            print(f"{BRIGHT_CYAN}{'=' * 60}{RESET}")
            print()
            print("  Let's set up your default configuration...")
            print()

            from .config_builder import ConfigBuilder

            builder = ConfigBuilder(default_mode=True)
            result = builder.run()

            if result and len(result) == 2:
                filepath, question = result
                if filepath:
                    args.config = filepath
                    if question:
                        args.question = question
                    else:
                        print("\n✅ Configuration saved! You can now run queries.")
                        print('Example: massgen "Your question here"')
                        return
                else:
                    return
            else:
                return

    # Now call the async main with the parsed arguments
    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        # User pressed Ctrl+C - exit gracefully without traceback
        pass


if __name__ == "__main__":
    cli_main()
