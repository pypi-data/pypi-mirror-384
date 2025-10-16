"""Enhanced Shell Command Functions with Smart Triage System"""

import asyncio
import os
import platform
import time
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
from ...core.triage import SmartCommandTriage, CommandSafety, SafetyAnalyzer


class EnhancedShellCommandFunction(FunctionPlugin):
    """Enhanced shell command function with intelligent triage system"""

    def __init__(self):
        super().__init__()
        self.triage_engine = SmartCommandTriage()
        self.safety_analyzer = SafetyAnalyzer()

        # Show triage stats in debug mode
        import os
        if os.getenv('AII_DEBUG'):
            print(f"🔍 DEBUG: Smart Command Triage initialized: {self.triage_engine.get_stats()}")
            print(f"🔍 DEBUG: Safety Analyzer initialized")

    @property
    def name(self) -> str:
        return "shell_command"

    @property
    def description(self) -> str:
        return "Generate and execute shell commands with intelligent safety triage and performance optimization"

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
                default=True,  # v0.4.13: Default to True - users expect execution
                description="Whether to execute the command after generation (requires confirmation for risky commands)",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        # Dynamic confirmation based on command safety
        return False  # We'll handle confirmation logic in execute()

    @property
    def safety_level(self) -> FunctionSafety:
        # Dynamic safety level based on triage
        return FunctionSafety.CONTEXT_DEPENDENT

    @property
    def default_output_mode(self) -> "OutputMode":
        """Default output mode: clean command and result only"""
        from ...core.models import OutputMode
        return OutputMode.CLEAN

    @property
    def supports_output_modes(self) -> list["OutputMode"]:
        """Supports all output modes"""
        from ...core.models import OutputMode
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(self, context: ExecutionContext) -> ValidationResult:
        """Check prerequisites - LLM is optional now thanks to triage"""
        # For trivial/safe commands, we don't need LLM
        # For complex commands, we'll check LLM availability in execute()
        return ValidationResult(valid=True)

    async def execute(self, parameters: dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        """Execute with smart triage preprocessing"""

        request = parameters["request"]
        execute_command = parameters.get("execute", True)  # v0.4.13: Default to True - users expect execution
        start_time = time.time()

        try:
            # SMART TRIAGE (LLM-first with regex fallback)
            triage_result = await self.triage_engine.triage(request, context.llm_provider)

            if triage_result.bypass_llm:
                # Direct execution path for TRIVIAL/SAFE commands
                return await self._execute_direct_path(triage_result, request, execute_command, start_time, context)
            else:
                # LLM path for RISKY/DESTRUCTIVE/UNKNOWN commands
                if not context.llm_provider:
                    return ExecutionResult(
                        success=False,
                        message=f"LLM provider required for {triage_result.safety.value} command analysis"
                    )
                return await self._execute_llm_path(triage_result, request, execute_command, context, start_time)

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Command processing failed: {str(e)}"
            )

    async def _execute_direct_path(self, triage_result, request: str, execute_command: bool, start_time: float, context: ExecutionContext = None) -> ExecutionResult:
        """Direct execution path for trivial/safe commands with optional safety analysis"""

        command = triage_result.command

        # Check for dangerous patterns even in "safe" commands
        if execute_command and self.safety_analyzer.is_dangerous_pattern(command):
            # Fast dangerous pattern detected - get detailed analysis
            if context and context.llm_provider:
                analysis = await self.safety_analyzer.analyze_command(
                    command,
                    context.llm_provider
                )

                if analysis and analysis.level.value == "dangerous":
                    # Show warning and require explicit confirmation
                    confirmation_prompt = await self.safety_analyzer.get_confirmation_prompt(
                        command,
                        analysis
                    )

                    return ExecutionResult(
                        success=True,
                        message=confirmation_prompt,
                        data={
                            "command": command,
                            "safety_analysis": {
                                "level": analysis.level.value,
                                "summary": analysis.summary,
                                "risks": analysis.risks,
                                "recommendations": analysis.recommendations,
                                "alternatives": analysis.alternatives,
                            },
                            "requires_execution_confirmation": True,
                            "confirmation_type": "explicit",  # Requires "yes" not just "y"
                            "clean_output": command,
                        }
                    )

        if os.getenv("AII_DEBUG"):
            print(f"🔍 DEBUG: Checking execution path - execute_command={execute_command}, confirmation_required={triage_result.confirmation_required}, safety={triage_result.safety}")

        if execute_command and not triage_result.confirmation_required:
            # Execute immediately for trivial/safe commands
            if os.getenv("AII_DEBUG"):
                print(f"🔍 DEBUG: Taking immediate execution path (no confirmation needed)")
            try:
                exec_result = await self.triage_engine.execute_direct(triage_result, timeout=10)

                if exec_result["success"]:
                    total_time = exec_result["execution_time"]

                    return ExecutionResult(
                        success=True,
                        message=f"✓ {command}\n{exec_result['stdout']}",
                        data={
                            "command": command,
                            "output": exec_result["stdout"],
                            "clean_output": exec_result['stdout'].strip(),
                            "execution_time": total_time,
                            "safety": triage_result.safety.value,
                            "reasoning": triage_result.reasoning,
                            "bypassed_llm": True,
                            "tokens_saved": "~300-500",
                            "time_saved": f"~{14-total_time:.1f}s",
                            "confirmation_bypassed": True,
                            "triage_enabled": True
                        }
                    )
                else:
                    return ExecutionResult(
                        success=False,
                        message=f"❌ Command failed: {exec_result.get('stderr', exec_result.get('error', 'Unknown error'))}",
                        data={
                            "command": command,
                            "clean_output": exec_result.get('stderr', 'Command failed'),
                            "error": exec_result.get("error"),
                            "execution_time": exec_result["execution_time"],
                            "bypassed_llm": True
                        }
                    )

            except Exception as e:
                return ExecutionResult(
                    success=False,
                    message=f"❌ Execution error: {str(e)}",
                    data={"bypassed_llm": True, "clean_output": f"Error: {str(e)}"}
                )
        else:
            # Show command with confirmation prompt if execution is requested
            processing_time = time.time() - start_time

            # Debug logging
            if os.getenv("AII_DEBUG"):
                print(f"🔍 DEBUG: Direct path - execute_command={execute_command}, confirmation_required={triage_result.confirmation_required}")

            # If user wants execution but confirmation is required, add confirmation prompt
            if execute_command and triage_result.confirmation_required:
                if os.getenv("AII_DEBUG"):
                    print(f"🔍 DEBUG: Returning confirmation prompt for command: {command}")
                return ExecutionResult(
                    success=True,
                    message=f"Generated command: `{command}`\n\n{triage_result.reasoning}\n\nExecute this command? (y/n):",
                    data={
                        "command": command,
                        "clean_output": command,
                        "explanation": triage_result.reasoning,
                        "safety": triage_result.safety.value,
                        "bypassed_llm": True,
                        "tokens_saved": "~300-500",
                        "time_saved": f"~{14-processing_time:.1f}s",
                        "processing_time": processing_time,
                        "requires_execution_confirmation": True,
                        "triage_enabled": True
                    }
                )
            else:
                # Just show the generated command (no execution requested)
                return ExecutionResult(
                    success=True,
                    message=f"Generated command: `{command}`\n\n{triage_result.reasoning}",
                    data={
                        "command": command,
                        "clean_output": command,
                        "explanation": triage_result.reasoning,
                        "safety": triage_result.safety.value,
                        "bypassed_llm": True,
                        "tokens_saved": "~300-500",
                        "time_saved": f"~{14-processing_time:.1f}s",
                        "processing_time": processing_time,
                        "requires_execution_confirmation": False,
                        "triage_enabled": True
                    }
                )

    async def _execute_llm_path(self, triage_result, request: str, execute_command: bool, context: ExecutionContext, start_time: float) -> ExecutionResult:
        """Enhanced LLM path with safety analysis for risky/destructive commands"""

        try:
            # Get system info
            system_info = self._get_system_info()

            # Generate command using LLM
            prompt = self._build_command_generation_prompt(request, system_info, triage_result)

            if hasattr(context.llm_provider, "complete_with_usage"):
                llm_response = await context.llm_provider.complete_with_usage(prompt)
                response_content = llm_response.content
                usage = llm_response.usage or {}
            else:
                response_content = await context.llm_provider.complete(prompt)
                usage = {}

            # Parse command from response
            parsed = self._parse_command_response(response_content)
            if not parsed:
                return ExecutionResult(
                    success=False,
                    message="Failed to generate a valid shell command"
                )

            command = parsed["command"]
            explanation = parsed.get("explanation", "")

            # Check for dangerous patterns with safety analysis
            if self.safety_analyzer.is_dangerous_pattern(command):
                # Get detailed safety analysis
                analysis = await self.safety_analyzer.analyze_command(
                    command,
                    context.llm_provider
                )

                if analysis:
                    # Generate enhanced confirmation prompt
                    confirmation_prompt = await self.safety_analyzer.get_confirmation_prompt(
                        command,
                        analysis
                    )

                    return ExecutionResult(
                        success=True,
                        message=confirmation_prompt,
                        data={
                            "command": command,
                            "clean_output": command,
                            "explanation": explanation,
                            "safety_analysis": {
                                "level": analysis.level.value,
                                "summary": analysis.summary,
                                "risks": analysis.risks,
                                "recommendations": analysis.recommendations,
                                "alternatives": analysis.alternatives,
                            },
                            "requires_execution_confirmation": True,
                            "confirmation_type": "explicit" if analysis.level.value == "dangerous" else "standard",
                            "input_tokens": usage.get("input_tokens"),
                            "output_tokens": usage.get("output_tokens"),
                            "triage_safety": triage_result.safety.value,
                        }
                    )

            # Standard confirmation for non-dangerous commands
            if execute_command:
                return ExecutionResult(
                    success=True,
                    message=f"Generated command: `{command}`\n\n{explanation}\n\nExecute this command? (y/n):",
                    data={
                        "command": command,
                        "clean_output": command,
                        "explanation": explanation,
                        "requires_execution_confirmation": True,
                        "input_tokens": usage.get("input_tokens"),
                        "output_tokens": usage.get("output_tokens"),
                        "triage_safety": triage_result.safety.value,
                    }
                )
            else:
                return ExecutionResult(
                    success=True,
                    message=f"Generated command: `{command}`\n\n{explanation}",
                    data={
                        "command": command,
                        "clean_output": command,
                        "explanation": explanation,
                        "input_tokens": usage.get("input_tokens"),
                        "output_tokens": usage.get("output_tokens"),
                        "triage_safety": triage_result.safety.value,
                    }
                )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Command generation failed: {str(e)}",
                data={"clean_output": f"Error: {str(e)}"}
            )

    def _build_command_generation_prompt(self, request: str, system_info: dict[str, str], triage_result=None) -> str:
        """Build prompt for shell command generation with safety context"""

        safety_context = ""
        if triage_result:
            safety_context = f"\nSafety Level: {triage_result.safety.value}\n"
            if triage_result.reasoning:
                safety_context += f"Context: {triage_result.reasoning}\n"

        return f"""You are an expert system administrator. Generate a shell command based on the user's natural language request.

System Information:
- OS: {system_info['os']}
- Shell: {system_info['shell']}
- Platform: {system_info['platform']}
- Home Directory: {system_info['home_dir']}
- Current Directory: {system_info['current_dir']}
{safety_context}
User Request: "{request}"

Generate the actual shell command that accomplishes the user's request. Consider:
1. Use appropriate commands for the detected OS/shell
2. Generate the ACTUAL command (not a checking/preview script)
3. Use human-readable output when possible
4. Handle edge cases (empty results, permissions, etc.)
5. Prefer portable commands when possible

IMPORTANT: Generate the ACTUAL command the user wants to run. The system will handle confirmation prompts for dangerous operations - don't generate "checking" or "preview" scripts.

Examples:
- User: "remove file.txt" → `rm -i file.txt` (actual deletion, not echo/checking)
- User: "delete all logs" → `rm -i *.log` (actual deletion)
- User: "list files" → `ls -la` (listing is safe)

Respond with JSON in this format:
{{
  "command": "the actual shell command",
  "explanation": "clear explanation of what the command does",
  "safety_notes": ["list of safety considerations or warnings"],
  "confidence": 85.0,
  "reasoning": "why this command was chosen"
}}

If the request is ambiguous, choose the most reasonable interpretation."""

    async def execute_confirmed_command(
        self,
        command: str,
        context: ExecutionContext,
        original_tokens: dict[str, int] | None = None,
    ) -> ExecutionResult:
        """Execute a confirmed shell command"""
        import asyncio
        import os

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
                stdout_text = stdout.decode("utf-8").strip()
                if stdout_text:
                    output_lines.append(stdout_text)

            if stderr:
                stderr_text = stderr.decode("utf-8").strip()
                if stderr_text:
                    output_lines.append(f"⚠️  stderr: {stderr_text}")

            output = "\n".join(output_lines) if output_lines else ""
            success = process.returncode == 0

            # Prepare result data
            result_data = {
                "command": command,
                "output": output,
                "return_code": process.returncode,
                "success": success,
                "clean_output": output if output else "Command executed successfully",  # For CLEAN mode
            }

            # Include original tokens if provided
            if original_tokens:
                result_data["input_tokens"] = original_tokens.get("input_tokens")
                result_data["output_tokens"] = original_tokens.get("output_tokens")

            # Format message based on success
            if success:
                # v0.4.13: Don't repeat command (user already saw it in confirmation prompt)
                if output_lines:  # Check if there was actual output
                    message = f"✅ Command executed successfully:\n\n{output}"
                else:
                    message = "✅ Command executed successfully"
            else:
                # On failure, show command for debugging
                message = f"❌ Command failed (exit code {process.returncode}):\n\n```\n$ {command}\n```\n\n{output}"

            return ExecutionResult(
                success=success,
                message=message,
                data=result_data,
                function_name="shell_command",
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"❌ Failed to execute command: {str(e)}",
                data={
                    "command": command,
                    "error": str(e),
                    "clean_output": f"Error: {str(e)}",
                },
                function_name="shell_command",
            )

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
            data = json.loads(json_str)

            return data

        except Exception:
            return None

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