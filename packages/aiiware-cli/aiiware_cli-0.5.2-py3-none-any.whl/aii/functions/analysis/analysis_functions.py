"""Analysis and explanation functions"""

from pathlib import Path
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


class ExplainFunction(FunctionPlugin):
    """Explain concepts, technologies, or topics (NOT shell commands - use explain_command for those)"""

    @property
    def name(self) -> str:
        return "explain"

    @property
    def description(self) -> str:
        return "Explain concepts, technologies, or topics (e.g., machine learning, kubernetes, DNS). DO NOT use for shell commands - use explain_command instead."

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.ANALYSIS

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "topic": ParameterSchema(
                name="topic",
                type="string",
                required=True,
                description="The concept, technology, or topic to explain",
            ),
            "language": ParameterSchema(
                name="language",
                type="string",
                required=False,
                description="Output language for the explanation (e.g., 'English', 'Chinese', 'Spanish', 'French')",
                default="English",
            ),
            "audience": ParameterSchema(
                name="audience",
                type="string",
                required=False,
                description="Target audience level",
                choices=["beginner", "intermediate", "advanced", "expert"],
                default="intermediate",
            ),
            "include_examples": ParameterSchema(
                name="include_examples",
                type="boolean",
                required=False,
                description="Include practical examples",
                default=True,
            ),
            "max_words": ParameterSchema(
                name="max_words",
                type="integer",
                required=False,
                description="Maximum word count for explanation (e.g., 50, 100, 200)",
            ),
            "brevity": ParameterSchema(
                name="brevity",
                type="string",
                required=False,
                description="Level of brevity for explanation",
                choices=["brief", "concise", "standard", "detailed", "comprehensive"],
                default="standard",
            ),
            "format_style": ParameterSchema(
                name="format_style",
                type="string",
                required=False,
                description="Output format style",
                choices=["paragraph", "bullet_points", "structured", "definition", "summary"],
                default="structured",
            ),
            "constraints": ParameterSchema(
                name="constraints",
                type="string",
                required=False,
                description="Additional constraints or requirements (e.g., 'within 50 words', 'one sentence', 'no technical jargon')",
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
        """Explain should show clean output by default (just the explanation)"""
        return OutputMode.CLEAN

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Explain supports all output modes"""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check if LLM provider is available"""
        if not context.llm_provider:
            return ValidationResult(
                valid=False,
                errors=["LLM provider required for explanations"],
            )
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute explanation"""
        topic = parameters["topic"]
        language = parameters.get("language", "English")
        audience = parameters.get("audience", "intermediate")
        include_examples = parameters.get("include_examples", True)
        max_words = parameters.get("max_words")
        brevity = parameters.get("brevity", "standard")
        format_style = parameters.get("format_style", "structured")
        constraints = parameters.get("constraints")

        try:
            explanation, usage = await self._generate_explanation(
                topic,
                language,
                audience,
                include_examples,
                max_words,
                brevity,
                format_style,
                constraints,
                context.llm_provider,
                context.web_client,
            )

            # Count actual words for verification
            actual_word_count = len(explanation.split())

            return ExecutionResult(
                success=True,
                message=f"# Explanation: {topic}\n\n{explanation}",
                data={
                    "clean_output": explanation,  # For CLEAN mode
                    "topic": topic,
                    "language": language,
                    "audience": audience,
                    "explanation": explanation,
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "reasoning_tokens": usage.get("reasoning_tokens", 0),
                    "include_examples": include_examples,
                    "max_words": max_words,
                    "brevity": brevity,
                    "format_style": format_style,
                    "constraints": constraints,
                    "word_count": actual_word_count,
                    "truncated": usage.get("truncated", False),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Explanation failed: {str(e)}"
            )

    async def _generate_explanation(
        self,
        topic: str,
        language: str,
        audience: str,
        include_examples: bool,
        max_words: int = None,
        brevity: str = "standard",
        format_style: str = "structured",
        constraints: str = None,
        llm_provider: Any = None,
        web_client: Any = None,
    ) -> str:
        """Generate constraint-aware explanation"""

        # Build constraint-aware prompt with strong emphasis on limits
        prompt_parts = []

        # CRITICAL CONSTRAINTS FIRST - Language and Word Count
        if language and language.lower() != "english":
            prompt_parts.append(f"🚨 CRITICAL CONSTRAINT #1: Output language MUST be {language} (NOT English, NOT any other language)")
            prompt_parts.append(f"📝 Your ENTIRE explanation must be written in {language}. Every single word must be in {language}.")

        if max_words:
            prompt_parts.append(f"🚨 CRITICAL CONSTRAINT #2: Your explanation must be EXACTLY {max_words} words or less. This is a HARD LIMIT.")
            prompt_parts.append(f"📊 Word count requirement: {max_words} words maximum. You MUST count your words carefully.")

        # Brevity instructions
        brevity_instructions = {
            "brief": "Provide only the most essential information in the shortest form possible. Focus on core definition and key points only.",
            "concise": "Be concise and focused, avoiding unnecessary details. Cover main concepts efficiently.",
            "standard": "Provide balanced coverage with clear explanations and key details.",
            "detailed": "Provide comprehensive coverage with thorough explanations and context.",
            "comprehensive": "Include extensive details, examples, and related concepts with full context."
        }

        if brevity in brevity_instructions:
            prompt_parts.append(f"📝 Brevity level: {brevity_instructions[brevity]}")

        # Format instructions
        format_instructions = {
            "bullet_points": "Format as clear bullet points with short, direct statements.",
            "definition": "Provide a clear, concise definition in paragraph form. Focus on what it is and why it matters.",
            "summary": "Write as a summary paragraph covering the essential information.",
            "paragraph": "Write in flowing paragraph form with smooth transitions.",
            "structured": "Use clear headings and organized sections for easy reading."
        }

        if format_style in format_instructions:
            prompt_parts.append(f"📋 Format: {format_instructions[format_style]}")

        # Additional constraints
        if constraints:
            prompt_parts.append(f"⚠️ Additional requirements: {constraints}")

        # Audience guidance
        audience_guidance = {
            "beginner": "Assume no prior knowledge. Use simple terms and analogies. Avoid technical jargon.",
            "intermediate": "Assume basic knowledge. Include technical details but explain concepts clearly.",
            "advanced": "Assume good technical background. Focus on implementation details and advanced concepts.",
            "expert": "Assume deep expertise. Focus on edge cases, optimization, and cutting-edge developments.",
        }

        guidance = audience_guidance.get(audience, audience_guidance["intermediate"])
        prompt_parts.append(f"🎯 Audience: {audience} level. {guidance}")

        # Core explanation request
        prompt_parts.append(f"📖 Topic to explain: {topic}")

        # Example handling based on constraints
        if include_examples:
            if max_words and max_words <= 50:
                prompt_parts.append("Examples: Mention only if absolutely essential and word count allows.")
            elif max_words and max_words <= 100:
                prompt_parts.append("Examples: Include one brief example if word count allows.")
            else:
                prompt_parts.append("Examples: Include relevant, practical examples.")
        else:
            prompt_parts.append("Examples: Do not include examples.")

        # Web context (if available)
        context_info = ""
        if web_client and not max_words:  # Skip web search for very constrained responses
            try:
                search_results = await web_client.search(
                    f"{topic} explanation tutorial", num_results=2
                )
                if search_results:
                    context_info = "\n\n🌐 Current information:\n"
                    for result in search_results[:2]:
                        context_info += f"- {result.title}: {result.snippet}\n"
                    prompt_parts.append(context_info)
            except Exception:
                pass

        # Structure guidance based on format and constraints
        if format_style == "definition":
            prompt_parts.append("\n🏗️ Structure: Provide a clear definition followed by brief explanation of significance.")
        elif format_style == "bullet_points":
            prompt_parts.append("\n🏗️ Structure: Use bullet points to cover key aspects: definition, how it works, importance.")
        elif format_style == "summary":
            prompt_parts.append("\n🏗️ Structure: Write a cohesive summary covering what it is, how it works, and why it matters.")
        elif not max_words or max_words > 150:
            # Only use full structure for longer explanations
            prompt_parts.append(f"""
🏗️ Structure your explanation as follows:
1. **Overview**: What is {topic}?
2. **Key Concepts**: Core principles and terminology
3. **How It Works**: Technical details appropriate for {audience} level
{'4. **Examples**: Practical examples and use cases' if include_examples else ''}
5. **Applications**: Real-world uses and importance
{'6. **Further Learning**: Next steps or related topics' if not max_words or max_words > 200 else ''}""")

        # CONSTRAINT REINFORCEMENT for language and word limits
        if language and language.lower() != "english":
            prompt_parts.append(f"\n🔢 FINAL REMINDER #1: Write ENTIRELY in {language}. Do not mix languages or use English.")

        if max_words:
            prompt_parts.append(f"\n🔢 FINAL REMINDER #2: Your response must not exceed {max_words} words. Count carefully!")
            prompt_parts.append(f"🎯 If approaching the limit, prioritize: definition → how it works → importance")

        # Combine all parts
        full_prompt = "\n\n".join(prompt_parts)

        try:
            # Get streaming callback if available
            streaming_callback = getattr(llm_provider, '_streaming_callback', None)

            # Execute LLM request with constraint-aware prompt
            if hasattr(llm_provider, "complete_with_usage"):
                llm_response = await llm_provider.complete_with_usage(
                    full_prompt,
                    on_token=streaming_callback
                )
                result = llm_response.content
                usage = llm_response.usage or {}
            else:
                result = await llm_provider.complete(full_prompt)
                usage = {}

            if result is None:
                return "Failed to generate explanation", usage

            # POST-PROCESSING: Word count validation and intelligent truncation
            result_str = str(result)
            word_count = len(result_str.split())
            usage["word_count"] = word_count

            if max_words and word_count > max_words:
                # Attempt intelligent truncation
                truncated = self._intelligent_truncate(result_str, max_words)
                usage["truncated"] = True
                usage["original_word_count"] = word_count
                usage["final_word_count"] = len(truncated.split())
                return truncated, usage

            return result_str, usage

        except Exception as e:
            raise RuntimeError(f"Failed to generate explanation: {str(e)}") from e

    def _intelligent_truncate(self, text: str, max_words: int) -> str:
        """Intelligently truncate text to word limit while preserving meaning"""
        words = text.split()
        if len(words) <= max_words:
            return text

        # Allow 10% tolerance for natural sentence boundaries
        tolerance = int(max_words * 0.1)
        max_allowed = max_words + tolerance

        # If within tolerance, check if we're at a natural break
        if len(words) <= max_allowed:
            # Check if text ends with sentence-ending punctuation
            if text.rstrip().endswith(('.', '!', '?', '。', '！', '？')):
                return text

        # Need to truncate - try to do so at sentence boundaries
        # Handle both English (.) and CJK (。) sentence endings
        sentence_endings = ['. ', '! ', '? ', '。', '！', '？']

        # Find sentence boundaries within word limit
        truncated_sentences = []
        word_count = 0
        current_sentence = []

        for i, word in enumerate(words):
            current_sentence.append(word)
            word_count += 1

            # Check if this word ends a sentence
            is_sentence_end = any(word.endswith(ending.strip()) for ending in sentence_endings)

            if is_sentence_end and word_count <= max_words:
                # Complete sentence within limit - keep it
                truncated_sentences.extend(current_sentence)
                current_sentence = []
            elif word_count > max_words:
                # Exceeded limit
                if truncated_sentences:
                    # We have complete sentences, stop here
                    break
                else:
                    # No complete sentences yet, truncate at word limit
                    truncated_text = ' '.join(words[:max_words])
                    # Add ellipsis if not ending with punctuation
                    if not truncated_text.rstrip().endswith(('.', '!', '?', '。', '！', '？')):
                        truncated_text += '...'
                    return truncated_text

        # Join preserved sentences
        if truncated_sentences:
            result = ' '.join(truncated_sentences)
            return result

        # Fallback: hard truncate at max_words
        truncated_text = ' '.join(words[:max_words])
        if not truncated_text.rstrip().endswith(('.', '!', '?', '。', '！', '？')):
            truncated_text += '...'
        return truncated_text

    def supports_streaming(self) -> bool:
        """This function supports streaming responses"""
        return True

    def build_prompt(self, parameters: dict[str, Any]) -> str:
        """Build LLM prompt for streaming explanation

        Args:
            parameters: Function parameters

        Returns:
            str: Formatted prompt for LLM
        """
        topic = parameters.get("topic", "")
        detail_level = parameters.get("detail_level", "medium")
        target_audience = parameters.get("target_audience", "general")
        include_examples = parameters.get("include_examples", True)

        # Build explanation prompt
        prompt_parts = [f"Explain the following topic: {topic}"]

        # Detail level
        if detail_level == "brief":
            prompt_parts.append("\nProvide a brief, concise explanation (2-3 paragraphs).")
        elif detail_level == "detailed":
            prompt_parts.append("\nProvide a comprehensive, detailed explanation with examples.")
        else:  # medium
            prompt_parts.append("\nProvide a clear explanation with appropriate depth.")

        # Target audience
        if target_audience != "general":
            prompt_parts.append(f"\nTarget audience: {target_audience}")
            prompt_parts.append(f"Adjust technical language and depth accordingly.")

        # Examples
        if include_examples:
            prompt_parts.append("\nInclude relevant examples to illustrate key concepts.")

        prompt_parts.append("\nBegin your explanation now:")

        return "\n".join(prompt_parts)


class SummarizeFunction(FunctionPlugin):
    """Summarize documents, articles, or content"""

    @property
    def name(self) -> str:
        return "summarize"

    @property
    def description(self) -> str:
        return "Summarize documents, articles, or text content"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.ANALYSIS

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "content": ParameterSchema(
                name="content",
                type="string",
                required=False,
                description="Text content to summarize (if not using file_path)",
            ),
            "file_path": ParameterSchema(
                name="file_path",
                type="string",
                required=False,
                description="Path to file to summarize (if not using content)",
            ),
            "length": ParameterSchema(
                name="length",
                type="string",
                required=False,
                description="Summary length",
                choices=["brief", "medium", "detailed"],
                default="medium",
            ),
            "format": ParameterSchema(
                name="format",
                type="string",
                required=False,
                description="Summary format",
                choices=["paragraph", "bullet_points", "structured"],
                default="structured",
            ),
            "language": ParameterSchema(
                name="language",
                type="string",
                required=False,
                description="Output language for the summary (e.g., 'chinese', 'english', 'spanish')",
                choices=["chinese", "english", "spanish", "french", "german", "japanese", "korean", "italian", "portuguese"],
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
        """Summarize should show clean output by default (just the summary)"""
        return OutputMode.CLEAN

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Summarize supports all output modes"""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check prerequisites"""
        content = context.parameters.get("content")
        file_path = context.parameters.get("file_path")

        if not content and not file_path:
            return ValidationResult(
                valid=False,
                errors=["Either content or file_path must be provided"],
            )

        if file_path:
            path = Path(file_path)
            if not path.exists():
                return ValidationResult(
                    valid=False, errors=[f"File not found: {file_path}"]
                )

            # Check file size (max 500KB)
            if path.stat().st_size > 500 * 1024:
                return ValidationResult(
                    valid=False,
                    errors=["File too large for summarization (max 500KB)"],
                )

        if not context.llm_provider:
            return ValidationResult(
                valid=False,
                errors=["LLM provider required for summarization"],
            )

        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute summarization"""
        content = parameters.get("content")
        file_path = parameters.get("file_path")
        length = parameters.get("length", "medium")
        format_type = parameters.get("format", "structured")

        try:
            # Get content
            if file_path and not content:
                path = Path(file_path)
                content = path.read_text(encoding="utf-8")
                source = f"file: {file_path}"
            else:
                source = "provided text"

            if not content:
                return ExecutionResult(success=False, message="No content to summarize")

            # Extract language parameter for language-specific summaries
            language = parameters.get("language")

            summary, usage = await self._generate_summary(
                content, length, format_type, context.llm_provider, language
            )

            return ExecutionResult(
                success=True,
                message=f"# Summary ({source})\n\n{summary}",
                data={
                    "clean_output": summary,  # For CLEAN mode
                    "summary": summary,
                    "source": source,
                    "length": length,
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "reasoning_tokens": usage.get("reasoning_tokens", 0),
                    "format": format_type,
                    "original_length": len(content),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Summarization failed: {str(e)}"
            )

    async def _generate_summary(
        self, content: str, length: str, format_type: str, llm_provider: Any, language: str = None
    ) -> str:
        """Generate summary using LLM"""
        length_instructions = {
            "brief": "Create a very concise summary (2-3 sentences)",
            "medium": "Create a balanced summary (1-2 paragraphs)",
            "detailed": "Create a comprehensive summary with key details",
        }

        format_instructions = {
            "paragraph": "Format as flowing paragraphs",
            "bullet_points": "Format as bullet points",
            "structured": "Use structured format with headers and bullet points",
        }

        length_instruction = length_instructions.get(
            length, length_instructions["medium"]
        )
        format_instruction = format_instructions.get(
            format_type, format_instructions["structured"]
        )

        # Truncate content if too long for LLM
        if len(content) > 8000:
            content = content[:8000] + "..."

        # Add language instruction if specified
        language_instruction = ""
        if language:
            language_map = {
                "chinese": "中文 (Chinese)",
                "english": "English",
                "spanish": "Spanish",
                "french": "French",
                "german": "German",
                "japanese": "Japanese",
                "korean": "Korean",
                "italian": "Italian",
                "portuguese": "Portuguese",
            }
            language_name = language_map.get(language.lower(), language)
            language_instruction = f"**CRITICAL REQUIREMENT**: Write the ENTIRE summary in {language_name} ONLY. Do not use English at all"

        # Build requirements list
        requirements = [
            length_instruction,
            format_instruction,
            "Focus on the most important points and key takeaways",
            "Maintain accuracy and don't add information not in the original",
            "Use clear, concise language",
            "If structured format, use markdown headers and bullet points"
        ]

        # Add language instruction if specified
        if language_instruction:
            requirements.insert(0, language_instruction)  # Put language first for emphasis

        requirements_text = "\n".join(f"- {req}" for req in requirements)

        # Special handling for language-specific summaries
        if language:
            prompt = f"""IMPORTANT: You must write the summary in {language_map.get(language.lower(), language)} ONLY. Do not use English.

Summarize the following content in {language_map.get(language.lower(), language)}:

{content}

Requirements:
{requirements_text}

Generate the summary in {language_map.get(language.lower(), language)}:"""
        else:
            prompt = f"""Summarize the following content:

{content}

Requirements:
{requirements_text}

Generate the summary:"""

        try:
            # Get streaming callback if available
            streaming_callback = getattr(llm_provider, '_streaming_callback', None)

            # Use complete_with_usage to track token consumption
            if hasattr(llm_provider, "complete_with_usage"):
                llm_response = await llm_provider.complete_with_usage(
                    prompt,
                    on_token=streaming_callback
                )
                result = llm_response.content
                usage = llm_response.usage or {}
            else:
                result = await llm_provider.complete(prompt)
                usage = {}

            return (
                str(result) if result is not None else "Failed to generate summary",
                usage
            )
        except Exception as e:
            raise RuntimeError(f"Failed to generate summary: {str(e)}") from e


class ResearchFunction(FunctionPlugin):
    """Research topics using web search and analysis"""

    @property
    def name(self) -> str:
        return "research"

    @property
    def description(self) -> str:
        return (
            "Research topics using web search (news, articles, documentation) and provide comprehensive analysis. "
            "Use for: general knowledge queries, current events, technical concepts, product comparisons, industry trends. "
            "NOT for: GitHub repository searches (use mcp_tool for 'search repos', 'find repositories', 'popular repos')."
        )

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.ANALYSIS

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "query": ParameterSchema(
                name="query",
                type="string",
                required=True,
                description="Research query or topic",
            ),
            "depth": ParameterSchema(
                name="depth",
                type="string",
                required=False,
                description="Research depth",
                choices=["overview", "detailed", "comprehensive"],
                default="detailed",
            ),
            "sources": ParameterSchema(
                name="sources",
                type="integer",
                required=False,
                description="Number of sources to research",
                default=5,
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return True  # Web search requires confirmation

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        """Research should show thinking mode by default (sources + reasoning)"""
        return OutputMode.THINKING

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Research supports all output modes"""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check prerequisites - only LLM provider is required, web search is optional"""
        errors = []

        if not context.llm_provider:
            errors.append("LLM provider required for research analysis")

        # Note: web_client is optional - we'll fall back to LLM-only mode if unavailable

        if errors:
            return ValidationResult(valid=False, errors=errors)

        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute research with web search or LLM-only fallback"""
        query = parameters["query"]
        depth = parameters.get("depth", "detailed")
        max_sources = parameters.get("sources", 5)

        # Initialize progress tracker
        progress = ProgressTracker(use_emojis=True, use_animations=True)

        # Try web-based research first, fall back to LLM-only if unavailable
        use_web = context.web_client is not None
        web_attempted = use_web  # Track if we tried web search
        search_results = []

        # Define workflow steps based on mode
        if use_web:
            progress.add_step(f"Searching and analyzing sources", icon="🔍")
            progress.add_step("Synthesizing findings", icon="🤖")
        else:
            progress.add_step("Analyzing topic", icon="🤖")
            progress.add_step("Generating research report", icon="✨")

        step_index = 0

        if use_web:
            try:
                # Step 1: Search web sources
                progress.start_step(step_index)
                search_results = await context.web_client.search(
                    query, num_results=max_sources
                )

                if not search_results:
                    # No results found, fall back to LLM-only
                    progress.complete_step(step_index, success=False)
                    progress.finish()
                    use_web = False
                    # Restart with LLM-only mode
                    progress = ProgressTracker(use_emojis=True, use_animations=True)
                    progress.add_step("Analyzing topic", icon="🤖")
                    progress.add_step("Generating research report", icon="✨")
                    step_index = 0
                else:
                    progress.complete_step(step_index, success=True)
                    step_index += 1

            except Exception as e:
                # Web search failed (API error, network issue, etc.)
                # Fall back to LLM-only mode
                progress.complete_step(step_index, success=False)
                progress.finish()
                use_web = False
                # Restart with LLM-only mode
                progress = ProgressTracker(use_emojis=True, use_animations=True)
                progress.add_step("Analyzing topic", icon="🤖")
                progress.add_step("Generating research report", icon="✨")
                step_index = 0

        # Generate research report (web-based or LLM-only)
        try:
            if use_web and search_results:
                # Step 1 already completed (searching and analyzing)
                step_index += 1

                # Step 2: Synthesize findings
                progress.start_step(step_index)
                # CRITICAL: Stop progress animation before LLM streaming starts
                # Progress animation interferes with token-by-token streaming output
                progress._stop_animated_step()
                research_report, usage = await self._generate_research_report_with_web(
                    query, search_results, depth, context.llm_provider
                )
                research_mode = "web-based"
                progress.complete_step(step_index, success=True)
            else:
                # Step 1: Analyze topic (LLM-only)
                progress.start_step(step_index)
                progress.complete_step(step_index, success=True)
                step_index += 1

                # Step 2: Generate report
                progress.start_step(step_index)
                # CRITICAL: Stop progress animation before LLM streaming starts
                # Progress animation interferes with token-by-token streaming output
                progress._stop_animated_step()
                research_report, usage = await self._generate_research_report_llm_only(
                    query, depth, context.llm_provider
                )
                research_mode = "llm-only"
                search_results = []  # Ensure empty for consistency
                progress.complete_step(step_index, success=True)

            progress.finish()

            # Add helpful note for LLM-only mode
            message = f"# Research Report: {query}\n\n"
            if research_mode == "llm-only" and web_attempted:
                # Web was attempted but failed - inform user
                message += "💡 **Tip:** Web search failed (DuckDuckGo API unreliable). For web-based research:\n"
                message += "   1. Get free Brave Search API key: https://brave.com/search/api/\n"
                message += "   2. Add to `~/.aii/secrets.yaml`: `brave_api_key: your-key`\n"
                message += "   3. Update `~/.aii/config.yaml`: `web_search.provider: brave`\n\n"

            message += research_report

            return ExecutionResult(
                success=True,
                message=message,
                data={
                    "clean_output": research_report,  # For CLEAN mode
                    "query": query,
                    "report": research_report,
                    "research_mode": research_mode,
                    "sources_found": len(search_results),
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "reasoning_tokens": usage.get("reasoning_tokens", 0),
                    "depth": depth,
                    "sources": [
                        {"title": r.title, "url": r.url, "snippet": r.snippet}
                        for r in search_results
                    ] if search_results else [],
                },
            )

        except Exception as e:
            return ExecutionResult(success=False, message=f"Research failed: {str(e)}")

    async def _generate_research_report_with_web(
        self, query: str, search_results: Any, depth: str, llm_provider: Any
    ) -> tuple[str, dict[str, Any]]:
        """Generate comprehensive research report from web search results"""
        depth_instructions = {
            "overview": "Provide a high-level overview with key points",
            "detailed": "Provide detailed analysis with multiple perspectives",
            "comprehensive": "Provide comprehensive analysis with deep insights and implications",
        }

        depth_instruction = depth_instructions.get(
            depth, depth_instructions["detailed"]
        )

        # Compile search results
        sources_text = "\n\n".join(
            [
                f"**Source {i+1}: {result.title}**\n{result.snippet}\nURL: {result.url}"
                for i, result in enumerate(search_results[:5])
            ]
        )

        # Enhanced prompt with better synthesis instructions
        prompt = f"""You are a research analyst tasked with synthesizing information from multiple web sources.

**Research Topic:** {query}

**Available Sources:**
{sources_text}

**Your Task:**
Create a comprehensive, well-synthesized research report that:
- {depth_instruction}
- Synthesizes information across all sources (don't just summarize each source separately)
- Identifies key themes, patterns, and consensus viewpoints
- Highlights any conflicting information or different perspectives
- Includes current trends and recent developments
- Provides balanced analysis on controversial topics
- Cites sources inline using [Source N] format
- Uses clear markdown structure with headings and sections

**Report Structure:**

## Executive Summary
Brief 2-3 sentence overview of the topic and key findings.

## Key Findings
- Bullet points of the most important discoveries
- Each point should synthesize information from multiple sources
- Cite sources: [Source 1], [Source 2], etc.

## Current State and Trends
Detailed analysis of the current landscape and emerging trends. Synthesize cross-source information.

## Different Perspectives
(If applicable) Present varying viewpoints or debates on the topic with source citations.

## Implications and Impact
Analyze the significance and potential consequences. What does this mean for stakeholders?

## Future Outlook
Based on the sources, what are the predicted developments or areas to watch?

## Sources and References
{chr(10).join([f"[Source {i+1}] {result.title} - {result.url}" for i, result in enumerate(search_results)])}

Generate the research report following the structure above:"""

        try:
            # Get streaming callback if available
            streaming_callback = getattr(llm_provider, '_streaming_callback', None)

            # Use complete_with_usage to track token consumption
            if hasattr(llm_provider, "complete_with_usage"):
                llm_response = await llm_provider.complete_with_usage(
                    prompt,
                    on_token=streaming_callback
                )
                result = llm_response.content
                usage = llm_response.usage or {}
            else:
                result = await llm_provider.complete(prompt)
                usage = {}

            return (
                str(result) if result is not None else "Failed to generate research report",
                usage
            )
        except Exception as e:
            raise RuntimeError(f"Failed to generate research report: {str(e)}") from e

    async def _generate_research_report_llm_only(
        self, query: str, depth: str, llm_provider: Any
    ) -> tuple[str, dict[str, Any]]:
        """Generate research report using only LLM knowledge (fallback when web unavailable)"""
        depth_instructions = {
            "overview": "Provide a high-level overview with key points from your knowledge",
            "detailed": "Provide detailed analysis based on your training data",
            "comprehensive": "Provide comprehensive analysis with deep insights from your knowledge base",
        }

        depth_instruction = depth_instructions.get(
            depth, depth_instructions["detailed"]
        )

        prompt = f"""You are a knowledgeable research analyst. Web search is currently unavailable, so provide a research report based on your training data and knowledge.

**Research Topic:** {query}

**Your Task:**
Create a well-structured research report based on your knowledge that:
- {depth_instruction}
- Clearly indicates this is based on your training data (knowledge cutoff: January 2025)
- Highlights what information might be outdated or require current sources
- Provides balanced analysis when discussing controversial topics
- Uses clear markdown structure with headings and sections
- Notes where web sources would provide more current information

**Report Structure:**

## Executive Summary
Brief 2-3 sentence overview of the topic based on your knowledge.

## Key Concepts and Background
Core information about the topic from your training data.

## Known Developments (as of training cutoff)
What you know about this topic up to January 2025.

## Limitations of This Analysis
Explicitly state:
- This analysis is based on training data (knowledge cutoff: January 2025)
- Areas where current web sources would provide more up-to-date information
- Topics that may have evolved significantly since your training

## Recommendations
Suggest areas where the user should seek current sources for the most accurate information.

**Note:** Please start your response with a clear disclaimer: "⚠️ LLM-Only Mode: This research is based on training data (knowledge cutoff: January 2025) without current web sources."

Generate the research report following the structure above:"""

        try:
            # Get streaming callback if available
            streaming_callback = getattr(llm_provider, '_streaming_callback', None)

            # Use complete_with_usage to track token consumption
            if hasattr(llm_provider, "complete_with_usage"):
                llm_response = await llm_provider.complete_with_usage(
                    prompt,
                    on_token=streaming_callback
                )
                result = llm_response.content
                usage = llm_response.usage or {}
            else:
                result = await llm_provider.complete(prompt)
                usage = {}

            return (
                str(result) if result is not None else "Failed to generate research report",
                usage
            )
        except Exception as e:
            raise RuntimeError(f"Failed to generate LLM-only research report: {str(e)}") from e
