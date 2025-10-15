"""
Explain complex shell commands with safety analysis.

Features:
- LLM-powered command breakdown
- Safety risk analysis (safe/caution/dangerous)
- Suggest safer alternatives
- Example output visualization
"""

import json
from typing import Dict, Any
from aii.core.models import FunctionPlugin, FunctionSafety, ExecutionResult, ExecutionContext, OutputMode


class ExplainCommandFunction(FunctionPlugin):
    """
    Explain what a SHELL COMMAND does, with safety analysis.

    Use this for shell/bash commands with syntax (flags, pipes, etc).
    For concepts, use the 'explain' function instead.

    Examples:
    - aii explain-cmd "find . -name '*.py' | xargs rm"
    - aii explain "git reset --hard HEAD~3"
    - aii "what does rm -rf do?"
    """

    # Plugin registration attributes
    name = "explain_command"
    description = "Explain shell/bash commands with safety analysis. Use this when input contains command syntax (flags, pipes, shell commands). For concepts, use 'explain' function."
    category = "shell"
    parameters = {}
    requires_confirmation = False

    # Legacy attributes (for compatibility)
    function_name = "explain_command"
    function_description = "Explain shell/bash commands with safety analysis. Use this when input contains command syntax (flags, pipes, shell commands). For concepts, use 'explain' function."

    @property
    def default_output_mode(self) -> OutputMode:
        return OutputMode.CLEAN  # Users want just the explanation

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to explain"
                },
                "detail_level": {
                    "type": "string",
                    "enum": ["basic", "detailed", "expert"],
                    "description": "Level of detail in explanation",
                    "default": "detailed"
                }
            },
            "required": ["command"]
        }

    def get_function_safety(self) -> FunctionSafety:
        return FunctionSafety.SAFE  # Just explaining, not executing

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> ExecutionResult:
        """Execute command explanation with LLM analysis."""

        command = parameters.get("command", "")
        detail_level = parameters.get("detail_level", "detailed")

        if not command:
            return ExecutionResult(
                success=False,
                message="No command provided to explain",
                data={"clean_output": "Error: No command provided"}
            )

        # Check if LLM is available
        if not context.llm_provider:
            return ExecutionResult(
                success=False,
                message="LLM provider required for command explanation",
                data={"clean_output": "Error: LLM provider required. Run: aii config init"}
            )

        try:
            # LLM-powered command analysis
            explanation = await self._analyze_command(
                command,
                detail_level,
                context.llm_provider
            )

            # Format output
            output = self._format_explanation(explanation)

            return ExecutionResult(
                success=True,
                message=output,
                data={
                    "command": command,
                    "explanation": explanation,
                    "clean_output": output  # For CLEAN mode
                }
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Failed to explain command: {str(e)}",
                data={"clean_output": f"Error: {str(e)}"}
            )

    async def _analyze_command(
        self,
        command: str,
        detail_level: str,
        llm_provider
    ) -> Dict[str, Any]:
        """Use LLM to analyze command comprehensively."""

        prompt = f"""You are a shell command expert. Analyze this command comprehensively:

Command: {command}

Provide a detailed analysis with the following structure:

1. **Summary**: One-line description of what the command does

2. **Breakdown**: Explain each part of the command (split by pipes, flags, arguments)
   Format as a list of objects with:
   - syntax: the exact part of the command
   - description: what it does

3. **Safety Analysis**:
   - level: "safe" | "caution" | "dangerous"
   - risks: list of potential risks (can be empty for safe commands)
   - recommendations: list of safety recommendations (can be empty for safe commands)

4. **Alternatives**: Safer or more efficient alternative commands (can be empty if command is already safe/optimal)

5. **Example Output**: Show what the command would typically produce (brief example)

Detail level: {detail_level}

Return ONLY valid JSON with this exact structure (no markdown, no code blocks):
{{
  "summary": "...",
  "breakdown": [
    {{"syntax": "...", "description": "..."}},
    ...
  ],
  "safety": {{
    "level": "safe",
    "risks": ["...", ...],
    "recommendations": ["...", ...]
  }},
  "alternatives": ["...", ...],
  "example_output": "..."
}}
"""

        try:
            # Use LLM to generate structured response
            # Try complete first (most common for PydanticAI)
            if hasattr(llm_provider, 'complete') and callable(llm_provider.complete):
                response = await llm_provider.complete(prompt)
            elif hasattr(llm_provider, 'complete_with_usage') and callable(llm_provider.complete_with_usage):
                llm_response = await llm_provider.complete_with_usage(prompt)
                response = llm_response.content
            elif hasattr(llm_provider, 'generate') and callable(llm_provider.generate):
                response = await llm_provider.generate(prompt)
            else:
                raise AttributeError("LLM provider has no compatible method (complete/complete_with_usage/generate)")

            # Parse JSON response
            # Clean response (remove markdown code blocks if present)
            response_text = response.strip()
            if response_text.startswith("```"):
                # Remove code block markers
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1] if len(lines) > 2 else lines)
                if response_text.startswith("json"):
                    response_text = response_text[4:].strip()

            explanation = json.loads(response_text)

            # Validate structure
            required_keys = ["summary", "breakdown", "safety", "alternatives", "example_output"]
            for key in required_keys:
                if key not in explanation:
                    explanation[key] = {} if key == "safety" else [] if key in ["breakdown", "alternatives"] else ""

            # Ensure safety has required fields
            if "level" not in explanation["safety"]:
                explanation["safety"]["level"] = "unknown"
            if "risks" not in explanation["safety"]:
                explanation["safety"]["risks"] = []
            if "recommendations" not in explanation["safety"]:
                explanation["safety"]["recommendations"] = []

            return explanation

        except json.JSONDecodeError as e:
            # Fallback with basic structure
            return {
                "summary": f"Command: {command}",
                "breakdown": [{"syntax": command, "description": "Unable to parse detailed breakdown"}],
                "safety": {
                    "level": "unknown",
                    "risks": ["Could not analyze safety - please verify command before running"],
                    "recommendations": ["Consult command documentation"]
                },
                "alternatives": [],
                "example_output": "Unable to generate example"
            }
        except Exception as e:
            # Fallback on any error
            return {
                "summary": f"Command: {command}",
                "breakdown": [{"syntax": command, "description": f"Analysis error: {str(e)}"}],
                "safety": {
                    "level": "unknown",
                    "risks": ["Unable to analyze command safety"],
                    "recommendations": []
                },
                "alternatives": [],
                "example_output": ""
            }

    def _format_explanation(self, explanation: Dict[str, Any]) -> str:
        """Format explanation for CLI output."""

        output = []

        # Summary
        output.append("📝 Command Summary")
        output.append(f"{explanation.get('summary', 'N/A')}\n")

        # Breakdown
        breakdown = explanation.get('breakdown', [])
        if breakdown:
            output.append("🔍 Breakdown:")
            for i, part in enumerate(breakdown, 1):
                syntax = part.get('syntax', '')
                desc = part.get('description', '')
                output.append(f"  {i}. `{syntax}`")
                output.append(f"     → {desc}")
            output.append("")

        # Safety analysis
        safety = explanation.get('safety', {})
        safety_level = safety.get('level', 'unknown')
        safety_icons = {
            "safe": "✅",
            "caution": "⚠️",
            "dangerous": "🚨",
            "unknown": "❓"
        }

        icon = safety_icons.get(safety_level, "❓")
        output.append(f"{icon} Safety: {safety_level.upper()}")

        risks = safety.get('risks', [])
        if risks:
            output.append("Potential Risks:")
            for risk in risks:
                output.append(f"  • {risk}")

        recommendations = safety.get('recommendations', [])
        if recommendations:
            output.append("\nRecommendations:")
            for rec in recommendations:
                output.append(f"  • {rec}")

        output.append("")

        # Alternatives
        alternatives = explanation.get('alternatives', [])
        if alternatives:
            output.append("💡 Safer/Better Alternatives:")
            for alt in alternatives:
                output.append(f"  • `{alt}`")
            output.append("")

        # Example output
        example = explanation.get('example_output', '')
        if example:
            output.append("📄 Example Output:")
            output.append("```")
            output.append(example)
            output.append("```")

        return "\n".join(output)
