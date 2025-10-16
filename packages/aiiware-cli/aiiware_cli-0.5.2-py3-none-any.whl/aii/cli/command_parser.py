"""Command Parser - Parse CLI commands and arguments"""

import argparse
import sys
from dataclasses import dataclass, field
from typing import Any

# Dynamic version from package metadata
try:
    from importlib.metadata import version
    __version__ = version("aiiware-cli")
except Exception:
    __version__ = "0.4.3"  # Fallback


@dataclass
class ParsedCommand:
    """Represents a parsed CLI command"""

    command: str | None = None
    args: dict[str, Any] = field(default_factory=dict)
    input_text: str = ""
    continue_chat: str | None = None
    new_chat: bool = False
    offline: bool = False
    interactive: bool = False


class CommandParser:
    """Main command parser for AII CLI"""

    def __init__(self) -> None:
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser"""
        parser = argparse.ArgumentParser(
            prog="aii",
            description="AII - LLM-powered CLI assistant with intelligent intent recognition",
        )

        # Version option (dynamic from package metadata)
        parser.add_argument(
            "--version", action="version", version=f"aiiware-cli {__version__}"
        )

        # Global options
        parser.add_argument(
            "--continue-chat", "-c", type=str, help="Continue specific chat by ID"
        )

        parser.add_argument(
            "--new-chat", "-n", action="store_true", help="Force new chat session"
        )

        parser.add_argument(
            "--offline",
            action="store_true",
            help="Run in offline mode (no web/MCP access)",
        )

        parser.add_argument(
            "--config",
            type=str,
            default="~/.aii/config.yaml",
            help="Configuration file path",
        )

        # Output mode options (mutually exclusive)
        output_mode_group = parser.add_mutually_exclusive_group()
        output_mode_group.add_argument(
            "--clean", action="store_true",
            help="Clean output mode (just the result, no metadata)"
        )
        output_mode_group.add_argument(
            "--standard", action="store_true",
            help="Standard output mode (result + basic metrics)"
        )
        output_mode_group.add_argument(
            "--thinking", action="store_true",
            help="Thinking mode (full reasoning and context)"
        )

        # Legacy verbosity options (mapped to output modes for compatibility)
        verbosity_group = parser.add_mutually_exclusive_group()
        verbosity_group.add_argument(
            "--minimal", "-m", action="store_true",
            help="Minimal output (legacy: maps to --clean)"
        )
        verbosity_group.add_argument(
            "--verbose", "-v", action="store_true",
            help="Verbose output (legacy: maps to --thinking)"
        )
        verbosity_group.add_argument(
            "--debug", "-d", action="store_true",
            help="Debug output (all metrics, trace info, and performance data)"
        )

        # Output customization options
        parser.add_argument(
            "--no-colors", action="store_true",
            help="Disable colored output"
        )
        parser.add_argument(
            "--no-emojis", action="store_true",
            help="Disable emoji icons"
        )
        parser.add_argument(
            "--no-animations", action="store_true",
            help="Disable loading animations"
        )
        parser.add_argument(
            "--show-tokens", action="store_true",
            help="Always show token usage"
        )
        parser.add_argument(
            "--show-confidence", action="store_true",
            help="Always show confidence scores"
        )
        parser.add_argument(
            "--show-cost", action="store_true",
            help="Show cost estimates"
        )

        # Streaming options
        parser.add_argument(
            "--no-streaming", action="store_true",
            help="Disable response streaming (show loading spinner instead)"
        )
        parser.add_argument(
            "--streaming-buffer-size", type=int, default=None,
            help="Token buffer size for streaming (advanced, default: 10)"
        )

        parser.add_argument(
            "--interactive", "-i", action="store_true", help="Enter interactive mode"
        )

        # Subcommands - these will consume all remaining args when matched
        subparsers = parser.add_subparsers(
            dest="command", help="Available commands", required=False
        )

        # Chat history management
        self._add_history_commands(subparsers)

        # Configuration commands
        self._add_config_commands(subparsers)

        # Health check command
        doctor_parser = subparsers.add_parser("doctor", help="Run system health checks")

        # Template commands (v0.4.7)
        self._add_template_commands(subparsers)

        # Stats commands (v0.4.7)
        self._add_stats_commands(subparsers)

        # MCP commands (v0.4.8)
        self._add_mcp_commands(subparsers)

        # Shell completion commands
        self._add_completion_commands(subparsers)

        # API server command (v0.4.12)
        serve_parser = subparsers.add_parser("serve", help="Start AII API server")
        serve_parser.add_argument(
            "--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)"
        )
        serve_parser.add_argument(
            "--port", type=int, default=16169, help="Server port (default: 16169)"
        )
        serve_parser.add_argument(
            "--api-key", action="append", dest="api_keys", help="API key (can be specified multiple times, auto-generates if not provided)"
        )

        # Interactive mode
        chat_parser = subparsers.add_parser("chat", help="Enter interactive chat mode")
        chat_parser.add_argument(
            "--continue-chat", "-c", type=str, help="Continue specific chat"
        )

        return parser

    def _add_history_commands(self, subparsers: Any) -> None:
        """Add chat history management commands"""
        history_parser = subparsers.add_parser(
            "history", help="Chat history management"
        )
        history_subparsers = history_parser.add_subparsers(
            dest="history_action", required=False
        )

        # List chats
        list_parser = history_subparsers.add_parser("list", help="List chat history")
        list_parser.add_argument(
            "--detailed", action="store_true", help="Show detailed info"
        )
        list_parser.add_argument("--since", type=str, help="Show chats since date/time")
        list_parser.add_argument(
            "--from", dest="from_date", type=str, help="Start date"
        )
        list_parser.add_argument("--to", dest="to_date", type=str, help="End date")

        # Search chats
        search_parser = history_subparsers.add_parser(
            "search", help="Search chat history"
        )
        search_parser.add_argument("query", help="Search query")
        search_parser.add_argument("--tag", type=str, help="Filter by tag")
        search_parser.add_argument(
            "--content", action="store_true", help="Search in content"
        )

        # Continue chat
        continue_parser = history_subparsers.add_parser(
            "continue", help="Continue chat"
        )
        continue_parser.add_argument("chat_id", help="Chat ID to continue")
        continue_parser.add_argument(
            "--context-limit", type=int, default=20, help="Number of messages to load"
        )

        # Export/Import
        export_parser = history_subparsers.add_parser("export", help="Export chat")
        export_parser.add_argument("chat_id", nargs="?", help="Chat ID to export")
        export_parser.add_argument(
            "--format",
            choices=["json", "markdown"],
            default="json",
            help="Export format",
        )
        export_parser.add_argument(
            "--all", action="store_true", help="Export all chats"
        )
        export_parser.add_argument("--since", type=str, help="Export since date")

        import_parser = history_subparsers.add_parser("import", help="Import chat")
        import_parser.add_argument("file_path", help="File to import")

        # Management operations
        rename_parser = history_subparsers.add_parser("rename", help="Rename chat")
        rename_parser.add_argument("chat_id", help="Chat ID")
        rename_parser.add_argument("new_name", help="New chat name")

        tag_parser = history_subparsers.add_parser("tag", help="Tag chat")
        tag_parser.add_argument("chat_id", help="Chat ID")
        tag_parser.add_argument("tags", nargs="+", help="Tags to add")

        archive_parser = history_subparsers.add_parser("archive", help="Archive chat")
        archive_parser.add_argument("chat_id", help="Chat ID")

        delete_parser = history_subparsers.add_parser("delete", help="Delete chat")
        delete_parser.add_argument("chat_id", help="Chat ID")
        delete_parser.add_argument(
            "--confirm", action="store_true", required=True, help="Confirm deletion"
        )

    def _add_config_commands(self, subparsers: Any) -> None:
        """Add configuration management commands"""
        config_parser = subparsers.add_parser("config", help="Configuration management")
        config_subparsers = config_parser.add_subparsers(
            dest="config_action", required=False
        )

        # Initialize config
        config_subparsers.add_parser("init", help="Initialize configuration")

        # Show config
        show_parser = config_subparsers.add_parser("show", help="Show configuration")
        show_parser.add_argument("--section", type=str, help="Show specific section")

        # Validate config
        config_subparsers.add_parser("validate", help="Validate configuration and show issues")

        # Set config values
        set_parser = config_subparsers.add_parser("set", help="Set configuration value")
        set_parser.add_argument("key", help="Configuration key")
        set_parser.add_argument("value", help="Configuration value")

        # Model selection
        model_parser = config_subparsers.add_parser("model", help="Change LLM model")
        model_parser.add_argument("model_id", nargs="?", help="Model ID (e.g., claude-sonnet-4-5-20250929)")

        # Provider selection
        provider_parser = config_subparsers.add_parser("provider", help="Change LLM provider")
        provider_parser.add_argument("provider_name", nargs="?", help="Provider name (anthropic, openai, gemini)")

        # Web search configuration
        websearch_parser = config_subparsers.add_parser("web-search", help="Configure web search")
        websearch_parser.add_argument("action", nargs="?", choices=["enable", "disable", "set-provider"], help="Action to perform")
        websearch_parser.add_argument("provider", nargs="?", help="Provider name (brave, google, duckduckgo)")

        # API key management
        key_parser = config_subparsers.add_parser("key", help="API key management")
        key_subparsers = key_parser.add_subparsers(dest="key_action", required=False)

        set_key_parser = key_subparsers.add_parser("set", help="Set API key")
        set_key_parser.add_argument(
            "provider", help="Provider name (openai, anthropic, etc.)"
        )

        # List configured providers parser
        key_subparsers.add_parser("list", help="List configured providers")

        # OAuth login/logout commands
        oauth_parser = config_subparsers.add_parser("oauth", help="OAuth authentication")
        oauth_subparsers = oauth_parser.add_subparsers(dest="oauth_action", required=False)

        # Login command
        oauth_subparsers.add_parser("login", help="Login with subscription account")

        # Logout command
        oauth_subparsers.add_parser("logout", help="Logout and clear credentials")

        # Status command
        oauth_subparsers.add_parser("status", help="Show authentication status")

    def _add_template_commands(self, subparsers: Any) -> None:
        """Add template management commands (v0.4.7)"""
        template_parser = subparsers.add_parser(
            "template",
            help="Content templates for common use cases"
        )
        template_subparsers = template_parser.add_subparsers(
            dest="template_action", required=False
        )

        # List templates
        list_parser = template_subparsers.add_parser(
            "list",
            aliases=["ls"],
            help="List all available templates"
        )
        list_parser.set_defaults(template_action="list")

        # Show template details
        show_parser = template_subparsers.add_parser(
            "show",
            help="Show template details and variables"
        )
        show_parser.add_argument("template_name", help="Template name")
        show_parser.set_defaults(template_action="show")

        # Use/generate from template
        use_parser = template_subparsers.add_parser(
            "use",
            help="Generate content from a template"
        )
        use_parser.add_argument("template_name", help="Template name (e.g., product-announcement, blog-intro)")
        use_parser.add_argument(
            "--product", type=str, help="Product name (for product-announcement)"
        )
        use_parser.add_argument(
            "--version", type=str, help="Version number (for product-announcement, release-notes)"
        )
        use_parser.add_argument(
            "--date", type=str, help="Release date (for product-announcement, release-notes)"
        )
        use_parser.add_argument(
            "--topic", type=str, help="Topic (for blog-intro, social-post)"
        )
        use_parser.add_argument(
            "--subject", type=str, help="Email subject (for email-professional)"
        )
        use_parser.add_argument(
            "--recipient", type=str, help="Email recipient (for email-professional)"
        )
        use_parser.add_argument(
            "--title", type=str, help="PR title (for pr-description)"
        )
        use_parser.add_argument(
            "--meeting-title", type=str, help="Meeting title (for meeting-notes)"
        )
        use_parser.add_argument(
            "--key-benefit", type=str, help="Key benefit (for tweet-launch)"
        )
        use_parser.add_argument(
            "--key-features", type=str, help="Key features (for product-announcement)"
        )
        use_parser.add_argument(
            "--hook", type=str, help="Hook type (for blog-intro)"
        )
        use_parser.add_argument(
            "--platform", type=str, help="Platform (for social-post)"
        )
        use_parser.add_argument(
            "--cta", type=str, help="Call to action (for social-post, tweet-launch)"
        )
        use_parser.add_argument(
            "--context", type=str, help="Additional context (for email-professional)"
        )
        use_parser.add_argument(
            "--hashtags", type=str, help="Hashtags (for tweet-launch)"
        )
        # Allow arbitrary variables via --var key=value
        use_parser.add_argument(
            "--var", "-v",
            action="append",
            metavar="KEY=VALUE",
            help="Additional template variable (can be used multiple times)"
        )
        use_parser.set_defaults(template_action="use")

        # If no subcommand, show help
        template_parser.set_defaults(template_action="help")

    def _add_stats_commands(self, subparsers: Any) -> None:
        """Add statistics and analytics commands (v0.4.7)"""
        stats_parser = subparsers.add_parser(
            "stats",
            help="Usage statistics and analytics"
        )

        # Period filter
        stats_parser.add_argument(
            "--period",
            type=str,
            choices=["7d", "30d", "90d", "all"],
            default="30d",
            help="Time period for statistics (default: 30d)"
        )

        # Breakdown filter
        stats_parser.add_argument(
            "--breakdown",
            type=str,
            choices=["functions", "tokens", "cost", "all"],
            default="all",
            help="Type of breakdown to show (default: all)"
        )

        # Exclude stats function from results
        stats_parser.add_argument(
            "--exclude-stats",
            action="store_true",
            help="Exclude stats function from results (avoid observer effect)"
        )

    def _add_mcp_commands(self, subparsers: Any) -> None:
        """Add MCP (Model Context Protocol) commands (v0.4.8+)"""
        mcp_parser = subparsers.add_parser(
            "mcp",
            help="MCP (Model Context Protocol) operations"
        )

        mcp_subparsers = mcp_parser.add_subparsers(
            dest="mcp_action", required=False
        )

        # Server management commands (v0.4.9)
        # Add server
        add_parser = mcp_subparsers.add_parser(
            "add",
            help="Add MCP server to configuration"
        )
        add_parser.add_argument("server_name", help="Server name (e.g., chrome, github, postgres)")
        add_parser.add_argument("server_command", help="Command to run (e.g., npx, uvx, node)")
        add_parser.add_argument("server_args", nargs="+", help="Command arguments")
        add_parser.add_argument("--env", type=str, help="Environment variables as JSON")
        add_parser.add_argument("--transport", choices=["stdio", "sse", "http"], default="stdio", help="Transport protocol")

        # Remove server
        remove_parser = mcp_subparsers.add_parser(
            "remove",
            help="Remove MCP server from configuration"
        )
        remove_parser.add_argument("server_name", help="Server name to remove")

        # List servers
        list_parser = mcp_subparsers.add_parser(
            "list",
            help="List configured MCP servers"
        )

        # Enable server
        enable_parser = mcp_subparsers.add_parser(
            "enable",
            help="Enable MCP server"
        )
        enable_parser.add_argument("server_name", help="Server name to enable")

        # Disable server
        disable_parser = mcp_subparsers.add_parser(
            "disable",
            help="Disable MCP server"
        )
        disable_parser.add_argument("server_name", help="Server name to disable")

        # Show catalog
        catalog_parser = mcp_subparsers.add_parser(
            "catalog",
            help="Show popular MCP server catalog"
        )

        # Install from catalog
        install_parser = mcp_subparsers.add_parser(
            "install",
            help="Install MCP server from catalog"
        )
        install_parser.add_argument("server_name", help="Server name from catalog")
        install_parser.add_argument("--env", type=str, help="Environment variables as JSON")

        # Status subcommand (v0.4.10)
        status_parser = mcp_subparsers.add_parser(
            "status",
            help="Show health status for MCP servers"
        )
        status_parser.add_argument(
            "server_name",
            nargs="?",
            type=str,
            help="Server name to check (optional, shows all if not specified)"
        )
        status_parser.add_argument(
            "--all",
            action="store_true",
            help="Show all servers including disabled"
        )

        # Test subcommand (v0.4.10)
        test_parser = mcp_subparsers.add_parser(
            "test",
            help="Test MCP server connectivity and diagnose issues"
        )
        test_parser.add_argument(
            "server_name",
            nargs="?",
            type=str,
            help="Server name to test (optional, tests all if not specified)"
        )
        test_parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed diagnostic information"
        )

        # Update subcommand (v0.4.10)
        update_parser = mcp_subparsers.add_parser(
            "update",
            help="Update MCP server(s) to latest version"
        )
        update_parser.add_argument(
            "server_names",
            type=str,
            help="Server name(s) to update (comma-separated for multiple, or 'all' for all servers)"
        )
        update_parser.add_argument(
            "--auto-confirm",
            action="store_true",
            help="Skip confirmation prompt"
        )

        # List tools subcommand
        list_tools_parser = mcp_subparsers.add_parser(
            "list-tools",
            help="List available MCP tools from all or specific server"
        )
        list_tools_parser.add_argument(
            "server_name",
            nargs="?",
            type=str,
            help="Server name to list tools from (optional, lists all if not specified)"
        )
        list_tools_parser.add_argument(
            "--detailed",
            action="store_true",
            help="Show detailed parameter information"
        )

        # Direct tool invocation (legacy, kept for backward compatibility)
        invoke_parser = mcp_subparsers.add_parser(
            "invoke",
            help="Invoke an MCP tool directly"
        )

        # Tool name (required)
        invoke_parser.add_argument(
            "tool_name",
            type=str,
            help="Name of the MCP tool to invoke (e.g., read_text_file, list_directory, write_file)"
        )

        # Tool arguments as flags
        invoke_parser.add_argument(
            "--path",
            type=str,
            help="File path argument (for read_text_file, write_file, etc.)"
        )

        invoke_parser.add_argument(
            "--content",
            type=str,
            help="Content argument (for write_file)"
        )

        invoke_parser.add_argument(
            "--args",
            type=str,
            help="JSON string of additional arguments"
        )

        # Server selection
        invoke_parser.add_argument(
            "--server",
            type=str,
            help="MCP server name (default: auto-detect from tool)"
        )

        # If no subcommand specified, default to showing help
        mcp_parser.set_defaults(mcp_action="help")

    def _add_completion_commands(self, subparsers: Any) -> None:
        """Add shell completion commands"""
        # Install completion
        install_completion = subparsers.add_parser(
            "install-completion",
            help="Install shell tab completion"
        )
        install_completion.add_argument(
            "--shell",
            choices=["bash", "zsh", "fish"],
            help="Shell to install for (auto-detected if omitted)"
        )

        # Uninstall completion
        uninstall_completion = subparsers.add_parser(
            "uninstall-completion",
            help="Uninstall shell tab completion"
        )
        uninstall_completion.add_argument(
            "--shell",
            choices=["bash", "zsh", "fish"],
            help="Shell to uninstall from (auto-detected if omitted)"
        )

    def parse_args(self, args: list[str] | None = None) -> ParsedCommand:
        """Parse command line arguments"""
        if args is None:
            args = sys.argv[1:]

        # Check for --version or --help flag first (should be handled by argparse and exit)
        if "--version" in args or "--help" in args or "-h" in args:
            # Let argparse handle --version, --help and exit
            self.parser.parse_args(args)
            # This should never be reached because argparse exits after these flags
            raise SystemExit(0)

        # Check if this looks like a structured command first
        if args and args[0] in ["history", "config", "chat", "doctor", "template", "stats", "mcp", "serve", "install-completion", "uninstall-completion"]:
            # Try parsing as structured command
            import io
            import contextlib

            # Capture stderr to get argparse error messages
            stderr_capture = io.StringIO()
            try:
                with contextlib.redirect_stderr(stderr_capture):
                    parsed = self.parser.parse_args(args)
                return ParsedCommand(
                    command=parsed.command,
                    args=vars(parsed),
                    input_text="",
                    continue_chat=getattr(parsed, "continue_chat", None),
                    new_chat=getattr(parsed, "new_chat", False),
                    offline=getattr(parsed, "offline", False),
                    interactive=getattr(parsed, "interactive", False)
                    or parsed.command == "chat",
                )
            except SystemExit as e:
                # If structured parsing failed, show the error and exit
                error_msg = stderr_capture.getvalue()
                if error_msg:
                    # Argparse printed an error message
                    print(error_msg, end='', file=sys.stderr)
                    raise SystemExit(e.code)
                # If no error message, fall through to free-form
                pass

        # Treat as free-form input - parse global options manually
        filtered_input_args = []
        extracted_options = {
            "continue_chat": None,
            "new_chat": False,
            "offline": False,
            "config": "~/.aii/config.yaml",
            "verbose": False,
            "minimal": False,
            "debug": False,
            "interactive": False,
            "no_colors": False,
            "no_emojis": False,
            "no_animations": False,
            "show_tokens": False,
            "show_confidence": False,
            "show_cost": False,
            # Output mode flags
            "clean": False,
            "standard": False,
            "thinking": False,
        }

        i = 0
        while i < len(args):
            arg = args[i]
            if arg == "--continue-chat" or arg == "-c":
                if i + 1 < len(args):
                    extracted_options["continue_chat"] = args[i + 1]
                    i += 2
                else:
                    i += 1
            elif arg == "--new-chat" or arg == "-n":
                extracted_options["new_chat"] = True
                i += 1
            elif arg == "--offline":
                extracted_options["offline"] = True
                i += 1
            elif arg == "--verbose" or arg == "-v":
                extracted_options["verbose"] = True
                i += 1
            elif arg == "--minimal" or arg == "-m":
                extracted_options["minimal"] = True
                i += 1
            elif arg == "--debug" or arg == "-d":
                extracted_options["debug"] = True
                i += 1
            elif arg == "--no-colors":
                extracted_options["no_colors"] = True
                i += 1
            elif arg == "--no-emojis":
                extracted_options["no_emojis"] = True
                i += 1
            elif arg == "--no-animations":
                extracted_options["no_animations"] = True
                i += 1
            elif arg == "--show-tokens":
                extracted_options["show_tokens"] = True
                i += 1
            elif arg == "--show-confidence":
                extracted_options["show_confidence"] = True
                i += 1
            elif arg == "--show-cost":
                extracted_options["show_cost"] = True
                i += 1
            elif arg == "--interactive" or arg == "-i":
                extracted_options["interactive"] = True
                i += 1
            elif arg == "--clean":
                extracted_options["clean"] = True
                i += 1
            elif arg == "--standard":
                extracted_options["standard"] = True
                i += 1
            elif arg == "--thinking":
                extracted_options["thinking"] = True
                i += 1
            elif arg == "--config":
                if i + 1 < len(args):
                    extracted_options["config"] = args[i + 1]
                    i += 2
                else:
                    i += 1
            elif arg.startswith("--config="):
                extracted_options["config"] = arg.split("=", 1)[1]
                i += 1
            else:
                filtered_input_args.append(arg)
                i += 1

        input_text = " ".join(filtered_input_args) if filtered_input_args else None
        interactive = extracted_options["interactive"] or (
            not input_text and not extracted_options["continue_chat"]
        )

        return ParsedCommand(
            command="main",
            args={**extracted_options, "command": None},
            input_text=input_text or "",
            continue_chat=(
                extracted_options["continue_chat"]
                if isinstance(extracted_options["continue_chat"], str)
                else None
            ),
            new_chat=bool(extracted_options["new_chat"]),
            offline=bool(extracted_options["offline"]),
            interactive=bool(interactive),
        )

    def print_help(self) -> None:
        """Print help message"""
        self.parser.print_help()
