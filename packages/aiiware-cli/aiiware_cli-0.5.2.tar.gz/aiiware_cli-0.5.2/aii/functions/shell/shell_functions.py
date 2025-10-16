"""Shell Command Functions - AI-powered shell command generation and execution"""

import asyncio
import os
import platform
from datetime import datetime
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


class ShellCommandFunction(FunctionPlugin):
    """Generate and execute shell commands based on natural language input"""

    @property
    def name(self) -> str:
        return "shell_command"

    @property
    def description(self) -> str:
        return (
            "Generate and execute shell commands based on natural language descriptions"
        )

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "request": ParameterSchema(
                name="request",
                type="string",
                required=True,
                description="Natural language description of what shell command to run",
            ),
            "execute": ParameterSchema(
                name="execute",
                type="boolean",
                required=False,
                default=False,
                description="Whether to execute the command after generation (requires confirmation)",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return True  # Always require confirmation for shell commands

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.RISKY

    @property
    def default_output_mode(self) -> OutputMode:
        """Default output mode: clean command and result only"""
        return OutputMode.CLEAN

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Supports all output modes"""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check if LLM provider and shell access are available"""
        if not context.llm_provider:
            return ValidationResult(
                valid=False,
                errors=["LLM provider required for shell command generation"],
            )
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Generate shell command and optionally execute with user confirmation"""

        request = parameters["request"]
        execute_command = parameters.get("execute", False)

        try:
            # Detect system information
            system_info = self._get_system_info()

            # Generate shell command using LLM
            if hasattr(context.llm_provider, "complete_with_usage"):
                llm_response = await context.llm_provider.complete_with_usage(
                    self._build_command_generation_prompt(request, system_info)
                )
                response_content = llm_response.content
                usage = llm_response.usage or {}
            else:
                # Fallback to regular completion
                response_content = await context.llm_provider.complete(
                    self._build_command_generation_prompt(request, system_info)
                )
                usage = {}

            # Parse the LLM response
            parsed_response = self._parse_command_response(response_content)

            if not parsed_response:
                return ExecutionResult(
                    success=False, message="Failed to generate a valid shell command"
                )

            command = parsed_response["command"]
            explanation = parsed_response.get("explanation", "Shell command generated")
            safety_notes = parsed_response.get("safety_notes", [])

            # Prepare result data
            result_data = {
                "command": command,
                "explanation": explanation,
                "system_info": system_info,
                "safety_notes": safety_notes,
                "thinking_mode": True,
                "provider": (
                    context.llm_provider.model_info
                    if hasattr(context.llm_provider, "model_info")
                    else "Unknown"
                ),
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
                "confidence": parsed_response.get("confidence", 85.0),
                "reasoning": f"Generated shell command for: {request}",
                "requires_execution_confirmation": execute_command,
                "timestamp": datetime.now().isoformat(),
            }

            # If execution is requested, prepare for confirmation
            if execute_command:
                result_data["requires_execution_confirmation"] = True
                result_data["pending_command"] = command

                return ExecutionResult(
                    success=True,
                    message=f"Generated command: `{command}`\n\n{explanation}\n\nExecute this command? [y/N]:",
                    data=result_data,
                )
            else:
                # Just return the generated command
                return ExecutionResult(
                    success=True,
                    message=f"Generated command: `{command}`\n\n{explanation}",
                    data=result_data,
                )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Shell command generation failed: {str(e)}"
            )

    def _get_system_info(self) -> dict[str, str]:
        """Get system information for command generation"""
        system = platform.system().lower()

        # Detect shell
        shell = os.environ.get("SHELL", "/bin/bash")
        if "zsh" in shell:
            shell_type = "zsh"
        elif "bash" in shell:
            shell_type = "bash"
        elif "fish" in shell:
            shell_type = "fish"
        else:
            shell_type = "bash"  # default

        return {
            "os": system,
            "shell": shell_type,
            "platform": platform.platform(),
            "home_dir": os.path.expanduser("~"),
            "current_dir": os.getcwd(),
        }

    def _build_command_generation_prompt(
        self, request: str, system_info: dict[str, str]
    ) -> str:
        """Build prompt for shell command generation"""

        return f"""You are an expert system administrator. Generate a shell command based on the user's natural language request.

System Information:
- OS: {system_info['os']}
- Shell: {system_info['shell']}
- Platform: {system_info['platform']}
- Home Directory: {system_info['home_dir']}
- Current Directory: {system_info['current_dir']}

User Request: "{request}"

Generate a safe, efficient shell command that accomplishes the user's request. Consider:
1. Use appropriate commands for the detected OS/shell
2. Include safety considerations (avoid destructive operations without explicit confirmation)
3. Use human-readable output when possible
4. Handle edge cases (empty results, permissions, etc.)
5. Prefer portable commands when possible

Respond with JSON in this format:
{{
  "command": "the actual shell command",
  "explanation": "clear explanation of what the command does",
  "safety_notes": ["list of safety considerations or warnings"],
  "confidence": 85.0,
  "reasoning": "why this command was chosen"
}}

Important: The command should be safe to run and accomplish exactly what the user requested. If the request is ambiguous, choose the most reasonable interpretation."""

    def _parse_command_response(self, response: str) -> dict[str, Any] | None:
        """Parse LLM response for shell command generation"""
        try:
            import json
            import re

            # Clean response and extract JSON
            response = response.strip()

            # Remove control characters that can break JSON parsing
            response = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", response)

            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                return None

            json_str = response[start_idx:end_idx]
            # Try parsing the JSON
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as json_err:
                # Try to fix common JSON issues
                print(f"JSON parse error: {json_err}, attempting to fix...")

                # Fix unescaped newlines and quotes in explanation
                json_str = json_str.replace("\n", "\\n").replace("\r", "\\r")
                json_str = re.sub(r'(?<!\\)"(?=.*")', '\\"', json_str)

                try:
                    data = json.loads(json_str)
                    print("Successfully parsed after cleanup")
                except json.JSONDecodeError:
                    print("Could not fix JSON, falling back to regex extraction")
                    # Last resort: regex extraction
                    command_match = re.search(r'"command"\s*:\s*"([^"]+)"', response)
                    explanation_match = re.search(
                        r'"explanation"\s*:\s*"([^"]+)"', response
                    )

                    if command_match:
                        data = {
                            "command": command_match.group(1),
                            "explanation": (
                                explanation_match.group(1)
                                if explanation_match
                                else "Command generated"
                            ),
                        }
                    else:
                        return None

            # Validate required fields
            if "command" not in data:
                return None

            return data

        except (ValueError, KeyError) as e:
            print(f"Failed to parse command response: {e}")
            return None

    async def execute_confirmed_command(
        self,
        command: str,
        context: ExecutionContext,
        original_tokens: dict[str, int] | None = None,
    ) -> ExecutionResult:
        """Execute a confirmed shell command"""
        try:
            # Execute the command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd(),
            )

            stdout, stderr = await process.communicate()

            # Prepare output
            output_lines = []

            if stdout:
                output_lines.append("📤 Output:")
                output_lines.append(stdout.decode("utf-8", errors="ignore").strip())

            if stderr:
                output_lines.append("⚠️  Error output:")
                output_lines.append(stderr.decode("utf-8", errors="ignore").strip())

            if not stdout and not stderr:
                output_lines.append("✅ Command completed with no output")

            output_text = "\n".join(output_lines)

            # Prepare data with token information
            data = {
                "command": command,
                "return_code": process.returncode,
                "stdout": stdout.decode("utf-8", errors="ignore") if stdout else "",
                "stderr": stderr.decode("utf-8", errors="ignore") if stderr else "",
                "execution_time": datetime.now().isoformat(),
            }

            # Include original token usage if provided
            if original_tokens:
                data.update(
                    {
                        "input_tokens": original_tokens.get("input_tokens"),
                        "output_tokens": original_tokens.get("output_tokens"),
                    }
                )

            return ExecutionResult(
                success=process.returncode == 0,
                message=f"Command executed: `{command}`\n\n{output_text}",
                data=data,
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Command execution failed: {str(e)}",
                data={"command": command, "error": str(e)},
            )


class FindCommandFunction(FunctionPlugin):
    """Specialized function for finding files and directories"""

    @property
    def name(self) -> str:
        return "find_files"

    @property
    def description(self) -> str:
        return "Find files and directories using intelligent search patterns"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "search_request": ParameterSchema(
                name="search_request",
                type="string",
                required=True,
                description="Natural language description of what to find (e.g., 'largest files in Downloads')",
            ),
            "path": ParameterSchema(
                name="path",
                type="string",
                required=False,
                default=".",
                description="Path to search in (default: current directory)",
            ),
            "execute": ParameterSchema(
                name="execute",
                type="boolean",
                required=False,
                default=True,
                description="Whether to execute the find command",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return True

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.RISKY

    @property
    def default_output_mode(self) -> OutputMode:
        """Default output mode: clean command and result only"""
        return OutputMode.CLEAN

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Supports all output modes"""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check if LLM provider is available"""
        if not context.llm_provider:
            return ValidationResult(
                valid=False,
                errors=["LLM provider required for intelligent file finding"],
            )
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute intelligent file finding"""

        search_request = parameters["search_request"]
        search_path = parameters.get("path", ".")
        execute_command = parameters.get("execute", True)

        try:
            # Expand path shortcuts
            if search_path.startswith("~/"):
                search_path = os.path.expanduser(search_path)
            elif search_path == "Downloads":
                search_path = os.path.expanduser("~/Downloads")
            elif search_path == "Desktop":
                search_path = os.path.expanduser("~/Desktop")
            elif search_path == "Documents":
                search_path = os.path.expanduser("~/Documents")

            # Get system information
            system_info = self._get_system_info()

            # Generate find command using LLM
            if hasattr(context.llm_provider, "complete_with_usage"):
                llm_response = await context.llm_provider.complete_with_usage(
                    self._build_find_prompt(search_request, search_path, system_info)
                )
                response_content = llm_response.content
                usage = llm_response.usage or {}
            else:
                response_content = await context.llm_provider.complete(
                    self._build_find_prompt(search_request, search_path, system_info)
                )
                usage = {}

            # Parse the response
            parsed_response = self._parse_find_response(response_content)

            if not parsed_response:
                return ExecutionResult(
                    success=False, message="Failed to generate a valid find command"
                )

            command = parsed_response["command"]
            explanation = parsed_response.get("explanation", "Find command generated")

            # Prepare result data
            result_data = {
                "command": command,
                "explanation": explanation,
                "search_request": search_request,
                "search_path": search_path,
                "thinking_mode": True,
                "provider": (
                    context.llm_provider.model_info
                    if hasattr(context.llm_provider, "model_info")
                    else "Unknown"
                ),
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
                "confidence": parsed_response.get("confidence", 90.0),
                "reasoning": f"Generated find command for: {search_request}",
                "timestamp": datetime.now().isoformat(),
            }

            # If execution is requested, prepare for confirmation
            if execute_command:
                result_data["requires_execution_confirmation"] = True
                result_data["pending_command"] = command

                clean_msg = f"Generated command: `{command}`\n\n{explanation}\n\nExecute this command? [y/N]:"
                result_data["clean_output"] = clean_msg  # For CLEAN mode

                return ExecutionResult(
                    success=True,
                    message=clean_msg,
                    data=result_data,
                )
            else:
                clean_msg = f"Generated find command: `{command}`\n\n{explanation}"
                return ExecutionResult(
                    success=True,
                    message=clean_msg,
                    data={
                        "clean_output": clean_msg,  # For CLEAN mode
                        "command": command,
                        "explanation": explanation,
                        "search_request": search_request,
                        "search_path": search_path,
                        "reasoning": f"Generated find command for: {search_request}",
                    },
                )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Find command generation failed: {str(e)}"
            )

    def _get_system_info(self) -> dict[str, str]:
        """Get system information for find command generation"""
        system = platform.system().lower()

        return {
            "os": system,
            "platform": platform.platform(),
            "home_dir": os.path.expanduser("~"),
            "current_dir": os.getcwd(),
        }

    def _build_find_prompt(
        self, search_request: str, search_path: str, system_info: dict[str, str]
    ) -> str:
        """Build prompt for find command generation"""

        return f"""You are an expert in file system navigation. Generate an efficient find command based on the user's request.

System Information:
- OS: {system_info['os']}
- Platform: {system_info['platform']}
- Search Path: {search_path}
- Current Directory: {system_info['current_dir']}

User Request: "{search_request}"

Generate a find command that:
1. Searches in the specified path: {search_path}
2. Uses appropriate options for the detected OS
3. Provides human-readable output
4. Handles common edge cases
5. Is optimized for the specific search request

Common patterns and REQUIRED implementations:
- For largest files: MUST use `find path -type f -exec du -h {{}} + | sort -rh | head -n N`
- For recent files: use find with -mtime
- For specific file types: use find with -name or -type
- For size-based searches: use find with -size

CRITICAL PERFORMANCE RULES:
1. For file size operations, ALWAYS use `du` NOT `ls`
2. ALWAYS use `{{}} +` (batching) NOT `{{}} \\;` (per-file execution)
3. For sorting sizes, use `sort -rh` for human-readable sizes
4. Example: find ~/Downloads -type f -exec du -h {{}} + | sort -rh | head -n 1

Respond with JSON:
{{
  "command": "complete find command following performance rules above",
  "explanation": "what the command does and why it's efficient",
  "confidence": 95.0,
  "reasoning": "why this approach was chosen for performance"
}}

Make the command efficient and safe to run."""

    def _parse_find_response(self, response: str) -> dict[str, Any] | None:
        """Parse LLM response for find command generation"""
        try:
            import json
            import re

            # Clean response and extract JSON
            response = response.strip()

            # Remove control characters that can break JSON parsing
            response = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", response)

            # Try multiple extraction methods
            json_patterns = [
                r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}",  # Nested JSON
                r"\{.*?\}",  # Simple JSON
            ]

            json_str = None
            for pattern in json_patterns:
                matches = re.findall(pattern, response, re.DOTALL)
                if matches:
                    json_str = matches[-1]  # Take the last match
                    break

            if not json_str:
                # Fallback: find first and last braces
                start_idx = response.find("{")
                end_idx = response.rfind("}") + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response[start_idx:end_idx]
                else:
                    return None

            # Clean the JSON string from control characters
            json_str = "".join(
                char for char in json_str if ord(char) >= 32 or char in "\n\r\t"
            )

            # Try parsing with enhanced error handling
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}, attempting to fix...")
                # Try to fix common JSON issues with multi-line explanations
                json_str_fixed = re.sub(
                    r'(?<!\\)"([^"]*\n[^"]*)"',
                    lambda m: '"'
                    + m.group(1).replace("\n", "\\n").replace('"', '\\"')
                    + '"',
                    json_str,
                )

                try:
                    data = json.loads(json_str_fixed)
                    print("Successfully parsed after cleanup")
                except json.JSONDecodeError:
                    print("Could not fix JSON, falling back to regex extraction")
                    # Last resort: extract command directly
                    command_match = re.search(r'"command"\s*:\s*"([^"]+)"', json_str)
                    if command_match:
                        data = {
                            "command": command_match.group(1),
                            "explanation": "Command generated with fallback parsing",
                        }
                    else:
                        print(f"Failed to extract command from: {json_str[:200]}...")
                        return None

            if "command" not in data:
                return None

            return data

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Failed to parse find response: {e}")
            print(f"Response was: {response[:200]}...")
            return None

    async def _execute_find_command(self, command: str) -> dict[str, Any]:
        """Execute the find command and return results"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd(),
            )

            stdout, stderr = await process.communicate()

            stdout_text = stdout.decode("utf-8", errors="ignore").strip()
            stderr_text = stderr.decode("utf-8", errors="ignore").strip()

            if process.returncode == 0 and stdout_text:
                return {
                    "success": True,
                    "output": f"🔍 Find Results:\n{stdout_text}",
                    "raw_output": stdout_text,
                }
            elif stderr_text:
                return {
                    "success": False,
                    "output": f"❌ Find command failed:\n{stderr_text}",
                    "raw_output": stderr_text,
                }
            else:
                return {
                    "success": True,
                    "output": "🔍 No results found matching your search criteria",
                    "raw_output": "",
                }

        except Exception as e:
            return {
                "success": False,
                "output": f"❌ Command execution failed: {str(e)}",
                "raw_output": str(e),
            }

    async def execute_confirmed_command(
        self,
        command: str,
        context: ExecutionContext,
        original_tokens: dict[str, int] | None = None,
    ) -> ExecutionResult:
        """Execute a confirmed find command"""
        try:
            # Track execution time
            start_time = datetime.now()

            # Execute the find command
            execution_result = await self._execute_find_command(command)

            # Calculate execution time
            end_time = datetime.now()
            execution_duration = end_time - start_time
            execution_time_str = f"{execution_duration.total_seconds():.2f}s"

            # Prepare data with token information
            data = {
                "command": command,
                "execution_output": execution_result.get("raw_output", ""),
                "execution_time": execution_time_str,
                "execution_start": start_time.isoformat(),
                "thinking_mode": True,  # Add this to trigger shell thinking mode formatter
            }

            # Include original token usage if provided
            if original_tokens:
                data.update(
                    {
                        "input_tokens": original_tokens.get("input_tokens"),
                        "output_tokens": original_tokens.get("output_tokens"),
                    }
                )

            return ExecutionResult(
                success=execution_result["success"],
                message=f"Command executed: `{command}`\n\n{execution_result['output']}",
                data=data,
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Find command execution failed: {str(e)}",
                data={"command": command, "error": str(e)},
            )
