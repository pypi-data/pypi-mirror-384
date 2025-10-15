# ⭐ Star Shell

An AI-powered command line assistant that generates and executes shell commands using natural language.

## Features

- 🤖 **AI-Powered**: Uses OpenAI GPT or Google Gemini to understand your requests
- 💬 **Interactive Chat Mode**: Have conversations with your shell assistant
- 🛡️ **Safety First**: Built-in command safety checks and confirmations
- 🎯 **Context Aware**: Understands your current directory and system environment
- 🔒 **Secure**: Encrypted API key storage
- 🎨 **Beautiful Output**: Rich formatting and syntax highlighting

## Installation

```bash
pip install star-shell
```

## Quick Start

1. **Initialize Star Shell**:
   ```bash
   star-shell init
   ```
   Choose your AI backend (OpenAI or Gemini) and provide your API key.

2. **Ask for commands**:
   ```bash
   star-shell ask "list all Python files in this directory"
   ```

3. **Start interactive chat**:
   ```bash
   star-shell chat
   ```

## Commands

- `star-shell init` - Set up your AI backend and API keys
- `star-shell ask "your request"` - Generate a command for your request
- `star-shell chat` - Start an interactive chat session

## Supported AI Backends

- **OpenAI GPT-3.5 Turbo** - Requires OpenAI API key
- **Google Gemini Pro** - Requires Google AI API key

## Safety Features

Star Shell includes built-in safety checks for potentially dangerous commands:
- Warns about destructive operations (rm, format, etc.)
- Confirms before executing system-level changes
- Provides clear descriptions of what commands do

## Examples

```bash
# File operations
star-shell ask "create a backup of my config files"

# System information
star-shell ask "show me disk usage"

# Development tasks
star-shell ask "start a Python web server on port 8000"

# Git operations
star-shell ask "commit all changes with message 'update docs'"
```

## Requirements

- Python 3.8+
- OpenAI API key OR Google AI API key

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.