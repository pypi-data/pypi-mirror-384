"""Git Functions - Git workflow automation with AI assistance"""

import json
import os
import subprocess
import tempfile
from typing import Any

from ...cli.status_display import ProgressTracker
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
from .branch_namer import BranchNamer, BranchNameConfig
from .github_client import GitHubClient
from .pr_generator import PRGenerator


class GitCommitFunction(FunctionPlugin):
    """Generate AI-powered git commit message and execute commit"""

    # Class-level state to persist between function calls
    _global_pending_commit_message = None
    _global_pending_thinking_data = None

    @staticmethod
    def _get_pending_commit_file():
        """Get the path to the temporary file storing pending commit data"""
        return os.path.join(tempfile.gettempdir(), "aii_pending_commit.json")

    @staticmethod
    def _save_pending_commit(commit_data):
        """Save pending commit data to temporary file"""
        try:
            with open(GitCommitFunction._get_pending_commit_file(), "w") as f:
                json.dump(commit_data, f)
        except Exception:
            pass  # Fallback to static variables if file fails

    @staticmethod
    def _load_pending_commit():
        """Load pending commit data from temporary file"""
        try:
            file_path = GitCommitFunction._get_pending_commit_file()
            if os.path.exists(file_path):
                with open(file_path) as f:
                    return json.load(f)
        except Exception:
            pass  # Fallback to static variables if file fails
        return None

    @staticmethod
    def _clear_pending_commit():
        """Clear pending commit data from temporary file"""
        try:
            file_path = GitCommitFunction._get_pending_commit_file()
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass  # Fallback to static variables if file fails

    @property
    def name(self) -> str:
        return "git_commit"

    @property
    def description(self) -> str:
        return "Generate AI-powered git commit message and execute commit"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.GIT

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "context": ParameterSchema(
                name="context",
                type="string",
                required=False,
                description="Optional guidance for commit message generation",
            ),
            "auto_stage": ParameterSchema(
                name="auto_stage",
                type="boolean",
                required=False,
                default=False,
                description="Automatically stage changes before committing",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        # We handle our own custom confirmation workflow with thinking mode display
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        # Still risky, but we manage confirmation ourselves
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        """Default output mode: full reasoning and context"""
        return OutputMode.THINKING

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Supports all output modes"""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check if git is available and we're in a git repository"""
        try:
            # Check if git is available
            result = subprocess.run(
                ["git", "--version"], capture_output=True, text=True
            )
            if result.returncode != 0:
                return ValidationResult(
                    valid=False,
                    errors=["Git is not installed or not available in PATH"],
                )

            # Check if we're in a git repository
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"], capture_output=True, text=True
            )
            if result.returncode != 0:
                return ValidationResult(valid=False, errors=["Not in a git repository"])

            return ValidationResult(valid=True)

        except Exception as e:
            return ValidationResult(
                valid=False, errors=[f"Failed to validate git prerequisites: {str(e)}"]
            )

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute git commit with AI-generated message in thinking mode"""
        try:
            auto_stage = parameters.get("auto_stage", False)
            commit_context = parameters.get("context", "")

            # Initialize progress tracker
            progress = ProgressTracker(use_emojis=True, use_animations=True)

            # Define the workflow steps
            if auto_stage:
                progress.add_step("Staging changes", icon="📁")
            progress.add_step("Analyzing changes", icon="🔍")
            progress.add_step("Generating commit message", icon="🤖")
            progress.add_step("Formatting and validating", icon="✨")

            step_index = 0

            # Step 1: Auto-stage changes if requested
            if auto_stage:
                progress.start_step(step_index)
                result = subprocess.run(
                    ["git", "add", "-A"], capture_output=True, text=True
                )
                if result.returncode != 0:
                    progress.complete_step(step_index, success=False)
                    progress.finish()
                    return ExecutionResult(
                        success=False,
                        message=f"Failed to stage changes: {result.stderr}",
                    )
                progress.complete_step(step_index, success=True)
                step_index += 1

            # Step 2: Get staged changes
            progress.start_step(step_index)

            # Get diff with binary file detection
            diff_result = subprocess.run(
                ["git", "diff", "--cached", "--numstat"], capture_output=True, text=True
            )
            if diff_result.returncode != 0:
                progress.complete_step(step_index, success=False)
                progress.finish()
                return ExecutionResult(
                    success=False,
                    message=f"Failed to get staged changes: {diff_result.stderr}",
                )

            if not diff_result.stdout.strip():
                # Analysis succeeded, but no changes found - mark as successful
                progress.complete_step(step_index, success=True)
                progress.finish()
                return ExecutionResult(
                    success=False,
                    message="No staged changes found. Use 'git add' first or use --auto-stage",
                )

            # Detect binary files and get detailed diff for text files only
            binary_files = []
            text_files = []

            for line in diff_result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        added, removed, filename = parts[0], parts[1], parts[2]
                        # Binary files show as "-" for both added and removed
                        if added == '-' and removed == '-':
                            binary_files.append(filename)
                        else:
                            text_files.append(filename)

            # Get detailed diff for text files only
            detailed_diff_result = subprocess.run(
                ["git", "diff", "--cached"] + text_files if text_files else ["git", "diff", "--cached"],
                capture_output=True,
                text=True
            )

            # Build diff output with binary file summary
            diff_output = detailed_diff_result.stdout

            if binary_files:
                binary_summary = f"\n\n📦 Binary files changed ({len(binary_files)}):\n"
                binary_summary += "\n".join(f"  • {f}" for f in binary_files)
                diff_output += binary_summary

            progress.complete_step(step_index, success=True)
            step_index += 1

            # Step 3: Generate commit message using LLM with thinking mode
            if not context.llm_provider:
                progress.finish()
                return ExecutionResult(
                    success=False,
                    message="LLM provider not available for commit message generation",
                )

            progress.start_step(step_index)

            # Generate comprehensive commit analysis using LLM
            commit_result = await self._generate_commit_with_thinking(
                diff_output, commit_context, context.llm_provider
            )
            progress.complete_step(step_index, success=True)
            step_index += 1

            # Step 4: Formatting and validating
            progress.start_step(step_index)

            # Store the commit message and thinking mode data for later execution after user confirmation
            thinking_data = {
                "git_diff": diff_output,
                "commit_message": commit_result["commit_message"],
                "reasoning": commit_result["reasoning"],
                "confidence": commit_result["confidence"],
                "input_tokens": commit_result["input_tokens"],
                "output_tokens": commit_result["output_tokens"],
                "thinking_mode": True,
                "provider": (
                    context.llm_provider.model_info if context.llm_provider else "LLM"
                ),
                "binary_files": binary_files if binary_files else None,
            }

            # Save to both file-based storage and static variables for redundancy
            GitCommitFunction._global_pending_commit_message = commit_result[
                "commit_message"
            ]
            GitCommitFunction._global_pending_thinking_data = thinking_data
            self._save_pending_commit(thinking_data)

            progress.complete_step(step_index, success=True)
            progress.finish()

            # Return thinking mode data (no actual commit yet - will be confirmed by user)
            return ExecutionResult(
                success=True,
                message="",  # Empty message - thinking mode will handle display
                data={
                    "git_diff": diff_output,  # Use detailed diff with binary file handling
                    "commit_message": commit_result["commit_message"],
                    "reasoning": commit_result["reasoning"],
                    "confidence": commit_result["confidence"],
                    "input_tokens": commit_result["input_tokens"],
                    "output_tokens": commit_result["output_tokens"],
                    "thinking_mode": True,
                    "provider": (
                        context.llm_provider.model_info
                        if context.llm_provider
                        else "LLM"
                    ),
                    "requires_commit_confirmation": True,
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Git commit execution failed: {str(e)}"
            )

    async def _generate_commit_with_thinking(
        self, diff: str, context: str, llm_provider: Any
    ) -> dict[str, Any]:
        """Generate commit message with comprehensive thinking analysis"""

        # Build enhanced prompt for thinking mode based on aii_0_3_x pattern
        guidance = (
            context
            if context
            else "Generate a comprehensive commit message with proper conventional commit format"
        )

        prompt = f"""Analyze the following git diff and generate a Conventional Commit message.
Guidance: {guidance}

Git diff of staged changes:
```diff
{diff[:3000]}{"..." if len(diff) > 3000 else ""}
```

Please generate:
1. A concise commit message following Conventional Commits format (type(scope): description)
2. Use appropriate types: feat, fix, refactor, docs, style, test, chore, perf, ci, revert
3. Keep the subject line under 72 characters
4. Include a body if the changes are complex and need explanation
5. Focus on WHY the changes were made, not just WHAT was changed

Format your response as:
THINKING: [Your detailed analysis of what changed, the impact, and reasoning for the commit message]
COMMIT_MESSAGE: [The actual commit message in conventional format - plain text only, no markdown formatting]
CONFIDENCE: [percentage]

IMPORTANT: The commit message should be plain text only, without any markdown code blocks, backticks, or other formatting.

Rules for commit message:
- Use conventional commit format: type(scope): description
- Types: feat, fix, refactor, docs, style, test, chore, perf, ci, revert
- Keep the subject line under 72 characters
- Include a body if the changes are complex and need explanation
- Focus on WHY the changes were made, not just WHAT was changed
- Add footer: 🤖 Generated by aii - https://pypi.org/project/aiiware-cli"""

        try:
            import asyncio

            # Use complete_with_usage for accurate token tracking
            if hasattr(llm_provider, "complete_with_usage"):
                # Add timeout to LLM call to prevent hanging
                llm_response = await asyncio.wait_for(
                    llm_provider.complete_with_usage(prompt), timeout=30.0
                )
                response = llm_response.content.strip()
                usage = llm_response.usage or {}
            else:
                # Fallback to basic complete with estimates
                response = await asyncio.wait_for(
                    llm_provider.complete(prompt), timeout=30.0
                )
                usage = {
                    "input_tokens": len(prompt.split()) + len(diff.split()),
                    "output_tokens": len(response.split()) if response else 0
                }

            # Parse the structured response
            thinking, commit_message, confidence = self._parse_commit_response(
                response, diff
            )

            return {
                "commit_message": commit_message,
                "reasoning": thinking,
                "confidence": confidence,
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
            }

        except TimeoutError:
            # Fallback with basic analysis when LLM times out
            from ...main import GIT_COMMIT_SIGNATURE

            return {
                "commit_message": f"chore: update files\n\n{GIT_COMMIT_SIGNATURE}",
                "reasoning": "LLM call timed out after 30 seconds. Generated fallback commit message based on staged changes.",
                "confidence": 40.0,
                "input_tokens": len(prompt.split()) if "prompt" in locals() else 0,
                "output_tokens": 10,
            }
        except Exception as e:
            # Fallback with basic analysis for other errors
            from ...main import GIT_COMMIT_SIGNATURE

            return {
                "commit_message": f"chore: update files\n\n{GIT_COMMIT_SIGNATURE}",
                "reasoning": f"Failed to analyze diff due to error: {str(e)}. Generated fallback commit message.",
                "confidence": 30.0,
                "input_tokens": len(prompt.split()) if "prompt" in locals() else 0,
                "output_tokens": 10,
            }

    def _parse_commit_response(
        self, response: str, diff: str
    ) -> tuple[str, str, float]:
        """Parse the structured LLM response into thinking, commit message, and confidence"""
        try:
            lines = response.strip().split("\n")
            thinking = ""
            commit_message = ""
            confidence = 85.0

            current_section = None
            content_lines = []

            for line in lines:
                line = line.strip()
                if line.startswith("THINKING:"):
                    if current_section and content_lines:
                        if current_section == "thinking":
                            thinking = "\n".join(content_lines).strip()
                        elif current_section == "commit_message":
                            commit_message = "\n".join(content_lines).strip()

                    current_section = "thinking"
                    content_lines = [line[9:].strip()]  # Remove "THINKING: " prefix
                elif line.startswith("COMMIT_MESSAGE:"):
                    if current_section == "thinking" and content_lines:
                        thinking = "\n".join(content_lines).strip()

                    current_section = "commit_message"
                    content_lines = [
                        line[15:].strip()
                    ]  # Remove "COMMIT_MESSAGE: " prefix
                elif line.startswith("CONFIDENCE:"):
                    if current_section == "commit_message" and content_lines:
                        commit_message = "\n".join(content_lines).strip()

                    conf_text = line[11:].strip().rstrip("%")
                    try:
                        confidence = float(conf_text)
                    except ValueError:
                        confidence = 85.0
                    break
                else:
                    if current_section and line:
                        content_lines.append(line)

            # Handle the last section if CONFIDENCE wasn't found
            if current_section == "commit_message" and content_lines:
                commit_message = "\n".join(content_lines).strip()
            elif current_section == "thinking" and content_lines:
                thinking = "\n".join(content_lines).strip()

            # Fallback parsing if structured parsing fails
            if not commit_message:
                # Try to extract commit message from response
                commit_message = response.strip()
                thinking = f"Analyzed git diff containing {len(diff.split('@@'))} sections of changes."

            # Clean up any markdown formatting from the commit message
            commit_message = self._clean_markdown_formatting(commit_message)

            # Ensure proper conventional commit formatting (blank line between subject and body)
            commit_message = self._ensure_proper_commit_formatting(commit_message)

            # Ensure the footer is included with proper spacing
            # v0.4.10: Use unified markdown signature format
            if "Generated with [aii]" not in commit_message and "Generated with aii" not in commit_message and "Generated by aii" not in commit_message:
                # Add footer with proper spacing (markdown format)
                commit_message = (
                    commit_message.rstrip()
                )  # Remove any trailing whitespace/newlines
                commit_message += (
                    "\n\n🤖 Generated with [aii](https://pypi.org/project/aiiware-cli)"
                )
            else:
                # Footer already exists, ensure proper spacing before it
                # Split the message to separate content from footer (handle old formats)
                if "🤖 Generated with [aii]" in commit_message:
                    parts = commit_message.split("🤖 Generated with [aii]")
                elif "🤖 Generated with aii" in commit_message:
                    parts = commit_message.split("🤖 Generated with aii")
                else:
                    parts = commit_message.split("🤖 Generated by aii")

                if len(parts) == 2:
                    content = parts[0].rstrip()  # Remove trailing whitespace
                    # Use new markdown format
                    footer = "🤖 Generated with [aii](https://pypi.org/project/aiiware-cli)"
                    commit_message = content + "\n\n" + footer

            return thinking, commit_message, confidence

        except Exception:
            return (
                "Analysis of git diff with multiple file changes.",
                "chore: update files\n\n🤖 Generated with [aii](https://pypi.org/project/aiiware-cli)",
                75.0,
            )

    async def execute_confirmed_commit(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute the actual git commit after user confirmation"""
        try:
            # Try to get the commit data from file-based storage first, then fallback to static variables
            pending_data = self._load_pending_commit()
            if pending_data:
                commit_message = pending_data.get("commit_message")
                thinking_data = pending_data
            else:
                commit_message = GitCommitFunction._global_pending_commit_message
                thinking_data = GitCommitFunction._global_pending_thinking_data or {}

            if not commit_message:
                return ExecutionResult(
                    success=False,
                    message="No pending commit message found. Please run git commit again.",
                )

            # Perform the actual git commit
            result = subprocess.run(
                ["git", "commit", "-m", commit_message], capture_output=True, text=True
            )

            if result.returncode != 0:
                return ExecutionResult(
                    success=False, message=f"Git commit failed: {result.stderr}"
                )

            # thinking_data already retrieved above

            # Clear the pending commit message and thinking data from both storage methods
            GitCommitFunction._global_pending_commit_message = None
            GitCommitFunction._global_pending_thinking_data = None
            self._clear_pending_commit()

            return ExecutionResult(
                success=True,
                message=f"✅ Commit successful!\n\n{result.stdout}",
                data={
                    "commit_executed": True,
                    "git_output": result.stdout,
                    # Don't include thinking_mode to avoid duplicate display
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Git commit execution failed: {str(e)}"
            )

    def _clean_markdown_formatting(self, commit_message: str) -> str:
        """Remove markdown formatting from commit message"""
        import re

        # Remove code block backticks
        commit_message = re.sub(r"^```\s*\n?", "", commit_message, flags=re.MULTILINE)
        commit_message = re.sub(r"\n?```\s*$", "", commit_message, flags=re.MULTILINE)

        # Remove inline code backticks
        commit_message = re.sub(r"`([^`]+)`", r"\1", commit_message)

        # Remove any remaining backticks
        commit_message = commit_message.replace("`", "")

        # Clean up any extra whitespace
        commit_message = commit_message.strip()

        return commit_message

    def _ensure_proper_commit_formatting(self, commit_message: str) -> str:
        """Ensure proper conventional commit formatting with blank line between subject and body"""
        lines = commit_message.split("\n")

        if len(lines) <= 1:
            # Single line commit, no body
            return commit_message

        # Find the subject line (first non-empty line)
        subject_line = lines[0].strip()

        # Check if there's already a blank line after the subject
        if len(lines) >= 2 and lines[1].strip() == "":
            # Already properly formatted
            return commit_message

        # Need to add blank line between subject and body
        if len(lines) >= 2 and lines[1].strip() != "":
            # There's content immediately after subject, add blank line
            formatted_lines = [subject_line, ""] + lines[1:]
            return "\n".join(formatted_lines)

        return commit_message


class GitDiffFunction(FunctionPlugin):
    """Show git diff with optional AI analysis"""

    @property
    def name(self) -> str:
        return "git_diff"

    @property
    def description(self) -> str:
        return "Show git diff with optional AI analysis"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.GIT

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "staged": ParameterSchema(
                name="staged",
                type="boolean",
                required=False,
                default=False,
                description="Show staged changes (--cached)",
            ),
            "file_path": ParameterSchema(
                name="file_path",
                type="string",
                required=False,
                description="Specific file to diff",
            ),
            "analyze": ParameterSchema(
                name="analyze",
                type="boolean",
                required=False,
                default=False,
                description="Provide AI analysis of changes",
            ),
            "commit": ParameterSchema(
                name="commit",
                type="string",
                required=False,
                description="Show changes in specific commit (e.g., 'HEAD', 'HEAD~1', commit hash)",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check git availability"""
        try:
            result = subprocess.run(["git", "--version"], capture_output=True)
            if result.returncode != 0:
                return ValidationResult(valid=False, errors=["Git not available"])

            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"], capture_output=True
            )
            if result.returncode != 0:
                return ValidationResult(valid=False, errors=["Not in a git repository"])

            return ValidationResult(valid=True)

        except Exception as e:
            return ValidationResult(valid=False, errors=[str(e)])

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute git diff"""
        try:
            commit = parameters.get("commit")

            if commit:
                # Show changes in a specific commit
                if commit.lower() in ["head", "last", "latest"]:
                    cmd = ["git", "show", "--format=fuller", "HEAD"]
                else:
                    cmd = ["git", "show", "--format=fuller", commit]
            else:
                # Standard git diff
                cmd = ["git", "diff"]

                if parameters.get("staged", False):
                    cmd.append("--cached")

            file_path = parameters.get("file_path")
            if file_path and not commit:
                cmd.append(file_path)

            # First, get numstat to detect binary files
            numstat_cmd = cmd.copy()
            if "--cached" in numstat_cmd:
                # For staged changes, use --numstat with --cached
                numstat_cmd.append("--numstat")
            else:
                # For regular diff, use --numstat
                if "show" not in numstat_cmd[1]:
                    numstat_cmd.append("--numstat")

            # Detect binary files (only for regular diff, not commit show)
            binary_files = []
            if commit:
                # For commit show, just get the output
                result = subprocess.run(cmd, capture_output=True, text=True)
            else:
                # For regular diff, detect binary files first
                numstat_result = subprocess.run(numstat_cmd, capture_output=True, text=True)

                if numstat_result.returncode == 0 and numstat_result.stdout.strip():
                    for line in numstat_result.stdout.strip().split('\n'):
                        if line.strip():
                            parts = line.split('\t')
                            if len(parts) >= 3:
                                added, removed, filename = parts[0], parts[1], parts[2]
                                # Binary files show as "-" for both added and removed
                                if added == '-' and removed == '-':
                                    binary_files.append(filename)

                # Get detailed diff
                result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                return ExecutionResult(
                    success=False, message=f"Git diff failed: {result.stderr}"
                )

            diff_output = result.stdout

            # Add binary file summary if any
            if binary_files:
                binary_summary = f"\n\n📦 Binary files changed ({len(binary_files)}):\n"
                binary_summary += "\n".join(f"  • {f}" for f in binary_files)
                binary_summary += "\n\n(Binary file content not shown)"
                diff_output += binary_summary

            if not diff_output.strip() and not binary_files:
                return ExecutionResult(success=True, message="No changes to show")

            # AI analysis if requested
            analysis = ""
            usage = {}
            if parameters.get("analyze", False) and context.llm_provider:
                analysis, usage = await self._analyze_diff(diff_output, context.llm_provider)

            message = diff_output
            if analysis:
                message = f"AI Analysis:\\n{analysis}\\n\\nDiff:\\n{diff_output}"

            return ExecutionResult(
                success=True,
                message=message,
                data={
                    "diff": diff_output,
                    "analysis": analysis,
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Git diff execution failed: {str(e)}"
            )

    async def _analyze_diff(self, diff: str, llm_provider: Any) -> tuple[str, dict]:
        """Analyze diff using LLM and return analysis with token usage"""
        prompt = f"""Analyze this git diff and provide insights:

{diff[:1500]}{"..." if len(diff) > 1500 else ""}

Please provide:
1. Summary of changes
2. Potential impacts
3. Code quality observations
4. Security considerations (if any)

Keep analysis concise and focused."""

        try:
            # Use complete_with_usage for accurate token tracking
            if hasattr(llm_provider, "complete_with_usage"):
                llm_response = await llm_provider.complete_with_usage(prompt)
                analysis = llm_response.content.strip()
                usage = llm_response.usage or {}
            else:
                analysis = await llm_provider.complete(prompt)
                # Fallback to estimates if usage tracking unavailable
                usage = {
                    "input_tokens": len(prompt.split()) + len(diff[:1500].split()),
                    "output_tokens": len(analysis.split()) if analysis else 0
                }
            return analysis, usage
        except Exception:
            return "Analysis unavailable", {}


class GitStatusFunction(FunctionPlugin):
    """Show git status with helpful suggestions"""

    @property
    def name(self) -> str:
        return "git_status"

    @property
    def description(self) -> str:
        return "Show git status with helpful suggestions"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.GIT

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {}

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check git availability"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"], capture_output=True
            )
            return ValidationResult(valid=result.returncode == 0)
        except Exception:
            return ValidationResult(valid=False, errors=["Git not available"])

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute git status"""
        try:
            # Get git status
            result = subprocess.run(
                ["git", "status", "--porcelain"], capture_output=True, text=True
            )
            if result.returncode != 0:
                return ExecutionResult(
                    success=False, message=f"Git status failed: {result.stderr}"
                )

            status_lines = (
                result.stdout.strip().split("\\n") if result.stdout.strip() else []
            )

            # Get branch info
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"], capture_output=True, text=True
            )
            current_branch = (
                branch_result.stdout.strip()
                if branch_result.returncode == 0
                else "unknown"
            )

            # Parse status
            staged_files = []
            unstaged_files = []
            untracked_files = []

            for line in status_lines:
                if not line:
                    continue

                status = line[:2]
                filename = line[3:]

                if status[0] in ["A", "M", "D", "R", "C"]:  # Staged
                    staged_files.append(f"{status[0]} {filename}")
                if status[1] in ["M", "D"] or status == " M":  # Modified unstaged
                    unstaged_files.append(f"M {filename}")
                if status == "??":  # Untracked
                    untracked_files.append(filename)

            # Build status message
            message_parts = [f"On branch: {current_branch}"]

            if staged_files:
                message_parts.append(f"\\nStaged changes ({len(staged_files)} files):")
                message_parts.extend(f"  {f}" for f in staged_files)

            if unstaged_files:
                message_parts.append(
                    f"\\nUnstaged changes ({len(unstaged_files)} files):"
                )
                message_parts.extend(f"  {f}" for f in unstaged_files)

            if untracked_files:
                message_parts.append(
                    f"\\nUntracked files ({len(untracked_files)} files):"
                )
                message_parts.extend(f"  {f}" for f in untracked_files[:10])
                if len(untracked_files) > 10:
                    message_parts.append(f"  ... and {len(untracked_files) - 10} more")

            if not any([staged_files, unstaged_files, untracked_files]):
                message_parts.append("\\nWorking directory clean")

            # Add suggestions
            suggestions = []
            if unstaged_files or untracked_files:
                suggestions.append("Use 'git add <file>' to stage changes")
            if staged_files:
                suggestions.append(
                    "Use 'aii git commit' to commit with AI-generated message"
                )

            if suggestions:
                message_parts.append("\\nSuggestions:")
                message_parts.extend(f"  • {s}" for s in suggestions)

            return ExecutionResult(
                success=True,
                message="\\n".join(message_parts),
                data={
                    "branch": current_branch,
                    "staged_files": staged_files,
                    "unstaged_files": unstaged_files,
                    "untracked_files": untracked_files,
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Git status execution failed: {str(e)}"
            )


class GitPRFunction(FunctionPlugin):
    """Generate AI-powered pull request description and create PR on GitHub"""

    # Class-level state to persist between function calls (confirmation workflow)
    _global_pending_pr_data = None

    @staticmethod
    def _get_pending_pr_file():
        """Get the path to the temporary file storing pending PR data"""
        return os.path.join(tempfile.gettempdir(), "aii_pending_pr.json")

    @staticmethod
    def _save_pending_pr(pr_data):
        """Save pending PR data to temporary file"""
        try:
            with open(GitPRFunction._get_pending_pr_file(), "w") as f:
                json.dump(pr_data, f)
        except Exception:
            pass  # Fallback to static variables if file fails

    @staticmethod
    def _load_pending_pr():
        """Load pending PR data from temporary file"""
        try:
            file_path = GitPRFunction._get_pending_pr_file()
            if os.path.exists(file_path):
                with open(file_path) as f:
                    return json.load(f)
        except Exception:
            pass  # Fallback to static variables if file fails
        return None

    @staticmethod
    def _clear_pending_pr():
        """Clear pending PR data from temporary file"""
        try:
            file_path = GitPRFunction._get_pending_pr_file()
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

    @property
    def name(self) -> str:
        return "git_pr"

    @property
    def description(self) -> str:
        return "Create a GitHub pull request (PR) by analyzing commits and generating title and description"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.GIT

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "base_branch": ParameterSchema(
                name="base_branch",
                type="string",
                required=False,
                description="Base branch for PR (default: main/master)",
            ),
            "draft": ParameterSchema(
                name="draft",
                type="boolean",
                required=False,
                default=False,
                description="Create PR as draft",
            ),
            "auto_confirm": ParameterSchema(
                name="auto_confirm",
                type="boolean",
                required=False,
                default=False,
                description="Skip confirmation prompt",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        # We handle our own custom confirmation workflow with PR preview
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        # Still risky, but we manage confirmation ourselves
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        """Default output mode: show metrics, not full thinking"""
        return OutputMode.STANDARD

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Supports all output modes"""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check if gh is installed and authenticated"""
        github_client = GitHubClient()

        if not github_client.check_gh_installed():
            return ValidationResult(
                valid=False,
                errors=[
                    "GitHub CLI (gh) not installed. Install from: https://cli.github.com/"
                ],
            )

        if not github_client.check_gh_authenticated():
            return ValidationResult(
                valid=False,
                errors=[
                    "Not authenticated with GitHub. Run: gh auth login"
                ],
            )

        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute PR generation and preparation for confirmation"""
        try:
            # Clear any stale pending data from previous runs
            # When the user confirms, the engine will call execute_confirmed_pr() directly
            GitPRFunction._global_pending_pr_data = None
            self._clear_pending_pr()

            # Initialize GitHub client
            github_client = GitHubClient()

            # Get repository and branch info
            try:
                repo = github_client.get_repo_info()
                current_branch = github_client.get_current_branch()
                base_branch = parameters.get("base_branch") or repo.default_branch
            except Exception as e:
                return ExecutionResult(
                    success=False, message=f"Failed to get repository info: {str(e)}"
                )

            # Get commits since divergence
            try:
                commits = github_client.get_commits_since_divergence(
                    base_branch, current_branch
                )
            except Exception as e:
                return ExecutionResult(
                    success=False, message=f"Failed to get commits: {str(e)}"
                )

            if not commits:
                return ExecutionResult(
                    success=False,
                    message=f"No commits found on '{current_branch}' since '{base_branch}'. Nothing to create PR for.",
                )

            # Generate PR description with LLM
            if not context.llm_provider:
                return ExecutionResult(
                    success=False,
                    message="LLM provider not available for PR generation",
                )

            pr_generator = PRGenerator(context.llm_provider)
            pr_description, token_usage = await pr_generator.generate_pr_description(
                commits=commits, current_branch=current_branch, base_branch=base_branch
            )

            # Format PR for display
            pr_markdown = pr_description.to_markdown()

            display_text = f"""╭─────────────────────────────────────────────────────────╮
│ 🎯 Generated Pull Request                               │
╰─────────────────────────────────────────────────────────╯

Title: {pr_description.title}

{pr_markdown}
---
📊 Analyzed {len(commits)} commit(s) across {base_branch}..{current_branch}

Create this PR? (y/n): """

            # Store confirmation data for later execution
            confirmation_data = {
                "title": pr_description.title,
                "body": pr_markdown,
                "base_branch": base_branch,
                "draft": parameters.get("draft", False),
                "commits_analyzed": len(commits),
                "repo_owner": repo.owner,
                "repo_name": repo.name,
            }

            # Save to both file-based storage and static variables for redundancy
            GitPRFunction._global_pending_pr_data = confirmation_data
            self._save_pending_pr(confirmation_data)

            return ExecutionResult(
                success=True,
                message=display_text,  # Contains the formatted PR display with confirmation prompt
                data={
                    "clean_output": pr_description.title,  # For CLEAN mode
                    "pr_description": {
                        "title": pr_description.title,
                        "summary": pr_description.summary,
                        "changes": pr_description.changes,
                        "test_plan": pr_description.test_plan,
                        "related_issues": pr_description.related_issues,
                    },
                    "commits_analyzed": len(commits),
                    "input_tokens": token_usage.get("input_tokens", 0),
                    "output_tokens": token_usage.get("output_tokens", 0),
                    "thinking_mode": True,  # Enable thinking mode display path
                    "requires_pr_confirmation": True,  # Trigger confirmation workflow
                    "provider": context.llm_provider.model_info if context.llm_provider else "LLM",
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"PR generation failed: {str(e)}"
            )

    async def execute_confirmed_pr(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute the actual PR creation after user confirmation"""
        try:
            # Try to get the PR data from file-based storage first, then fallback to static variables
            pending_data = self._load_pending_pr()
            if pending_data:
                confirmation_data = pending_data
            else:
                confirmation_data = GitPRFunction._global_pending_pr_data

            if not confirmation_data:
                return ExecutionResult(
                    success=False,
                    message="No pending PR data found. Please run 'aii pr' again.",
                )

            # Create PR via GitHub CLI
            github_client = GitHubClient()

            try:
                pr_url = github_client.create_pr(
                    title=confirmation_data["title"],
                    body=confirmation_data["body"],
                    base_branch=confirmation_data.get("base_branch"),
                    draft=confirmation_data.get("draft", False),
                )
            except Exception as e:
                return ExecutionResult(
                    success=False, message=f"Failed to create PR: {str(e)}"
                )

            # Clear the pending PR data from both storage methods
            GitPRFunction._global_pending_pr_data = None
            self._clear_pending_pr()

            return ExecutionResult(
                success=True,
                message=f"✅ Pull request created: {pr_url}",
                data={
                    "clean_output": pr_url,
                    "pr_url": pr_url,
                    "commits_analyzed": confirmation_data.get("commits_analyzed", 0),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"PR creation failed: {str(e)}"
            )


class GitBranchFunction(FunctionPlugin):
    """Generate conventional branch names from descriptions and create branch"""

    # Class-level state to persist between function calls (confirmation workflow)
    _global_pending_branch_name = None

    @staticmethod
    def _get_pending_branch_file():
        """Get the path to the temporary file storing pending branch data"""
        return os.path.join(tempfile.gettempdir(), "aii_pending_branch.json")

    @staticmethod
    def _save_pending_branch(branch_data):
        """Save pending branch data to temporary file"""
        try:
            with open(GitBranchFunction._get_pending_branch_file(), "w") as f:
                json.dump(branch_data, f)
        except Exception:
            pass

    @staticmethod
    def _load_pending_branch():
        """Load pending branch data from temporary file"""
        try:
            file_path = GitBranchFunction._get_pending_branch_file()
            if os.path.exists(file_path):
                with open(file_path) as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    @staticmethod
    def _clear_pending_branch():
        """Clear pending branch data from temporary file"""
        try:
            file_path = GitBranchFunction._get_pending_branch_file()
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

    @property
    def name(self) -> str:
        return "git_branch"

    @property
    def description(self) -> str:
        return "Create a new git branch with a conventional name generated from a description"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.GIT

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "description": ParameterSchema(
                name="description",
                type="string",
                required=True,
                description="Description of what the branch is for",
            ),
            "prefix": ParameterSchema(
                name="prefix",
                type="string",
                required=False,
                description="Force a specific prefix (feature, bugfix, docs, etc.)",
            ),
            "auto_confirm": ParameterSchema(
                name="auto_confirm",
                type="boolean",
                required=False,
                default=False,
                description="Skip confirmation and create branch immediately",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        # We handle our own custom confirmation workflow with branch name preview
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        # Still risky, but we manage confirmation ourselves
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        """Default output mode: just show the branch name"""
        return OutputMode.CLEAN

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Supports CLEAN and STANDARD output modes"""
        return [OutputMode.CLEAN, OutputMode.STANDARD]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check if git is available and we're in a git repository"""
        try:
            # Check if git is available
            result = subprocess.run(
                ["git", "--version"], capture_output=True, text=True
            )
            if result.returncode != 0:
                return ValidationResult(
                    valid=False,
                    errors=["Git is not installed or not available in PATH"],
                )

            # Check if we're in a git repository
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"], capture_output=True, text=True
            )
            if result.returncode != 0:
                return ValidationResult(valid=False, errors=["Not in a git repository"])

            return ValidationResult(valid=True)

        except Exception as e:
            return ValidationResult(
                valid=False, errors=[f"Failed to validate git prerequisites: {str(e)}"]
            )

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute branch name generation"""
        try:
            # Check if this is a confirmed execution
            pending_data = self._load_pending_branch()
            if pending_data or GitBranchFunction._global_pending_branch_name:
                return await self.execute_confirmed_branch(parameters, context)

            description = parameters["description"]
            forced_prefix = parameters.get("prefix")

            # Load config for prefixes
            config = BranchNameConfig(
                prefixes={
                    "feature": "feature",
                    "bugfix": "bugfix",
                    "docs": "docs",
                    "refactor": "refactor",
                    "chore": "chore",
                    "hotfix": "hotfix",
                    "test": "test",
                }
            )

            # Generate branch name
            branch_namer = BranchNamer(config)
            if forced_prefix:
                # Override type detection with forced prefix
                branch_name = branch_namer.generate_branch_name(
                    description, forced_type=forced_prefix
                )
            else:
                branch_name = branch_namer.generate_branch_name(description)

            # Check if branch exists
            if branch_namer.check_branch_exists(branch_name):
                return ExecutionResult(
                    success=False, message=f"Branch '{branch_name}' already exists"
                )

            # Display for confirmation
            display_text = f"Generated branch name: {branch_name}\n\nCreate and switch to this branch? (y/n): "

            # Store confirmation data
            confirmation_data = {"branch_name": branch_name}

            # Save to both file-based storage and static variables for redundancy
            GitBranchFunction._global_pending_branch_name = branch_name
            self._save_pending_branch(confirmation_data)

            return ExecutionResult(
                success=True,
                message=display_text,
                data={
                    "clean_output": branch_name,
                    "branch_name": branch_name,
                    "requires_branch_confirmation": True,
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Branch name generation failed: {str(e)}"
            )

    async def execute_confirmed_branch(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute the actual branch creation after user confirmation"""
        try:
            # Try to get the branch data from file-based storage first, then fallback to static variables
            pending_data = self._load_pending_branch()
            if pending_data:
                branch_name = pending_data.get("branch_name")
            else:
                branch_name = GitBranchFunction._global_pending_branch_name

            if not branch_name:
                return ExecutionResult(
                    success=False,
                    message="No pending branch name found. Please run 'aii branch' again.",
                )

            # Create and switch to branch
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                # Clear pending data even on failure
                GitBranchFunction._global_pending_branch_name = None
                self._clear_pending_branch()

                return ExecutionResult(
                    success=False, message=f"Failed to create branch: {result.stderr}"
                )

            # Clear the pending branch data from both storage methods
            GitBranchFunction._global_pending_branch_name = None
            self._clear_pending_branch()

            return ExecutionResult(
                success=True,
                message=f"✅ Switched to new branch '{branch_name}'",
                data={"clean_output": branch_name, "branch_name": branch_name},
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Branch creation failed: {str(e)}"
            )
