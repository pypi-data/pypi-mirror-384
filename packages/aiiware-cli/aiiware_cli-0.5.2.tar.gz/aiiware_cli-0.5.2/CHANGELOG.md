# Change Log

All notable changes to Aii CLI will be documented in this file.

## [0.5.2] - 2025-10-16

### ✨ New

- **Claude Haiku 4.5 Support** - High-performance coding model with near-frontier quality at 75% lower cost than Sonnet

## [0.5.1] - 2025-10-14

### 🐛 Fixed

- **VSCode Token Display** - Fixed token usage and cost showing correctly in chat panel and status bar

## [0.5.0] - 2025-10-12

### ✨ New

- **HTTP API Server** - Run `aii serve` to enable VSCode and other IDE integrations
- **WebSocket Streaming** - Real-time responses for connected clients

## [0.4.13] - 2025-10-10

### 🐛 Fixed

- **Reliable Confirmations** - Fixed shell command confirmation flow (no more double prompts)
- **Accurate Token Tracking** - Session summaries now show correct token counts
- **Better Function Recognition** - Improved LLM understanding of your requests

## [0.4.12] - 2025-10-09

### ✨ New

- **API Server** - HTTP endpoints for integration with VSCode and other tools

## [0.4.11] - 2025-10-08

### ✨ Improved

- **Lazy MCP Connections** - Servers connect only when needed (faster startup)
- **Better Error Handling** - Clearer messages when MCP servers fail

## [0.4.10] - 2025-10-07

### ✨ New

- **Content Signatures** - Configurable signatures for AI-generated content (git commits, PRs, etc.)

## [0.4.9] - 2025-10-06

### ✨ New

- **Easy MCP Setup** - Browse and install MCP servers with one command (`aii mcp catalog`, `aii mcp install <server>`)
- **10+ Pre-configured Servers** - GitHub, Chrome DevTools, Postgres, and more

### 🐛 Fixed

- **MCP Token Tracking** - Operations now show correct token counts
- **Output Formatting** - Cleaner display without duplicate status lines

## [0.4.8] - 2025-10-05

### ✨ New

- **Multi-Step Tool Chaining** - Automatically execute complex workflows requiring multiple tools
- **Direct MCP Control** - `aii mcp invoke <tool>` for power users

### 🐛 Fixed

- **GitHub Integration** - Full access to 26 GitHub tools (search repos, create issues, etc.)

## [0.4.7] - 2025-10-03

### ✨ New

- **Template Library** - 8 pre-built templates for marketing, development, and business content (`aii template list`)
- **Usage Analytics** - Track your AI usage with `aii stats` (local storage, privacy-first)

## [0.4.6] - 2025-10-02

### ✨ Improved

- **Performance** - Faster processing for large files
- **Error Messages** - More actionable suggestions when things go wrong

## [0.4.5] - 2025-10-01

### ✨ New

- **Git PR Generator** - Create pull requests with AI-generated titles and descriptions (`aii pr`)
- **Smart Branch Naming** - Generate conventional branch names (`aii branch "add user auth"` → `feature/add-user-auth`)

## [0.4.4] - 2025-09-30

### ✨ New

- **Real-Time Streaming** - See responses as they generate for faster experience
- **Smart Output Modes** - CLEAN (just results), STANDARD (with metrics), THINKING (full reasoning)

## [0.4.3] - 2025-09-28

### ✨ New

- **Shell Autocomplete** - Tab completion for bash/zsh/fish (`aii install-completion`)
- **Command History** - Arrow keys to recall previous commands in interactive mode

## [0.4.2] - 2025-09-26

### ✨ New

- **Interactive Setup Wizard** - 2-minute guided setup with arrow key navigation (`aii config init`)
- **Cost Tracking** - See transparent pricing for all LLM operations
- **Quick Config** - Fast provider/model switching (`aii config provider`, `aii config model`)

## [0.4.1] - 2025-09-24

### ✨ New

- **Web Search Integration** - DuckDuckGo (free), Brave Search, and Google Search support
- **Health Diagnostics** - `aii doctor` troubleshoots configuration issues

## [0.4.0] - 2025-09-22

### ✨ New

- **Multi-LLM Support** - Choose between Claude, GPT, and Gemini models
- **Session Memory** - Conversations persist across commands
- **Smart Confirmations** - Only asks when operations are risky

## [0.3.0] - 2025-09-15

### ✨ New

- **Git Integration** - Smart commit messages, PR generation, branch naming
- **Code Tools** - Generate and review code in any language
- **Translation** - Support for 100+ languages

## [0.2.0] - 2025-09-08

### ✨ New

- **Content Generation** - Create emails, blogs, social media posts
- **Shell Automation** - Safe command generation with explanations
- **Analysis Tools** - Explain code, summarize documents, research topics

## [0.1.0] - 2025-09-01

### 🎉 Initial Release

- Natural language command interface
- Claude integration
- Git commit generation
