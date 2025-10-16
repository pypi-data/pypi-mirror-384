"""Function Plugin Layer - Universal function system with context gathering"""

from ..core.registry.function_registry import FunctionRegistry
from .analysis.analysis_functions import (
    ExplainFunction,
    ResearchFunction,
    SummarizeFunction,
)
from .code.code_functions import CodeGenerateFunction, CodeReviewFunction
from .content.content_functions import (
    ContentGenerateFunction,
    EmailContentFunction,
    SocialPostFunction,
    TwitterContentFunction,
    UniversalContentFunction,
)
from .content.template_functions import (
    TemplateFunction,
    TemplateListFunction,
)
from .context.context_functions import (
    FileContextFunction,
    GitContextFunction,
    SystemContextFunction,
)
from .git.git_functions import (
    GitBranchFunction,
    GitCommitFunction,
    GitDiffFunction,
    GitPRFunction,
    GitStatusFunction,
)
from .shell.contextual_shell_functions import (
    ContextualShellFunction,
)
from .shell.enhanced_shell_functions import (
    EnhancedShellCommandFunction,
)
from .shell.explain_command_function import (
    ExplainCommandFunction,
)
from .shell.shell_functions import (
    FindCommandFunction,
    ShellCommandFunction,
)
from .shell.streaming_shell_functions import (
    StreamingShellFunction,
)
from .system.stats_functions import StatsFunction
from .translation.translation_functions import TranslationFunction
from .mcp.mcp_functions import MCPToolFunction
from .mcp.mcp_management_functions import (
    MCPAddFunction,
    MCPRemoveFunction,
    MCPListFunction,
    MCPEnableFunction,
    MCPDisableFunction,
    MCPCatalogFunction,
    MCPInstallFunction,
    MCPStatusFunction,
    GitHubIssueFunction,
    MCPTestFunction,
    MCPUpdateFunction,
)


def register_all_functions(registry: FunctionRegistry) -> None:
    """Register all built-in functions with the registry"""

    # Context functions (fundamental)
    registry.register_plugin(GitContextFunction())
    registry.register_plugin(FileContextFunction())
    registry.register_plugin(SystemContextFunction())

    # Content generation functions (universal)
    registry.register_plugin(UniversalContentFunction())
    registry.register_plugin(TwitterContentFunction())
    registry.register_plugin(EmailContentFunction())
    registry.register_plugin(ContentGenerateFunction())
    registry.register_plugin(SocialPostFunction())

    # Template functions (v0.4.7)
    registry.register_plugin(TemplateFunction())
    registry.register_plugin(TemplateListFunction())

    # Git functions
    registry.register_plugin(GitCommitFunction())
    registry.register_plugin(GitDiffFunction())
    registry.register_plugin(GitStatusFunction())
    registry.register_plugin(GitPRFunction())
    registry.register_plugin(GitBranchFunction())

    # Translation functions
    registry.register_plugin(TranslationFunction())

    # Code functions
    registry.register_plugin(CodeReviewFunction())
    registry.register_plugin(CodeGenerateFunction())

    # Analysis functions
    registry.register_plugin(SummarizeFunction())
    registry.register_plugin(ExplainFunction())
    registry.register_plugin(ResearchFunction())

    # Shell functions with Smart Command Triage System
    registry.register_plugin(EnhancedShellCommandFunction())
    registry.register_plugin(FindCommandFunction())

    # Command explanation function (v0.4.12)
    registry.register_plugin(ExplainCommandFunction())

    # Streaming shell functions with real-time feedback
    registry.register_plugin(StreamingShellFunction())

    # Contextual shell functions with conversation memory
    registry.register_plugin(ContextualShellFunction())

    # System functions (v0.4.7)
    registry.register_plugin(StatsFunction())

    # MCP functions (v0.4.8)
    registry.register_plugin(MCPToolFunction())

    # MCP management functions (v0.4.9+)
    registry.register_plugin(MCPAddFunction())
    registry.register_plugin(MCPRemoveFunction())
    registry.register_plugin(MCPListFunction())
    registry.register_plugin(MCPEnableFunction())
    registry.register_plugin(MCPDisableFunction())
    registry.register_plugin(MCPCatalogFunction())
    registry.register_plugin(MCPInstallFunction())
    registry.register_plugin(MCPStatusFunction())  # v0.4.10
    registry.register_plugin(GitHubIssueFunction())  # v0.4.10
    registry.register_plugin(MCPTestFunction())  # v0.4.10
    registry.register_plugin(MCPUpdateFunction())  # v0.4.10

    # Function registration complete - no output needed for clean UX


__all__ = [
    "GitBranchFunction",
    "GitCommitFunction",
    "GitDiffFunction",
    "GitPRFunction",
    "GitStatusFunction",
    "TranslationFunction",
    "CodeGenerateFunction",
    "CodeReviewFunction",
    "SummarizeFunction",
    "ExplainFunction",
    "ResearchFunction",
    "GitContextFunction",
    "FileContextFunction",
    "SystemContextFunction",
    "UniversalContentFunction",
    "TwitterContentFunction",
    "EmailContentFunction",
    "ContentGenerateFunction",
    "SocialPostFunction",
    "TemplateFunction",
    "TemplateListFunction",
    "ShellCommandFunction",
    "FindCommandFunction",
    "EnhancedShellCommandFunction",
    "ExplainCommandFunction",
    "StreamingShellFunction",
    "ContextualShellFunction",
    "StatsFunction",
    "MCPToolFunction",
    "MCPAddFunction",
    "MCPRemoveFunction",
    "MCPListFunction",
    "MCPEnableFunction",
    "MCPDisableFunction",
    "MCPCatalogFunction",
    "MCPInstallFunction",
    "MCPStatusFunction",
    "GitHubIssueFunction",
    "MCPTestFunction",
    "MCPUpdateFunction",
    "register_all_functions",
]
