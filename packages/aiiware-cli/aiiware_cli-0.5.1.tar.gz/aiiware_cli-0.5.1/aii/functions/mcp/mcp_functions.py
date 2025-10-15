"""MCP Tool Function - Invoke tools from connected MCP servers"""

import json
import logging
from typing import Any

from ...core.models import (
    ExecutionContext,
    ExecutionResult,
    FunctionCategory,
    FunctionPlugin,
    FunctionSafety,
    OutputMode,
    ParameterSchema,
    ValidationResult,
)
from ...data.integrations.mcp.content_formatter import MCPContentFormatter, create_formatter_from_config

logger = logging.getLogger(__name__)


class MCPToolFunction(FunctionPlugin):
    """
    Invoke tools from connected MCP servers.

    This function allows the LLM to discover and use tools from any connected
    MCP server (filesystem, GitHub, PostgreSQL, 12306 railway, etc.).

    Examples:
        Filesystem:
        - "list files in my home directory" → filesystem.list_directory
        - "read the contents of README.md" → filesystem.read_file

        Chinese Railway (12306):
        - "查询10月15号从北京到上海的高铁票" → 12306-mcp.get-tickets
        - "帮我查询北京南站的信息" → 12306-mcp.get-station-code-by-names
        - "查看G1次列车的经停站" → 12306-mcp.get-train-route-stations

        Other Services:
        - "create a new GitHub issue" → github.create_issue
        - "query the users table" → postgres.query
    """

    @property
    def name(self) -> str:
        return "mcp_tool"

    @property
    def description(self) -> str:
        return (
            "USE THIS FUNCTION for Model Context Protocol (MCP) operations including: "
            "1. GitHub operations: When user wants to search/list/create repositories, issues, or code on GitHub. "
            "   Keywords: 'github', 'repositories', 'repos', 'issues', 'pull requests', 'search github', 'my repos', "
            "   'popular repos', 'search for repos', 'find repos', 'search repositories', 'github repos'. "
            "   Available GitHub tools: search_repositories, create_repository, create_issue, create_pull_request, fork_repository, list_commits, etc. "
            "   Example: 'search for popular python ML repos' → Use this function (searches GitHub repositories) "
            "   Example: 'list my repositories' → Use this function (NOT get_git_context which is local only) "
            "2. Filesystem operations: Read file contents, write files, list directories, manage filesystem. "
            "   Available filesystem tools: read_text_file, write_file, list_directory, create_directory, edit_file, move_file, search_files, get_file_info. "
            "3. Chinese railway/train queries: 火车票, 高铁, 动车, 余票, 12306, 车站, 列车, 查询火车, 查询车票. "
            "   Available 12306 tools: get-tickets, get-station-code-of-citys, get-stations-code-in-city, get-train-route-stations, get-interline-tickets. "
            "4. Other MCP servers: PostgreSQL, and any other configured MCP services. "
            "CRITICAL: "
            "- For searching/finding repositories (even without 'github' keyword) → USE THIS FUNCTION "
            "- For reading file contents → USE THIS FUNCTION (NOT get_file_context) "
            "- get_file_context only provides metadata, not content "
            "- get_git_context is for local .git repository info, NOT for GitHub API searches "
            "- research function is for web articles/news, NOT for GitHub repository searches"
        )

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "user_request": ParameterSchema(
                name="user_request",
                type="string",
                required=True,
                description=(
                    "The user's original request in natural language. "
                    "This will be used to automatically select the appropriate MCP tool and generate arguments."
                ),
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        """Context-dependent: safe tools auto-execute, risky tools need confirmation"""
        return False  # Will check dynamically based on tool

    @property
    def safety_level(self) -> FunctionSafety:
        """Context-dependent: depends on which tool is being invoked"""
        return FunctionSafety.CONTEXT_DEPENDENT

    @property
    def default_output_mode(self) -> OutputMode:
        """Standard mode: show result + metadata"""
        return OutputMode.STANDARD

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Supports all output modes"""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check if MCP client is available and connected"""
        if not context.mcp_client:
            return ValidationResult(
                valid=False,
                errors=["MCP client is not available. Enable MCP in config or install MCP servers."],
            )

        # Initialize MCP client on first use if not already initialized
        if not context.mcp_client.is_connected():
            try:
                logger.info("MCP client not connected, initializing...")
                await context.mcp_client.initialize()
            except Exception as e:
                logger.error(f"Failed to initialize MCP client: {e}")
                return ValidationResult(
                    valid=False,
                    errors=[f"Failed to initialize MCP client: {str(e)}"],
                )

        # Check if any servers are configured (v0.4.11 lazy connection support)
        # Note: We check configured (not connected) because lazy connection
        # means servers connect on-demand when first used
        if not context.mcp_client.has_configured_servers():
            return ValidationResult(
                valid=False,
                errors=["No MCP servers are configured. Run 'aii mcp add' to add servers."],
            )

        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """
        Execute an MCP tool with multi-step chaining support.

        This function uses LLM-based tool selection with automatic multi-step chaining:
        1. Get available tools from MCP servers
        2. Use LLM to select appropriate tool and generate arguments
        3. Check if multi-step chaining is needed
        4. Execute the selected tool or tool chain
        5. Format and return results

        Args:
            parameters: User's natural language request
            context: Execution context with mcp_client and llm_provider

        Returns:
            ExecutionResult with tool output
        """
        user_request = parameters.get("user_request", "")

        logger.info(f"Processing MCP request: {user_request}")

        # Initialize token usage tracking
        total_input_tokens = 0
        total_output_tokens = 0

        try:
            # Step 1: Get available tools (v0.4.11: smart lazy connection with server inference)
            available_tools = await context.mcp_client.discover_all_tools(user_request=user_request)

            if not available_tools:
                return ExecutionResult(
                    success=False,
                    message="No MCP tools available. Check your MCP server configuration.",
                    data={"clean_output": "No MCP tools available"},
                )

            logger.info(f"Found {len(available_tools)} available MCP tools")

            # Step 2: Use LLM to select tool and generate arguments
            tool_selection = await self._select_tool_with_llm(
                user_request, available_tools, context
            )

            if not tool_selection:
                return ExecutionResult(
                    success=False,
                    message="Could not determine appropriate MCP tool for this request",
                    data={"clean_output": "Could not determine appropriate tool"},
                )

            tool_name = tool_selection["tool_name"]
            arguments = tool_selection["arguments"]

            # Accumulate token usage from tool selection
            if "token_usage" in tool_selection:
                usage = tool_selection["token_usage"]
                total_input_tokens += usage.get("input_tokens", 0)
                total_output_tokens += usage.get("output_tokens", 0)

            logger.info(f"Selected tool: {tool_name} with arguments: {arguments}")

            # Step 2.5: Add AII signature to content-generating tools (v0.4.10)
            arguments = self._add_signature_to_content(tool_name, arguments, context)

            # Step 3: Check if multi-step chaining is needed
            from ...data.integrations.mcp.tool_chain_orchestrator import ToolChainOrchestrator

            orchestrator = ToolChainOrchestrator(
                mcp_client=context.mcp_client,
                llm_provider=context.llm_provider,
                verbose=True
            )

            should_chain = await orchestrator.should_chain(user_request, tool_name, arguments)

            if should_chain:
                logger.info("Multi-step chaining detected, planning chain...")

                # Plan the chain
                chain_plan = await orchestrator.plan_chain(user_request, tool_name, arguments)

                if chain_plan:
                    logger.info(f"Chain planned with {len(chain_plan.steps)} steps")

                    # Execute the chain
                    chain_result = await orchestrator.execute_chain(chain_plan)

                    return self._format_chain_result(chain_result)
                else:
                    logger.warning("Chain planning failed, falling back to single tool execution")

            # Accumulate orchestrator's token usage (from should_chain and possibly plan_chain calls)
            total_input_tokens += orchestrator._orchestrator_input_tokens
            total_output_tokens += orchestrator._orchestrator_output_tokens

            # Step 4: Execute single tool (no chaining or chaining failed)
            result = await context.mcp_client.call_tool(tool_name, arguments)

            if result.success:
                # Format the tool output
                output_text = self._format_tool_output(result, tool_name)

                # Convert raw_content to JSON-serializable format
                serializable_content = self._make_content_serializable(result.content)

                return ExecutionResult(
                    success=True,
                    message=output_text,
                    data={
                        "clean_output": self._extract_clean_output(result),
                        "tool_name": tool_name,
                        "server_name": result.server_name,
                        "raw_content": serializable_content,
                        "confidence": 1.0,  # Tool execution is deterministic
                        "input_tokens": total_input_tokens,
                        "output_tokens": total_output_tokens,
                    },
                )
            else:
                # Tool execution failed
                error_msg = result.error or "Unknown error"
                logger.error(f"MCP tool '{tool_name}' failed: {error_msg}")

                # Special handling for GitHub errors
                # 1. Missing parameters (owner/repo/title not provided)
                if "Required" in error_msg and ("owner" in error_msg or "repo" in error_msg):
                    error_msg = (
                        "❌ Cannot create issue - repository not specified.\n\n"
                        "Please specify which repository to create the issue in.\n"
                        "Examples:\n"
                        '  • "create an issue in ttware/aii about adding tests"\n'
                        '  • "create an issue in facebook/react titled \'Bug fix\'"\n\n'
                        "To see your repositories, try:\n"
                        '  • "list my github repositories"'
                    )
                # 2. Repository not found errors
                elif "Repository" in error_msg and "not found" in error_msg:
                    # Extract attempted repository name
                    if "@me/current" in error_msg or "current" in error_msg:
                        error_msg = (
                            "❌ Cannot create issue - repository not specified.\n\n"
                            "Please specify which repository to create the issue in.\n"
                            "Examples:\n"
                            '  • "create an issue in ttware/aii about adding tests"\n'
                            '  • "create an issue in owner/repo titled \'Bug fix\'"\n\n'
                            "To see your repositories, try:\n"
                            '  • "list my github repositories"'
                        )

                return ExecutionResult(
                    success=False,
                    message=f"Tool '{tool_name}' failed: {error_msg}",
                    data={
                        "clean_output": f"Error: {error_msg}",
                        "tool_name": tool_name,
                        "server_name": result.server_name,
                        "error": error_msg,
                    },
                )

        except Exception as e:
            logger.error(f"Error executing MCP tool: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                message=f"Error executing MCP tool: {str(e)}",
                data={
                    "clean_output": f"Error: {str(e)}",
                    "error": str(e),
                },
            )

    def _format_chain_result(self, chain_result: Any) -> ExecutionResult:
        """
        Format the result of a multi-step tool chain.

        Args:
            chain_result: ChainResult from ToolChainOrchestrator

        Returns:
            ExecutionResult with formatted chain output
        """
        if not chain_result.success:
            # Chain failed
            error_msg = chain_result.error or "Chain execution failed"
            return ExecutionResult(
                success=False,
                message=f"Multi-step chain failed: {error_msg}",
                data={
                    "clean_output": f"Error: {error_msg}",
                    "error": error_msg,
                    "chain_steps": len(chain_result.steps),
                },
            )

        # Chain succeeded - format output
        lines = []
        lines.append("🔗 Multi-Step Tool Chain")
        lines.append("")

        # Show each step
        for step in chain_result.steps:
            lines.append(f"Step {step.step}/{len(chain_result.steps)}: {step.tool_name}")
            lines.append(f"  Input: {json.dumps(step.parameters, ensure_ascii=False)}")
            if step.result and step.result.success:
                lines.append(f"  ✓ Complete ({step.execution_time:.1f}s)")
            else:
                error_msg = step.result.error if step.result else "Unknown error"
                lines.append(f"  ✗ Failed: {error_msg}")
            lines.append("")

        # Show final result
        if chain_result.final_result:
            lines.append("Results:")
            clean_output = self._extract_clean_output(chain_result.final_result)
            lines.append(clean_output)
            lines.append("")

        # Show summary
        lines.append(f"⏱️  Total Time: {chain_result.total_time:.1f}s")
        if chain_result.total_input_tokens > 0 or chain_result.total_output_tokens > 0:
            lines.append(f"🔢 Tokens: Input: {chain_result.total_input_tokens} • Output: {chain_result.total_output_tokens}")

        output_text = "\n".join(lines)

        # Prepare data
        serializable_content = None
        server_name = None
        if chain_result.final_result:
            serializable_content = self._make_content_serializable(chain_result.final_result.content)
            server_name = chain_result.final_result.server_name

        return ExecutionResult(
            success=True,
            message=output_text,
            data={
                "clean_output": self._extract_clean_output(chain_result.final_result) if chain_result.final_result else "No output",
                "chain_steps": len(chain_result.steps),
                "total_time": chain_result.total_time,
                "server_name": server_name,
                "raw_content": serializable_content,
                "confidence": 1.0,
                "input_tokens": chain_result.total_input_tokens,
                "output_tokens": chain_result.total_output_tokens,
            },
        )

    def _format_tool_output(self, result: Any, tool_name: str) -> str:
        """
        Format tool output for display.

        Args:
            result: ToolCallResult from MCP client
            tool_name: Name of the tool

        Returns:
            Formatted output string
        """
        lines = []
        lines.append(f"🔧 Tool: {tool_name}")
        lines.append(f"📡 Server: {result.server_name}")
        lines.append("")

        # Format the content
        if isinstance(result.content, list):
            # MCP returns content as list of content blocks
            for block in result.content:
                if hasattr(block, 'text'):
                    lines.append(block.text)
                elif isinstance(block, dict):
                    if 'text' in block:
                        lines.append(block['text'])
                    else:
                        lines.append(json.dumps(block, indent=2))
                else:
                    lines.append(str(block))
        elif isinstance(result.content, dict):
            lines.append(json.dumps(result.content, indent=2))
        else:
            lines.append(str(result.content))

        return "\n".join(lines)

    def _extract_clean_output(self, result: Any) -> str:
        """
        Extract clean output for CLEAN mode (just the result, no metadata).

        Args:
            result: ToolCallResult from MCP client

        Returns:
            Clean output string
        """
        if isinstance(result.content, list):
            # Extract text from content blocks
            texts = []
            for block in result.content:
                if hasattr(block, 'text'):
                    texts.append(block.text)
                elif isinstance(block, dict) and 'text' in block:
                    texts.append(block['text'])
                else:
                    texts.append(str(block))
            return "\n".join(texts)
        elif isinstance(result.content, dict):
            # If dict has a 'text' field, use that
            if 'text' in result.content:
                return result.content['text']
            # Otherwise, pretty-print JSON
            return json.dumps(result.content, indent=2)
        else:
            return str(result.content)

    async def _select_tool_with_llm(
        self, user_request: str, available_tools: list, context: ExecutionContext
    ) -> dict[str, Any] | None:
        """
        Use LLM to select the appropriate tool and generate arguments.

        Args:
            user_request: User's natural language request
            available_tools: List of MCPTool objects
            context: Execution context with llm_provider

        Returns:
            Dict with 'tool_name', 'arguments', and 'token_usage', or None if selection failed
        """
        if not context.llm_provider:
            logger.error("No LLM provider available for tool selection")
            return None

        # Format tools for LLM
        tools_description = []
        for tool in available_tools:
            tool_info = f"Tool: {tool.name}\n"
            tool_info += f"Server: {tool.server_name}\n"
            tool_info += f"Description: {tool.description}\n"
            tool_info += f"Parameters: {json.dumps(tool.input_schema, indent=2)}\n"
            tools_description.append(tool_info)

        tools_text = "\n---\n".join(tools_description)

        # Create prompt for LLM
        prompt = f"""You are an MCP (Model Context Protocol) tool selector. Given a user request and a list of available tools, select the most appropriate tool and generate the required arguments.

User Request:
{user_request}

Available Tools:
{tools_text}

Task:
1. Select the EXACT tool name from the list above that best matches the user's request
2. Generate appropriate arguments based on the tool's parameter schema
3. Return ONLY a JSON object with this structure:
{{
  "tool_name": "exact_tool_name_from_list",
  "arguments": {{"param1": "value1", "param2": "value2"}},
  "reasoning": "brief explanation of why you selected this tool"
}}

IMPORTANT:
- Use the EXACT tool name as listed (e.g., "get-tickets", not "query_tickets")
- Match the parameter names exactly as specified in the schema
- For Chinese railway queries, use "get-tickets" tool with parameters like from_station, to_station, date
- For GitHub authenticated queries (when user says "my repositories", "my issues", etc.):
  * The GitHub server is authenticated via GITHUB_PERSONAL_ACCESS_TOKEN
  * For "my repositories": use search_repositories with query "user:@me" (NOT "user:USERNAME")
  * For "my public repos": use query "user:@me is:public"
  * For "my private repos": use query "user:@me is:private"
  * Do NOT use placeholders like "YOUR_GITHUB_USERNAME" or "user:USERNAME"
  * Use @me as the authenticated user identifier
- For GitHub operations requiring repository specification (create_issue, create_pull_request, push_files):
  * CRITICAL: Repository must be in "owner/repo" format (e.g., "ttware/aii", "facebook/react")
  * If user provides clear owner/repo → use create_issue
  * If user doesn't specify repository → use search_repositories with query="user:@me" (to help user see their repos)
  * NEVER use placeholders like "@me/current", "current", or invented repo names
  * NEVER guess or invent repository names
  * Examples:
    - "create an issue about tests" → USE search_repositories with query="user:@me" (shows user's repos)
    - "create a github issue about adding tests" → USE search_repositories with query="user:@me"
    - "create an issue in aii about tests" → USE search_repositories with query="user:@me repo:aii"
    - "create an issue in ttware/aii about tests" → USE create_issue with owner="ttware", repo="aii"
  * Valid repository formats: "owner/repo" must be explicitly stated by user
- For GitHub public repository searches (when user searches for popular/public repos):
  * Use search_repositories tool with GitHub search syntax in the query parameter
  * Include language filter: "language:python" for Python repos
  * Include sort criteria: Add "sort:stars" or use stars filter "stars:>1000" for popular repos
  * Combine filters with spaces: "language:python machine learning stars:>1000"
  * Examples:
    - "search for popular python ML repos" → query: "language:python machine learning stars:>1000 sort:stars"
    - "find popular ML repositories" → query: "machine learning stars:>5000 sort:stars"
    - "search python repos about deep learning" → query: "language:python deep learning sort:stars"
    - "find trending AI repositories" → query: "artificial intelligence stars:>1000 sort:stars"
  * NEVER leave query empty or use placeholder text
  * Always include stars filter (stars:>1000) for "popular" queries
  * Always include language filter when user specifies language
- Return ONLY the JSON object, no other text

JSON Response:"""

        try:
            # Call LLM with usage tracking
            llm_response = await context.llm_provider.complete_with_usage(prompt)
            response = llm_response.content

            # Parse JSON from response
            # Extract JSON from response (handle markdown code blocks)
            response_text = response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            tool_selection = json.loads(response_text)

            # Validate selection
            if "tool_name" not in tool_selection:
                logger.error("LLM response missing 'tool_name' field")
                return None

            # Verify tool exists
            tool_names = [t.name for t in available_tools]
            if tool_selection["tool_name"] not in tool_names:
                logger.error(f"LLM selected non-existent tool: {tool_selection['tool_name']}")
                logger.error(f"Available tools: {tool_names}")
                return None

            logger.info(f"LLM selected tool: {tool_selection['tool_name']}")
            if "reasoning" in tool_selection:
                logger.info(f"LLM reasoning: {tool_selection['reasoning']}")

            return {
                "tool_name": tool_selection["tool_name"],
                "arguments": tool_selection.get("arguments", {}),
                "token_usage": llm_response.usage,  # Include token usage
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response was: {response[:500]}")
            return None
        except Exception as e:
            logger.error(f"Error in LLM tool selection: {e}", exc_info=True)
            return None

    def _make_content_serializable(self, content: Any) -> Any:
        """
        Convert MCP response content to JSON-serializable format.

        MCP SDK returns TextContent objects that aren't directly JSON serializable.
        This method converts them to plain Python types.

        Args:
            content: Raw content from MCP tool result

        Returns:
            JSON-serializable version of the content
        """
        if isinstance(content, list):
            # Convert list of content blocks
            serializable = []
            for block in content:
                if hasattr(block, 'text'):
                    # TextContent object - extract text
                    serializable.append({"type": "text", "text": block.text})
                elif isinstance(block, dict):
                    # Already a dict - keep as is
                    serializable.append(block)
                else:
                    # Other types - convert to string
                    serializable.append({"type": "unknown", "value": str(block)})
            return serializable
        elif isinstance(content, dict):
            # Already JSON-serializable
            return content
        elif hasattr(content, 'text'):
            # Single TextContent object
            return {"type": "text", "text": content.text}
        else:
            # Fallback: convert to string
            return {"type": "string", "value": str(content)}

    def _add_signature_to_content(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        context: ExecutionContext
    ) -> dict[str, Any]:
        """
        Add AII signature to content-generating tool arguments (v0.4.10).

        For tools that create content (GitHub issues, PRs, comments), this adds
        an AII signature to the content to provide transparency and branding.

        Signature is configurable via config.yaml:
            mcp:
              signature:
                enabled: true
                style: "full"  # full, minimal, or none

        Args:
            tool_name: Name of the tool being invoked (e.g., "create_issue")
            arguments: Tool arguments dictionary
            context: Execution context

        Returns:
            Updated arguments with signature added (if applicable)
        """
        # Create formatter from config
        from ...config.manager import ConfigManager
        config_manager = ConfigManager()
        formatter = create_formatter_from_config(config_manager)

        # Content field names for different GitHub tools
        CONTENT_FIELDS = {
            "create_issue": "body",
            "create_pull_request": "body",
            "create_comment": "body",
            "create_or_update_file": "content",
        }

        # Check if this tool generates content
        content_field = CONTENT_FIELDS.get(tool_name)
        if not content_field:
            return arguments  # Not a content-generating tool

        # Check if content field exists in arguments
        if content_field not in arguments:
            return arguments  # No content to sign

        # Get original content
        original_content = arguments[content_field]
        if not isinstance(original_content, str):
            return arguments  # Content is not a string

        # Add signature
        signed_content = formatter.add_signature(
            content=original_content,
            function_name=f"github_{tool_name}"  # Match SIGNED_FUNCTIONS naming
        )

        # Update arguments with signed content
        if signed_content != original_content:
            logger.info(f"Added AII signature to {tool_name} content")
            arguments = dict(arguments)  # Create copy to avoid modifying original
            arguments[content_field] = signed_content

        return arguments
