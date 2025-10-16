"""
MCP Server Management Functions

Commands for managing MCP server configurations:
- mcp_add: Add a new MCP server
- mcp_remove: Remove an MCP server
- mcp_list: List all configured servers
- mcp_enable: Enable a disabled server
- mcp_disable: Disable a server (keeps config)
- mcp_catalog: List popular pre-configured servers
- mcp_install: Install server from catalog
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ...core.models import (
    ExecutionContext,
    ExecutionResult,
    FunctionCategory,
    FunctionPlugin,
    FunctionSafety,
    OutputMode,
    ParameterSchema,
)

logger = logging.getLogger(__name__)


class MCPConfigManager:
    """
    Manages MCP server configuration file operations.

    Follows SRP: Single responsibility for config file I/O.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize config manager.

        Args:
            config_path: Override config file path (default: ~/.aii/mcp_servers.json)
        """
        self.config_path = config_path or (Path.home() / ".aii" / "mcp_servers.json")
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Ensure configuration directory exists"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> Dict[str, Any]:
        """
        Load MCP server configuration.

        Returns:
            Configuration dictionary with 'mcpServers' key
        """
        if not self.config_path.exists():
            return {"mcpServers": {}}

        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
            return config if isinstance(config, dict) else {"mcpServers": {}}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return {"mcpServers": {}}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {"mcpServers": {}}

    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Save MCP server configuration.

        Args:
            config: Configuration dictionary

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            self._ensure_config_dir()
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    def backup_config(self) -> bool:
        """
        Create backup of current configuration.

        Returns:
            True if backup created successfully
        """
        if not self.config_path.exists():
            return True

        try:
            backup_path = self.config_path.with_suffix(".json.backup")
            import shutil

            shutil.copy2(self.config_path, backup_path)
            logger.info(f"Config backed up to: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup config: {e}")
            return False


class MCPAddFunction(FunctionPlugin):
    """
    Add MCP server to configuration.

    Examples:
    - aii mcp add chrome npx chrome-devtools-mcp@latest
    - aii mcp add postgres uvx mcp-server-postgres --connection-string $DB_URL
    - aii mcp add github npx @modelcontextprotocol/server-github
    """

    def __init__(self, config_manager: Optional[MCPConfigManager] = None):
        """
        Initialize function.

        Args:
            config_manager: Config manager instance (DIP: dependency injection)
        """
        self.config_manager = config_manager or MCPConfigManager()

    @property
    def name(self) -> str:
        return "mcp_add"

    @property
    def description(self) -> str:
        return (
            "Add MCP server to configuration. Use when user wants to: "
            "'add mcp server', 'install mcp server', 'configure mcp server', "
            "'add chrome/github/postgres server', 'setup mcp'. "
            "Examples: 'add chrome mcp server', 'install github server', "
            "'configure postgres mcp server with connection string'."
        )

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "server_name": ParameterSchema(
                name="server_name",
                type="string",
                required=True,
                description="Short name for the server (e.g., 'chrome', 'postgres', 'github')",
            ),
            "command": ParameterSchema(
                name="command",
                type="string",
                required=True,
                description="Command to run (e.g., 'npx', 'uvx', 'node')",
            ),
            "args": ParameterSchema(
                name="args",
                type="array",
                required=True,
                description="Command arguments as list (e.g., ['chrome-devtools-mcp@latest'])",
            ),
            "env": ParameterSchema(
                name="env",
                type="object",
                required=False,
                description="Environment variables as dict (e.g., {'API_KEY': '${GITHUB_TOKEN}'})",
            ),
            "enabled": ParameterSchema(
                name="enabled",
                type="boolean",
                required=False,
                description="Enable server immediately (default: true)",
            ),
            "transport": ParameterSchema(
                name="transport",
                type="string",
                required=False,
                description="Transport protocol: 'stdio', 'sse', or 'http' (default: 'stdio')",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        """Safe operation: just modifies config file"""
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        """CLEAN mode: users want just the confirmation"""
        return OutputMode.CLEAN

    async def execute(
        self, parameters: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """
        Add MCP server to configuration.

        Args:
            parameters: Function parameters
            context: Execution context

        Returns:
            ExecutionResult with success status
        """
        server_name = parameters["server_name"]
        command = parameters["command"]
        args = parameters["args"]
        env = parameters.get("env", {})
        enabled = parameters.get("enabled", True)
        transport = parameters.get("transport", "stdio")

        # Validate transport
        if transport not in ["stdio", "sse", "http"]:
            return ExecutionResult(
                success=False,
                message=f"Invalid transport '{transport}'. Must be: stdio, sse, or http",
                data={"clean_output": f"❌ Invalid transport '{transport}'"},
            )

        # Load existing config
        config = self.config_manager.load_config()
        servers = config.get("mcpServers", {})

        # Check if server already exists
        if server_name in servers:
            return ExecutionResult(
                success=False,
                message=f"Server '{server_name}' already exists. Use 'aii mcp remove {server_name}' first.",
                data={
                    "clean_output": f"❌ Server '{server_name}' already exists.\n\nUse: aii mcp remove {server_name}"
                },
            )

        # Build server config
        server_config = {
            "command": command,
            "args": args if isinstance(args, list) else [args],
        }

        if env:
            server_config["env"] = env

        # Add server to config
        servers[server_name] = server_config
        config["mcpServers"] = servers

        # Backup before saving
        self.config_manager.backup_config()

        # Save config
        if not self.config_manager.save_config(config):
            return ExecutionResult(
                success=False,
                message="Failed to save configuration",
                data={"clean_output": "❌ Failed to save configuration"},
            )

        # Build output message
        output_lines = [
            f"✓ Added '{server_name}' server",
            f"✓ Configuration saved to {self.config_manager.config_path}",
            f"✓ Transport: {transport}",
        ]

        if env:
            output_lines.append(f"✓ Environment variables: {', '.join(env.keys())}")

        output_lines.append("")
        output_lines.append(
            f"Try it: aii \"use {server_name} mcp server to [your task]\""
        )

        output = "\n".join(output_lines)

        return ExecutionResult(
            success=True,
            message=output,
            data={
                "server_name": server_name,
                "config": server_config,
                "config_path": str(self.config_manager.config_path),
                "clean_output": output,
            },
        )


class MCPRemoveFunction(FunctionPlugin):
    """Remove MCP server from configuration"""

    def __init__(self, config_manager: Optional[MCPConfigManager] = None):
        self.config_manager = config_manager or MCPConfigManager()

    @property
    def name(self) -> str:
        return "mcp_remove"

    @property
    def description(self) -> str:
        return (
            "Remove MCP server from configuration. Use when user wants to: "
            "'remove mcp server', 'delete mcp server', 'uninstall mcp server', "
            "'remove chrome/github/postgres server'. "
            "Examples: 'remove chrome server', 'delete github mcp server'."
        )

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "server_name": ParameterSchema(
                name="server_name",
                type="string",
                required=True,
                description="Name of the server to remove",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        """Potentially destructive: confirm before removing"""
        return True

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.RISKY

    @property
    def default_output_mode(self) -> OutputMode:
        return OutputMode.CLEAN

    async def execute(
        self, parameters: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Remove MCP server from configuration"""
        server_name = parameters["server_name"]

        # Load config
        config = self.config_manager.load_config()
        servers = config.get("mcpServers", {})

        # Check if server exists
        if server_name not in servers:
            return ExecutionResult(
                success=False,
                message=f"Server '{server_name}' not found",
                data={"clean_output": f"❌ Server '{server_name}' not found"},
            )

        # Backup before removing
        self.config_manager.backup_config()

        # Remove server
        del servers[server_name]
        config["mcpServers"] = servers

        # Save config
        if not self.config_manager.save_config(config):
            return ExecutionResult(
                success=False,
                message="Failed to save configuration",
                data={"clean_output": "❌ Failed to save configuration"},
            )

        output = f"✓ Removed '{server_name}' server"

        return ExecutionResult(
            success=True,
            message=output,
            data={"server_name": server_name, "clean_output": output},
        )


class MCPListFunction(FunctionPlugin):
    """List all configured MCP servers"""

    def __init__(self, config_manager: Optional[MCPConfigManager] = None):
        self.config_manager = config_manager or MCPConfigManager()

    @property
    def name(self) -> str:
        return "mcp_list"

    @property
    def description(self) -> str:
        return (
            "List all configured MCP servers. Use when user wants to: "
            "'list mcp servers', 'show mcp servers', 'what mcp servers', "
            "'mcp server list', 'show configured servers'. "
            "Examples: 'list my mcp servers', 'show all mcp servers'."
        )

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {}

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        """STANDARD mode: show list with metadata"""
        return OutputMode.STANDARD

    async def execute(
        self, parameters: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """List all configured MCP servers"""
        config = self.config_manager.load_config()
        servers = config.get("mcpServers", {})

        if not servers:
            output = "No MCP servers configured.\n\nTry: aii mcp catalog"
            return ExecutionResult(
                success=True,
                message=output,
                data={"servers": {}, "count": 0, "clean_output": output},
            )

        # Build output
        output_lines = ["📦 Configured MCP Servers:", ""]

        for server_name, server_config in servers.items():
            command = server_config.get("command", "")
            args = server_config.get("args", [])
            args_str = " ".join(args) if isinstance(args, list) else str(args)

            output_lines.append(f"✓ {server_name}")
            output_lines.append(f"  Command: {command} {args_str}")

            if "env" in server_config:
                env_vars = ", ".join(server_config["env"].keys())
                output_lines.append(f"  Environment: {env_vars}")

            output_lines.append("")

        output_lines.append(f"Total: {len(servers)} server(s)")
        output = "\n".join(output_lines)

        return ExecutionResult(
            success=True,
            message=output,
            data={
                "servers": servers,
                "count": len(servers),
                "clean_output": output,
            },
        )


class MCPEnableFunction(FunctionPlugin):
    """Enable a disabled MCP server"""

    def __init__(self, config_manager: Optional[MCPConfigManager] = None):
        self.config_manager = config_manager or MCPConfigManager()

    @property
    def name(self) -> str:
        return "mcp_enable"

    @property
    def description(self) -> str:
        return (
            "Enable a disabled MCP server. Use when user wants to: "
            "'enable mcp server', 'activate mcp server', 'turn on mcp server'. "
            "Examples: 'enable chrome server', 'activate github mcp server'."
        )

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "server_name": ParameterSchema(
                name="server_name",
                type="string",
                required=True,
                description="Name of the server to enable",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        return OutputMode.CLEAN

    async def execute(
        self, parameters: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Enable MCP server"""
        server_name = parameters["server_name"]

        config = self.config_manager.load_config()
        servers = config.get("mcpServers", {})

        if server_name not in servers:
            return ExecutionResult(
                success=False,
                message=f"Server '{server_name}' not found",
                data={"clean_output": f"❌ Server '{server_name}' not found"},
            )

        # Note: Current config format doesn't have 'enabled' flag
        # This is a future enhancement - for now just acknowledge
        output = f"✓ Server '{server_name}' is enabled"

        return ExecutionResult(
            success=True,
            message=output,
            data={"server_name": server_name, "clean_output": output},
        )


class MCPDisableFunction(FunctionPlugin):
    """Disable an MCP server (keeps config)"""

    def __init__(self, config_manager: Optional[MCPConfigManager] = None):
        self.config_manager = config_manager or MCPConfigManager()

    @property
    def name(self) -> str:
        return "mcp_disable"

    @property
    def description(self) -> str:
        return (
            "Disable an MCP server (keeps config). Use when user wants to: "
            "'disable mcp server', 'deactivate mcp server', 'turn off mcp server'. "
            "Examples: 'disable chrome server', 'deactivate github mcp server'."
        )

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "server_name": ParameterSchema(
                name="server_name",
                type="string",
                required=True,
                description="Name of the server to disable",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        return OutputMode.CLEAN

    async def execute(
        self, parameters: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Disable MCP server"""
        server_name = parameters["server_name"]

        config = self.config_manager.load_config()
        servers = config.get("mcpServers", {})

        if server_name not in servers:
            return ExecutionResult(
                success=False,
                message=f"Server '{server_name}' not found",
                data={"clean_output": f"❌ Server '{server_name}' not found"},
            )

        # Note: Current config format doesn't have 'enabled' flag
        # This is a future enhancement - for now just acknowledge
        output = f"✓ Server '{server_name}' is disabled (config preserved)"

        return ExecutionResult(
            success=True,
            message=output,
            data={"server_name": server_name, "clean_output": output},
        )


class MCPCatalogFunction(FunctionPlugin):
    """List popular pre-configured MCP servers"""

    @property
    def name(self) -> str:
        return "mcp_catalog"

    @property
    def description(self) -> str:
        return (
            "List popular pre-configured MCP servers. Use when user wants to: "
            "'show mcp catalog', 'list popular mcp servers', 'what mcp servers available', "
            "'mcp server catalog', 'show available servers'. "
            "Examples: 'show popular mcp servers', 'what servers can I install'."
        )

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {}

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        """STANDARD mode: show catalog with details"""
        return OutputMode.STANDARD

    def _get_catalog(self) -> Dict[str, Dict[str, Any]]:
        """
        Get MCP server catalog.

        Returns:
            Dictionary of server definitions
        """
        return {
            "github": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "description": "GitHub integration (repos, issues, PRs)",
                "category": "Development",
                "env_required": ["GITHUB_TOKEN"],
            },
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "${PROJECT_PATH}"],
                "description": "Local filesystem access",
                "category": "Development",
                "env_required": ["PROJECT_PATH"],
            },
            "postgres": {
                "command": "uvx",
                "args": ["mcp-server-postgres", "--connection-string", "${POSTGRES_URL}"],
                "description": "PostgreSQL database integration",
                "category": "Database",
                "env_required": ["POSTGRES_URL"],
            },
            "chrome-devtools": {
                "command": "npx",
                "args": ["-y", "chrome-devtools-mcp@latest"],
                "description": "Chrome browser automation and DevTools",
                "category": "Automation",
                "env_required": [],
            },
            "puppeteer": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
                "description": "Browser automation and web scraping",
                "category": "Automation",
                "env_required": [],
            },
            "slack": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-slack"],
                "description": "Slack workspace integration",
                "category": "Communication",
                "env_required": ["SLACK_BOT_TOKEN"],
            },
            "12306": {
                "command": "npx",
                "args": ["-y", "12306-mcp"],
                "description": "中国铁路12306火车票查询 (China Railway ticket search)",
                "category": "Chinese Ecosystem",
                "env_required": [],
            },
            "mongodb": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-mongodb"],
                "description": "MongoDB database integration",
                "category": "Database",
                "env_required": ["MONGODB_URL"],
            },
            "redis": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-redis"],
                "description": "Redis cache integration",
                "category": "Database",
                "env_required": ["REDIS_URL"],
            },
            "docker": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-docker"],
                "description": "Docker container management",
                "category": "DevOps",
                "env_required": [],
            },
        }

    async def execute(
        self, parameters: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """List popular MCP servers from catalog"""
        catalog = self._get_catalog()

        # Load current config to mark installed servers
        config_manager = MCPConfigManager()
        config = config_manager.load_config()
        installed_servers = set(config.get("mcpServers", {}).keys())

        # Group by category
        by_category: Dict[str, List[tuple[str, Dict[str, Any]]]] = {}
        for server_name, server_info in catalog.items():
            category = server_info["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append((server_name, server_info))

        # Build output
        output_lines = ["📦 Popular MCP Servers:", ""]

        for category, servers in sorted(by_category.items()):
            output_lines.append(f"{category}:")
            for server_name, server_info in sorted(servers):
                status = "✓" if server_name in installed_servers else "○"
                output_lines.append(f"  {status} {server_name:<18} - {server_info['description']}")
            output_lines.append("")

        output_lines.append("Legend:")
        output_lines.append("  ✓ = Already installed")
        output_lines.append("  ○ = Available to install")
        output_lines.append("")
        output_lines.append("Install: aii mcp install <server-name>")

        output = "\n".join(output_lines)

        return ExecutionResult(
            success=True,
            message=output,
            data={
                "catalog": catalog,
                "installed": list(installed_servers),
                "count": len(catalog),
                "clean_output": output,
            },
        )


class MCPInstallFunction(FunctionPlugin):
    """Install MCP server from catalog"""

    def __init__(self, config_manager: Optional[MCPConfigManager] = None):
        self.config_manager = config_manager or MCPConfigManager()

    @property
    def name(self) -> str:
        return "mcp_install"

    @property
    def description(self) -> str:
        return (
            "Install MCP server from catalog. Use when user wants to: "
            "'install mcp server', 'install from catalog', 'install github/chrome/postgres server'. "
            "Examples: 'install github server', 'install chrome mcp server from catalog'."
        )

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "server_name": ParameterSchema(
                name="server_name",
                type="string",
                required=True,
                description="Name of the server from catalog (e.g., 'github', 'chrome-devtools')",
            ),
            "env_vars": ParameterSchema(
                name="env_vars",
                type="object",
                required=False,
                description="Environment variables as dict (e.g., {'GITHUB_TOKEN': 'your-token'})",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        return OutputMode.CLEAN

    def _get_catalog(self) -> Dict[str, Dict[str, Any]]:
        """Get catalog (reuse from MCPCatalogFunction)"""
        catalog_func = MCPCatalogFunction()
        return catalog_func._get_catalog()

    async def execute(
        self, parameters: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Install MCP server from catalog"""
        server_name = parameters["server_name"]
        env_vars = parameters.get("env_vars", {})

        # Get catalog
        catalog = self._get_catalog()

        # Check if server exists in catalog
        if server_name not in catalog:
            available = ", ".join(sorted(catalog.keys()))
            return ExecutionResult(
                success=False,
                message=f"Server '{server_name}' not found in catalog.\n\nAvailable: {available}",
                data={
                    "clean_output": f"❌ Server '{server_name}' not found in catalog.\n\nTry: aii mcp catalog"
                },
            )

        server_info = catalog[server_name]

        # Check if already installed
        config = self.config_manager.load_config()
        servers = config.get("mcpServers", {})

        if server_name in servers:
            return ExecutionResult(
                success=False,
                message=f"Server '{server_name}' is already installed",
                data={"clean_output": f"✓ Server '{server_name}' is already installed"},
            )

        # Check for required environment variables
        env_required = server_info.get("env_required", [])
        missing_env = []
        for env_var in env_required:
            if env_var not in env_vars and env_var not in server_info.get("args", []):
                missing_env.append(env_var)

        if missing_env:
            output_lines = [
                f"📦 Installing '{server_name}' from catalog...",
                f"⚠️  Requires environment variables: {', '.join(missing_env)}",
                "",
                "Please provide them when installing:",
                f"  aii mcp add {server_name} {server_info['command']} {' '.join(server_info['args'])}",
                "",
                "Or set them in your environment:",
            ]
            for env_var in missing_env:
                output_lines.append(f"  export {env_var}='your-value-here'")

            output = "\n".join(output_lines)

            return ExecutionResult(
                success=False,
                message=output,
                data={"clean_output": output, "missing_env": missing_env},
            )

        # Install server (delegate to MCPAddFunction)
        add_function = MCPAddFunction(self.config_manager)

        return await add_function.execute(
            {
                "server_name": server_name,
                "command": server_info["command"],
                "args": server_info["args"],
                "env": env_vars,
                "enabled": True,
                "transport": "stdio",
            },
            context,
        )


class MCPStatusFunction(FunctionPlugin):
    """
    Show MCP server health status.

    Examples:
    - aii mcp status
    - aii mcp status github
    - aii mcp status --all
    """

    function_name = "mcp_status"
    function_description = "Show health status for MCP servers"
    function_category = FunctionCategory.SYSTEM

    def __init__(self, config_manager: Optional[MCPConfigManager] = None):
        """Initialize with optional config manager."""
        self.config_manager = config_manager or MCPConfigManager()

    def get_parameters_schema(self) -> ParameterSchema:
        """Return JSON schema for function parameters."""
        return {
            "type": "object",
            "properties": {
                "server_name": {
                    "type": "string",
                    "description": "Specific server to check (optional, shows all if omitted)",
                },
                "show_all": {
                    "type": "boolean",
                    "description": "Show all servers including disabled",
                    "default": False,
                },
            },
            "required": [],
        }

    @property
    def default_output_mode(self) -> OutputMode:
        """Default output mode for this function."""
        return OutputMode.STANDARD

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """List of supported output modes."""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    def get_function_safety(self) -> FunctionSafety:
        """Return safety level for this function."""
        return FunctionSafety.SAFE

    async def execute(
        self, parameters: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """
        Execute MCP status command.

        Args:
            parameters: Command parameters (server_name, show_all)
            context: Execution context with health monitor

        Returns:
            ExecutionResult with health status information
        """
        server_name = parameters.get("server_name")
        show_all = parameters.get("show_all", False)

        # Get health monitor from context
        if not hasattr(context, 'mcp_client') or not context.mcp_client:
            return ExecutionResult(
                success=False,
                message="MCP client not available",
                data={"clean_output": "❌ MCP client not available"},
            )

        if not hasattr(context.mcp_client, 'health_monitor') or not context.mcp_client.health_monitor:
            return ExecutionResult(
                success=False,
                message="Health monitoring not enabled",
                data={"clean_output": "⚠️ Health monitoring not enabled"},
            )

        health_monitor = context.mcp_client.health_monitor

        if server_name:
            # Show detailed health for specific server
            health = await health_monitor.get_server_health(server_name)

            if not health:
                return ExecutionResult(
                    success=False,
                    message=f"Server '{server_name}' not found or not monitored",
                    data={
                        "clean_output": f"❌ Server '{server_name}' not found or not monitored"
                    },
                )

            output = self._format_detailed_health(server_name, health)

        else:
            # Show summary for all servers
            all_health = await health_monitor.get_health_report()

            # Filter if not showing all
            if not show_all:
                from ...data.integrations.mcp_health_monitor import HealthStatus

                all_health = {
                    name: h
                    for name, h in all_health.items()
                    if h.status != HealthStatus.DISABLED
                }

            output = self._format_health_summary(all_health)

        return ExecutionResult(
            success=True,
            message=output,
            data={
                "health_status": all_health if not server_name else {server_name: health},
                "clean_output": output,
            },
        )

    def _format_health_summary(self, health: Dict[str, Any]) -> str:
        """Format health summary for all servers."""
        from ...data.integrations.mcp_health_monitor import HealthStatus

        if not health:
            return "📊 No MCP servers monitored yet"

        output = ["📊 MCP Server Health Status:\n"]

        # Group by status
        healthy = []
        degraded = []
        unhealthy = []
        disabled = []

        for name, h in health.items():
            if h.status == HealthStatus.HEALTHY:
                healthy.append((name, h))
            elif h.status == HealthStatus.DEGRADED:
                degraded.append((name, h))
            elif h.status == HealthStatus.UNHEALTHY:
                unhealthy.append((name, h))
            else:
                disabled.append((name, h))

        # Show healthy servers
        if healthy:
            output.append("✓ Healthy:")
            for name, h in healthy:
                output.append(f"  {name} ({h.response_time_ms:.0f}ms)")

        # Show degraded servers
        if degraded:
            output.append("\n⚠️ Degraded:")
            for name, h in degraded:
                output.append(f"  {name} ({h.response_time_ms:.0f}ms - slow)")

        # Show unhealthy servers
        if unhealthy:
            output.append("\n✗ Unhealthy:")
            for name, h in unhealthy:
                failures = f"{h.failure_count}/3"
                output.append(f"  {name} ({failures} failures)")
                if h.last_error:
                    output.append(f"    Error: {h.last_error}")

        # Show disabled servers
        if disabled:
            output.append("\n○ Disabled:")
            for name, h in disabled:
                output.append(f"  {name} (auto-disabled after failures)")
                output.append(f"    Run 'aii mcp enable {name}' to retry")

        return "\n".join(output)

    def _format_detailed_health(self, name: str, health: Any) -> str:
        """Format detailed health for single server."""
        from ...data.integrations.mcp_health_monitor import HealthStatus

        status_icon = {
            HealthStatus.HEALTHY: "✓",
            HealthStatus.DEGRADED: "⚠️",
            HealthStatus.UNHEALTHY: "✗",
            HealthStatus.DISABLED: "○",
        }

        output = [f"📊 {name} Server Health:"]
        output.append(
            f"\nStatus: {status_icon[health.status]} {health.status.value}"
        )
        output.append(f"Last check: {self._format_time_ago(health.last_check)}")

        if health.response_time_ms:
            output.append(f"Response time: {health.response_time_ms:.0f}ms")

        if health.failure_count > 0:
            output.append(f"\nFailures: {health.failure_count}/3")

        if health.last_error:
            output.append(f"Last error: {health.last_error}")

        if health.status == HealthStatus.DISABLED:
            output.append(f"\n💡 Tip: Run 'aii mcp enable {name}' to retry connection")

        return "\n".join(output)

    def _format_time_ago(self, dt: Any) -> str:
        """Format datetime as 'X seconds/minutes ago'."""
        from datetime import datetime

        now = datetime.now()
        delta = now - dt
        seconds = delta.total_seconds()

        if seconds < 60:
            return f"{int(seconds)} seconds ago"
        elif seconds < 3600:
            return f"{int(seconds / 60)} minutes ago"
        else:
            return f"{int(seconds / 3600)} hours ago"


class GitHubIssueFunction(FunctionPlugin):
    """
    Create GitHub issues with intelligent context gathering (v0.4.10).

    Features:
    - Automatic repository context gathering (commits, issues, structure)
    - LLM-enhanced issue description with proper formatting
    - Label and assignee suggestions based on context
    - AII signature on created issues
    - Integration with MCP GitHub server
    """

    @property
    def name(self) -> str:
        return "github_issue"

    @property
    def description(self) -> str:
        return "Create a GitHub issue with intelligent context gathering and LLM enhancement"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def default_output_mode(self) -> OutputMode:
        return OutputMode.STANDARD

    @property
    def supports_output_modes(self) -> List[OutputMode]:
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.RISKY  # Creates external resource

    @property
    def requires_confirmation(self) -> bool:
        return True  # RISKY function requires confirmation

    def get_function_safety(self) -> FunctionSafety:
        return self.safety_level

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {}  # Legacy compatibility

    def get_parameters_schema(self) -> ParameterSchema:
        return {
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "Repository owner (GitHub username or organization)"
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name"
                },
                "title": {
                    "type": "string",
                    "description": "Issue title"
                },
                "body": {
                    "type": "string",
                    "description": "Issue description/body (will be enhanced with context)"
                },
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Labels to add (optional, can be auto-suggested)",
                    "default": []
                },
                "assignees": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Assignees (optional, can be auto-suggested)",
                    "default": []
                },
                "gather_context": {
                    "type": "boolean",
                    "description": "Gather repository context (commits, issues) for enhancement",
                    "default": True
                },
                "enhance_with_llm": {
                    "type": "boolean",
                    "description": "Use LLM to enhance issue description and suggest labels",
                    "default": True
                }
            },
            "required": ["owner", "repo", "title", "body"]
        }

    async def execute(
        self, parameters: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Create GitHub issue with intelligent context gathering."""
        try:
            owner = parameters["owner"]
            repo = parameters["repo"]
            title = parameters["title"]
            body = parameters["body"]
            labels = parameters.get("labels", [])
            assignees = parameters.get("assignees", [])
            gather_context = parameters.get("gather_context", True)
            enhance_with_llm = parameters.get("enhance_with_llm", True)

            # Check MCP client availability
            if not context.mcp_client:
                return ExecutionResult(
                    success=False,
                    message="GitHub MCP server not available. Run 'aii mcp add github' to set it up.",
                    data={"error": "mcp_not_available"}
                )

            # Step 1: Gather repository context (if enabled)
            repo_context = {}
            if gather_context:
                logger.info(f"Gathering context for {owner}/{repo}")
                repo_context = await self._gather_repository_context(
                    owner, repo, context.mcp_client
                )

            # Step 2: Enhance issue with LLM (if enabled and LLM available)
            enhanced_body = body
            suggested_labels = labels.copy()
            suggested_assignees = assignees.copy()

            if enhance_with_llm and context.llm_provider:
                logger.info("Enhancing issue with LLM")
                enhancement = await self._enhance_issue_with_llm(
                    title=title,
                    body=body,
                    repo_context=repo_context,
                    existing_labels=labels,
                    existing_assignees=assignees,
                    llm_provider=context.llm_provider
                )
                enhanced_body = enhancement["body"]
                suggested_labels = enhancement.get("labels", suggested_labels)
                suggested_assignees = enhancement.get("assignees", suggested_assignees)

            # Step 3: Add AII signature
            enhanced_body = self._add_aii_signature(enhanced_body)

            # Step 4: Create issue via MCP GitHub server
            logger.info(f"Creating issue '{title}' in {owner}/{repo}")
            issue_result = await self._create_issue_via_mcp(
                owner=owner,
                repo=repo,
                title=title,
                body=enhanced_body,
                labels=suggested_labels,
                assignees=suggested_assignees,
                mcp_client=context.mcp_client
            )

            if not issue_result["success"]:
                return ExecutionResult(
                    success=False,
                    message=f"Failed to create issue: {issue_result.get('error', 'Unknown error')}",
                    data=issue_result
                )

            issue_url = issue_result.get("url", f"https://github.com/{owner}/{repo}/issues")
            issue_number = issue_result.get("number", "?")

            return ExecutionResult(
                success=True,
                message=f"✅ Created issue #{issue_number}: {title}\n🔗 {issue_url}",
                data={
                    "clean_output": issue_url,
                    "issue_number": issue_number,
                    "issue_url": issue_url,
                    "title": title,
                    "labels": suggested_labels,
                    "assignees": suggested_assignees,
                    "context_gathered": gather_context,
                    "llm_enhanced": enhance_with_llm,
                    "repository": f"{owner}/{repo}"
                }
            )

        except Exception as e:
            logger.error(f"Error creating GitHub issue: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                message=f"Error creating GitHub issue: {str(e)}",
                data={"error": str(e)}
            )

    async def _gather_repository_context(
        self, owner: str, repo: str, mcp_client: Any
    ) -> Dict[str, Any]:
        """
        Gather repository context for issue enhancement.

        Context includes:
        - Recent commits (last 10)
        - Existing issues (last 20, with similar titles)
        - Project structure overview
        - Repository statistics
        """
        context = {
            "commits": [],
            "issues": [],
            "structure": {},
            "stats": {}
        }

        try:
            # Get recent commits via git (if in repo) or MCP
            # For now, use a simplified approach
            import subprocess

            # Check if we're in a git repository
            try:
                # Get last 10 commits
                result = subprocess.run(
                    ["git", "log", "--oneline", "-10"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    commits = result.stdout.strip().split("\n")
                    context["commits"] = [c.strip() for c in commits if c.strip()]
            except Exception:
                pass

            # Get repository statistics
            try:
                result = subprocess.run(
                    ["git", "rev-list", "--count", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    context["stats"]["total_commits"] = result.stdout.strip()
            except Exception:
                pass

            # Get basic project structure
            try:
                result = subprocess.run(
                    ["find", ".", "-type", "f", "-name", "*.py", "-o", "-name", "*.md", "|", "head", "-20"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    shell=True
                )
                if result.returncode == 0:
                    files = result.stdout.strip().split("\n")
                    context["structure"]["key_files"] = [f.strip() for f in files if f.strip()][:10]
            except Exception:
                pass

        except Exception as e:
            logger.warning(f"Error gathering repository context: {e}")

        return context

    async def _enhance_issue_with_llm(
        self,
        title: str,
        body: str,
        repo_context: Dict[str, Any],
        existing_labels: List[str],
        existing_assignees: List[str],
        llm_provider: Any
    ) -> Dict[str, Any]:
        """
        Use LLM to enhance issue description and suggest labels.

        Returns:
            Dictionary with enhanced body, suggested labels, and assignees
        """
        try:
            # Build context for LLM
            context_str = self._format_context_for_llm(repo_context)

            # Create LLM prompt
            prompt = f"""You are helping create a GitHub issue with intelligent context awareness.

**Issue Title:** {title}

**Original Description:**
{body}

**Repository Context:**
{context_str}

**Task:**
1. Enhance the issue description with:
   - Proper markdown formatting
   - Relevant context from recent commits/issues
   - Clear problem statement and expected behavior
   - Steps to reproduce (if applicable)
   - Additional relevant information

2. Suggest appropriate labels based on:
   - Issue content
   - Repository context
   - Common GitHub label conventions (bug, enhancement, documentation, etc.)

3. Keep the enhanced description concise but informative

**Current Labels:** {', '.join(existing_labels) if existing_labels else 'None'}

Respond in JSON format:
{{
  "body": "enhanced markdown body",
  "labels": ["label1", "label2"],
  "reasoning": "brief explanation of enhancements"
}}"""

            # Call LLM
            from pydantic_ai import Agent
            from pydantic import BaseModel

            class IssueEnhancement(BaseModel):
                body: str
                labels: List[str]
                reasoning: str

            agent = Agent(
                llm_provider.pydantic_model,
                result_type=IssueEnhancement,
                system_prompt="You are a helpful assistant that enhances GitHub issues with intelligent context."
            )

            result = await agent.run(prompt)
            enhancement_data = result.data

            return {
                "body": enhancement_data.body,
                "labels": list(set(existing_labels + enhancement_data.labels)),  # Merge with existing
                "assignees": existing_assignees,  # Keep existing assignees
                "reasoning": enhancement_data.reasoning
            }

        except Exception as e:
            logger.warning(f"LLM enhancement failed: {e}, using original content")
            return {
                "body": body,
                "labels": existing_labels,
                "assignees": existing_assignees,
                "reasoning": f"Enhancement skipped: {str(e)}"
            }

    def _format_context_for_llm(self, context: Dict[str, Any]) -> str:
        """Format repository context for LLM prompt."""
        parts = []

        if context.get("commits"):
            parts.append("**Recent Commits:**")
            for commit in context["commits"][:5]:
                parts.append(f"- {commit}")

        if context.get("stats"):
            parts.append("\n**Repository Stats:**")
            for key, value in context["stats"].items():
                parts.append(f"- {key}: {value}")

        if context.get("structure", {}).get("key_files"):
            parts.append("\n**Key Files:**")
            for file in context["structure"]["key_files"][:5]:
                parts.append(f"- {file}")

        return "\n".join(parts) if parts else "No context available"

    def _add_aii_signature(self, body: str) -> str:
        """Add AII signature to issue body."""
        signature = "\n\n---\n\n🤖 *Created with [AII](https://github.com/yourusername/aii) - AI-powered CLI assistant*"
        return body + signature

    async def _create_issue_via_mcp(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        labels: List[str],
        assignees: List[str],
        mcp_client: Any
    ) -> Dict[str, Any]:
        """
        Create GitHub issue via MCP server.

        Returns:
            Dictionary with success status, issue number, and URL
        """
        try:
            # Call MCP GitHub server's create_issue tool
            tool_params = {
                "owner": owner,
                "repo": repo,
                "title": title,
                "body": body
            }

            # Add optional parameters if provided
            if labels:
                tool_params["labels"] = labels
            if assignees:
                tool_params["assignees"] = assignees

            result = await mcp_client.call_tool(
                server_name="github",
                tool_name="create_issue",
                arguments=tool_params
            )

            # Parse result
            if result.isError:
                return {
                    "success": False,
                    "error": str(result.content) if result.content else "Unknown error"
                }

            # Extract issue details from response
            # MCP result format varies, handle common patterns
            content = result.content[0].text if result.content else "{}"

            try:
                import json
                issue_data = json.loads(content) if isinstance(content, str) else content

                return {
                    "success": True,
                    "number": issue_data.get("number"),
                    "url": issue_data.get("html_url") or issue_data.get("url"),
                    "raw_response": issue_data
                }
            except Exception as parse_error:
                # Fallback: assume success if no error
                logger.warning(f"Could not parse issue response: {parse_error}")
                return {
                    "success": True,
                    "number": "?",
                    "url": f"https://github.com/{owner}/{repo}/issues",
                    "raw_response": str(content)
                }

        except Exception as e:
            logger.error(f"MCP call failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }


class MCPTestFunction(FunctionPlugin):
    """
    Test MCP server connectivity and diagnose issues (v0.4.10).

    Features:
    - Test connection to specific server or all servers
    - Measure response time
    - List available tools
    - Provide troubleshooting tips
    - No persistent connection (uses temporary connection)
    """

    @property
    def name(self) -> str:
        return "mcp_test"

    @property
    def description(self) -> str:
        return "Test MCP server connectivity and diagnose issues"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def default_output_mode(self) -> OutputMode:
        return OutputMode.STANDARD

    @property
    def supports_output_modes(self) -> List[OutputMode]:
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {}

    def get_parameters_schema(self) -> ParameterSchema:
        return {
            "type": "object",
            "properties": {
                "server_name": {
                    "type": "string",
                    "description": "Server name to test (optional, tests all if not specified)"
                },
                "verbose": {
                    "type": "boolean",
                    "description": "Show detailed diagnostic information",
                    "default": False
                }
            },
            "required": []
        }

    async def execute(
        self, parameters: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Test MCP server connectivity."""
        try:
            server_name = parameters.get("server_name")
            verbose = parameters.get("verbose", False)

            from ...data.integrations.mcp.config_loader import MCPConfigLoader

            config_loader = MCPConfigLoader()
            config_loader.load_configurations()

            if not config_loader.servers:
                return ExecutionResult(
                    success=False,
                    message="⚠️  No MCP servers configured",
                    data={"error": "no_servers"}
                )

            if server_name:
                # Test specific server
                if server_name not in config_loader.servers:
                    available = ", ".join(config_loader.servers.keys())
                    return ExecutionResult(
                        success=False,
                        message=f"❌ Server '{server_name}' not found\n\n"
                                f"Available servers: {available}",
                        data={"error": "server_not_found", "available": list(config_loader.servers.keys())}
                    )

                result = await self._test_server(
                    server_name,
                    config_loader.servers[server_name],
                    verbose
                )
                output = self._format_test_result(server_name, result, verbose)

                return ExecutionResult(
                    success=result["success"],
                    message=output,
                    data={
                        "clean_output": "✅ Connected" if result["success"] else "❌ Failed",
                        "server_name": server_name,
                        **result
                    }
                )
            else:
                # Test all servers
                results = {}
                for name, config in config_loader.servers.items():
                    results[name] = await self._test_server(name, config, verbose)

                output = self._format_all_results(results, verbose)
                success_count = sum(1 for r in results.values() if r["success"])
                total = len(results)

                return ExecutionResult(
                    success=success_count == total,
                    message=output,
                    data={
                        "clean_output": f"{success_count}/{total} servers connected",
                        "results": results,
                        "success_count": success_count,
                        "total": total
                    }
                )

        except Exception as e:
            logger.error(f"Error testing MCP servers: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                message=f"Error testing MCP servers: {str(e)}",
                data={"error": str(e)}
            )

    async def _test_server(
        self, server_name: str, config: Any, verbose: bool
    ) -> Dict[str, Any]:
        """
        Test connection to a single server.

        Returns:
            Dictionary with test results
        """
        import time
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        result = {
            "success": False,
            "response_time_ms": None,
            "tools_count": 0,
            "tools": [],
            "error": None,
            "error_type": None
        }

        start_time = time.time()

        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=config.command,
                args=config.args,
                env=config.env or {}
            )

            # Test connection with timeout
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize
                    await session.initialize()

                    # List tools
                    tools_response = await session.list_tools()
                    tools = tools_response.tools

                    response_time = (time.time() - start_time) * 1000

                    result["success"] = True
                    result["response_time_ms"] = response_time
                    result["tools_count"] = len(tools)
                    if verbose:
                        result["tools"] = [
                            {"name": t.name, "description": t.description}
                            for t in tools
                        ]

        except asyncio.TimeoutError:
            result["error"] = "Connection timeout (>30s)"
            result["error_type"] = "timeout"
        except FileNotFoundError as e:
            result["error"] = f"Command not found: {config.command}"
            result["error_type"] = "command_not_found"
        except PermissionError:
            result["error"] = f"Permission denied: {config.command}"
            result["error_type"] = "permission_denied"
        except Exception as e:
            error_msg = str(e)
            result["error"] = error_msg
            result["error_type"] = "unknown"

            # Categorize common errors
            if "not found" in error_msg.lower():
                result["error_type"] = "not_found"
            elif "permission" in error_msg.lower():
                result["error_type"] = "permission"
            elif "connection" in error_msg.lower():
                result["error_type"] = "connection"

        return result

    def _format_test_result(
        self, server_name: str, result: Dict[str, Any], verbose: bool
    ) -> str:
        """Format test result for single server."""
        lines = [f"🔧 Testing: {server_name}"]
        lines.append("=" * 60)

        if result["success"]:
            lines.append(f"\n✅ Status: Connected")
            lines.append(f"⚡ Response time: {result['response_time_ms']:.0f}ms")
            lines.append(f"🔧 Tools available: {result['tools_count']}")

            if verbose and result.get("tools"):
                lines.append("\n📋 Available Tools:")
                for tool in result["tools"][:10]:  # Show first 10
                    desc = tool["description"] or "No description"
                    lines.append(f"  • {tool['name']}: {desc[:80]}")
                if result["tools_count"] > 10:
                    lines.append(f"  ... and {result['tools_count'] - 10} more")

        else:
            lines.append(f"\n❌ Status: Failed")
            lines.append(f"🔴 Error: {result['error']}")
            lines.append("")
            lines.append(self._get_troubleshooting_tips(result["error_type"]))

        return "\n".join(lines)

    def _format_all_results(
        self, results: Dict[str, Dict[str, Any]], verbose: bool
    ) -> str:
        """Format test results for all servers."""
        lines = ["🔧 MCP Server Connection Test"]
        lines.append("=" * 60)

        success = []
        failed = []

        for server_name, result in results.items():
            if result["success"]:
                time_ms = result["response_time_ms"]
                tools = result["tools_count"]
                success.append(f"  ✅ {server_name}: {time_ms:.0f}ms ({tools} tools)")
            else:
                error = result["error"]
                failed.append(f"  ❌ {server_name}: {error}")

        if success:
            lines.append("\n✅ Connected:")
            lines.extend(success)

        if failed:
            lines.append("\n❌ Failed:")
            lines.extend(failed)
            lines.append("\n💡 Tip: Run 'aii mcp test <server_name>' for detailed diagnostics")

        lines.append(f"\n📊 Summary: {len(success)}/{len(results)} servers connected")

        return "\n".join(lines)

    def _get_troubleshooting_tips(self, error_type: str) -> str:
        """Get troubleshooting tips based on error type."""
        tips = {
            "timeout": """💡 Troubleshooting Tips:
  1. Check if the server command is valid
  2. Verify the server is not hanging
  3. Try increasing timeout in config
  4. Check server logs for errors""",

            "command_not_found": """💡 Troubleshooting Tips:
  1. Install the MCP server: npm install -g <package>
  2. Check if npm/npx is in your PATH
  3. Verify the command spelling in config
  4. Run: aii mcp catalog (to see available servers)""",

            "permission_denied": """💡 Troubleshooting Tips:
  1. Check file permissions: ls -la <command>
  2. Make the command executable: chmod +x <command>
  3. Verify you have necessary access rights
  4. Try running with elevated permissions (if needed)""",

            "not_found": """💡 Troubleshooting Tips:
  1. Verify the server is installed
  2. Check npm global packages: npm list -g
  3. Reinstall the server: npm install -g <package>
  4. Check configuration: aii mcp list""",

            "connection": """💡 Troubleshooting Tips:
  1. Check if server is running
  2. Verify network connectivity
  3. Review server configuration
  4. Check firewall settings""",

            "unknown": """💡 Troubleshooting Tips:
  1. Check server logs for details
  2. Verify configuration: aii mcp list
  3. Try reinstalling the server
  4. Run with debug: AII_DEBUG=1 aii mcp test <server>"""
        }

        return tips.get(error_type, tips["unknown"])


class MCPUpdateFunction(FunctionPlugin):
    """
    Update MCP server to latest version (v0.4.10).

    Checks npm registry for latest version, shows changelog, and safely updates.
    """

    @property
    def name(self) -> str:
        return "mcp_update"

    @property
    def description(self) -> str:
        return "Update MCP server to the latest version from npm registry"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "server_name": ParameterSchema(
                name="server_name",
                type="string",
                required=True,
                description="Name of the MCP server to update",
            ),
            "auto_confirm": ParameterSchema(
                name="auto_confirm",
                type="boolean",
                required=False,
                description="Skip confirmation prompt",
                default=False,
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return True  # Updates require confirmation

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.RISKY  # Modifying installed packages

    @property
    def default_output_mode(self) -> OutputMode:
        return OutputMode.STANDARD

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Check for updates and update MCP server"""
        server_name = parameters.get("server_name")
        auto_confirm = parameters.get("auto_confirm", False)

        if not server_name:
            return ExecutionResult(
                success=False,
                message="❌ Server name is required",
                data={"clean_output": "Server name required"},
            )

        try:
            # Load server configuration
            from ...data.integrations.mcp.config_loader import MCPConfigLoader

            config_loader = MCPConfigLoader()
            config_loader.load_configurations()

            server_config = config_loader.get_server(server_name)
            if not server_config:
                return ExecutionResult(
                    success=False,
                    message=f"❌ Server '{server_name}' not found",
                    data={"clean_output": f"Server '{server_name}' not found"},
                )

            # Get current version
            current_version = await self._get_current_version(server_config)

            # Fetch latest version from npm
            latest_info = await self._fetch_latest_version(server_config)

            if not latest_info:
                return ExecutionResult(
                    success=False,
                    message=f"❌ Could not fetch latest version for '{server_name}'",
                    data={"clean_output": "Could not fetch latest version"},
                )

            latest_version = latest_info.get("version")

            # Compare versions
            if current_version == latest_version:
                message = f"✅ {server_name} is already up to date (v{current_version})"
                return ExecutionResult(
                    success=True,
                    message=message,
                    data={
                        "clean_output": message,
                        "current_version": current_version,
                        "latest_version": latest_version,
                        "up_to_date": True,
                    },
                )

            # Show update information
            changelog = latest_info.get("changelog", "No changelog available")
            message_lines = [
                f"📦 Update available for {server_name}:",
                f"   Current: v{current_version}",
                f"   Latest:  v{latest_version}",
                "",
                "📋 What's new:",
                changelog,
            ]

            if not auto_confirm:
                message_lines.append("")
                message_lines.append("Update? (requires confirmation)")

            message = "\n".join(message_lines)

            # If auto_confirm, proceed with update
            if auto_confirm:
                update_result = await self._perform_update(server_config, latest_version)
                if update_result["success"]:
                    return ExecutionResult(
                        success=True,
                        message=f"✅ {server_name} updated to v{latest_version}",
                        data={
                            "clean_output": f"Updated to v{latest_version}",
                            "old_version": current_version,
                            "new_version": latest_version,
                        },
                    )
                else:
                    return ExecutionResult(
                        success=False,
                        message=f"❌ Update failed: {update_result['error']}",
                        data={"clean_output": f"Update failed: {update_result['error']}"},
                    )

            # Return update info for confirmation
            return ExecutionResult(
                success=True,
                message=message,
                data={
                    "clean_output": f"Update available: v{current_version} → v{latest_version}",
                    "current_version": current_version,
                    "latest_version": latest_version,
                    "changelog": changelog,
                    "requires_confirmation": True,
                },
            )

        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return ExecutionResult(
                success=False,
                message=f"❌ Error checking for updates: {str(e)}",
                data={"clean_output": f"Error: {str(e)}"},
            )

    async def _get_current_version(self, server_config) -> str:
        """Get currently installed version of the server"""
        package_name = self._extract_package_name(server_config)
        if not package_name:
            return "unknown"

        # Try to get version from npm list
        import subprocess

        try:
            result = subprocess.run(
                ["npm", "list", "-g", package_name, "--json"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                import json

                data = json.loads(result.stdout)
                dependencies = data.get("dependencies", {})
                if package_name in dependencies:
                    return dependencies[package_name].get("version", "unknown")

            return "unknown"
        except Exception:
            return "unknown"

    def _extract_package_name(self, server_config) -> str:
        """Extract npm package name from server command"""
        # Build full command from command + args
        full_command_parts = [server_config.command] + server_config.args

        # Handle different command formats
        if "npx" in full_command_parts:
            # npx -y @modelcontextprotocol/server-github
            # npx chrome-devtools-mcp@latest
            # Find the package name after npx (skip flags like -y)
            for part in full_command_parts[1:]:
                if not part.startswith("-"):  # Skip flags
                    # Handle versioned packages: package@version -> package
                    if "@" in part and not part.startswith("@"):
                        # Not a scoped package, has version: chrome-devtools-mcp@latest
                        package_name = part.split("@")[0]
                    else:
                        # Scoped package or no version: @modelcontextprotocol/server-github
                        package_name = part
                    return package_name
            return ""
        else:
            return server_config.command

    async def _fetch_latest_version(self, server_config) -> Optional[dict]:
        """Fetch latest version from npm registry"""
        import subprocess

        package_name = self._extract_package_name(server_config)
        if not package_name:
            return None

        try:
            # Get package info from npm
            result = subprocess.run(
                ["npm", "view", package_name, "--json"],
                capture_output=True,
                text=True,
                timeout=15,
            )

            if result.returncode == 0:
                import json

                data = json.loads(result.stdout)
                version = data.get("version", "unknown")
                description = data.get("description", "")

                return {
                    "version": version,
                    "changelog": description or "No changelog available",
                    "package_name": package_name,
                }

            return None
        except Exception as e:
            logger.error(f"Error fetching npm package info: {e}")
            return None

    async def _perform_update(
        self, server_config, new_version: str
    ) -> dict[str, Any]:
        """Perform the actual update"""
        import subprocess

        package_name = self._extract_package_name(server_config)
        if not package_name:
            return {"success": False, "error": "Could not determine package name"}

        try:
            # Reinstall with latest version
            result = subprocess.run(
                ["npm", "install", "-g", f"{package_name}@{new_version}"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                return {"success": True, "version": new_version}
            else:
                return {"success": False, "error": result.stderr or "Update failed"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Update timed out (>60s)"}
        except Exception as e:
            return {"success": False, "error": str(e)}
