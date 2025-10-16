#!/usr/bin/env python3
"""
Basic Agent Chat Loop - Interactive CLI for AI Agents

A feature-rich, unified chat interface for any AI agent with token tracking,
prompt templates, configuration management, and extensive UX enhancements.

Features:
- Async streaming support with real-time response display
- Command history with readline (↑↓ to navigate, saved to ~/.chat_history)
- Agent logs saved to ~/.chat_loop_logs/<agent_name>_chat.log
- Multi-line input support (type \\\\ to enter multi-line mode)
- Token tracking and cost estimation per query and session
- Prompt templates from ~/.prompts/ with variable substitution
- Configuration file support (~/.chatrc or .chatrc in project root)
- Status bar with real-time metrics (queries, tokens, duration)
- Session summary on exit with full statistics
- Automatic error recovery with retry logic
- Rich markdown rendering with syntax highlighting
- Agent metadata display (model, tools, capabilities)

Usage:
    chat_loop path/to/agent.py
    chat_loop my_agent_alias
    chat_loop <agent_path> --config ~/.chatrc-custom
"""

import argparse
import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import readline

    READLINE_AVAILABLE = True
except ImportError:
    READLINE_AVAILABLE = False


# Components
# Configuration management
from .chat_config import ChatConfig, get_config
from .components import (
    AliasManager,
    Colors,
    DependencyManager,
    DisplayManager,
    StatusBar,
    TemplateManager,
    TokenTracker,
    extract_agent_metadata,
    load_agent_module,
    load_environment_variables,
)

# Rich library for better formatting
try:
    from rich.console import Console
    from rich.live import Live
    from rich.markdown import Markdown
    from rich.spinner import Spinner

    RICH_AVAILABLE = True
    ConsoleType = Console
    MarkdownType = Markdown
except ImportError:
    RICH_AVAILABLE = False
    ConsoleType = None  # type: ignore
    MarkdownType = None  # type: ignore

# Setup logging directory in home directory for easy access
# Default: ~/.chat_loop_logs/
log_dir = Path.home() / ".chat_loop_logs"

# Command history configuration
READLINE_HISTORY_LENGTH = 1000

# Use a single consistent logger throughout the module
logger = logging.getLogger("basic_agent_chat_loop")


def setup_logging(agent_name: str) -> bool:
    """
    Setup logging with agent-specific filename.

    Args:
        agent_name: Name of the agent for the log file

    Returns:
        True if logging was successfully configured, False otherwise
    """
    try:
        # Ensure log directory exists
        log_dir.mkdir(exist_ok=True)

        # Create log file path with sanitized agent name
        safe_name = agent_name.lower().replace(" ", "_").replace("/", "_")
        log_file = log_dir / f"{safe_name}_chat.log"

        # Configure our logger
        logger.setLevel(logging.INFO)

        # Remove any existing handlers to avoid duplicates
        logger.handlers = []

        # Add file handler with formatting
        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)

        # Also add console handler for errors (stderr only)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(console_handler)

        logger.info(f"Logging initialized for agent: {agent_name}")
        logger.info(f"Log file: {log_file}")
        return True

    except Exception as e:
        # Fallback: print to stderr if logging setup fails
        print(f"Warning: Could not setup logging: {e}", file=sys.stderr)
        # Set up minimal console-only logging as fallback
        logger.setLevel(logging.WARNING)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(console_handler)
        return False


def setup_readline_history() -> Optional[Path]:
    """
    Setup readline command history with persistence.

    Returns:
        Path to history file if successful, None otherwise
    """
    if not READLINE_AVAILABLE:
        logger.debug("Readline not available, history will not be saved")
        return None

    try:
        # History file in user's home directory
        history_file = Path.home() / ".chat_history"

        # Set history length
        readline.set_history_length(READLINE_HISTORY_LENGTH)

        # Enable tab completion and better editing
        try:
            # Suppress CPR warning by redirecting stderr temporarily
            old_stderr = sys.stderr
            sys.stderr = open(os.devnull, "w")

            try:
                # Parse readline init file if it exists
                readline.parse_and_bind("tab: complete")

                # Enable vi or emacs mode (emacs is default)
                readline.parse_and_bind("set editing-mode emacs")

                # Disable horizontal scroll to prevent CPR check
                readline.parse_and_bind("set horizontal-scroll-mode off")

                # Enable better line editing
                readline.parse_and_bind("set show-all-if-ambiguous on")
                readline.parse_and_bind("set completion-ignore-case on")
            finally:
                # Restore stderr
                sys.stderr.close()
                sys.stderr = old_stderr
        except Exception as e:
            logger.debug(f"Could not configure readline bindings: {e}")
            # Continue anyway, basic history will still work

        # Load existing history
        if history_file.exists():
            try:
                readline.read_history_file(str(history_file))
                count = readline.get_current_history_length()
                logger.debug(f"Loaded {count} history entries")
            except Exception as e:
                logger.warning(f"Could not load history from {history_file}: {e}")
                # Continue anyway, we'll create new history

        logger.debug(f"Command history will be saved to: {history_file}")
        return history_file

    except Exception as e:
        logger.warning(f"Could not setup command history: {e}")
        return None


def save_readline_history(history_file: Optional[Path]) -> bool:
    """
    Save readline command history.

    Args:
        history_file: Path to history file

    Returns:
        True if history was successfully saved, False otherwise
    """
    if not history_file:
        return False

    if not READLINE_AVAILABLE:
        return False

    try:
        # Ensure parent directory exists
        history_file.parent.mkdir(parents=True, exist_ok=True)

        # Save history
        readline.write_history_file(str(history_file))

        # Set secure permissions (readable/writable by owner only)
        history_file.chmod(0o600)

        count = readline.get_current_history_length()
        logger.debug(f"Saved {count} history entries to {history_file}")
        return True

    except Exception as e:
        logger.warning(f"Could not save command history to {history_file}: {e}")
        return False


class ChatLoop:
    """Generic chat loop for any AI agent with async streaming support."""

    def __init__(
        self,
        agent,
        agent_name: str,
        agent_description: str,
        agent_factory=None,
        config: Optional["ChatConfig"] = None,
    ):
        self.agent = agent
        self.agent_name = agent_name
        self.agent_description = agent_description
        self.agent_factory = agent_factory  # Function to create fresh agent instance
        self.history_file = None
        self.last_response = ""  # Track last response for copy command

        # Conversation tracking for auto-save
        self.conversation_history: list[Dict[str, Any]] = []

        # Load or use provided config
        self.config = config if config else get_config()

        # Apply configuration values (with agent-specific overrides)
        if self.config:
            self.max_retries = int(
                self.config.get("behavior.max_retries", 3, agent_name=agent_name)
            )
            self.retry_delay = float(
                self.config.get("behavior.retry_delay", 2.0, agent_name=agent_name)
            )
            self.timeout = float(
                self.config.get("behavior.timeout", 120.0, agent_name=agent_name)
            )
            self.spinner_style = self.config.get(
                "behavior.spinner_style", "dots", agent_name=agent_name
            )

            # Feature flags
            self.auto_save = self.config.get(
                "features.auto_save", False, agent_name=agent_name
            )
            self.show_metadata = self.config.get(
                "features.show_metadata", True, agent_name=agent_name
            )
            self.show_thinking = self.config.get(
                "ui.show_thinking_indicator", True, agent_name=agent_name
            )
            self.show_duration = self.config.get(
                "ui.show_duration", True, agent_name=agent_name
            )
            self.show_banner = self.config.get(
                "ui.show_banner", True, agent_name=agent_name
            )

            # Rich override
            rich_enabled = self.config.get(
                "features.rich_enabled", True, agent_name=agent_name
            )
            self.use_rich = RICH_AVAILABLE and rich_enabled
        else:
            # Defaults when no config
            self.max_retries = 3
            self.retry_delay = 2.0
            self.timeout = 120.0
            self.spinner_style = "dots"
            self.auto_save = False
            self.show_metadata = True
            self.show_thinking = True
            self.show_duration = True
            self.show_banner = True
            self.use_rich = RICH_AVAILABLE

        # Setup rich console if available and enabled
        self.console: Optional[Console] = Console() if self.use_rich else None

        # Extract agent metadata
        self.agent_metadata = extract_agent_metadata(self.agent)

        # Setup prompt templates directory
        self.prompts_dir = Path.home() / ".prompts"

        # Create template manager
        self.template_manager = TemplateManager(self.prompts_dir)

        # Setup token tracking (always enabled for session summary)
        self.show_tokens = (
            self.config.get("features.show_tokens", False, agent_name=agent_name)
            if self.config
            else False
        )
        model_for_pricing = self.agent_metadata.get("model_id", "Unknown")

        # Check for config override
        if self.config:
            model_override = self.config.get(
                "agents." + agent_name + ".model_display_name", None
            )
            if model_override:
                model_for_pricing = model_override

        # Always create token tracker for session summary
        # (not just when show_tokens is true)
        self.token_tracker = TokenTracker(model_for_pricing)

        # Track session start time for summary
        self.session_start_time = time.time()
        self.query_count = 0

        # Setup status bar if enabled
        self.show_status_bar_enabled = (
            self.config.get("ui.show_status_bar", False, agent_name=agent_name)
            if self.config
            else False
        )
        self.status_bar = None
        if self.show_status_bar_enabled:
            model_info = self.agent_metadata.get("model_id", "Unknown Model")

            # Check for config override
            if self.config:
                model_override = self.config.get(
                    "agents." + agent_name + ".model_display_name", None
                )
                if model_override:
                    model_info = model_override

            # Shorten long model IDs
            if len(model_info) > 30:
                model_info = model_info[:27] + "..."

            self.status_bar = StatusBar(
                agent_name, model_info, show_tokens=self.show_tokens
            )

            # Log for debugging
            logger.debug(
                f"Status bar initialized: agent={agent_name}, "
                f"model={model_info}, show_tokens={self.show_tokens}"
            )

        # Create display manager
        self.display_manager = DisplayManager(
            agent_name=self.agent_name,
            agent_description=self.agent_description,
            agent_metadata=self.agent_metadata,
            show_banner=self.show_banner,
            show_metadata=self.show_metadata,
            use_rich=self.use_rich,
            auto_save=self.auto_save,
            config=self.config,
            status_bar=self.status_bar,
        )

    def _extract_token_usage(self, response_obj) -> Optional[Dict[str, int]]:
        """
        Extract token usage from response object.

        Args:
            response_obj: Response object from agent

        Returns:
            Dict with 'input_tokens' and 'output_tokens', or None if not available
        """
        if not response_obj:
            return None

        # Try common attribute patterns
        usage = None

        # Pattern 1: response['result'].metrics.accumulated_usage (AWS Bedrock style)
        if isinstance(response_obj, dict) and "result" in response_obj:
            result = response_obj["result"]
            if hasattr(result, "metrics") and hasattr(
                result.metrics, "accumulated_usage"
            ):
                usage = result.metrics.accumulated_usage

        # Pattern 2: response.usage (Anthropic/Claude style)
        elif hasattr(response_obj, "usage"):
            usage = response_obj.usage

        # Pattern 3: response['usage'] (dict style)
        elif isinstance(response_obj, dict) and "usage" in response_obj:
            usage = response_obj["usage"]

        # Pattern 4: response.metadata.usage
        elif hasattr(response_obj, "metadata") and hasattr(
            response_obj.metadata, "usage"
        ):
            usage = response_obj.metadata.usage

        # Pattern 5: response.data.usage (streaming event)
        elif hasattr(response_obj, "data") and hasattr(response_obj.data, "usage"):
            usage = response_obj.data.usage

        # Pattern 6: response.data['usage'] (streaming event dict)
        elif (
            hasattr(response_obj, "data")
            and isinstance(response_obj.data, dict)
            and "usage" in response_obj.data
        ):
            usage = response_obj.data["usage"]

        if not usage:
            return None

        # Extract input and output tokens
        input_tokens = 0
        output_tokens = 0

        # Try different attribute names (check dict keys first, then attributes)
        if isinstance(usage, dict):
            # AWS Bedrock camelCase
            if "inputTokens" in usage:
                input_tokens = usage["inputTokens"]
            elif "input_tokens" in usage:
                input_tokens = usage["input_tokens"]
            elif "prompt_tokens" in usage:
                input_tokens = usage["prompt_tokens"]

            if "outputTokens" in usage:
                output_tokens = usage["outputTokens"]
            elif "output_tokens" in usage:
                output_tokens = usage["output_tokens"]
            elif "completion_tokens" in usage:
                output_tokens = usage["completion_tokens"]
        else:
            # Object attributes
            if hasattr(usage, "input_tokens"):
                input_tokens = usage.input_tokens
            elif hasattr(usage, "prompt_tokens"):
                input_tokens = usage.prompt_tokens

            if hasattr(usage, "output_tokens"):
                output_tokens = usage.output_tokens
            elif hasattr(usage, "completion_tokens"):
                output_tokens = usage.completion_tokens

        if input_tokens > 0 or output_tokens > 0:
            return {"input_tokens": input_tokens, "output_tokens": output_tokens}

        return None

    def save_conversation(self) -> bool:
        """
        Save conversation history to markdown file.

        Returns:
            True if save was successful, False otherwise
        """
        # Only save if there's conversation history
        if not self.conversation_history:
            logger.debug("No conversation history to save")
            return False

        try:
            # Get save location from config or use default
            save_location = (
                self.config.expand_path(
                    self.config.get("paths.save_location", "~/agent-conversations")
                )
                if self.config
                else Path.home() / "agent-conversations"
            )

            # Ensure directory exists
            save_location.mkdir(parents=True, exist_ok=True)

            # Generate filename with timestamp
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_agent_name = self.agent_name.lower()
            safe_agent_name = safe_agent_name.replace(" ", "_").replace("/", "_")
            filename = f"{safe_agent_name}_{timestamp}.md"
            filepath = save_location / filename

            # Format conversation as markdown
            content_lines = [
                f"# {self.agent_name} Conversation",
                f"\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"\n**Agent:** {self.agent_name}",
                f"\n**Description:** {self.agent_description}",
                f"\n**Total Queries:** {len(self.conversation_history)}",
                "\n---\n",
            ]

            # Add each conversation entry
            for i, entry in enumerate(self.conversation_history, 1):
                ts = entry["timestamp"]
                entry_timestamp = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
                duration = entry.get("duration", 0)

                # Add query
                content_lines.append(f"\n## Query {i} ({entry_timestamp})\n")
                content_lines.append(f"**You:** {entry['query']}\n")

                # Add response
                content_lines.append(f"\n**{self.agent_name}:** {entry['response']}\n")

                # Add metadata
                metadata_parts = [f"Time: {duration:.1f}s"]

                # Add token info if available
                usage = entry.get("usage")
                if usage and usage is not None:
                    input_tok = usage.get("input_tokens", 0)
                    output_tok = usage.get("output_tokens", 0)
                    total_tok = input_tok + output_tok
                    if total_tok > 0:
                        tok_str = f"Tokens: {total_tok:,} "
                        tok_str += f"(in: {input_tok:,}, out: {output_tok:,})"
                        metadata_parts.append(tok_str)

                if metadata_parts:
                    content_lines.append(f"\n*{' | '.join(metadata_parts)}*\n")

                content_lines.append("\n---\n")

            # Write to file
            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(content_lines)

            # Set secure permissions (readable/writable by owner only)
            filepath.chmod(0o600)

            logger.info(f"Conversation saved to: {filepath}")
            print(Colors.success(f"\n💾 Conversation saved to: {filepath}"))
            return True

        except Exception as e:
            logger.warning(f"Failed to save conversation: {e}")
            print(Colors.error(f"\n⚠️  Could not save conversation: {e}"))
            return False

    async def get_multiline_input(self) -> str:
        """Get multi-line input from user. Empty line submits."""
        lines = []
        print(Colors.system("Multi-line mode (empty line to submit):"))

        while True:
            # Don't use executor - it breaks readline editing
            line = input(Colors.user("... "))

            if not line.strip():  # Empty line submits
                break

            lines.append(line)

        return "\n".join(lines)

    async def _show_thinking_indicator(self, stop_event: asyncio.Event):
        """Show thinking indicator while waiting for response."""
        if not self.show_thinking:
            # Just wait silently
            while not stop_event.is_set():
                await asyncio.sleep(0.1)
            return

        if not self.use_rich:
            # Fallback to simple dots animation
            print(Colors.system("Thinking"), end="", flush=True)
            dot_count = 0
            while not stop_event.is_set():
                print(".", end="", flush=True)
                dot_count += 1
                if dot_count >= 3:
                    print("\b\b\b   \b\b\b", end="", flush=True)  # Clear dots
                    dot_count = 0
                await asyncio.sleep(0.5)
            print("\r" + " " * 15 + "\r", end="", flush=True)  # Clear line
        else:
            # Use rich spinner with configured style
            spinner_style = (
                self.spinner_style if hasattr(self, "spinner_style") else "dots"
            )
            with Live(
                Spinner(spinner_style, text=Colors.system("Thinking...")),
                console=self.console,
                refresh_per_second=10,
            ):
                while not stop_event.is_set():
                    await asyncio.sleep(0.1)

    async def _stream_agent_response(self, query: str) -> Dict[str, Any]:
        """
        Stream agent response asynchronously.

        Returns:
            Dict with 'duration' and optional 'usage' (input_tokens, output_tokens)
        """
        start_time = time.time()
        response_text = []  # Collect response for rich rendering
        response_obj = None  # Store the response object for token extraction

        # Agent name in blue
        print(f"\n{Colors.agent(self.agent_name)}: ", end="", flush=True)

        # Setup thinking indicator
        stop_thinking = asyncio.Event()
        thinking_task = None

        try:
            # Start thinking indicator if enabled
            if self.show_thinking:
                thinking_task = asyncio.create_task(
                    self._show_thinking_indicator(stop_thinking)
                )

            first_token_received = False

            # Check if agent supports streaming
            if hasattr(self.agent, "stream_async"):
                async for event in self.agent.stream_async(query):
                    # Store last event for token extraction
                    response_obj = event

                    # Stop thinking indicator on first token
                    if not first_token_received:
                        stop_thinking.set()
                        if thinking_task:
                            await thinking_task
                        first_token_received = True

                    # Handle different event types
                    if hasattr(event, "data"):
                        data = event.data
                        if isinstance(data, str):
                            response_text.append(data)
                            if self.use_rich:
                                # Don't print during streaming, render at end
                                pass
                            else:
                                print(data, end="", flush=True)
                        elif isinstance(data, dict):
                            # Handle structured data
                            if "text" in data:
                                text = data["text"]
                                response_text.append(text)
                                if not self.use_rich:
                                    print(text, end="", flush=True)
                            elif "content" in data:
                                content = data["content"]
                                if isinstance(content, list):
                                    for block in content:
                                        if isinstance(block, dict) and "text" in block:
                                            text = block["text"]
                                            response_text.append(text)
                                            if not self.use_rich:
                                                print(text, end="", flush=True)
                                else:
                                    text = str(content)
                                    response_text.append(text)
                                    if not self.use_rich:
                                        print(text, end="", flush=True)
            else:
                # Fallback to synchronous call if streaming not supported
                response = await asyncio.get_event_loop().run_in_executor(
                    None, self.agent, query
                )
                response_obj = response  # Store for token extraction

                # Stop thinking indicator
                stop_thinking.set()
                if thinking_task:
                    await thinking_task

                # Format and display response
                if hasattr(response, "message"):
                    message = response.message
                    if isinstance(message, dict) and "content" in message:
                        content = message["content"]
                        if isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and "text" in block:
                                    response_text.append(block["text"])
                        else:
                            response_text.append(str(content))
                    else:
                        response_text.append(str(message))
                else:
                    response_text.append(str(response))

            # Render collected response
            full_response = "".join(response_text)
            self.last_response = full_response

            if self.use_rich and full_response.strip() and self.console:
                # Use rich markdown rendering
                print()  # New line after agent name
                md = Markdown(full_response)
                self.console.print(md)
            elif not self.use_rich and response_text:
                # Already printed during streaming, just add newline
                if not first_token_received:
                    # Non-streaming case where nothing was printed yet
                    print(full_response)

            duration = time.time() - start_time

            # Extract token usage if available
            usage_info = self._extract_token_usage(response_obj)

            # Extract additional metrics (framework-specific)
            cycle_count = None
            tool_count = None
            if isinstance(response_obj, dict) and "result" in response_obj:
                result = response_obj["result"]
                if hasattr(result, "metrics"):
                    metrics = result.metrics
                    if hasattr(metrics, "cycle_count"):
                        cycle_count = metrics.cycle_count
                    if hasattr(metrics, "tool_metrics") and metrics.tool_metrics:
                        # Count total tool calls across all tools
                        try:
                            if isinstance(metrics.tool_metrics, dict):
                                tool_count = sum(
                                    len(calls)
                                    for calls in metrics.tool_metrics.values()
                                )
                            elif hasattr(metrics.tool_metrics, "__len__"):
                                tool_count = len(metrics.tool_metrics)
                            elif hasattr(metrics.tool_metrics, "__dict__"):
                                # ToolMetrics object - count attributes
                                # that look like tool calls
                                tool_count = len(
                                    [
                                        k
                                        for k in metrics.tool_metrics.__dict__.keys()
                                        if not k.startswith("_")
                                    ]
                                )
                        except Exception as e:
                            logger.debug(f"Could not extract tool count: {e}")
                            tool_count = None

            # Track tokens (always, for session summary)
            if usage_info:
                self.token_tracker.add_usage(
                    usage_info["input_tokens"], usage_info["output_tokens"]
                )

                # Update status bar
                if self.status_bar:
                    self.status_bar.update_tokens(self.token_tracker.get_total_tokens())

            # Increment query count for session summary
            self.query_count += 1

            # Display duration and token info
            # Determine what to show
            show_info_line = (
                self.show_duration
                or (self.show_tokens and usage_info)
                or cycle_count
                or tool_count
            )

            if show_info_line:
                print(f"\n{Colors.DIM}{'-' * 60}{Colors.RESET}")

                info_parts = []
                if self.show_duration:
                    info_parts.append(f"Time: {duration:.1f}s")

                # Show agent metrics (cycles, tools) - always show if available
                if cycle_count is not None and cycle_count > 0:
                    cycle_word = "cycle" if cycle_count == 1 else "cycles"
                    info_parts.append(f"{cycle_count} {cycle_word}")

                if tool_count is not None and tool_count > 0:
                    tool_word = "tool" if tool_count == 1 else "tools"
                    info_parts.append(f"{tool_count} {tool_word}")

                # Only show tokens if show_tokens is enabled
                if self.show_tokens and usage_info:
                    input_tok = usage_info["input_tokens"]
                    output_tok = usage_info["output_tokens"]
                    total_tok = input_tok + output_tok

                    # Format tokens
                    token_str = (
                        f"Tokens: {self.token_tracker.format_tokens(total_tok)} "
                    )
                    token_str += f"(in: {self.token_tracker.format_tokens(input_tok)}, "
                    token_str += f"out: {self.token_tracker.format_tokens(output_tok)})"
                    info_parts.append(token_str)

                    # Show cost (session total)
                    cost = self.token_tracker.get_cost()
                    if cost > 0:
                        info_parts.append(f"Cost: {self.token_tracker.format_cost()}")

                if info_parts:  # Only print if we have something to show
                    print(Colors.system(" │ ".join(info_parts)))

            logger.info(f"Query completed successfully in {duration:.1f}s")

            # Track conversation for auto-save if enabled
            if self.auto_save:
                self.conversation_history.append(
                    {
                        "timestamp": time.time(),
                        "query": query,
                        "response": full_response,
                        "duration": duration,
                        "usage": usage_info,
                    }
                )

            return {"duration": duration, "usage": usage_info}

        except Exception as e:
            # Cleanup thinking indicator on error
            stop_thinking.set()
            if thinking_task and not thinking_task.done():
                await thinking_task

            duration = time.time() - start_time
            print(f"\n{Colors.DIM}{'-' * 60}{Colors.RESET}")
            print(Colors.error(f"{self.agent_name}: Query failed - {e}"))
            print(
                Colors.system(
                    "Try rephrasing your question or check the logs for details."
                )
            )
            logger.error(
                f"Agent query failed after {duration:.1f}s: {e}", exc_info=True
            )

            return {"duration": duration, "usage": None}

    async def process_query(self, query: str):
        """Process query through agent with streaming and error recovery."""
        for attempt in range(1, self.max_retries + 1):
            try:
                await self._stream_agent_response(query)
                return  # Success, exit retry loop

            except asyncio.TimeoutError:
                print(
                    Colors.error(f"\n⚠️  Timeout (attempt {attempt}/{self.max_retries})")
                )
                if attempt < self.max_retries:
                    print(Colors.system(f"Retrying in {self.retry_delay}s..."))
                    await asyncio.sleep(self.retry_delay)
                    logger.warning(f"Timeout on attempt {attempt}, retrying...")
                else:
                    print(Colors.error("Max retries reached. Please try again later."))
                    logger.error("Max retries reached after timeout")

            except ConnectionError as e:
                print(Colors.error(f"\n⚠️  Connection error: {e}"))
                if attempt < self.max_retries:
                    print(Colors.system(f"Retrying in {self.retry_delay}s..."))
                    await asyncio.sleep(self.retry_delay)
                    logger.warning(
                        f"Connection error on attempt {attempt}, retrying..."
                    )
                else:
                    print(
                        Colors.error(
                            "Max retries reached. Check your network connection."
                        )
                    )
                    logger.error(f"Max retries reached after connection error: {e}")

            except Exception as e:
                # For other exceptions, don't retry - they're likely not transient
                error_msg = str(e)

                # Check for rate limit errors
                if "rate" in error_msg.lower() or "429" in error_msg:
                    print(Colors.error("\n⚠️  Rate limit reached"))
                    if attempt < self.max_retries:
                        wait_time = self.retry_delay * (
                            2 ** (attempt - 1)
                        )  # Exponential backoff
                        print(
                            Colors.system(f"Waiting {wait_time:.0f}s before retry...")
                        )
                        await asyncio.sleep(wait_time)
                        logger.warning(
                            f"Rate limit on attempt {attempt}, backing off..."
                        )
                    else:
                        print(
                            Colors.error(
                                "Rate limit persists. Please wait and try again."
                            )
                        )
                        logger.error("Max retries reached due to rate limiting")
                else:
                    # Non-retryable error, log and exit
                    logger.error(f"Non-retryable error: {e}", exc_info=True)
                    raise

    async def _async_run(self):
        """Async implementation of the chat loop."""
        # Setup readline history
        self.history_file = setup_readline_history()

        self.display_manager.display_banner()

        try:
            while True:
                try:
                    # Get user input directly (blocking is fine for user input)
                    # Don't use executor as it breaks readline editing
                    user_input = input(f"\n{Colors.user('You')}: ").strip()

                    # Handle commands
                    if user_input.lower() in ["exit", "quit", "bye"]:
                        print(
                            Colors.system(
                                f"\nGoodbye! Thanks for using {self.agent_name}!"
                            )
                        )
                        break
                    elif user_input.lower() == "help":
                        self.display_manager.display_help()
                        continue
                    elif user_input.lower() == "info":
                        self.display_manager.display_info()
                        continue
                    elif user_input.lower() == "templates":
                        # List available prompt templates
                        templates = (
                            self.template_manager.list_templates_with_descriptions()
                        )
                        self.display_manager.display_templates(
                            templates, self.prompts_dir
                        )
                        continue
                    elif user_input.startswith("/") and len(user_input) > 1:
                        # Template command: /template_name <optional input>
                        parts = user_input[1:].split(maxsplit=1)
                        template_name = parts[0]
                        input_text = parts[1] if len(parts) > 1 else ""

                        # Try to load template
                        template = self.template_manager.load_template(
                            template_name, input_text
                        )
                        if template:
                            print(Colors.system(f"✓ Loaded template: {template_name}"))
                            # Use the template as the user input
                            user_input = template
                        else:
                            print(Colors.error(f"Template not found: {template_name}"))
                            templates = self.template_manager.list_templates()
                            tmpl_list = ", ".join(templates) or "none"
                            print(f"Available templates: {tmpl_list}")
                            print(f"Create at: {self.prompts_dir}/{template_name}.md")
                            continue
                    elif user_input.lower() == "clear":
                        # Clear screen (cross-platform)
                        os.system("clear" if os.name != "nt" else "cls")

                        # Reset agent session if factory available
                        if self.agent_factory:
                            try:
                                # Cleanup old agent if possible
                                if hasattr(self.agent, "cleanup"):
                                    try:
                                        if asyncio.iscoroutinefunction(
                                            self.agent.cleanup
                                        ):
                                            await self.agent.cleanup()
                                        else:
                                            self.agent.cleanup()
                                    except Exception as e:
                                        logger.debug(f"Error during agent cleanup: {e}")

                                # Create fresh agent instance
                                self.agent = self.agent_factory()
                                print(
                                    Colors.success(
                                        "✓ Screen cleared and agent session reset"
                                    )
                                )
                                logger.info("Agent session reset via clear command")
                            except Exception as e:
                                print(
                                    Colors.error(
                                        f"⚠️  Could not reset agent session: {e}"
                                    )
                                )
                                logger.error(f"Failed to reset agent session: {e}")
                                print(
                                    Colors.system(
                                        "Screen cleared but agent session maintained"
                                    )
                                )
                        else:
                            print(Colors.success("✓ Screen cleared"))

                        self.display_manager.display_banner()
                        continue
                    elif user_input == "\\\\":  # Multi-line input trigger
                        user_input = await self.get_multiline_input()
                        if not user_input.strip():
                            continue
                    elif not user_input:
                        continue

                    # Process query through agent
                    logger.info(f"Processing query: {user_input[:100]}...")

                    # Update status bar before query
                    if self.status_bar:
                        self.status_bar.increment_query()
                        # Clear screen and redraw status bar
                        print("\033[2J\033[H", end="")  # Clear screen, move to top
                        print(self.status_bar.render())
                        print()  # Blank line after status bar

                    await self.process_query(user_input)

                except KeyboardInterrupt:
                    print(
                        Colors.system(
                            f"\n\nChat interrupted. Thanks for using {self.agent_name}!"
                        )
                    )
                    break
                except EOFError:
                    print(
                        Colors.system(
                            f"\n\nChat ended. Thanks for using {self.agent_name}!"
                        )
                    )
                    break

        finally:
            # Save command history
            save_readline_history(self.history_file)

            # Save conversation if auto-save is enabled
            if self.auto_save:
                self.save_conversation()

            # Cleanup agent if it has cleanup method
            if hasattr(self.agent, "cleanup"):
                try:
                    if asyncio.iscoroutinefunction(self.agent.cleanup):
                        await self.agent.cleanup()
                    else:
                        self.agent.cleanup()
                except Exception as e:
                    logger.warning(f"Error during agent cleanup: {e}")

            # Display session summary
            self.display_manager.display_session_summary(
                self.session_start_time, self.query_count, self.token_tracker
            )

            print(Colors.success(f"\n{self.agent_name} session complete!"))

    def run(self):
        """Run the interactive chat loop."""
        try:
            asyncio.run(self._async_run())
        except KeyboardInterrupt:
            print(f"\n\nChat interrupted. Thanks for using {self.agent_name}!")
        except Exception as e:
            logger.error(f"Fatal error in chat loop: {e}", exc_info=True)
            print(f"\nFatal error: {e}")


def main():
    """Main entry point for the chat loop."""
    # Load environment variables FIRST, before any imports or parsing
    # This ensures credentials are available when agent modules are loaded
    env_path = load_environment_variables()

    parser = argparse.ArgumentParser(
        description=(
            "Interactive CLI for AI Agents with token tracking "
            "and rich features"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run with agent path
    chat_loop path/to/agent.py

    # Run with alias
    chat_loop my_agent

    # Auto-install dependencies
    chat_loop my_agent --auto-setup
    chat_loop path/to/agent.py -a

    # Alias management
    chat_loop --save-alias my_agent path/to/agent.py
    chat_loop --list-aliases
    chat_loop --remove-alias my_agent
        """,
    )

    # Import version for --version flag
    try:
        from . import __version__

        version_string = f"%(prog)s {__version__}"
    except ImportError:
        version_string = "%(prog)s (version unknown)"

    parser.add_argument(
        "--version",
        action="version",
        version=version_string,
    )

    parser.add_argument("agent", nargs="?", help="Agent path or alias name")

    parser.add_argument(
        "--config", help="Path to configuration file (default: ~/.chatrc or .chatrc)"
    )

    # Alias management commands
    alias_group = parser.add_argument_group("alias management")

    alias_group.add_argument(
        "--save-alias",
        nargs=2,
        metavar=("ALIAS", "PATH"),
        help="Save an agent alias: --save-alias pete path/to/agent.py",
    )

    alias_group.add_argument(
        "--list-aliases", action="store_true", help="List all saved aliases"
    )

    alias_group.add_argument(
        "--remove-alias", metavar="ALIAS", help="Remove an alias: --remove-alias pete"
    )

    alias_group.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing alias when using --save-alias",
    )

    # Dependency management
    parser.add_argument(
        "--auto-setup",
        "-a",
        action="store_true",
        help=(
            "Automatically install agent dependencies "
            "(requirements.txt, pyproject.toml)"
        ),
    )

    args = parser.parse_args()

    # Handle alias management commands
    alias_manager = AliasManager()

    if args.save_alias:
        alias_name, agent_path = args.save_alias
        success, message = alias_manager.add_alias(
            alias_name, agent_path, overwrite=args.overwrite
        )
        if success:
            print(Colors.success(message))
            sys.exit(0)
        else:
            print(Colors.error(message))
            sys.exit(1)

    if args.list_aliases:
        aliases = alias_manager.list_aliases()
        if aliases:
            print(f"\n{Colors.system('Saved Agent Aliases')} ({len(aliases)}):")
            print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")
            for alias_name, agent_path in sorted(aliases.items()):
                # Check if path still exists
                if Path(agent_path).exists():
                    print(f"  {Colors.success(alias_name):<20} → {agent_path}")
                else:
                    status = f"{Colors.YELLOW}(missing){Colors.RESET}"
                    print(f"  {Colors.error(alias_name):<20} → {agent_path} {status}")
            print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")
            print(f"\nUsage: {Colors.system('chat_loop <alias>')}")
        else:
            print(f"\n{Colors.system('No aliases saved yet')}")
            print("\nCreate an alias with:")
            print(f"  {Colors.system('chat_loop --save-alias <name> <path>')}")
        sys.exit(0)

    if args.remove_alias:
        success, message = alias_manager.remove_alias(args.remove_alias)
        if success:
            print(Colors.success(message))
            sys.exit(0)
        else:
            print(Colors.error(message))
            sys.exit(1)

    # Require agent argument if not doing alias management
    if not args.agent:
        print(Colors.error("Error: Agent path or alias required"))
        print()
        print("Usage:")
        print(f"  {Colors.system('chat_loop <agent_path>')}")
        print(f"  {Colors.system('chat_loop <alias>')}")
        print()
        print("Alias Management:")
        print(f"  {Colors.system('chat_loop --save-alias <name> <path>')}")
        print(f"  {Colors.system('chat_loop --list-aliases')}")
        print(f"  {Colors.system('chat_loop --remove-alias <name>')}")
        sys.exit(1)

    # Resolve agent path (try as path first, then as alias)
    agent_path = alias_manager.resolve_agent_path(args.agent)

    if not agent_path:
        print(Colors.error(f"Error: Agent not found: {args.agent}"))
        print()
        print("Not found as:")
        print(f"  • File path: {args.agent}")
        print(f"  • Alias name: {args.agent}")
        print()
        print("Available aliases:")
        aliases = alias_manager.list_aliases()
        if aliases:
            for alias_name in sorted(aliases.keys()):
                print(f"  • {alias_name}")
        else:
            print("  (none)")
        sys.exit(1)

    # Handle dependency installation if requested
    dep_manager = DependencyManager(agent_path)

    if args.auto_setup:
        # User explicitly requested dependency installation
        dep_info = dep_manager.detect_dependency_file()
        if dep_info:
            file_type, file_path = dep_info
            print(
                Colors.system(f"📦 Found {file_path.name}, installing dependencies...")
            )
            success, message = dep_manager.install_dependencies(file_type, file_path)
            if success:
                print(Colors.success(message))
            else:
                print(Colors.error(message))
                print(Colors.system("\nContinuing without dependency installation..."))
        else:
            msg = (
                "💡 No dependency files found "
                "(requirements.txt, pyproject.toml, setup.py)"
            )
            print(Colors.system(msg))
    else:
        # Check if dependencies exist and suggest using --auto-setup
        suggestion = dep_manager.suggest_auto_setup()
        if suggestion:
            print(Colors.system(suggestion))
            print()  # Extra spacing

    try:
        # Load configuration FIRST (before any print statements)
        config = None
        config_path = Path(args.config) if args.config else None
        config = get_config(config_path)

        # Apply color configuration immediately
        if config:
            color_config = config.get_section("colors")
            Colors.configure(color_config)

        # Now print messages with colors configured
        if env_path:
            print(Colors.system(f"Loaded environment from: {env_path}"))

        # Show config info
        if config:
            if args.config:
                print(Colors.system(f"Loaded configuration from: {args.config}"))
            else:
                # Check which config file was loaded
                global_config = Path.home() / ".chatrc"
                project_config = Path.cwd() / ".chatrc"
                if project_config.exists():
                    print(Colors.system(f"Loaded configuration from: {project_config}"))
                elif global_config.exists():
                    print(Colors.system(f"Loaded configuration from: {global_config}"))

        # Load the agent
        # Show what we're loading (path or alias)
        if agent_path != args.agent:
            print(Colors.system(f"Resolved alias '{args.agent}' → {agent_path}"))
        print(Colors.system(f"Loading agent from: {agent_path}"))
        agent, agent_name, agent_description = load_agent_module(agent_path)

        # Setup logging with agent name
        setup_logging(agent_name)

        if env_path:
            logger.info(f"Loaded environment from: {env_path}")

        print(Colors.success(f"Agent loaded successfully: {agent_name}"))
        logger.info(f"Agent loaded successfully: {agent_name} - {agent_description}")

        # Create agent factory for session reset
        def create_fresh_agent():
            """Factory function to create a fresh agent instance."""
            new_agent, _, _ = load_agent_module(agent_path)
            return new_agent

        # Start chat loop with config
        chat_loop = ChatLoop(
            agent,
            agent_name,
            agent_description,
            agent_factory=create_fresh_agent,
            config=config,
        )
        chat_loop.run()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
