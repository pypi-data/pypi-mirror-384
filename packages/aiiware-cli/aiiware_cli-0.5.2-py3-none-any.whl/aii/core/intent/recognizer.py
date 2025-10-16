"""Intent Recognizer - Analyze user input and determine intended action"""

import json
import os
from typing import Any

from ..context.models import ChatContext
from ..models import FunctionSafety, RecognitionResult, RouteSource
from .models import BUILT_IN_INTENTS, IntentTemplate

# LLMOrchestrator imported dynamically when needed to avoid circular imports

# Debug mode flag (set via environment variable)
DEBUG_MODE = os.getenv("AII_DEBUG", "").lower() in ("1", "true", "yes")


class IntentRecognizer:
    """LLM-powered intent classification engine"""

    def __init__(self, llm_provider: Any | None = None):
        """Initialize with LLM provider"""
        self.llm_provider = llm_provider
        self.intent_templates = BUILT_IN_INTENTS.copy()
        self.function_registry: Any | None = None  # Will be injected
        self.recognition_cache: dict[str, RecognitionResult] = {}

    def register_function_registry(self, registry: Any) -> None:
        """Register function registry for dynamic function discovery"""
        self.function_registry = registry

    def add_intent_template(self, template: IntentTemplate) -> None:
        """Add custom intent template"""
        self.intent_templates.append(template)

    async def recognize_intent(
        self, user_input: str, context: ChatContext | None = None
    ) -> RecognitionResult:
        """Analyze user input and return recognized intent with confidence"""
        if not user_input or not user_input.strip():
            return RecognitionResult(
                intent="invalid_input",
                confidence=0.0,
                parameters={},
                function_name="help",
                requires_confirmation=False,
                reasoning="Empty input provided",
                source=RouteSource.DIRECT_MATCH,
            )

        user_input = user_input.strip()

        # DIRECT MATCH: Git PR keywords (before LLM to avoid misclassification)
        pr_keywords = ["pull request", "create pr", "github pr", "make pr", "pr create", "create pull request"]
        if any(keyword in user_input.lower() for keyword in pr_keywords) or user_input.lower() in ["pr", "pullrequest"]:
            return RecognitionResult(
                intent="git_pr",
                confidence=0.95,
                parameters={},
                function_name="git_pr",
                requires_confirmation=False,  # Function handles its own confirmation with PR preview
                reasoning="Direct match for pull request creation keywords",
                source=RouteSource.DIRECT_MATCH,
            )

        # DIRECT MATCH: Git branch keywords
        user_lower = user_input.lower()

        # Check for "branch <description>" pattern (simple case)
        if user_lower.startswith("branch "):
            description = user_input[7:].strip()  # Remove "branch " prefix
            if description:
                return RecognitionResult(
                    intent="git_branch",
                    confidence=0.95,
                    parameters={"description": description},
                    function_name="git_branch",
                    requires_confirmation=False,  # Function handles its own confirmation with branch name preview
                    reasoning="Direct match for 'branch <description>' pattern",
                    source=RouteSource.DIRECT_MATCH,
                )

        # Check for longer branch keywords
        branch_keywords = ["create branch", "new branch", "make branch", "branch create"]
        if any(keyword in user_lower for keyword in branch_keywords):
            # Extract description from input
            for keyword in branch_keywords:
                if keyword in user_lower:
                    description = user_input.lower().replace(keyword, "").strip()
                    if description:
                        return RecognitionResult(
                            intent="git_branch",
                            confidence=0.90,
                            parameters={"description": description},
                            function_name="git_branch",
                            requires_confirmation=False,  # Function handles its own confirmation with branch name preview
                            reasoning="Direct match for branch creation keywords",
                            source=RouteSource.DIRECT_MATCH,
                        )

        # LLM-First Approach: Try LLM recognition first for better flexibility
        llm_result = None
        if self.llm_provider:
            try:
                llm_result = await self._llm_recognition(user_input, context)

                import os
                if os.getenv("AII_DEBUG") and llm_result:
                    tokens = llm_result.intent_recognition_tokens or {}
                    print(f"🔍 DEBUG: LLM recognition result - function={llm_result.function_name}, confidence={llm_result.confidence}, tokens={tokens}")

                # Accept LLM results with moderate confidence
                if llm_result and llm_result.confidence >= 0.7:
                    # Apply smart confirmation logic to direct LLM results
                    needs_confirmation, confirmation_reason = (
                        self.should_confirm_function(
                            llm_result.function_name,
                            llm_result.confidence,
                            llm_result.parameters,
                        )
                    )

                    result = RecognitionResult(
                        intent=llm_result.intent,
                        confidence=llm_result.confidence,
                        parameters=llm_result.parameters,
                        function_name=llm_result.function_name,
                        requires_confirmation=needs_confirmation,
                        reasoning=f"{llm_result.reasoning}. Confirmation: {confirmation_reason}",
                        source=llm_result.source,
                    )
                    # v0.4.13: Preserve token usage from LLM recognition
                    result.intent_recognition_tokens = llm_result.intent_recognition_tokens
                    return result
            except Exception as e:
                print(f"LLM recognition failed: {e}")

        # Check if this should use universal orchestrator for content generation
        if self.llm_provider and self._is_universal_content_request(user_input):
            universal_result = await self._route_to_universal_orchestrator(
                user_input, context
            )
            if universal_result:
                return universal_result

        # Fallback to direct pattern matching for validation/enhancement
        direct_result = self._try_direct_pattern_match(user_input)
        if direct_result:
            # If we have both LLM and pattern results, enhance with pattern validation
            if llm_result:
                return self._enhance_with_patterns(llm_result, direct_result)
            # Use direct result if confidence is high enough
            elif direct_result.confidence >= 0.8:
                return direct_result

        # Last resort - suggest help or clarification
        return RecognitionResult(
            intent="clarification_needed",
            confidence=0.2,
            parameters={"original_input": user_input},
            function_name="clarify",
            requires_confirmation=True,
            reasoning="Could not determine intent from input",
            source=RouteSource.FALLBACK,
        )

    def _try_direct_pattern_match(self, user_input: str) -> RecognitionResult | None:
        """Try to match input against direct patterns"""
        best_match = None
        best_score = 0.0

        for template in self.intent_templates:
            score = 0.0

            # Check pattern match
            if template.matches_pattern(user_input):
                score += 0.6  # Base score for pattern match

            # Check keyword presence
            keyword_count = template.has_keywords(user_input)
            if keyword_count > 0:
                keyword_score = min(0.3, keyword_count * 0.1)  # Up to 0.3 for keywords
                score += keyword_score

            # Add template-specific confidence boost
            score += template.confidence_boost

            # Ensure score doesn't exceed 1.0
            score = min(1.0, score)

            if (
                score > best_score and score >= 0.3
            ):  # Lowered threshold - let LLM handle more cases
                best_score = score
                best_match = template

        if best_match:
            # Extract parameters based on the matched template
            parameters = self._extract_parameters(user_input, best_match)

            return RecognitionResult(
                intent=best_match.intent_name,
                confidence=best_score,
                parameters=parameters,
                function_name=best_match.function_name,
                requires_confirmation=best_score < 0.8,
                reasoning=f"Matched pattern for {best_match.intent_name}",
                source=RouteSource.DIRECT_MATCH,
            )

        return None

    async def _llm_recognition(
        self, user_input: str, context: ChatContext | None = None
    ) -> RecognitionResult | None:
        """Use LLM for intent recognition"""
        if not self.llm_provider:
            return None

        try:
            prompt = self._build_recognition_prompt(user_input, context)

            # Use complete_with_usage to track token consumption
            if hasattr(self.llm_provider, "complete_with_usage"):
                llm_response = await self.llm_provider.complete_with_usage(prompt)
                response = llm_response.content
                usage = llm_response.usage or {}
            else:
                response = await self.llm_provider.complete(prompt)
                usage = {}

            result = self._parse_llm_response(response, user_input, context)

            # Add token usage to the result if available
            if result and usage:
                result.intent_recognition_tokens = {
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "reasoning_tokens": usage.get("reasoning_tokens", 0)
                }

            return result
        except Exception as e:
            print(f"LLM recognition failed: {e}")
            return None

    def _get_current_date_context(self) -> str:
        """Get current date context for prompt (v0.4.10)."""
        from datetime import datetime

        now = datetime.now()
        return now.strftime("%Y-%m-%d (%B %d, %Y)")

    def _get_tomorrow_date(self) -> str:
        """Get tomorrow's date (v0.4.10)."""
        from datetime import datetime, timedelta

        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.strftime("%Y-%m-%d")

    def _interpret_date_example(self, month_day: str) -> str:
        """
        Generate date interpretation example for prompt (v0.4.10).

        Args:
            month_day: Date in MM-DD format (e.g., "10-12")

        Returns:
            Interpreted date with year (e.g., "2025-10-12" or "2026-10-12")
        """
        from datetime import datetime

        now = datetime.now()
        month, day = map(int, month_day.split("-"))

        # Create date with current year
        try:
            candidate_date = datetime(now.year, month, day)
        except ValueError:
            # Invalid date (like Feb 30)
            return f"{now.year}-{month:02d}-{day:02d}"

        # If date is in the past, use next year
        if candidate_date.date() < now.date():
            return f"{now.year + 1}-{month:02d}-{day:02d}"
        else:
            return f"{now.year}-{month:02d}-{day:02d}"

    def _build_recognition_prompt(
        self, user_input: str, context: ChatContext | None = None
    ) -> str:
        """Build prompt for LLM intent recognition"""
        # Get available functions
        available_functions = self._get_function_descriptions()

        # Build context summary with location awareness
        context_summary = ""
        if context and context.messages:
            recent_messages = context.get_recent_messages(5)
            context_lines = []
            for msg in recent_messages[-3:]:  # Last 3 messages for context
                role = msg.role
                content = (
                    msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                )
                context_lines.append(f"{role}: {content}")

                # Extract location patterns from previous commands/responses
                if "Downloads" in content or "~/Downloads" in content:
                    context_lines.append(
                        "LOCATION_CONTEXT: Previous operation involved ~/Downloads"
                    )
                elif "Documents" in content or "~/Documents" in content:
                    context_lines.append(
                        "LOCATION_CONTEXT: Previous operation involved ~/Documents"
                    )
                elif "Desktop" in content or "~/Desktop" in content:
                    context_lines.append(
                        "LOCATION_CONTEXT: Previous operation involved ~/Desktop"
                    )

            context_summary = "\\n".join(context_lines)

        prompt = f"""You are an intent classifier for the "aii" CLI application. Analyze the user input and determine the most likely intended action.

Available Functions:
{available_functions}

{"Recent Chat Context:" + chr(10) + context_summary + chr(10) if context_summary else ""}
User Input: "{user_input}"

🗓️ CRITICAL DATE INTERPRETATION RULE (v0.4.10):
Current date: {self._get_current_date_context()}

When users specify dates WITHOUT year (e.g., "10月12日", "October 12", "12号"), ALWAYS assume:
- If date is in FUTURE of current month/year → use CURRENT YEAR
- If date is in PAST (earlier than today) → use NEXT YEAR (next occurrence)

Date Interpretation Examples (today is {self._get_current_date_context()}):
- "10月12日" (Oct 12) → {self._interpret_date_example("10-12")}
- "10月5日" (Oct 5) → {self._interpret_date_example("10-05")}
- "1月15日" (Jan 15) → {self._interpret_date_example("01-15")}
- "12月25日" (Dec 25) → {self._interpret_date_example("12-25")}
- "明天" (tomorrow) → {self._get_tomorrow_date()}
- "下周一" (next Monday) → Calculate based on current date

🎯 CRITICAL: If resulting date is in the PAST, ADD 1 YEAR to get next occurrence.

Examples with context (today is {self._get_current_date_context()}):
✅ CORRECT: "10月5日" → {self._interpret_date_example("10-05")} (next occurrence)
❌ WRONG: "10月5日" → 2024-10-05 (would be in the past!)

CRITICAL GIT OPERATIONS RULE: If the user mentions "pr", "pull request", "create pr", or "github pr", they want to use the git_pr function to create a GitHub pull request, NOT shell_command or content_generate.

If the user mentions "branch", "create branch", "new branch", they want to use the git_branch function to create a git branch with a conventional name, NOT shell_command.

CRITICAL MCP/RAILWAY OPERATIONS RULE - HIGHEST PRIORITY:
If the user query contains ANY of these Chinese railway keywords: "火车票", "高铁", "动车", "余票", "12306", "车站", "列车", "查询火车", "查询车票", "北京", "上海", "车次" combined with train/ticket context, you MUST use the mcp_tool function to query the 12306-mcp server.
DO NOT use research, web_search, universal_generate, or any other function for Chinese railway ticket queries.
The mcp_tool function has direct access to real-time 12306 railway data through MCP servers.

CRITICAL GITHUB OPERATIONS RULE - HIGHEST PRIORITY:
If the user query contains ANY mention of GitHub operations including:
- Repository search: "search github", "find github repos", "search for repos", "popular repos", "search repositories", "find repositories"
- Repository listing: "list my repos", "my repositories", "my github repos"
- Repository creation/forking: "create github repo", "fork repository"
- Issues/PRs: "github issues", "create github issue", "pull requests"
- Code search: "search github code", "find code on github"
- ANY combination of "github" + "search/find/list/create"

You MUST use the mcp_tool function, NOT research or web_search.
The mcp_tool has direct GitHub API access through MCP servers.
The research function is ONLY for web articles/news/documentation, NOT for GitHub repository operations.

Examples that should use mcp_tool:
- "search github for popular python ML repos" → mcp_tool (GitHub repository search)
- "find popular ML repositories" → mcp_tool (GitHub repository search)
- "search for python repos on github" → mcp_tool (GitHub repository search)
- "list my github repositories" → mcp_tool (GitHub API call)
- "search github code for function definition" → mcp_tool (GitHub code search)

Examples that should use research:
- "research machine learning trends" → research (web articles/news)
- "find articles about Python ML" → research (web content, not GitHub repos)

🔍 CRITICAL MCP INTROSPECTION RULE (v0.4.10) - ABSOLUTE PRIORITY:
When user asks about MCP server capabilities, tools, or operations, ALWAYS use mcp_tool, NEVER web_search.

MCP Introspection queries (USE mcp_tool):
- "what tools are available in [server]?" → mcp_tool (list_tools for server)
- "list tools in github mcp" → mcp_tool (NOT web_search!)
- "what can [server] do?" → mcp_tool (server capabilities)
- "show me github server capabilities" → mcp_tool (NOT web_search!)
- "capabilities of [server]" → mcp_tool (introspection)
- ANY query mentioning MCP server by name + "tools/capabilities/features" → mcp_tool

Conceptual queries (USE web_search):
- "what is github?" → web_search (concept explanation, not MCP introspection)
- "what is MCP?" → web_search (general information)

🎯 KEY DISTINCTION:
- MCP server operations/capabilities → mcp_tool (introspection via MCP protocol)
- Concept/definition/general info → web_search or research

Other MCP operations:
- Filesystem: "read file", "list directory", "write file" (when mentioning specific file paths, use mcp_tool with filesystem server)

CRITICAL CONTEXT RULE: If the user says "second largest", "now check", "next one", etc., and the recent context shows a previous command used a specific directory (~/Downloads, ~/Documents, etc.), you MUST use that same directory as the path parameter.

For example:
- If previous context shows "find ~/Downloads" or "Downloads" directory
- And user says "now check the second largest"
- You MUST set path parameter to "~/Downloads"

Look for these location patterns in the context:
- ~/Downloads, ~/Documents, ~/Desktop
- Any path that starts with ~/ or /
- Any mention of Downloads, Documents, Desktop folders

🎯 CRITICAL FUNCTION DISAMBIGUATION RULE (v0.4.13) - EXPLAIN FUNCTIONS:

**explain_command** (shell commands):
- User wants to explain a SHELL COMMAND
- Command syntax present: flags (--, -), pipes (|), redirection (>, >>)
- Shell commands: rm, find, grep, chmod, dd, ls, cd, mv, cp, git, curl, wget, etc.
- Patterns: "explain [command]", "what does [command] do", "analyze this command"
- Keywords: explain + (shell/bash/command/terminal) OR command syntax present
- Examples:
  ✅ "explain rm -rf /" → explain_command
  ✅ "what does find . -name '*.py' do" → explain_command
  ✅ "analyze this command: ls -la" → explain_command
  ✅ "describe the shell command chmod 777" → explain_command
  ✅ "explain git status" → explain_command

**explain** (concepts):
- User asks about CONCEPT, IDEA, or TOPIC
- NO command syntax present
- General knowledge questions
- Examples:
  ✅ "explain machine learning" → explain
  ✅ "what is kubernetes" → explain
  ✅ "describe how DNS works" → explain
  ✅ "explain the concept of recursion" → explain

🚨 CRITICAL: If input contains shell command syntax (flags, pipes, shell commands) → USE explain_command
Shell syntax indicators:
- Flags: --, -, flags like -la, -rf, --help
- Pipes: |
- Redirection: >, >>, <
- Shell commands: rm, find, grep, chmod, dd, mkfs, ls, cd, mv, cp, cat, git, curl, wget, etc.

If BOTH "explain" keyword AND shell syntax present → ALWAYS use explain_command (NOT explain)

Analyze the input and respond with JSON only:
{{
  "intent": "function_name",
  "confidence": 0.95,
  "parameters": {{"key": "value", "path": "contextual_path_if_applicable"}},
  "reasoning": "Why this function was selected and any contextual information used"
}}

Rules:
1. Confidence > 0.8 for direct execution
2. Confidence 0.5-0.8 requires user confirmation
3. Confidence < 0.5 requires clarification
4. Extract relevant parameters from the input
5. For contextual requests like "second largest", "now check", etc.:
   - Set search_request to a descriptive version like "find second largest file"
   - If LOCATION_CONTEXT shows a previous location, use that as the path parameter
   - Always include required parameters even if they need to be inferred from context
5. Consider the chat context when determining intent
6. Respond with valid JSON only, no additional text"""

        return prompt

    def _parse_llm_response(
        self, response: str, user_input: str, context: ChatContext | None = None
    ) -> RecognitionResult | None:
        """Parse LLM response into RecognitionResult"""
        try:
            # Clean response - sometimes LLMs add extra text
            response = response.strip()

            # Find JSON in response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                return None

            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)

            # Debug: Print what LLM generated for troubleshooting
            if "path" in data.get("parameters", {}):
                # LLM parameter mapping with path
                pass
            else:
                # LLM parameter mapping completed
                pass

            # Validate required fields
            if not all(key in data for key in ["intent", "confidence", "parameters"]):
                return None

            confidence = float(data["confidence"])
            confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1 range

            # BULLETPROOF CONTEXT EXTRACTION - Override LLM with deterministic logic
            parameters = data.get("parameters", {})
            if data.get("intent") == "find_files":
                if DEBUG_MODE: print("🔍 DEBUG: Applying bulletproof fix for find_files intent")
                parameters = self._force_contextual_parameters(
                    parameters, user_input, context
                )
            elif data.get("intent") == "shell_command":
                # Normalize shell_command parameters - LLM might return 'command' but function expects 'request'
                if "command" in parameters and "request" not in parameters:
                    parameters["request"] = parameters.pop("command")
                elif "request" not in parameters:
                    # Fallback: use the original user input
                    parameters["request"] = user_input.strip()

                # For shell_command, default execute to True (with confirmation) unless explicitly set
                if "execute" not in parameters:
                    parameters["execute"] = True

                if DEBUG_MODE: print(f"🔍 DEBUG: Normalized shell_command parameters: {parameters}")

            # Fix parameter mapping for content generation
            if data.get("intent") == "content_generate":
                # If LLM didn't provide specification, create it from the original input
                if "specification" not in parameters:
                    parameters["specification"] = user_input
                # Map common LLM parameter names
                if "type" in parameters and "content_type" not in parameters:
                    parameters["content_type"] = parameters.pop("type")

                # Map content type variations to supported types
                if "content_type" in parameters:
                    content_type = str(parameters["content_type"]).lower()
                    content_type_mapping = {
                        # Direct mappings
                        "thank_you_note": "note",
                        "thanks": "note",
                        "note": "note",
                        "letter": "document",
                        "post": "message",
                        "tweet": "message",
                        "email": "email",
                        # Style/format mappings to content types
                        "technical": "document",
                        "professional": "document",
                        "casual": "text",
                        "formal": "document",
                        "business": "document",
                        "academic": "document",
                        "summary": "document",
                        "guide": "document",
                        "tutorial": "document",
                        "explanation": "text",
                        "overview": "document",
                    }

                    # Try direct mapping first
                    if content_type in content_type_mapping:
                        parameters["content_type"] = content_type_mapping[content_type]
                    else:
                        # Fallback to "auto" for any unrecognized content type
                        parameters["content_type"] = "auto"

                # Handle format parameter mapping
                if "format" in parameters:
                    format_val = str(parameters["format"]).lower()
                    format_mapping = {
                        "list": "structured",
                        "bullet": "structured",
                        "points": "structured",
                        "markdown": "markdown",
                        "md": "markdown",
                        "plain": "plain",
                        "text": "plain",
                    }
                    if format_val in format_mapping:
                        parameters["format"] = format_mapping[format_val]
                    else:
                        parameters["format"] = "auto"

                # Clean up any unrecognized parameters that might cause validation errors
                # Keep only parameters that content_generate function recognizes
                recognized_params = {
                    "content_type",
                    "specification",
                    "start_date",
                    "duration",
                    "format",
                }
                cleaned_parameters = {}

                for key, value in parameters.items():
                    if key in recognized_params:
                        cleaned_parameters[key] = value
                    else:
                        # Map common alternative parameter names
                        if key in ["topic", "subject", "theme"]:
                            if "specification" not in cleaned_parameters:
                                cleaned_parameters["specification"] = str(value)
                        elif key in ["style", "tone", "mode"]:
                            # Style/tone can affect format choice
                            if "format" not in cleaned_parameters:
                                if str(value).lower() in [
                                    "structured",
                                    "list",
                                    "points",
                                ]:
                                    cleaned_parameters["format"] = "structured"
                                else:
                                    cleaned_parameters["format"] = "auto"

                parameters = cleaned_parameters

            # Enhanced parameter mapping for code generation
            if data.get("intent") == "code_generate":
                parameters = self._enhance_code_generate_parameters(parameters, user_input)

            # Enhanced parameter mapping for code review
            if data.get("intent") == "code_review":
                parameters = self._enhance_code_review_parameters(parameters, user_input)

            # Enhanced parameter mapping for explain function
            if data.get("intent") == "explain":
                parameters = self._enhance_explain_parameters(parameters, user_input)

            # Enhanced parameter mapping for email generation
            if data.get("intent") == "generate_email":
                parameters = self._enhance_email_generate_parameters(parameters, user_input)

            # Enhanced parameter mapping for git diff
            if data.get("intent") == "git_diff":
                parameters = self._enhance_git_diff_parameters(parameters, user_input)

            # Enhanced parameter mapping for summarize
            if data.get("intent") == "summarize":
                parameters = self._enhance_summarize_parameters(parameters, user_input)

            # Enhanced parameter mapping for translate
            if data.get("intent") == "translate":
                parameters = self._enhance_translate_parameters(parameters, user_input)

            # Enhanced parameter mapping for research
            if data.get("intent") == "research":
                parameters = self._enhance_research_parameters(parameters, user_input)

            # Enhanced parameter mapping for MCP tool
            if data.get("intent") == "mcp_tool":
                parameters = self._enhance_mcp_tool_parameters(parameters, user_input)

            return RecognitionResult(
                intent=data["intent"],
                confidence=confidence,
                parameters=parameters,
                function_name=data.get(
                    "intent"
                ),  # Use intent as function name by default
                requires_confirmation=confidence < 0.8,
                reasoning=data.get("reasoning", "LLM classification"),
                source=RouteSource.LLM_RECOGNITION,
            )

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Failed to parse LLM response: {e}")
            return None

    def _enhance_explain_parameters(self, parameters: dict, user_input: str) -> dict:
        """Enhanced parameter mapping for explain function with constraint intelligence"""
        import re

        # 1. WORD LIMIT DETECTION
        word_limit_patterns = [
            r"within (\d+) words?",
            r"in (\d+) words? or less",
            r"no more than (\d+) words?",
            r"(\d+) words? max",
            r"(\d+)-word explanation",
            r"limit to (\d+) words?",
            r"under (\d+) words?",
            r"maximum (\d+) words?",
        ]

        for pattern in word_limit_patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                word_count = int(match.group(1))
                parameters["max_words"] = word_count

                # Auto-adjust brevity based on word count
                if word_count <= 25:
                    parameters["brevity"] = "brief"
                elif word_count <= 75:
                    parameters["brevity"] = "concise"
                elif word_count <= 150:
                    parameters["brevity"] = "standard"
                else:
                    parameters["brevity"] = "detailed"
                break

        # 2. BREVITY INDICATORS (order matters - most specific first)
        brevity_patterns = [
            (r"\b(brief|briefly|short|shortly|quick|quickly)\b", "brief"),
            (r"\b(concise|concisely|succinct|terse)\b", "concise"),
            (r"\b(extensive|exhaustive|comprehensive|complete|full)\b", "comprehensive"),
            (r"\b(detailed|thorough|in-depth)\b", "detailed"),
        ]

        for pattern, brevity_level in brevity_patterns:
            if re.search(pattern, user_input.lower()):
                if "brevity" not in parameters:
                    parameters["brevity"] = brevity_level
                break

        # 3. FORMAT CONSTRAINTS
        format_patterns = {
            r"\b(bullet points?|list|bulleted|points)\b": "bullet_points",
            r"\b(one sentence|single sentence|definition only)\b": "definition",
            r"\b(summary|summarize)\b": "summary",
            r"\b(paragraph|prose)\b": "paragraph",
        }

        for pattern, format_style in format_patterns.items():
            if re.search(pattern, user_input.lower()):
                parameters["format_style"] = format_style
                break

        # 4. SPECIAL CONSTRAINTS
        constraint_indicators = [
            r"(no|without) (technical jargon|jargon|technical terms)",
            r"(simple language|plain english|easy to understand)",
            r"(one sentence|single sentence)",
            r"(definition only|just the definition)",
            r"(without examples|no examples)",
        ]

        constraints = []
        for pattern in constraint_indicators:
            if re.search(pattern, user_input.lower()):
                constraints.append(re.search(pattern, user_input.lower()).group())

        if constraints:
            parameters["constraints"] = "; ".join(constraints)

        # 5. HANDLE EXAMPLES BASED ON CONSTRAINTS
        if re.search(r"\b(without examples|no examples|skip examples)\b", user_input.lower()):
            parameters["include_examples"] = False

        if DEBUG_MODE: print(f"🔍 DEBUG: Enhanced explain parameters: {parameters}")
        return parameters

    def _enhance_code_generate_parameters(self, parameters: dict, user_input: str) -> dict:
        """Enhanced parameter mapping for code_generate function with language detection"""
        import re

        # If LLM didn't provide specification, create it from the original input
        if "specification" not in parameters:
            # Extract the core request without language indicators
            spec_patterns = [
                r"write me an? (\w+) implementation (?:for|of) (.+)",  # "write me a Golang implementation for X"
                r"(?:create|write|implement|generate) (?:a )?(.+) in (\w+)",  # "create X in Python"
                r"(?:create|write|implement|generate) (?:a )?(\w+) (.+)",  # "create Python script"
                r"(?:create|write|implement|generate) (.+)",  # "create edit distance algorithm"
            ]

            specification = user_input
            detected_language = None

            for pattern in spec_patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    if len(groups) == 2:
                        # Pattern with language and specification
                        lang_candidate, spec_candidate = groups
                        if self._is_programming_language(lang_candidate):
                            detected_language = lang_candidate.lower()
                            specification = spec_candidate
                        elif self._is_programming_language(spec_candidate):
                            detected_language = spec_candidate.lower()
                            specification = lang_candidate
                        else:
                            specification = f"{lang_candidate} {spec_candidate}"
                    else:
                        specification = groups[0]
                    break

            parameters["specification"] = specification

            # Set detected language if found
            if detected_language and "language" not in parameters:
                # Map common language names to standard ones
                language_mapping = {
                    "golang": "go",
                    "go": "go",
                    "python": "python",
                    "py": "python",
                    "javascript": "javascript",
                    "js": "javascript",
                    "typescript": "typescript",
                    "ts": "typescript",
                    "java": "java",
                    "c++": "cpp",
                    "cpp": "cpp",
                    "rust": "rust",
                    "rs": "rust",
                }
                parameters["language"] = language_mapping.get(detected_language, detected_language)

        # Language detection from input if not already set
        if "language" not in parameters or parameters.get("language") in [None, "", "auto"]:
            language_patterns = [
                (r"\b(golang|go)\b", "go"),
                (r"\b(python|py)\b", "python"),
                (r"\b(javascript|js)\b", "javascript"),
                (r"\b(typescript|ts)\b", "typescript"),
                (r"\b(java)\b", "java"),
                (r"\b(c\+\+|cpp)\b", "cpp"),
                (r"\b(rust|rs)\b", "rust"),
            ]

            for pattern, lang in language_patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    parameters["language"] = lang
                    break

            # Default to auto if still not detected
            if "language" not in parameters:
                parameters["language"] = "auto"

        # Ensure language is a valid choice
        valid_languages = ["python", "javascript", "typescript", "java", "cpp", "go", "rust", "text", "auto"]
        if parameters.get("language") not in valid_languages:
            parameters["language"] = "auto"

        if DEBUG_MODE: print(f"🔍 DEBUG: Enhanced code_generate parameters: {parameters}")
        return parameters

    def _is_programming_language(self, text: str) -> bool:
        """Check if text is a programming language name"""
        languages = ["golang", "go", "python", "py", "javascript", "js", "typescript", "ts",
                    "java", "c++", "cpp", "rust", "rs"]
        return text.lower() in languages

    def _enhance_code_review_parameters(self, parameters: dict, user_input: str) -> dict:
        """Enhanced parameter mapping for code_review function with path extraction"""
        import re

        # If LLM didn't provide file_path, extract it from user input
        if "file_path" not in parameters:
            # Common patterns for code review requests
            path_patterns = [
                r"analyze (?:the )?code in (?:the )?(?:folder|directory) (.+)",
                r"review (?:the )?code in (?:the )?(?:folder|directory) (.+)",
                r"analyze (?:the )?(?:folder|directory) (.+)",
                r"review (?:the )?(?:folder|directory) (.+)",
                r"analyze (?:the )?file (.+)",
                r"review (?:the )?file (.+)",
                r"code review (?:for|of) (.+)",
                r"check (?:the )?code in (.+)",
                r"examine (?:the )?code in (.+)",
            ]

            for pattern in path_patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    file_path = match.group(1).strip()
                    # Clean up common artifacts
                    file_path = file_path.replace(" folder", "").replace(" directory", "")
                    file_path = file_path.strip('"\'')
                    parameters["file_path"] = file_path
                    break

            # If still no path found, try to extract any path-like string
            if "file_path" not in parameters:
                # Look for path-like patterns (contains / or specific folder names)
                path_candidates = re.findall(r'[a-zA-Z_][a-zA-Z0-9_/.-]*[a-zA-Z0-9_]', user_input)
                for candidate in path_candidates:
                    if '/' in candidate or any(folder in candidate.lower() for folder in ['core', 'src', 'lib', 'functions', 'utils']):
                        parameters["file_path"] = candidate
                        break

        # Focus area detection
        if "focus" not in parameters:
            focus_patterns = {
                r"\b(security|secure|vulnerability|vulnerabilities)\b": "security",
                r"\b(performance|speed|optimize|optimization|efficient)\b": "performance",
                r"\b(style|format|formatting|convention|conventions)\b": "style",
                r"\b(all|everything|complete|comprehensive|full)\b": "all",
            }

            for pattern, focus_value in focus_patterns.items():
                if re.search(pattern, user_input, re.IGNORECASE):
                    parameters["focus"] = focus_value
                    break

            # Default focus
            if "focus" not in parameters:
                parameters["focus"] = "all"

        if DEBUG_MODE: print(f"🔍 DEBUG: Enhanced code_review parameters: {parameters}")
        return parameters

    def _enhance_email_generate_parameters(self, parameters: dict, user_input: str) -> dict:
        """Enhanced parameter mapping for generate_email function with purpose extraction"""
        import re

        # Extract the purpose from the user input
        # Remove common email generation prefixes to get the core purpose
        purpose_patterns = [
            r"write (?:a |an )?(?:professional )?email (declining|accepting|about|regarding|for|to) (.+)",
            r"generate (?:a |an )?(?:professional )?email (declining|accepting|about|regarding|for|to) (.+)",
            r"create (?:a |an )?(?:professional )?email (declining|accepting|about|regarding|for|to) (.+)",
            r"compose (?:a |an )?(?:professional )?email (declining|accepting|about|regarding|for|to) (.+)",
            r"draft (?:a |an )?(?:professional )?email (declining|accepting|about|regarding|for|to) (.+)",
            r"write (?:a |an )?(?:professional )?email (.+)",
            r"generate (?:a |an )?(?:professional )?email (.+)",
            r"create (?:a |an )?(?:professional )?email (.+)",
        ]

        purpose = user_input  # Default fallback
        for pattern in purpose_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    # Pattern with action and object (e.g., "declining a meeting")
                    action, obj = match.groups()
                    purpose = f"{action} {obj}".strip()
                else:
                    # Simple pattern with just the purpose
                    purpose = match.group(1).strip()
                break

        # Clean up the purpose
        purpose = purpose.strip('"\'.,!?')
        if not purpose:
            purpose = user_input

        parameters["purpose"] = purpose

        # Detect recipient type from context
        recipient_patterns = {
            "client": ["client", "customer"],
            "manager": ["manager", "supervisor", "boss"],
            "team": ["team", "colleagues", "everyone"],
            "external": ["external", "vendor", "partner"],
        }

        recipient_type = "colleague"  # Default
        user_lower = user_input.lower()
        for rec_type, keywords in recipient_patterns.items():
            if any(keyword in user_lower for keyword in keywords):
                recipient_type = rec_type
                break

        parameters["recipient_type"] = recipient_type

        # Detect tone from input
        tone_patterns = {
            "formal": ["formal", "official"],
            "friendly": ["friendly", "casual", "warm"],
            "urgent": ["urgent", "asap", "immediate", "quickly"],
        }

        tone = "professional"  # Default
        for tone_type, keywords in tone_patterns.items():
            if any(keyword in user_lower for keyword in keywords):
                tone = tone_type
                break

        parameters["tone"] = tone

        return parameters

    def _enhance_git_diff_parameters(self, parameters: dict, user_input: str) -> dict:
        """Enhanced parameter mapping for git_diff function with commit detection"""
        import re

        # Detect if user wants to see changes in a specific commit
        commit_patterns = [
            r"(?:what|show)\s+changed\s+in\s+(?:the\s+)?last\s+commit",
            r"(?:what|show)\s+(?:was\s+)?in\s+(?:the\s+)?last\s+commit",
            r"diff\s+(?:of\s+)?(?:the\s+)?last\s+commit",
            r"(?:what|show)\s+changed\s+in\s+(?:the\s+)?(?:latest|recent)\s+commit",
            r"show\s+(?:me\s+)?(?:the\s+)?(?:latest|last|recent)\s+commit",
            r"(?:what|show)\s+changed\s+in\s+HEAD",
            r"git\s+show",
        ]

        user_lower = user_input.lower()
        for pattern in commit_patterns:
            if re.search(pattern, user_lower):
                parameters["commit"] = "HEAD"
                parameters["analyze"] = True  # Auto-enable analysis for commit diffs
                break

        # Detect if user wants staged changes
        if any(keyword in user_lower for keyword in ["staged", "cached", "--cached"]):
            parameters["staged"] = True

        # Detect if user wants to analyze the diff
        if any(keyword in user_lower for keyword in ["analyze", "analysis", "explain", "review"]):
            parameters["analyze"] = True

        return parameters

    def _enhance_summarize_parameters(self, parameters: dict, user_input: str) -> dict:
        """Enhanced parameter mapping for summarize function with content extraction"""
        import re

        # Extract content from various summarize command patterns
        content_patterns = [
            r"summarize\s+this\s+article\s+in\s+\w+:\s*[\"'](.+?)[\"']",
            r"summarize\s+this\s+text\s+in\s+\w+:\s*[\"'](.+?)[\"']",
            r"summarize\s+this\s+in\s+\w+:\s*[\"'](.+?)[\"']",
            r"summarize\s+this\s+article:\s*[\"'](.+?)[\"']",
            r"summarize\s+this\s+text:\s*[\"'](.+?)[\"']",
            r"summarize\s+this:\s*[\"'](.+?)[\"']",
            r"summarize\s+[\"'](.+?)[\"']",
            r"create\s+(?:a\s+)?summary\s+of\s+this:\s*(.+?)(?:\.\s+output|\.\s+write|\.\s+please|\.$|$)",
            r"summarize\s+this\s+article\s+in\s+\w+:\s*(.+)",
            r"summarize\s+this\s+text\s+in\s+\w+:\s*(.+)",
            r"summarize\s+this\s+in\s+\w+:\s*(.+)",
            r"summarize\s+this\s+article:\s*(.+)",
            r"summarize\s+this\s+text:\s*(.+)",
            r"summarize\s+this:\s*(.+)",
            r"summarize\s+(.+)",
        ]

        content = ""
        for pattern in content_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                # Clean up common artifacts
                content = content.strip('"\'')
                # Remove escaped characters that might come from shell
                content = content.replace('\\', '')
                break

        if content:
            parameters["content"] = content

        # Detect language preference
        language_patterns = {
            r"in\s+chinese": "chinese",
            r"in\s+english": "english",
            r"in\s+spanish": "spanish",
            r"in\s+french": "french",
            r"in\s+german": "german",
            r"in\s+japanese": "japanese",
            r"in\s+korean": "korean",
            r"in\s+italian": "italian",
            r"in\s+portuguese": "portuguese",
            r"output.*in\s+chinese\s+language": "chinese",
            r"output.*in\s+english\s+language": "english",
            r"output.*in\s+spanish\s+language": "spanish",
            r"output.*in\s+french\s+language": "french",
            r"write.*in\s+chinese": "chinese",
            r"write.*in\s+english": "english",
            r"用中文": "chinese",
            r"用英文": "english",
        }

        for pattern, language in language_patterns.items():
            if re.search(pattern, user_input.lower()):
                parameters["language"] = language
                break

        # Detect length preferences
        length_patterns = {
            r"(?:brief|short|concise|brief summary)": "brief",
            r"(?:long|detailed|comprehensive|in-depth)": "detailed",
            r"(?:bullet|bullets|bullet points|list)": "bullet_points",
            r"(?:executive|executive summary)": "executive",
        }

        for pattern, length_type in length_patterns.items():
            if re.search(pattern, user_input.lower()):
                if length_type == "bullet_points":
                    parameters["format"] = "bullet_points"
                elif length_type == "executive":
                    parameters["format"] = "executive"
                elif length_type == "brief":
                    parameters["length"] = "brief"
                elif length_type == "detailed":
                    parameters["length"] = "detailed"
                break

        return parameters

    def _enhance_translate_parameters(self, parameters: dict, user_input: str) -> dict:
        """Enhanced parameter mapping for translate function with text and language extraction"""
        import re

        # Extract text to translate from various patterns
        text_patterns = [
            r"translate\s+this\s+to\s+\w+:\s*[\"'](.+?)[\"']",  # translate this to spanish: "text"
            r"translate\s+this\s+to\s+\w+:\s*(.+)$",  # translate this to spanish: text
            r"translate\s+[\"'](.+?)[\"']\s+to\s+\w+",  # translate "text" to spanish
            r"translate\s+(.+?)\s+to\s+\w+",  # translate text to spanish
            r"translate\s+[\"'](.+?)[\"']",  # translate "text"
            r"translate:\s*(.+)$",  # translate: text
            r"translate\s+(.+)$",  # translate text (last resort)
        ]

        text = ""
        for pattern in text_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE | re.DOTALL)
            if match:
                text = match.group(1).strip()
                # Clean up common artifacts
                text = text.strip('"\'')
                # Remove trailing punctuation if it's part of the command
                if text.endswith('.') and len(text) < 50:  # Only remove period from short texts
                    text = text.rstrip('.')
                break

        if text:
            parameters["text"] = text

        # Extract target language
        target_language_patterns = {
            r"to\s+spanish": "spanish",
            r"to\s+french": "french",
            r"to\s+german": "german",
            r"to\s+english": "english",
            r"to\s+chinese": "chinese",
            r"to\s+japanese": "japanese",
            r"to\s+korean": "korean",
            r"to\s+italian": "italian",
            r"to\s+portuguese": "portuguese",
            r"to\s+russian": "russian",
            r"to\s+arabic": "arabic",
            r"in\s+spanish": "spanish",
            r"in\s+french": "french",
            r"in\s+german": "german",
            r"in\s+english": "english",
            r"in\s+chinese": "chinese",
            r"in\s+japanese": "japanese",
            r"in\s+korean": "korean",
        }

        for pattern, language in target_language_patterns.items():
            if re.search(pattern, user_input.lower()):
                parameters["target_language"] = language
                break

        # Extract source language if specified
        source_language_patterns = {
            r"from\s+spanish": "spanish",
            r"from\s+french": "french",
            r"from\s+german": "german",
            r"from\s+english": "english",
            r"from\s+chinese": "chinese",
            r"from\s+japanese": "japanese",
            r"from\s+korean": "korean",
        }

        for pattern, language in source_language_patterns.items():
            if re.search(pattern, user_input.lower()):
                parameters["source_language"] = language
                break

        return parameters

    def _enhance_research_parameters(self, parameters: dict, user_input: str) -> dict:
        """Enhanced parameter mapping for research function with query extraction"""
        import re

        # Extract research query from various patterns
        query_patterns = [
            r"research\s+(?:about\s+|on\s+|the\s+)?(.+?)(?:\s+with\s+\d+\s+sources|\s+in\s+detail|\s+comprehensively|$)",
            r"research:\s*(.+)$",
            r"look\s+up\s+(?:information\s+(?:about\s+|on\s+))?(.+)$",
            r"find\s+(?:information\s+(?:about\s+|on\s+))?(.+)$",
            r"search\s+(?:for\s+)?(?:information\s+(?:about\s+|on\s+))?(.+)$",
        ]

        query = ""
        for pattern in query_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE | re.DOTALL)
            if match:
                query = match.group(1).strip()
                # Clean up common artifacts
                query = query.strip('"\'')
                # Remove trailing punctuation that's part of the command
                if query.endswith('.') and len(query) < 100:
                    query = query.rstrip('.')
                break

        # If no pattern matched, use the whole input minus the trigger word
        if not query:
            query = re.sub(r'^(?:research|look\s+up|find|search)\s+', '', user_input, flags=re.IGNORECASE).strip()

        if query:
            parameters["query"] = query

        # Extract depth preference
        depth_patterns = {
            r"(?:brief|quick|overview|high-level)": "overview",
            r"(?:detailed|thorough)": "detailed",
            r"(?:comprehensive|in-depth|extensive|complete)": "comprehensive",
        }

        for pattern, depth_level in depth_patterns.items():
            if re.search(pattern, user_input.lower()):
                parameters["depth"] = depth_level
                break

        # Extract number of sources if specified
        sources_match = re.search(r"(\d+)\s+sources?", user_input.lower())
        if sources_match:
            try:
                parameters["sources"] = int(sources_match.group(1))
            except ValueError:
                pass

        return parameters

    def _enhance_mcp_tool_parameters(self, parameters: dict, user_input: str) -> dict:
        """Enhanced parameter mapping for mcp_tool function

        MCP tool function expects a 'user_request' parameter containing the full
        natural language request. The function will then use LLM to select the
        appropriate MCP tool and generate arguments.
        """
        # Always provide the full user input as user_request
        # This allows the MCP function to do its own tool selection
        parameters["user_request"] = user_input

        return parameters

    def _force_contextual_parameters(
        self,
        original_params: dict[str, Any],
        user_input: str,
        context: ChatContext | None = None,
    ) -> dict[str, Any]:
        """BULLETPROOF: Force correct contextual parameters regardless of LLM output"""

        # Copy original parameters
        params = original_params.copy()

        # Detect contextual patterns in user input
        user_lower = user_input.lower()
        contextual_patterns = [
            "second",
            "next",
            "another",
            "third",
            "now",
            "then",
            "also",
        ]
        detected_patterns = [
            pattern for pattern in contextual_patterns if pattern in user_lower
        ]
        is_contextual = len(detected_patterns) > 0

        if DEBUG_MODE: print(f"🔍 DEBUG: User input: '{user_input}'")
        if DEBUG_MODE: print(f"🔍 DEBUG: Detected contextual patterns: {detected_patterns}")
        if DEBUG_MODE: print(f"🔍 DEBUG: Is contextual: {is_contextual}")

        if is_contextual and context and context.messages:
            # DETERMINISTIC LOCATION EXTRACTION from chat history
            extracted_path = self._extract_location_from_chat_history(context)
            if DEBUG_MODE: print(f"🔍 DEBUG: Extracted path from chat history: {extracted_path}")

            if extracted_path:
                params["path"] = extracted_path
                if DEBUG_MODE: print(f"🔧 BULLETPROOF FIX: Forcing path parameter to {extracted_path}")
            else:
                if DEBUG_MODE: print("🔍 DEBUG: No path extracted from chat history")

            # Ensure search_request is present for contextual queries
            if "search_request" not in params or not params["search_request"]:
                if "second" in user_lower:
                    params["search_request"] = "find second largest file"
                elif "third" in user_lower:
                    params["search_request"] = "find third largest file"
                elif any(word in user_lower for word in ["next", "another"]):
                    params["search_request"] = "find next largest file"
                else:
                    params["search_request"] = user_input

        return params

    def _extract_location_from_chat_history(self, context: ChatContext) -> str | None:
        """DETERMINISTIC: Extract location from chat history and recent chat files"""
        import json
        import re
        from pathlib import Path

        # First try context messages
        recent_messages = context.get_recent_messages(5)
        # Debug: print(f"🔍 DEBUG: Examining {len(recent_messages)} context messages for path extraction")

        for message in reversed(recent_messages):
            content = message.content.lower()
            # Pattern 1: ~/Directory paths
            home_paths: list[str] = re.findall(
                r"~/[a-zA-Z][a-zA-Z0-9_-]*", message.content
            )
            if home_paths:
                if DEBUG_MODE: print(f"🔍 DEBUG: Found home path in context: {home_paths[-1]}")
                return home_paths[-1]

            # Pattern 2: Common directory names
            if "downloads" in content:
                if DEBUG_MODE: print("🔍 DEBUG: Found 'downloads' in context message")
                return "~/Downloads"

        # If no path found in context, check recent chat files on disk
        if DEBUG_MODE: print("🔍 DEBUG: No path in context, checking recent chat files on disk")
        try:
            chat_dir = Path.home() / ".aii"
            chat_files = list(chat_dir.glob("chat-*.json"))

            # Sort by modification time, newest first
            chat_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

            # Check the most recent 10 chat files
            for chat_file in chat_files[:10]:
                try:
                    if DEBUG_MODE: print(f"🔍 DEBUG: Checking chat file: {chat_file.name}")
                    with open(chat_file) as f:
                        chat_data = json.load(f)

                    for message in chat_data.get("messages", []):
                        content = message.get("content", "").lower()
                        if DEBUG_MODE: print(f"🔍 DEBUG: File message content: '{content[:50]}...'")

                        # Pattern 1: ~/Directory paths
                        chat_home_paths: list[str] = re.findall(
                            r"~/[a-zA-Z][a-zA-Z0-9_-]*", message.get("content", "")
                        )
                        if chat_home_paths:
                            print(
                                f"🔍 DEBUG: Found home path in recent chat file: {chat_home_paths[-1]}"
                            )
                            return chat_home_paths[-1]

                        # Pattern 2: Common directory names
                        if "downloads" in content:
                            if DEBUG_MODE: print(
                                f"🔍 DEBUG: Found 'downloads' in recent chat file: {chat_file.name}"
                            )
                            return "~/Downloads"
                except Exception as e:
                    if DEBUG_MODE: print(f"🔍 DEBUG: Error processing {chat_file.name}: {e}")
                    continue  # Skip corrupted files

        except Exception as e:
            if DEBUG_MODE: print(f"🔍 DEBUG: Error checking chat files: {e}")

        if DEBUG_MODE: print("🔍 DEBUG: No path found in context or recent chat files")
        return None

    def _get_function_descriptions(self) -> str:
        """Get descriptions of available functions"""
        descriptions = []

        # Add built-in intents
        for template in self.intent_templates:
            example = template.examples[0] if template.examples else "No example"
            descriptions.append(
                f'- {template.function_name}: {template.intent_name} (e.g., "{example}")'
            )

        # Add functions from registry if available
        # CRITICAL FIX: Use live plugin descriptions from self.plugins instead of stale FunctionDefinition
        if self.function_registry:
            try:
                # Get template function names to avoid duplicates
                template_functions = [t.function_name for t in self.intent_templates]

                # First priority: Use plugin descriptions (they have full enhanced descriptions)
                for func_name, plugin in self.function_registry.plugins.items():
                    if func_name not in template_functions:
                        # Get the LIVE description property from the plugin
                        descriptions.append(f"- {func_name}: {plugin.description}")

                # Fallback: Use FunctionDefinition for any functions without plugins
                for func_name, func_def in self.function_registry.functions.items():
                    if func_name not in template_functions and func_name not in self.function_registry.plugins:
                        descriptions.append(f"- {func_name}: {func_def.description}")
            except AttributeError:
                pass

        return "\\n".join(descriptions[:20])  # Limit to prevent prompt bloat

    def _extract_parameters(
        self, user_input: str, template: IntentTemplate
    ) -> dict[str, Any]:
        """Extract parameters from input based on template"""
        import re  # Import at the top of the function to avoid scoping issues

        parameters = {}

        # Basic parameter extraction patterns
        if template.function_name == "translate":
            # Extract target language

            lang_match = re.search(r"\\bto\\s+(\\w+)", user_input, re.IGNORECASE)
            if lang_match:
                parameters["target_language"] = lang_match.group(1).lower()

            # Extract text to translate (remove command words)
            text = user_input
            for pattern in ["translate", "to " + parameters.get("target_language", "")]:
                text = re.sub(pattern, "", text, flags=re.IGNORECASE)
            text = text.strip().strip('"').strip("'")
            if text:
                parameters["text"] = text

        elif template.function_name == "code_review":
            # Extract file path
            file_match = re.search(r"([\\w\\./]+\\.\\w+)", user_input)
            if file_match:
                parameters["file_path"] = file_match.group(1)

        elif template.function_name == "code_generate":
            # Extract specification for code/content generation
            # For content generation (tweets, posts, emails, etc.)
            if any(
                content_type in user_input.lower()
                for content_type in ["tweet", "post", "message", "content", "email"]
            ):
                # This is content generation, extract the full request as specification
                parameters["specification"] = user_input
                parameters["language"] = (
                    "text"  # Use 'text' to indicate non-code content
                )
            else:
                # This is code generation, extract code specification
                spec = user_input
                for keyword in [
                    "write",
                    "create",
                    "generate",
                    "code",
                    "function",
                    "script",
                    "program",
                ]:
                    spec = re.sub(rf"\\b{keyword}\\b", "", spec, flags=re.IGNORECASE)
                spec = spec.strip().strip('"').strip("'")
                if spec:
                    parameters["specification"] = spec

        elif template.function_name == "content_generate":
            # Extract parameters for flexible content generation
            # Extract the full request as specification
            parameters["specification"] = user_input

            # Detect content type from user input
            content_types = {
                "calendar": ["calendar", "schedule"],
                "list": ["list", "todo", "checklist"],
                "document": ["document", "doc", "report"],
                "message": ["message", "note"],
            }

            detected_type = "auto"
            for content_type, keywords in content_types.items():
                if any(keyword in user_input.lower() for keyword in keywords):
                    detected_type = content_type
                    break

            parameters["content_type"] = detected_type

            # Extract date if mentioned (YYYY-MM-DD format)
            date_match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", user_input)
            if date_match:
                parameters["start_date"] = date_match.group(0)

            # Extract duration
            duration_patterns = [
                r"for\s+(\d+\s+(?:month|week|day|year)s?)",
                r"(\d+\s+(?:month|week|day|year)s?)",
                r"(one\s+(?:month|week|day|year))",
                r"(1\s+(?:month|week|day|year))",
            ]
            for pattern in duration_patterns:
                duration_match = re.search(pattern, user_input, re.IGNORECASE)
                if duration_match:
                    parameters["duration"] = duration_match.group(1)
                    break

        elif template.function_name in ["explain", "summarize", "research"]:
            # Extract the subject/topic
            topic = user_input
            for keyword in template.keywords:
                topic = re.sub(rf"\\b{keyword}\\b", "", topic, flags=re.IGNORECASE)
            topic = topic.strip().strip('"').strip("'")
            if topic:
                parameters["topic"] = topic
        elif template.function_name == "find_files":
            # Extract search request and path for file finding
            search_request = user_input.strip()

            # Extract path if mentioned (Downloads, Desktop, Documents, etc.)
            path_matches = re.search(
                r"\\b(?:in|under|from)\\s+(\\w+)(?:\\s+folder|\\s+directory)?",
                user_input,
                re.IGNORECASE,
            )
            if path_matches:
                path = path_matches.group(1).lower()
                # Map common folder names
                if path in ["downloads", "download"]:
                    parameters["path"] = "Downloads"
                elif path in ["desktop"]:
                    parameters["path"] = "Desktop"
                elif path in ["documents", "docs"]:
                    parameters["path"] = "Documents"
                else:
                    parameters["path"] = path

            parameters["search_request"] = search_request
            # Check if user explicitly wants to execute (run, execute keywords)
            execute_keywords = [
                "run it",
                "execute it",
                "and run",
                "and execute",
                "run it in",
            ]
            user_lower = user_input.lower()
            should_execute = any(keyword in user_lower for keyword in execute_keywords)
            # Only set execute parameter if user explicitly wants to execute
            # Otherwise let the function use its default value (True)
            if should_execute:
                parameters["execute"] = True
        elif template.function_name == "shell_command":
            # Extract request for shell command generation
            parameters["request"] = user_input.strip()
            # Check if user wants to execute (run, execute keywords)
            execute_keywords = ["run", "execute", "perform", "do"]
            user_lower = user_input.lower()
            should_execute = any(keyword in user_lower for keyword in execute_keywords)
            parameters["execute"] = should_execute
        elif template.function_name == "enhanced_shell":
            # Extract request for enhanced shell command generation
            # Remove the trigger words to get the actual request
            cleaned_input = user_input
            for trigger in [
                "enhanced command to",
                "advanced command to",
                "smart command to",
                "ai command to",
                "enhanced",
                "advanced",
                "smart",
            ]:
                cleaned_input = re.sub(
                    rf"^{trigger}\s*", "", cleaned_input, flags=re.IGNORECASE
                )

            parameters["request"] = cleaned_input.strip()
            # Enhanced shell always executes by default
            parameters["execute"] = True
        elif template.function_name == "streaming_shell":
            # Extract request for streaming shell command generation
            # Remove streaming trigger words
            cleaned_input = user_input
            for trigger in [
                "streaming command to",
                "live command to",
                "stream",
                "streaming",
                "live",
                "real-time",
            ]:
                cleaned_input = re.sub(
                    rf"^{trigger}\s*", "", cleaned_input, flags=re.IGNORECASE
                )

            parameters["request"] = cleaned_input.strip()
            parameters["execute"] = True  # Always execute for streaming
            parameters["stream"] = True  # Enable streaming

        return parameters

    def _enhance_with_patterns(
        self, llm_result: RecognitionResult, pattern_result: RecognitionResult
    ) -> RecognitionResult:
        """Enhance LLM result with pattern validation"""
        # If both point to same function, boost confidence and merge parameters
        if llm_result.function_name == pattern_result.function_name:
            enhanced_confidence = min(1.0, llm_result.confidence + 0.15)
            # Use smart confirmation logic
            needs_confirmation, confirmation_reason = self.should_confirm_function(
                llm_result.function_name,
                enhanced_confidence,
                {**pattern_result.parameters, **llm_result.parameters},
            )

            return RecognitionResult(
                intent=llm_result.intent,
                confidence=enhanced_confidence,
                parameters={**pattern_result.parameters, **llm_result.parameters},
                function_name=llm_result.function_name,
                requires_confirmation=needs_confirmation,
                reasoning=f"LLM enhanced by pattern match: {llm_result.reasoning}. Confirmation: {confirmation_reason}",
                source=RouteSource.LLM_RECOGNITION,
            )

        # If they disagree but pattern has high confidence, consider hybrid approach
        if pattern_result.confidence >= 0.9:
            hybrid_confidence = (llm_result.confidence + pattern_result.confidence) / 2
            # Use smart confirmation logic
            needs_confirmation, confirmation_reason = self.should_confirm_function(
                pattern_result.function_name,
                hybrid_confidence,
                {**llm_result.parameters, **pattern_result.parameters},
            )

            return RecognitionResult(
                intent=pattern_result.intent,
                confidence=hybrid_confidence,
                parameters={**llm_result.parameters, **pattern_result.parameters},
                function_name=pattern_result.function_name,
                requires_confirmation=needs_confirmation,
                reasoning=f"Pattern validation over LLM: {pattern_result.intent} (pattern: {pattern_result.confidence:.2f}, llm: {llm_result.confidence:.2f}). Confirmation: {confirmation_reason}",
                source=RouteSource.LLM_RECOGNITION,
            )

        # Otherwise, trust the LLM result
        # Use smart confirmation logic for LLM result too
        needs_confirmation, confirmation_reason = self.should_confirm_function(
            llm_result.function_name, llm_result.confidence, llm_result.parameters
        )

        return RecognitionResult(
            intent=llm_result.intent,
            confidence=llm_result.confidence,
            parameters=llm_result.parameters,
            function_name=llm_result.function_name,
            requires_confirmation=needs_confirmation,
            reasoning=f"{llm_result.reasoning}. Confirmation: {confirmation_reason}",
            source=llm_result.source,
        )

    def _combine_results(
        self, direct_result: RecognitionResult, llm_result: RecognitionResult
    ) -> RecognitionResult:
        """Combine direct pattern match with LLM result"""
        # If both point to same function, boost confidence
        if direct_result.function_name == llm_result.function_name:
            combined_confidence = min(1.0, direct_result.confidence + 0.2)
            return RecognitionResult(
                intent=llm_result.intent,
                confidence=combined_confidence,
                parameters={**direct_result.parameters, **llm_result.parameters},
                function_name=llm_result.function_name,
                requires_confirmation=combined_confidence < 0.8,
                reasoning=f"Pattern match + LLM agreement: {llm_result.reasoning}",
                source=RouteSource.LLM_RECOGNITION,
            )

        # If different functions, prefer higher confidence
        if llm_result.confidence > direct_result.confidence:
            return llm_result
        else:
            return direct_result

    def should_confirm_function(
        self,
        function_name: str,
        confidence: float,
        parameters: dict[str, Any],
        user_context: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        """Smart risk-based confirmation logic"""

        # Define function safety categories (can be moved to config later)
        FUNCTION_SAFETY = {
            # SAFE - No confirmation needed (or handles own confirmation internally)
            "explain": FunctionSafety.SAFE,
            "translate": FunctionSafety.SAFE,
            "content_generate": FunctionSafety.SAFE,
            "summarize": FunctionSafety.SAFE,
            "research": FunctionSafety.SAFE,  # read-only
            # Shell commands handle their own confirmation internally (v0.4.13 bugfix)
            "shell_command": FunctionSafety.SAFE,  # Handles own confirmation - no double prompt
            "enhanced_shell": FunctionSafety.SAFE,  # Handles own confirmation - no double prompt
            "streaming_shell": FunctionSafety.SAFE,  # Handles own confirmation - no double prompt
            # Git operations handle their own confirmation
            "git_commit": FunctionSafety.SAFE,  # Handles own confirmation with thinking mode preview
            "git_pr": FunctionSafety.SAFE,  # Handles own confirmation with PR preview
            "git_branch": FunctionSafety.SAFE,  # Handles own confirmation with branch preview
            # CONTEXT_DEPENDENT - Confirm based on confidence/context
            "code_generate": FunctionSafety.CONTEXT_DEPENDENT,
            "email_generate": FunctionSafety.CONTEXT_DEPENDENT,
            "find_files": FunctionSafety.CONTEXT_DEPENDENT,  # Can execute commands
        }

        safety_level = FUNCTION_SAFETY.get(
            function_name, FunctionSafety.CONTEXT_DEPENDENT
        )
        user_context = user_context or {}

        # SAFE functions never need confirmation
        if safety_level == FunctionSafety.SAFE:
            return False, "Safe function - no confirmation needed"

        # RISKY and DESTRUCTIVE functions always need confirmation
        if safety_level in [FunctionSafety.RISKY, FunctionSafety.DESTRUCTIVE]:
            risk_level = (
                "HIGH RISK"
                if safety_level == FunctionSafety.DESTRUCTIVE
                else "MEDIUM RISK"
            )
            return True, f"{risk_level} operation requires confirmation"

        # CONTEXT_DEPENDENT functions - decide based on confidence and context
        if safety_level == FunctionSafety.CONTEXT_DEPENDENT:
            # Low confidence always requires confirmation
            if confidence < 0.7:
                return True, f"Low confidence ({confidence:.0%}) requires confirmation"

            # Check for destructive operations in parameters
            destructive_indicators = [
                "rm",
                "del",
                "delete",
                "remove",
                "drop",
                "destroy",
                "format",
                "wipe",
                "clear",
                "reset",
                "--force",
                "-f",
                "sudo",
                "admin",
                "system",
                "critical",
            ]

            param_str = " ".join(str(v).lower() for v in parameters.values())
            if any(indicator in param_str for indicator in destructive_indicators):
                return True, "Potentially destructive operation detected"

            # Check context for previous risky operations
            if user_context.get("recent_risky_operation", False):
                return True, "Following previous risky operation - extra caution"

        return False, "Context assessment passed - no confirmation needed"

    def _is_universal_content_request(self, user_input: str) -> bool:
        """Check if the request should use universal orchestrator"""
        user_input_lower = user_input.lower()

        # Patterns that indicate universal content generation
        universal_patterns = [
            "generate me a tweet",
            "create a tweet",
            "write me an email",
            "generate an email",
            "create a post",
            "write a post",
            "generate content",
            "create content",
            "create a social media post",
            "generate a social media post",
            "write a social media post",
            "social media post about",
        ]

        # Also check for git context references
        git_context_patterns = [
            "per the latest git commit",
            "based on the latest commit",
            "from the last git commit",
            "using git history",
        ]

        has_universal_pattern = any(
            pattern in user_input_lower for pattern in universal_patterns
        )
        has_git_context = any(
            pattern in user_input_lower for pattern in git_context_patterns
        )

        return has_universal_pattern or (
            has_git_context
            and any(
                content in user_input_lower for content in ["tweet", "email", "post"]
            )
        )

    async def _route_to_universal_orchestrator(
        self, user_input: str, context: ChatContext | None = None
    ) -> RecognitionResult | None:
        """Route to universal orchestrator for content generation"""
        try:
            return RecognitionResult(
                intent="universal_content_generation",
                confidence=0.9,  # High confidence for universal routing
                parameters={"request": user_input},
                function_name="universal_generate",
                requires_confirmation=False,
                reasoning="Routed to universal orchestrator for context-aware content generation",
                source=RouteSource.LLM_RECOGNITION,
            )
        except Exception as e:
            print(f"Universal orchestrator routing failed: {e}")
            return None
