# ⭐ Star Shell

An AI-powered command line assistant that generates and executes shell commands using natural language.

## Features

- 🤖 **AI-Powered**: Uses OpenAI GPT or Google Gemini to understand your requests
- 💬 **Interactive Terminal**: Natural conversation with command execution
- 🧠 **Smart Responses**: AI decides whether to run commands or provide information
- 🛡️ **Safety First**: Built-in command safety checks and confirmations
- 🎯 **Context Aware**: Understands your current directory and system environment
- 🔒 **Secure**: Encrypted API key storage
- 🎨 **Beautiful Output**: Rich formatting and syntax highlighting
- ⚡ **Streamlined UX**: Automatic initialization checks and intuitive commands

## Installation

```bash
pip install star-shell
```

## Quick Start

1. **First time setup**:
   ```bash
   star-shell init
   ```
   Choose your AI backend (OpenAI or Gemini) and provide your API key.

2. **Start the interactive terminal**:
   ```bash
   star-shell run
   ```
   This opens an AI-powered terminal where you can chat and get commands executed.

3. **Or ask for specific commands**:
   ```bash
   star-shell ask "list all Python files in this directory"
   ```

## Commands

- `star-shell` - Shows status and quick help
- `star-shell init` - Set up your AI backend and API keys  
- `star-shell run` - Start the interactive AI terminal
- `star-shell ask "your request"` - Generate a specific command

## Supported AI Backends

- **OpenAI GPT-3.5 Turbo** - Requires OpenAI API key
- **Google Gemini Pro** - Requires Google AI API key

## Safety Features

Star Shell includes built-in safety checks for potentially dangerous commands:
- Warns about destructive operations (rm, format, etc.)
- Confirms before executing system-level changes
- Provides clear descriptions of what commands do

## Examples

### Interactive Terminal Mode
```bash
star-shell run

⭐ > create a new directory called projects
# AI will generate and offer to execute: mkdir projects

⭐ > what's the difference between git merge and rebase?
# AI will explain the concepts in natural language

⭐ > help
# Shows available commands and examples
```

### Direct Command Mode
```bash
# File operations
star-shell ask "create a backup of my config files"

# System information  
star-shell ask "show me disk usage"

# Development tasks
star-shell ask "start a Python web server on port 8000"
```

## Requirements

- Python 3.8+
- OpenAI API key OR Google AI API key

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.