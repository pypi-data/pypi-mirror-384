<div align="center">
  <img src="aii-logo.png" alt="Aii Logo" width="128" height="128">

  # Aii - AI-Powered Assistant for VSCode

  **Version 0.1.0** - Natural language AI assistant with code generation, git commits, explanations, translation, and more. Works with multiple LLM providers.

  Response streaming • Guided setup • Extensible by design
</div>

## Features

### 💬 Interactive Chat
Chat with Aii directly in VSCode - similar to Cursor, Claude Code, and Continue.
- **Keyboard Shortcut:** `Cmd+Shift+A` (Mac) / `Ctrl+Shift+A` (Windows/Linux)
- **Command:** `Aii: Open Chat`
- **Features:**
  - Response streaming for fast display
  - Beautiful Markdown rendering with syntax highlighting (artifact mode)
  - Conversation history maintains context across messages
  - Ask questions, get explanations, generate code, and more

### 🔧 Code Generation
Generate code from natural language descriptions with streaming responses.
- **Keyboard Shortcut:** `Cmd+Shift+G` (Mac) / `Ctrl+Shift+G` (Windows/Linux)
- **Command:** `Aii: Generate Code`

### 📝 Git Commit Messages
AI-powered commit message generation from staged changes.
- **Keyboard Shortcut:** `Cmd+Shift+C` (Mac) / `Ctrl+Shift+C` (Windows/Linux)
- **Command:** `Aii: Generate Commit Message`

### 💡 Code Explanation
Understand complex code in plain English.
- **Command:** `Aii: Explain Code`
- Select code and run the command

### 🌍 Translation
Translate text/comments between languages.
- **Command:** `Aii: Translate Text`
- Select text and specify target language

## 📋 Requirements

**One-line install:** `uv tool install aiiware-cli`

The extension automatically handles:

- ✅ Server startup/shutdown
- ✅ Setup detection and guidance
- ✅ API key configuration

*Don't have `uv`? Install it first:*
- **macOS/Linux:** `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Windows:** `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

## 🚀 Quick Start

1. **Install the CLI:** `uv tool install aiiware-cli`
2. **Install this extension** from VSCode Marketplace
3. **Open VSCode** - the extension will guide you through first-time setup
4. **Run setup:** `aii config init` (guided automatically on first use)
5. **Start using:** Click the Aii icon in Activity Bar or use `Cmd+Shift+A`

The extension detects initialization status and provides guided setup when needed.

## Configuration

After initial setup (`aii config init`), the extension works automatically. For advanced customization:

- **`aii.streaming`** - Enable streaming mode for response display (default: `true`)
- **`aii.apiUrl`** - Customize API server URL (default: `http://localhost:16169`)
- **`aii.apiKey`** - Override API key (optional, auto-configured by default)

## Usage Examples

### Generate Code
1. Open a file in your preferred language
2. Press `Cmd+Shift+G`
3. Describe the code you want (e.g., "function to calculate fibonacci numbers")
4. Watch as code appears and inserts at cursor

### Generate Commit Message
1. Stage your changes: `git add .`
2. Press `Cmd+Shift+C`
3. Review AI-generated commit message
4. Confirm to commit

### Explain Code
1. Select code you want explained
2. Run `Aii: Explain Code` from Command Palette
3. View explanation in output panel

### Translate Text
1. Select text to translate
2. Run `Aii: Translate Text` from Command Palette
3. Enter target language
4. Choose to replace or keep both versions

## Features

✅ **Automatic server management** - No manual `aii serve` needed!
✅ **Real-time streaming** - Token-by-token display with <100ms latency
✅ **Guided setup** - Auto-detection with step-by-step initialization
✅ **Keyboard shortcuts** - 1-keystroke access to common operations
✅ **Natural language interface** - Chat naturally to generate code, commits, and more
✅ **Conversation history** - Multi-conversation management with persistence
✅ **Status bar indicator** - Connection status at a glance
✅ **Error recovery** - Graceful handling of network issues

## Troubleshooting

### Extension won't activate
- Ensure Aii CLI is installed: `which aii`
- If not installed: `uv tool install aiiware-cli`
- Check VSCode Output panel (View → Output → Aii Server)
- The extension automatically starts the server on activation

### Commands not working
- Check status bar shows "✓ Aii Server" (green)
- Verify server is running: `curl http://localhost:16169/api/status`
- Review error messages in Output panel (Aii Server or Aii channels)
- Try restarting VSCode to trigger re-initialization

### Streaming not working
- Enable streaming in settings: `aii.streaming: true`
- Check network connection to API server
- Ensure Aii CLI is up to date: `uv tool install --force aiiware-cli`
- Check server logs for errors
- Fallback to REST API if streaming fails

## 📄 License & Credits

**License:** Apache 2.0 • Copyright 2025-present aiiware.com

## 💬 Support & Community

- **🐦 Follow us**: [@aii_dev](https://x.com/aii_dev) - Release notes, tips, and updates
- **📖 Documentation**: Extension docs and troubleshooting guides in this README
- **💬 Questions**: VSCode Marketplace Q&A section
- **🐛 Issues**: Report bugs through the marketplace or extension feedback
