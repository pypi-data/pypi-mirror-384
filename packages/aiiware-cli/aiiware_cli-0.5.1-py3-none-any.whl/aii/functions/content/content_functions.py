"""Content Generation Functions - Pure content creation using universal architecture"""

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

# Note: LLMOrchestrator is used by the engine, not needed here


class UniversalContentFunction(FunctionPlugin):
    """Universal content generation function using orchestrated context gathering"""

    @property
    def name(self) -> str:
        return "universal_generate"

    @property
    def description(self) -> str:
        return "Generate any type of content using intelligent context gathering"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.CONTENT

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "request": ParameterSchema(
                name="request",
                type="string",
                required=True,
                description="Natural language description of what to generate",
            ),
            "format": ParameterSchema(
                name="format",
                type="string",
                required=False,
                description="Target format hint",
                choices=[
                    "auto",
                    "tweet",
                    "email",
                    "post",
                    "code",
                    "commit",
                    "explanation",
                ],
                default="auto",
            ),
            "tone": ParameterSchema(
                name="tone",
                type="string",
                required=False,
                description="Writing tone/style for the content",
                choices=["professional", "casual", "technical", "friendly"],
                default="professional",
            ),
            "conversation_history": ParameterSchema(
                name="conversation_history",
                type="array",
                required=False,
                description="Previous conversation messages for context",
                default=[],
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
        """Default output mode: just the result"""
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
                errors=["LLM provider required for universal content generation"],
            )
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute universal content generation using orchestrated approach"""

        request = parameters["request"]
        target_format = parameters.get("format", "auto")
        conversation_history = parameters.get("conversation_history", [])

        try:
            # If conversation history is provided, prepend it to the request
            enhanced_request = request
            if conversation_history and len(conversation_history) > 0:
                # Build conversation context from history
                history_text = "\n\n".join([
                    f"{'User' if msg.get('role') == 'user' else 'Assistant'}: {msg.get('content', '')}"
                    for msg in conversation_history[-10:]  # Last 10 messages for context
                ])
                enhanced_request = f"""Previous conversation:
{history_text}

Current request: {request}

Please respond to the current request while considering the conversation history above."""

            # Import orchestrator dynamically to avoid circular imports
            from ...core.orchestrator import LLMOrchestrator

            # Create a dummy function registry since we're using basic orchestrator
            # The orchestrator only needs basic context functions
            from ...core.registry.function_registry import FunctionRegistry

            registry = FunctionRegistry()

            # Create orchestrator instance
            orchestrator = LLMOrchestrator(
                llm_provider=context.llm_provider, function_registry=registry
            )

            # Process request using universal architecture with conversation history
            result = await orchestrator.process_universal_request(enhanced_request, context)

            if result.success:
                # Add metadata about the generation process
                result.data.update(
                    {
                        "generation_method": "universal_orchestrated",
                        "original_request": request,
                        "target_format": target_format,
                        "conversation_context_used": len(conversation_history) > 0,
                    }
                )

            return result

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Universal content generation failed: {str(e)}"
            )


class TwitterContentFunction(FunctionPlugin):
    """Specialized Twitter content generation with optimized prompting"""

    @property
    def name(self) -> str:
        return "generate_tweet"

    @property
    def description(self) -> str:
        return "Generate Twitter content optimized for engagement and format"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.CONTENT

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "topic": ParameterSchema(
                name="topic",
                type="string",
                required=True,
                description="Topic or theme for the tweet",
            ),
            "include_hashtags": ParameterSchema(
                name="include_hashtags",
                type="boolean",
                required=False,
                default=True,
                description="Whether to include relevant hashtags",
            ),
            "include_emojis": ParameterSchema(
                name="include_emojis",
                type="boolean",
                required=False,
                default=True,
                description="Whether to include relevant emojis",
            ),
            "tone": ParameterSchema(
                name="tone",
                type="string",
                required=False,
                choices=["professional", "casual", "technical", "friendly"],
                default="casual",
                description="Writing tone/style for the tweet",
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
        """Check if LLM provider is available"""
        if not context.llm_provider:
            return ValidationResult(
                valid=False, errors=["LLM provider required for tweet generation"]
            )
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute Twitter content generation with specialized prompting"""

        topic = parameters["topic"]
        include_hashtags = parameters.get("include_hashtags", True)
        include_emojis = parameters.get("include_emojis", True)
        tone = parameters.get("tone", "casual")

        try:
            # Build specialized tweet prompt
            prompt = f"""Create an engaging Twitter post about: {topic}

Requirements:
- Maximum 280 characters
- {tone} tone
- {'Include relevant hashtags' if include_hashtags else 'No hashtags'}
- {'Include appropriate emojis' if include_emojis else 'No emojis'}
- Focus on engagement and shareability
- Be authentic and valuable to the audience

Generate only the tweet text, no additional explanation:"""

            tweet = await context.llm_provider.complete(prompt)
            tweet = tweet.strip().strip('"').strip("'")

            # Validate length
            if len(tweet) > 280:
                return ExecutionResult(
                    success=False,
                    message=f"Generated tweet is too long ({len(tweet)} characters, max 280)",
                )

            return ExecutionResult(
                success=True,
                message=tweet,
                data={
                    "tweet": tweet,
                    "character_count": len(tweet),
                    "topic": topic,
                    "tone": tone,
                    "includes_hashtags": "#" in tweet,
                    "includes_emojis": any(ord(char) > 127 for char in tweet),
                    "timestamp": datetime.now().isoformat(),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Tweet generation failed: {str(e)}"
            )


class EmailContentFunction(FunctionPlugin):
    """Professional email content generation"""

    @property
    def name(self) -> str:
        return "generate_email"

    @property
    def description(self) -> str:
        return "Generate professional email content with proper structure"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.CONTENT

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "purpose": ParameterSchema(
                name="purpose",
                type="string",
                required=True,
                description="Purpose or main topic of the email",
            ),
            "recipient_type": ParameterSchema(
                name="recipient_type",
                type="string",
                required=False,
                choices=["colleague", "client", "manager", "external", "team"],
                default="colleague",
                description="Type of recipient to adjust formality",
            ),
            "tone": ParameterSchema(
                name="tone",
                type="string",
                required=False,
                choices=["professional", "casual", "technical", "friendly"],
                default="professional",
                description="Writing tone/style for the email",
            ),
            "include_context": ParameterSchema(
                name="include_context",
                type="boolean",
                required=False,
                default=True,
                description="Whether to include project/git context if available",
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
        """Check if LLM provider is available"""
        if not context.llm_provider:
            return ValidationResult(
                valid=False, errors=["LLM provider required for email generation"]
            )
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute email content generation"""

        purpose = parameters["purpose"]
        recipient_type = parameters.get("recipient_type", "colleague")
        tone = parameters.get("tone", "professional")
        include_context = parameters.get("include_context", True)

        try:
            # Get git context if requested and available
            context_info = ""
            if include_context:
                try:
                    import subprocess

                    result = subprocess.run(
                        ["git", "log", "-1", "--pretty=format:%s%n%b"],
                        capture_output=True,
                        text=True,
                        cwd=context.config.get("working_dir", "."),
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        context_info = (
                            f"\n\nLatest project update:\n{result.stdout.strip()}"
                        )
                except Exception:
                    pass

            # Build email prompt
            formality_guide = {
                "formal": "Very formal and structured",
                "professional": "Professional but approachable",
                "friendly": "Warm and friendly while maintaining professionalism",
                "urgent": "Direct and action-oriented",
            }

            recipient_guide = {
                "colleague": "peer-level professional",
                "client": "external client requiring clear communication",
                "manager": "supervisor requiring concise updates",
                "external": "external stakeholder",
                "team": "team members for coordination",
            }

            prompt = f"""Generate a professional email about: {purpose}

Context:
- Recipient: {recipient_guide.get(recipient_type, recipient_type)}
- Tone: {formality_guide.get(tone, tone)}
{context_info}

Structure:
- Subject line (clear and informative)
- Appropriate greeting
- Clear, well-organized body
- Professional closing
- Signature placeholder

Generate the complete email:"""

            # Get streaming callback if available
            streaming_callback = getattr(context.llm_provider, '_streaming_callback', None)

            # Use complete_with_usage for token tracking if available
            if hasattr(context.llm_provider, "complete_with_usage"):
                llm_response = await context.llm_provider.complete_with_usage(
                    prompt,
                    on_token=streaming_callback
                )
                email = llm_response.content.strip()
                usage = llm_response.usage or {}
            else:
                email = await context.llm_provider.complete(prompt)
                email = email.strip()
                usage = {}

            # Extract subject line if present
            subject = ""
            lines = email.split("\n")
            if lines and ("subject:" in lines[0].lower() or "re:" in lines[0].lower()):
                subject = (
                    lines[0].replace("Subject:", "").replace("subject:", "").strip()
                )
                email = "\n".join(lines[1:]).strip()

            return ExecutionResult(
                success=True,
                message=email,
                data={
                    "email_body": email,
                    "subject": subject,
                    "purpose": purpose,
                    "recipient_type": recipient_type,
                    "tone": tone,
                    "context_included": bool(context_info),
                    "word_count": len(email.split()),
                    "timestamp": datetime.now().isoformat(),
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Email generation failed: {str(e)}"
            )


class ContentGenerateFunction(FunctionPlugin):
    """General content generation function for any type of content"""

    @property
    def name(self) -> str:
        return "content_generate"

    @property
    def description(self) -> str:
        return "Generate any type of content based on natural language requests"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.CONTENT

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "content_type": ParameterSchema(
                name="content_type",
                type="string",
                required=False,
                description="Type of content to generate (auto-detected if not specified)",
                choices=[
                    "text",
                    "calendar",
                    "list",
                    "document",
                    "message",
                    "note",
                    "email",
                    "auto",
                ],
                default="auto",
            ),
            "specification": ParameterSchema(
                name="specification",
                type="string",
                required=True,
                description="Natural language description of what content to generate",
            ),
            "start_date": ParameterSchema(
                name="start_date",
                type="string",
                required=False,
                description="Start date for time-based content (YYYY-MM-DD format)",
            ),
            "duration": ParameterSchema(
                name="duration",
                type="string",
                required=False,
                description="Duration or time span for the content",
            ),
            "format": ParameterSchema(
                name="format",
                type="string",
                required=False,
                description="Output format preference",
                choices=["plain", "markdown", "structured", "auto"],
                default="auto",
            ),
            "tone": ParameterSchema(
                name="tone",
                type="string",
                required=False,
                description="Writing tone/style for the content",
                choices=["professional", "casual", "technical", "friendly"],
                default="professional",
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
        """Check if LLM provider is available"""
        if not context.llm_provider:
            return ValidationResult(
                valid=False, errors=["LLM provider required for content generation"]
            )
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute flexible content generation"""

        specification = parameters["specification"]
        content_type = parameters.get("content_type", "auto")
        start_date = parameters.get("start_date")
        duration = parameters.get("duration")
        format_pref = parameters.get("format", "auto")

        try:
            # Build context-aware prompt for content generation
            prompt_parts = [
                f"Generate content based on this request: {specification}",
                "",
            ]

            # Add specific parameters if provided
            if content_type != "auto":
                prompt_parts.append(f"Content type: {content_type}")

            if start_date:
                prompt_parts.append(f"Start date: {start_date}")

            if duration:
                prompt_parts.append(f"Duration/span: {duration}")

            # Add format instructions
            format_instructions = {
                "plain": "Return plain text format",
                "markdown": "Format using markdown syntax",
                "structured": "Use clear structure with headers and sections",
                "auto": "Use the most appropriate format for the content type",
            }

            prompt_parts.extend(
                [
                    "",
                    "Instructions:",
                    f"- {format_instructions.get(format_pref, 'Use appropriate formatting')}",
                    "- Be accurate and helpful",
                    "- Include all necessary details",
                    "- Make the content practical and usable",
                    "- Return only the requested content, no additional explanation",
                    "",
                    "Generate the content:",
                ]
            )

            prompt = "\n".join(prompt_parts)

            # Get streaming callback if available
            streaming_callback = getattr(context.llm_provider, '_streaming_callback', None)

            # Generate content using LLM
            if hasattr(context.llm_provider, "complete_with_usage"):
                llm_response = await context.llm_provider.complete_with_usage(
                    prompt,
                    on_token=streaming_callback
                )
                content = llm_response.content.strip()
                usage = llm_response.usage or {}
            else:
                content = await context.llm_provider.complete(prompt)
                content = content.strip()
                usage = {}

            return ExecutionResult(
                success=True,
                message=content,
                data={
                    "content": content,
                    "content_type": content_type,
                    "specification": specification,
                    "start_date": start_date,
                    "duration": duration,
                    "format": format_pref,
                    "word_count": len(content.split()),
                    "character_count": len(content),
                    "input_tokens": usage.get("input_tokens"),
                    "output_tokens": usage.get("output_tokens"),
                    "timestamp": datetime.now().isoformat(),
                    "provider": (
                        context.llm_provider.model_info
                        if hasattr(context.llm_provider, "model_info")
                        else "Unknown"
                    ),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Content generation failed: {str(e)}"
            )

    def supports_streaming(self) -> bool:
        """This function supports streaming responses"""
        return True

    def build_prompt(self, parameters: dict[str, Any]) -> str:
        """Build LLM prompt for streaming content generation

        Args:
            parameters: Function parameters

        Returns:
            str: Formatted prompt for LLM
        """
        specification = parameters.get("specification", "")
        content_type = parameters.get("content_type", "auto")
        output_format = parameters.get("format", "auto")
        start_date = parameters.get("start_date")
        duration = parameters.get("duration")

        # Build comprehensive prompt
        prompt_parts = []

        # Content type instruction
        if content_type and content_type != "auto":
            prompt_parts.append(f"Generate {content_type} content based on the following specification:")
        else:
            prompt_parts.append("Generate content based on the following specification:")

        # Main specification
        prompt_parts.append(f"\n{specification}")

        # Time-based instructions
        if start_date:
            prompt_parts.append(f"\nStart date: {start_date}")
        if duration:
            prompt_parts.append(f"\nDuration: {duration}")

        # Format instruction
        if output_format == "markdown":
            prompt_parts.append("\nFormat the output using markdown.")
        elif output_format == "structured":
            prompt_parts.append("\nProvide a well-structured, organized output.")
        elif output_format == "plain":
            prompt_parts.append("\nProvide plain text output without special formatting.")

        prompt_parts.append("\nProvide the complete content now:")

        return "\n".join(prompt_parts)


class SocialPostFunction(FunctionPlugin):
    """Social media post generation for various platforms"""

    @property
    def name(self) -> str:
        return "generate_social_post"

    @property
    def description(self) -> str:
        return "Generate social media posts optimized for different platforms"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.CONTENT

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "content": ParameterSchema(
                name="content",
                type="string",
                required=True,
                description="Topic or content to create a post about",
            ),
            "platform": ParameterSchema(
                name="platform",
                type="string",
                required=False,
                choices=["twitter", "linkedin", "facebook", "instagram", "general"],
                default="general",
                description="Target social media platform",
            ),
            "style": ParameterSchema(
                name="style",
                type="string",
                required=False,
                choices=[
                    "informative",
                    "promotional",
                    "personal",
                    "professional",
                    "humorous",
                ],
                default="informative",
                description="Style of the post",
            ),
            "tone": ParameterSchema(
                name="tone",
                type="string",
                required=False,
                description="Writing tone/style for the post",
                choices=["professional", "casual", "technical", "friendly"],
                default="casual",
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
        """Check if LLM provider is available"""
        if not context.llm_provider:
            return ValidationResult(
                valid=False, errors=["LLM provider required for social post generation"]
            )
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute social media post generation"""

        content = parameters["content"]
        platform = parameters.get("platform", "general")
        style = parameters.get("style", "informative")

        try:
            # Platform-specific guidelines
            platform_guides = {
                "twitter": "280 characters max, hashtags, engaging and concise",
                "linkedin": "Professional tone, industry insights, call-to-action",
                "facebook": "Casual but informative, encourage engagement",
                "instagram": "Visual focus, story-driven, relevant hashtags",
                "general": "Adaptable for multiple platforms, balanced approach",
            }

            guide = platform_guides.get(platform, platform_guides["general"])

            prompt = f"""Create a {platform} post about: {content}

Style: {style}
Platform guidelines: {guide}

Requirements:
- Match the {style} style appropriately
- Include relevant hashtags if appropriate for the platform
- Encourage engagement where suitable
- Make it shareable and valuable

Generate only the post content:"""

            post = await context.llm_provider.complete(prompt)
            post = post.strip().strip('"').strip("'")

            return ExecutionResult(
                success=True,
                message=post,
                data={
                    "post": post,
                    "platform": platform,
                    "style": style,
                    "content_topic": content,
                    "character_count": len(post),
                    "hashtag_count": post.count("#"),
                    "timestamp": datetime.now().isoformat(),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Social post generation failed: {str(e)}"
            )
