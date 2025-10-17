# Basic Agent Chat Loop

[![PyPI version](https://img.shields.io/pypi/v/basic-agent-chat-loop.svg)](https://pypi.org/project/basic-agent-chat-loop/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/actions/workflows/ci.yml/badge.svg)](https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/Open-Agent-Tools/Basic-Agent-Chat-Loop/branch/main/graph/badge.svg)](https://codecov.io/gh/Open-Agent-Tools/Basic-Agent-Chat-Loop)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A feature-rich, interactive CLI for AI agents with token tracking, prompt templates, agent aliases, and extensive configuration options.

## Features

- 🏷️ **Agent Aliases** - Save agents as short names (`chat_loop pete` instead of full paths)
- 📦 **Auto-Setup** - Automatically install agent dependencies from `requirements.txt` or `pyproject.toml`
- 📜 **Command History** - Navigate previous queries with ↑↓ arrows (persisted to `~/.chat_history`)
- ✍️ **Multi-line Input** - Type `\\` to enter multi-line mode for code blocks
- 💰 **Token Tracking** - Track tokens and costs per query and session
- 📝 **Prompt Templates** - Reusable prompts from `~/.prompts/`
- ⚙️ **Configuration** - YAML-based config with per-agent overrides
- 📊 **Status Bar** - Real-time metrics (queries, tokens, duration)
- 📈 **Session Summary** - Full statistics displayed on exit
- 🎨 **Rich Formatting** - Enhanced markdown rendering with syntax highlighting
- 🔄 **Error Recovery** - Automatic retry logic with exponential backoff
- 🔍 **Agent Metadata** - Display model, tools, and capabilities

## Installation

### Quick Install (Recommended)

```bash
pip install basic-agent-chat-loop
```

That's it! The package will automatically create:
- `~/.chatrc` - Configuration file with recommended defaults
- `~/.prompts/` - Sample prompt templates (on first use)

### Platform-Specific Options

**Windows (for command history support):**
```bash
pip install basic-agent-chat-loop[windows]
```

**AWS Bedrock integration:**
```bash
pip install basic-agent-chat-loop[bedrock]
```

### From Source

For development or the latest features:

```bash
git clone https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop.git
cd Basic-Agent-Chat-Loop
pip install -e ".[dev]"
```

See [docs/INSTALL.md](docs/INSTALL.md) for detailed installation instructions and troubleshooting.

## Quick Start

### Basic Usage

```bash
# Run with agent path
chat_loop path/to/your/agent.py

# Or use an alias (after saving)
chat_loop myagent
```

### Agent Aliases

Save frequently used agents for quick access:

```bash
# Save an agent as an alias
chat_loop --save-alias myagent path/to/agent.py

# Use the alias from anywhere
chat_loop myagent

# List all saved aliases
chat_loop --list-aliases

# Remove an alias
chat_loop --remove-alias myagent
```

**Example with real agents:**
```bash
# Save your agents
chat_loop --save-alias pete ~/agents/product_manager/agent.py
chat_loop --save-alias dev ~/agents/senior_developer/agent.py

# Use them from anywhere
cd ~/projects/my-app
chat_loop dev  # Get coding help
chat_loop pete  # Get product feedback
```

Aliases are stored in `~/.chat_aliases` and work from any directory.

### Auto-Setup Dependencies

Automatically install agent dependencies with the `--auto-setup` flag (or `-a` for short):

```bash
# Auto-install dependencies when running an agent
chat_loop myagent --auto-setup
chat_loop path/to/agent.py -a

# Works with any of these dependency files:
# - requirements.txt (most common)
# - pyproject.toml (modern Python projects)
# - setup.py (legacy projects)
```

**Smart detection**: If you run an agent without `--auto-setup` and dependency files are detected, you'll see a helpful suggestion:

```bash
chat_loop myagent
💡 Found requirements.txt in agent directory. Run with --auto-setup (or -a) to install dependencies automatically
```

**What gets installed:**
- `requirements.txt` → `pip install -r requirements.txt`
- `pyproject.toml` → `pip install -e <agent_directory>`
- `setup.py` → `pip install -e <agent_directory>`

This makes sharing agents easier—just include a `requirements.txt` with your agent and users can install everything with one command.

### Prompt Templates

The package automatically creates sample templates in `~/.prompts/` on first use:
- `explain.md` - Explain code in detail
- `review.md` - Code review with best practices
- `debug.md` - Help debugging issues
- `optimize.md` - Performance optimization suggestions
- `test.md` - Generate test cases
- `document.md` - Add documentation

**Use templates in chat:**
```bash
chat_loop myagent
You: /review src/app.py
You: /explain utils.py
You: /test my_function
```

**Create custom templates:**
```bash
# Create your own template
cat > ~/.prompts/security.md <<'EOF'
# Security Review

Please review this code for security vulnerabilities:

{input}

Focus on:
- Input validation
- Authentication/authorization
- Data sanitization
- Common security patterns
EOF

# Use it in chat
You: /security auth.py
```

## Configuration

A configuration file (`~/.chatrc`) is automatically created on first use with recommended defaults. You can customize it to your preferences:

```yaml
features:
  show_tokens: true           # Display token counts
  show_metadata: true         # Show agent model/tools info
  rich_enabled: true          # Enhanced formatting

ui:
  show_status_bar: true       # Top status bar
  show_duration: true         # Query duration

behavior:
  max_retries: 3              # Retry attempts on failure
  timeout: 120.0              # Request timeout (seconds)

# Per-agent overrides
agents:
  'Product Pete':
    features:
      show_tokens: false
```

See [CONFIG.md](CONFIG.md) for full configuration options.

## Commands

| Command | Description |
|---------|-------------|
| `help` | Show help message |
| `info` | Show agent details (model, tools) |
| `templates` | List available prompt templates |
| `/name` | Use prompt template from `~/.prompts/name.md` |
| `clear` | Clear screen and reset agent session |
| `exit`, `quit` | Exit chat (shows session summary) |

### Multi-line Input

Press `\\` to enter multi-line mode:

```
You: \\
... def factorial(n):
...     if n <= 1:
...         return 1
...     return n * factorial(n - 1)
...
[Press Enter on empty line to submit]
```

## Token Tracking

### During Chat

When `show_tokens: true` in config:

```
------------------------------------------------------------
Time: 6.3s │ 1 cycle │ Tokens: 4.6K (in: 4.4K, out: 237) │ Cost: $0.017
```

### Session Summary

Always shown on exit:

```
============================================================
Session Summary
------------------------------------------------------------
  Duration: 12m 34s
  Queries: 15
  Tokens: 67.8K (in: 45.2K, out: 22.6K)
  Total Cost: $0.475
============================================================
```

## Programmatic Usage

```python
from basic_agent_chat_loop import ChatLoop

# Create chat interface
chat = ChatLoop(
    agent=your_agent,
    name="My Agent",
    description="Agent description",
    config_path=Path("~/.chatrc")  # Optional
)

# Run interactive loop
chat.run()
```

## Requirements

### Core Dependencies

- **Python 3.8+**
- `pyyaml>=6.0.1` - Configuration file parsing
- `rich>=13.7.0` - Enhanced terminal rendering
- `python-dotenv>=1.0.0` - Environment variable management

### Optional Dependencies

- `pyreadline3>=3.4.1` - Command history on Windows (install with `[windows]`)
- `anthropic-bedrock>=0.8.0` - AWS Bedrock integration (install with `[bedrock]`)

### Built-in Features

- `readline` (built-in on Unix) - Command history on macOS/Linux

## Platform Support

- ✅ **macOS** - Full support with native readline
- ✅ **Linux** - Full support with native readline
- ✅ **Windows** - Full support with `pip install basic-agent-chat-loop[windows]`

## Architecture

```
src/basic_agent_chat_loop/
├── chat_loop.py          # Main orchestration
├── chat_config.py        # Configuration management
├── cli.py                # CLI entry point
├── components/           # Modular components
│   ├── ui_components.py      # Colors, StatusBar
│   ├── token_tracker.py      # Token/cost tracking
│   ├── template_manager.py   # Prompt templates
│   ├── display_manager.py    # Display formatting
│   ├── agent_loader.py       # Agent loading
│   └── alias_manager.py      # Alias management
docs/
├── ALIASES.md            # Alias system guide
├── CONFIG.md             # Configuration reference
├── INSTALL.md            # Installation instructions
└── Chat_TODO.md          # Roadmap and future features
```

## Documentation

- [docs/ALIASES.md](docs/ALIASES.md) - Agent alias system guide
- [docs/CONFIG.md](docs/CONFIG.md) - Configuration reference
- [docs/INSTALL.md](docs/INSTALL.md) - Installation instructions
- [docs/Chat_TODO.md](docs/Chat_TODO.md) - Roadmap and future features

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

### Latest Release: v0.1.0 (2025-10-09)

Initial public release with:
- 🏷️ Agent alias system
- 📝 Prompt templates with auto-setup
- 💰 Token tracking and cost estimation
- ⚙️ YAML configuration with auto-setup
- 📊 Status bar and session summaries
- 🎨 Rich markdown rendering
- 🔄 Automatic error recovery
- 📜 Persistent command history
- ✅ 61% test coverage (158 tests)

## Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common issues and solutions.

**Quick fixes:**
- **Package not found**: Run `pip install --upgrade basic-agent-chat-loop`
- **Command not found**: Ensure pip's bin directory is in your PATH
- **Import errors**: Try reinstalling with `pip install --force-reinstall basic-agent-chat-loop`

## Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/issues)
- 💡 **Feature Requests**: [GitHub Issues](https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/issues)
- 📖 **Documentation**: [docs/](docs/)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/discussions)
