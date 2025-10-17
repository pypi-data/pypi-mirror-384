import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from pydantic_ai import RunContext
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from textual import events, on, work
from textual.app import ComposeResult
from textual.command import CommandPalette
from textual.containers import Container, Grid
from textual.keys import Keys
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widget import Widget
from textual.widgets import Button, Label, Static

from shotgun.agents.agent_manager import (
    AgentManager,
    ClarifyingQuestionsMessage,
    MessageHistoryUpdated,
    PartialResponseMessage,
)
from shotgun.agents.config import get_provider_model
from shotgun.agents.conversation_history import (
    ConversationHistory,
    ConversationState,
)
from shotgun.agents.conversation_manager import ConversationManager
from shotgun.agents.models import (
    AgentDeps,
    AgentType,
    FileOperationTracker,
)
from shotgun.codebase.core.manager import CodebaseAlreadyIndexedError
from shotgun.codebase.models import IndexProgress, ProgressPhase
from shotgun.posthog_telemetry import track_event
from shotgun.sdk.codebase import CodebaseSDK
from shotgun.sdk.exceptions import CodebaseNotFoundError, InvalidPathError
from shotgun.tui.commands import CommandHandler
from shotgun.tui.filtered_codebase_service import FilteredCodebaseService
from shotgun.tui.screens.chat_screen.hint_message import HintMessage
from shotgun.tui.screens.chat_screen.history import ChatHistory
from shotgun.utils import get_shotgun_home

from ..components.prompt_input import PromptInput
from ..components.spinner import Spinner
from ..utils.mode_progress import PlaceholderHints
from .chat_screen.command_providers import (
    DeleteCodebasePaletteProvider,
    UnifiedCommandProvider,
)

logger = logging.getLogger(__name__)


class PromptHistory:
    def __init__(self) -> None:
        self.prompts: list[str] = ["Hello there!"]
        self.curr: int | None = None

    def next(self) -> str:
        if self.curr is None:
            self.curr = -1
        else:
            self.curr = -1
        return self.prompts[self.curr]

    def prev(self) -> str:
        if self.curr is None:
            raise Exception("current entry is none")
        if self.curr == -1:
            self.curr = None
            return ""
        self.curr += 1
        return ""

    def append(self, text: str) -> None:
        self.prompts.append(text)
        self.curr = None


@dataclass
class CodebaseIndexSelection:
    """User-selected repository path and name for indexing."""

    repo_path: Path
    name: str


class StatusBar(Widget):
    DEFAULT_CSS = """
        StatusBar {
            text-wrap: wrap;
            padding-left: 1;
        }
    """

    def __init__(self, working: bool = False) -> None:
        """Initialize the status bar.

        Args:
            working: Whether an agent is currently working.
        """
        super().__init__()
        self.working = working

    def render(self) -> str:
        # Check if in Q&A mode first (highest priority)
        try:
            chat_screen = self.screen
            if isinstance(chat_screen, ChatScreen) and chat_screen.qa_mode:
                return (
                    "[$foreground-muted][bold $text]esc[/] to exit Q&A mode • "
                    "[bold $text]enter[/] to send answer • [bold $text]ctrl+j[/] for newline[/]"
                )
        except Exception:  # noqa: S110
            # If we can't access chat screen, continue with normal display
            pass

        if self.working:
            return (
                "[$foreground-muted][bold $text]esc[/] to stop • "
                "[bold $text]enter[/] to send • [bold $text]ctrl+j[/] for newline • "
                "[bold $text]ctrl+p[/] command palette • [bold $text]shift+tab[/] cycle modes • "
                "/help for commands[/]"
            )
        else:
            return (
                "[$foreground-muted][bold $text]enter[/] to send • "
                "[bold $text]ctrl+j[/] for newline • [bold $text]ctrl+p[/] command palette • "
                "[bold $text]shift+tab[/] cycle modes • /help for commands[/]"
            )


class ModeIndicator(Widget):
    """Widget to display the current agent mode."""

    DEFAULT_CSS = """
        ModeIndicator {
            text-wrap: wrap;
            padding-left: 1;
        }
    """

    def __init__(self, mode: AgentType) -> None:
        """Initialize the mode indicator.

        Args:
            mode: The current agent type/mode.
        """
        super().__init__()
        self.mode = mode
        self.progress_checker = PlaceholderHints().progress_checker

    def render(self) -> str:
        """Render the mode indicator."""
        # Check if in Q&A mode first
        try:
            chat_screen = self.screen
            if isinstance(chat_screen, ChatScreen) and chat_screen.qa_mode:
                return (
                    "[bold $text-accent]Q&A mode[/]"
                    "[$foreground-muted] (Answer the clarifying questions or ESC to cancel)[/]"
                )
        except Exception:  # noqa: S110
            # If we can't access chat screen, continue with normal display
            pass

        mode_display = {
            AgentType.RESEARCH: "Research",
            AgentType.PLAN: "Planning",
            AgentType.TASKS: "Tasks",
            AgentType.SPECIFY: "Specify",
            AgentType.EXPORT: "Export",
        }
        mode_description = {
            AgentType.RESEARCH: (
                "Research topics with web search and synthesize findings"
            ),
            AgentType.PLAN: "Create comprehensive, actionable plans with milestones",
            AgentType.TASKS: (
                "Generate specific, actionable tasks from research and plans"
            ),
            AgentType.SPECIFY: (
                "Create detailed specifications and requirements documents"
            ),
            AgentType.EXPORT: "Export artifacts and findings to various formats",
        }

        mode_title = mode_display.get(self.mode, self.mode.value.title())
        description = mode_description.get(self.mode, "")

        # Check if mode has content
        has_content = self.progress_checker.has_mode_content(self.mode)
        status_icon = " ✓" if has_content else ""

        return (
            f"[bold $text-accent]{mode_title}{status_icon} mode[/]"
            f"[$foreground-muted] ({description})[/]"
        )


class CodebaseIndexPromptScreen(ModalScreen[bool]):
    """Modal dialog asking whether to index the detected codebase."""

    DEFAULT_CSS = """
        CodebaseIndexPromptScreen {
            align: center middle;
            background: rgba(0, 0, 0, 0.0);
        }

        CodebaseIndexPromptScreen > #index-prompt-dialog {
            width: 60%;
            max-width: 60;
            height: auto;
            border: wide $primary;
            padding: 1 2;
            layout: vertical;
            background: $surface;
            height: auto;
        }

        #index-prompt-buttons {
            layout: horizontal;
            align-horizontal: right;
            height: auto;
        }
    """

    def compose(self) -> ComposeResult:
        with Container(id="index-prompt-dialog"):
            yield Label("Index this codebase?", id="index-prompt-title")
            yield Static(
                f"Would you like to index the codebase at:\n{Path.cwd()}\n\n"
                "This is required for the agent to understand your code and answer "
                "questions about it. Without indexing, the agent cannot analyze "
                "your codebase."
            )
            with Container(id="index-prompt-buttons"):
                yield Button(
                    "Index now",
                    id="index-prompt-confirm",
                    variant="primary",
                )
                yield Button("Not now", id="index-prompt-cancel")

    @on(Button.Pressed, "#index-prompt-cancel")
    def handle_cancel(self, event: Button.Pressed) -> None:
        event.stop()
        self.dismiss(False)

    @on(Button.Pressed, "#index-prompt-confirm")
    def handle_confirm(self, event: Button.Pressed) -> None:
        event.stop()
        self.dismiss(True)


class ChatScreen(Screen[None]):
    CSS_PATH = "chat.tcss"

    BINDINGS = [
        ("ctrl+p", "command_palette", "Command Palette"),
        ("shift+tab", "toggle_mode", "Toggle mode"),
        ("ctrl+u", "show_usage", "Show usage"),
    ]

    COMMANDS = {
        UnifiedCommandProvider,
    }

    value = reactive("")
    mode = reactive(AgentType.RESEARCH)
    history: PromptHistory = PromptHistory()
    messages = reactive(list[ModelMessage | HintMessage]())
    working = reactive(False)
    indexing_job: reactive[CodebaseIndexSelection | None] = reactive(None)
    partial_message: reactive[ModelMessage | None] = reactive(None)
    _current_worker = None  # Track the current running worker for cancellation

    # Q&A mode state (for structured output clarifying questions)
    qa_mode = reactive(False)
    qa_questions: list[str] = []
    qa_current_index = reactive(0)
    qa_answers: list[str] = []

    def __init__(self, continue_session: bool = False) -> None:
        super().__init__()
        # Get the model configuration and services
        model_config = get_provider_model()
        # Use filtered service in TUI to restrict access to CWD codebase only
        storage_dir = get_shotgun_home() / "codebases"
        codebase_service = FilteredCodebaseService(storage_dir)
        self.codebase_sdk = CodebaseSDK()

        # Create shared deps without system_prompt_fn (agents provide their own)
        # We need a placeholder system_prompt_fn to satisfy the field requirement
        def _placeholder_system_prompt_fn(ctx: RunContext[AgentDeps]) -> str:
            raise RuntimeError(
                "This should not be called - agents provide their own system_prompt_fn"
            )

        self.deps = AgentDeps(
            interactive_mode=True,
            is_tui_context=True,
            llm_model=model_config,
            codebase_service=codebase_service,
            system_prompt_fn=_placeholder_system_prompt_fn,
        )
        self.agent_manager = AgentManager(deps=self.deps, initial_type=self.mode)
        self.command_handler = CommandHandler()
        self.placeholder_hints = PlaceholderHints()
        self.conversation_manager = ConversationManager()
        self.continue_session = continue_session

    def on_mount(self) -> None:
        self.query_one(PromptInput).focus(scroll_visible=True)
        # Hide spinner initially
        self.query_one("#spinner").display = False

        # Load conversation history if --continue flag was provided
        if self.continue_session and self.conversation_manager.exists():
            self._load_conversation()

        self.call_later(self.check_if_codebase_is_indexed)

    async def on_key(self, event: events.Key) -> None:
        """Handle key presses for cancellation."""
        # If escape is pressed during Q&A mode, exit Q&A
        if event.key in (Keys.Escape, Keys.ControlC) and self.qa_mode:
            self._exit_qa_mode()
            # Re-enable the input
            prompt_input = self.query_one(PromptInput)
            prompt_input.focus()
            # Prevent the event from propagating (don't quit the app)
            event.stop()
            return

        # If escape or ctrl+c is pressed while agent is working, cancel the operation
        if (
            event.key in (Keys.Escape, Keys.ControlC)
            and self.working
            and self._current_worker
        ):
            # Track cancellation event
            track_event(
                "agent_cancelled",
                {
                    "agent_mode": self.mode.value,
                    "cancel_key": event.key,
                },
            )

            # Cancel the running agent worker
            self._current_worker.cancel()
            # Show cancellation message
            self.mount_hint("⚠️ Cancelling operation...")
            # Re-enable the input
            prompt_input = self.query_one(PromptInput)
            prompt_input.focus()
            # Prevent the event from propagating (don't quit the app)
            event.stop()

    @work
    async def check_if_codebase_is_indexed(self) -> None:
        cur_dir = Path.cwd().resolve()
        is_empty = all(
            dir.is_dir() and dir.name in ["__pycache__", ".git", ".shotgun"]
            for dir in cur_dir.iterdir()
        )
        if is_empty or self.continue_session:
            return

        # Check if the current directory has any accessible codebases
        accessible_graphs = (
            await self.codebase_sdk.list_codebases_for_directory()
        ).graphs
        if accessible_graphs:
            self.mount_hint(help_text_with_codebase(already_indexed=True))
            return

        # Ask user if they want to index the current directory
        should_index = await self.app.push_screen_wait(CodebaseIndexPromptScreen())
        if not should_index:
            self.mount_hint(help_text_empty_dir())
            return

        self.mount_hint(help_text_with_codebase(already_indexed=False))

        # Auto-index the current directory with its name
        cwd_name = cur_dir.name
        selection = CodebaseIndexSelection(repo_path=cur_dir, name=cwd_name)
        self.call_later(lambda: self.index_codebase(selection))

    def watch_mode(self, new_mode: AgentType) -> None:
        """React to mode changes by updating the agent manager."""

        if self.is_mounted:
            self.agent_manager.set_agent(new_mode)

            mode_indicator = self.query_one(ModeIndicator)
            mode_indicator.mode = new_mode
            mode_indicator.refresh()

            prompt_input = self.query_one(PromptInput)
            # Force new hint selection when mode changes
            prompt_input.placeholder = self._placeholder_for_mode(
                new_mode, force_new=True
            )
            prompt_input.refresh()

    def watch_working(self, is_working: bool) -> None:
        """Show or hide the spinner based on working state."""
        if self.is_mounted:
            spinner = self.query_one("#spinner")
            spinner.set_classes("" if is_working else "hidden")
            spinner.display = is_working

            # Update the status bar to show/hide "ESC to stop"
            status_bar = self.query_one(StatusBar)
            status_bar.working = is_working
            status_bar.refresh()

    def watch_qa_mode(self, qa_mode_active: bool) -> None:
        """Update UI when Q&A mode state changes."""
        if self.is_mounted:
            # Update status bar to show "ESC to exit Q&A mode"
            status_bar = self.query_one(StatusBar)
            status_bar.refresh()

            # Update mode indicator to show "Q&A mode"
            mode_indicator = self.query_one(ModeIndicator)
            mode_indicator.refresh()

    def watch_messages(self, messages: list[ModelMessage | HintMessage]) -> None:
        """Update the chat history when messages change."""
        if self.is_mounted:
            chat_history = self.query_one(ChatHistory)
            chat_history.update_messages(messages)

    def action_toggle_mode(self) -> None:
        # Prevent mode switching during Q&A
        if self.qa_mode:
            self.notify(
                "Cannot switch modes while answering questions",
                severity="warning",
                timeout=3,
            )
            return

        modes = [
            AgentType.RESEARCH,
            AgentType.SPECIFY,
            AgentType.PLAN,
            AgentType.TASKS,
            AgentType.EXPORT,
        ]
        self.mode = modes[(modes.index(self.mode) + 1) % len(modes)]
        self.agent_manager.set_agent(self.mode)
        # whoops it actually changes focus. Let's be brutal for now
        self.call_later(lambda: self.query_one(PromptInput).focus())

    def action_show_usage(self) -> None:
        usage_hint = self.agent_manager.get_usage_hint()
        logger.info(f"Usage hint: {usage_hint}")
        if usage_hint:
            self.mount_hint(usage_hint)
        else:
            self.notify("No usage hint available", severity="error")

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        with Container(id="window"):
            yield self.agent_manager
            yield ChatHistory()
            with Container(id="footer"):
                yield Spinner(
                    text="Processing...",
                    id="spinner",
                    classes="" if self.working else "hidden",
                )
                yield StatusBar(working=self.working)
                yield PromptInput(
                    text=self.value,
                    highlight_cursor_line=False,
                    id="prompt-input",
                    placeholder=self._placeholder_for_mode(self.mode),
                )
                with Grid():
                    yield ModeIndicator(mode=self.mode)
                    yield Static("", id="indexing-job-display")

    def mount_hint(self, markdown: str) -> None:
        hint = HintMessage(message=markdown)
        self.agent_manager.add_hint_message(hint)

    @on(PartialResponseMessage)
    def handle_partial_response(self, event: PartialResponseMessage) -> None:
        self.partial_message = event.message
        history = self.query_one(ChatHistory)

        # Filter event.messages to exclude ModelRequest with only ToolReturnPart
        # These are intermediate tool results that would render as empty (UserQuestionWidget
        # filters out ToolReturnPart in format_prompt_parts), causing user messages to disappear
        from pydantic_ai.messages import ToolReturnPart

        filtered_event_messages: list[ModelMessage] = []
        for msg in event.messages:
            if isinstance(msg, ModelRequest):
                # Check if this ModelRequest has any user-visible parts
                has_user_content = any(
                    not isinstance(part, ToolReturnPart) for part in msg.parts
                )
                if has_user_content:
                    filtered_event_messages.append(msg)
                # Skip ModelRequest with only ToolReturnPart
            else:
                # Keep all ModelResponse and other message types
                filtered_event_messages.append(msg)

        # Only update messages if the message list changed
        new_message_list = self.messages + cast(
            list[ModelMessage | HintMessage], filtered_event_messages
        )
        if len(new_message_list) != len(history.items):
            history.update_messages(new_message_list)

        # Always update the partial response (reactive property handles the update)
        history.partial_response = self.partial_message

    def _clear_partial_response(self) -> None:
        partial_response_widget = self.query_one(ChatHistory)
        partial_response_widget.partial_response = None

    def _exit_qa_mode(self) -> None:
        """Exit Q&A mode and clean up state."""
        # Track cancellation event
        track_event(
            "qa_mode_cancelled",
            {
                "questions_total": len(self.qa_questions),
                "questions_answered": len(self.qa_answers),
            },
        )

        # Clear Q&A state
        self.qa_mode = False
        self.qa_questions = []
        self.qa_answers = []
        self.qa_current_index = 0

        # Show cancellation message
        self.mount_hint("⚠️ Q&A cancelled - You can continue the conversation.")

    @on(ClarifyingQuestionsMessage)
    def handle_clarifying_questions(self, event: ClarifyingQuestionsMessage) -> None:
        """Handle clarifying questions from agent structured output.

        Note: Hints are now added synchronously in agent_manager.run() before this
        handler is called, so we only need to set up Q&A mode state here.
        """
        # Clear any streaming partial response (removes final_result JSON)
        self._clear_partial_response()

        # Enter Q&A mode
        self.qa_mode = True
        self.qa_questions = event.questions
        self.qa_current_index = 0
        self.qa_answers = []

    @on(MessageHistoryUpdated)
    def handle_message_history_updated(self, event: MessageHistoryUpdated) -> None:
        """Handle message history updates from the agent manager."""
        self._clear_partial_response()
        self.messages = event.messages

        # Refresh placeholder and mode indicator in case artifacts were created
        prompt_input = self.query_one(PromptInput)
        prompt_input.placeholder = self._placeholder_for_mode(self.mode)
        prompt_input.refresh()

        mode_indicator = self.query_one(ModeIndicator)
        mode_indicator.refresh()

        # If there are file operations, add a message showing the modified files
        if event.file_operations:
            chat_history = self.query_one(ChatHistory)
            if chat_history.vertical_tail:
                tracker = FileOperationTracker(operations=event.file_operations)
                display_path = tracker.get_display_path()

                if display_path:
                    # Create a simple markdown message with the file path
                    # The terminal emulator will make this clickable automatically
                    from pathlib import Path

                    path_obj = Path(display_path)

                    if len(event.file_operations) == 1:
                        message = f"📝 Modified: `{display_path}`"
                    else:
                        num_files = len({op.file_path for op in event.file_operations})
                        if path_obj.is_dir():
                            message = (
                                f"📁 Modified {num_files} files in: `{display_path}`"
                            )
                        else:
                            # Common path is a file, show parent directory
                            message = (
                                f"📁 Modified {num_files} files in: `{path_obj.parent}`"
                            )

                    self.mount_hint(message)

    @on(PromptInput.Submitted)
    async def handle_submit(self, message: PromptInput.Submitted) -> None:
        text = message.text.strip()

        # If empty text, just clear input and return
        if not text:
            prompt_input = self.query_one(PromptInput)
            prompt_input.clear()
            self.value = ""
            return

        # Handle Q&A mode (from structured output clarifying questions)
        if self.qa_mode and self.qa_questions:
            # Collect answer
            self.qa_answers.append(text)

            # Show answer
            if len(self.qa_questions) == 1:
                self.agent_manager.add_hint_message(
                    HintMessage(message=f"**A:** {text}")
                )
            else:
                q_num = self.qa_current_index + 1
                self.agent_manager.add_hint_message(
                    HintMessage(message=f"**A{q_num}:** {text}")
                )

            # Move to next or finish
            self.qa_current_index += 1

            if self.qa_current_index < len(self.qa_questions):
                # Show next question
                next_q = self.qa_questions[self.qa_current_index]
                next_q_num = self.qa_current_index + 1
                self.agent_manager.add_hint_message(
                    HintMessage(message=f"**Q{next_q_num}:** {next_q}")
                )
            else:
                # All answered - format and send back
                if len(self.qa_questions) == 1:
                    # Single question - just send the answer
                    formatted_qa = f"Q: {self.qa_questions[0]}\nA: {self.qa_answers[0]}"
                else:
                    # Multiple questions - format all Q&A pairs
                    formatted_qa = "\n\n".join(
                        f"Q{i + 1}: {q}\nA{i + 1}: {a}"
                        for i, (q, a) in enumerate(
                            zip(self.qa_questions, self.qa_answers, strict=True)
                        )
                    )

                # Exit Q&A mode
                self.qa_mode = False
                self.qa_questions = []
                self.qa_answers = []
                self.qa_current_index = 0

                # Send answers back to agent
                self.run_agent(formatted_qa)

            # Clear input
            prompt_input = self.query_one(PromptInput)
            prompt_input.clear()
            self.value = ""
            return

        # Check if it's a command
        if self.command_handler.is_command(text):
            success, response = self.command_handler.handle_command(text)

            # Add the command to history
            self.history.append(message.text)

            # Display the command in chat history
            user_message = ModelRequest(parts=[UserPromptPart(content=text)])
            self.messages = self.messages + [user_message]

            # Display the response (help text or error message)
            response_message = ModelResponse(parts=[TextPart(content=response)])
            self.messages = self.messages + [response_message]

            # Clear the input
            prompt_input = self.query_one(PromptInput)
            prompt_input.clear()
            self.value = ""
            return

        # Not a command, process as normal
        self.history.append(message.text)

        # Add user message to agent_manager's history BEFORE running the agent
        # This ensures immediate visual feedback AND proper deduplication
        user_message = ModelRequest.user_text_prompt(text)
        self.agent_manager.ui_message_history.append(user_message)
        self.messages = self.agent_manager.ui_message_history.copy()

        # Clear the input
        self.value = ""
        self.run_agent(text)  # Use stripped text

        prompt_input = self.query_one(PromptInput)
        prompt_input.clear()

    def _placeholder_for_mode(self, mode: AgentType, force_new: bool = False) -> str:
        """Return the placeholder text appropriate for the current mode.

        Args:
            mode: The current agent mode.
            force_new: If True, force selection of a new random hint.

        Returns:
            Dynamic placeholder hint based on mode and progress.
        """
        return self.placeholder_hints.get_placeholder_for_mode(mode)

    def index_codebase_command(self) -> None:
        # Simplified: always index current working directory with its name
        cur_dir = Path.cwd().resolve()
        cwd_name = cur_dir.name
        selection = CodebaseIndexSelection(repo_path=cur_dir, name=cwd_name)
        self.call_later(lambda: self.index_codebase(selection))

    def delete_codebase_command(self) -> None:
        self.app.push_screen(
            CommandPalette(
                providers=[DeleteCodebasePaletteProvider],
                placeholder="Select a codebase to delete…",
            )
        )

    def delete_codebase_from_palette(self, graph_id: str) -> None:
        stack = getattr(self.app, "screen_stack", None)
        if stack and isinstance(stack[-1], CommandPalette):
            self.app.pop_screen()

        self.call_later(lambda: self.delete_codebase(graph_id))

    @work
    async def delete_codebase(self, graph_id: str) -> None:
        try:
            await self.codebase_sdk.delete_codebase(graph_id)
            self.notify(f"Deleted codebase: {graph_id}", severity="information")
        except CodebaseNotFoundError as exc:
            self.notify(str(exc), severity="error")
        except Exception as exc:  # pragma: no cover - defensive UI path
            self.notify(f"Failed to delete codebase: {exc}", severity="error")

    @work
    async def index_codebase(self, selection: CodebaseIndexSelection) -> None:
        label = self.query_one("#indexing-job-display", Static)
        label.update(
            f"[$foreground-muted]Indexing codebase: [bold $text-accent]{selection.name}[/][/]"
        )
        label.refresh()

        def create_progress_bar(percentage: float, width: int = 20) -> str:
            """Create a visual progress bar using Unicode block characters."""
            filled = int((percentage / 100) * width)
            empty = width - filled
            return "▓" * filled + "░" * empty

        # Spinner animation frames
        spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

        # Progress state (shared between timer and progress callback)
        progress_state: dict[str, int | float] = {
            "frame_index": 0,
            "percentage": 0.0,
        }

        def update_progress_display() -> None:
            """Update progress bar on timer - runs every 100ms."""
            # Advance spinner frame
            frame_idx = int(progress_state["frame_index"])
            progress_state["frame_index"] = (frame_idx + 1) % len(spinner_frames)
            spinner = spinner_frames[frame_idx]

            # Get current state
            pct = float(progress_state["percentage"])
            bar = create_progress_bar(pct)

            # Update label
            label.update(
                f"[$foreground-muted]Indexing codebase: {spinner} {bar} {pct:.0f}%[/]"
            )

        def progress_callback(progress_info: IndexProgress) -> None:
            """Update progress state (timer renders it independently)."""
            # Calculate overall percentage (0-95%, reserve 95-100% for finalization)
            if progress_info.phase == ProgressPhase.STRUCTURE:
                # Phase 1: 0-10%, always show 5% while running, 10% when complete
                overall_pct = 10.0 if progress_info.phase_complete else 5.0
            elif progress_info.phase == ProgressPhase.DEFINITIONS:
                # Phase 2: 10-80% based on files processed
                if progress_info.total and progress_info.total > 0:
                    phase_pct = (progress_info.current / progress_info.total) * 70.0
                    overall_pct = 10.0 + phase_pct
                else:
                    overall_pct = 10.0
            elif progress_info.phase == ProgressPhase.RELATIONSHIPS:
                # Phase 3: 80-95% based on relationships processed (cap at 95%)
                if progress_info.total and progress_info.total > 0:
                    phase_pct = (progress_info.current / progress_info.total) * 15.0
                    overall_pct = 80.0 + phase_pct
                else:
                    overall_pct = 80.0
            else:
                overall_pct = 0.0

            # Update shared state (timer will render it)
            progress_state["percentage"] = overall_pct

        # Start progress animation timer (10 fps = 100ms interval)
        progress_timer = self.set_interval(0.1, update_progress_display)

        try:
            # Pass the current working directory as the indexed_from_cwd
            logger.debug(
                f"Starting indexing - repo_path: {selection.repo_path}, "
                f"name: {selection.name}, cwd: {Path.cwd().resolve()}"
            )
            result = await self.codebase_sdk.index_codebase(
                selection.repo_path,
                selection.name,
                indexed_from_cwd=str(Path.cwd().resolve()),
                progress_callback=progress_callback,
            )

            # Stop progress animation
            progress_timer.stop()

            # Show 100% completion after indexing finishes
            final_bar = create_progress_bar(100.0)
            label.update(f"[$foreground-muted]Indexing codebase: {final_bar} 100%[/]")
            label.refresh()

            logger.info(
                f"Successfully indexed codebase '{result.name}' (ID: {result.graph_id})"
            )
            self.notify(
                f"Indexed codebase '{result.name}' (ID: {result.graph_id})",
                severity="information",
                timeout=8,
            )

        except CodebaseAlreadyIndexedError as exc:
            progress_timer.stop()
            logger.warning(f"Codebase already indexed: {exc}")
            self.notify(str(exc), severity="warning")
            return
        except InvalidPathError as exc:
            progress_timer.stop()
            logger.error(f"Invalid path error: {exc}")
            self.notify(str(exc), severity="error")

        except Exception as exc:  # pragma: no cover - defensive UI path
            # Log full exception details with stack trace
            logger.exception(
                f"Failed to index codebase - repo_path: {selection.repo_path}, "
                f"name: {selection.name}, error: {exc}"
            )
            self.notify(f"Failed to index codebase: {exc}", severity="error")
        finally:
            # Always stop the progress timer
            progress_timer.stop()
            label.update("")
            label.refresh()

    @work
    async def run_agent(self, message: str) -> None:
        prompt = None
        self.working = True

        # Store the worker so we can cancel it if needed
        from textual.worker import get_current_worker

        self._current_worker = get_current_worker()

        prompt = message

        try:
            await self.agent_manager.run(
                prompt=prompt,
            )
        except asyncio.CancelledError:
            # Handle cancellation gracefully - DO NOT re-raise
            self.mount_hint("⚠️ Operation cancelled by user")
        except Exception as e:
            # Log with full stack trace to shotgun.log
            logger.exception(
                "Agent run failed",
                extra={
                    "agent_mode": self.mode.value,
                    "error_type": type(e).__name__,
                },
            )

            # Determine user-friendly message based on error type
            error_name = type(e).__name__
            error_message = str(e)

            if "APIStatusError" in error_name and "overload" in error_message.lower():
                hint = "⚠️ The AI service is temporarily overloaded. Please wait a moment and try again."
            elif "APIStatusError" in error_name and "rate" in error_message.lower():
                hint = "⚠️ Rate limit reached. Please wait before trying again."
            elif "APIStatusError" in error_name:
                hint = f"⚠️ AI service error: {error_message}"
            else:
                hint = f"⚠️ An error occurred: {error_message}\n\nCheck logs at ~/.shotgun-sh/logs/shotgun.log"

            self.mount_hint(hint)
        finally:
            self.working = False
            self._current_worker = None

        # Save conversation after each interaction
        self._save_conversation()

        prompt_input = self.query_one(PromptInput)
        prompt_input.focus()

    def _save_conversation(self) -> None:
        """Save the current conversation to persistent storage."""
        # Get conversation state from agent manager
        state = self.agent_manager.get_conversation_state()

        # Create conversation history object
        conversation = ConversationHistory(
            last_agent_model=state.agent_type,
        )
        conversation.set_agent_messages(state.agent_messages)
        conversation.set_ui_messages(state.ui_messages)

        # Save to file
        self.conversation_manager.save(conversation)

    def _load_conversation(self) -> None:
        """Load conversation from persistent storage."""
        conversation = self.conversation_manager.load()
        if conversation is None:
            # Check if file existed but was corrupted (backup was created)
            backup_path = self.conversation_manager.conversation_path.with_suffix(
                ".json.backup"
            )
            if backup_path.exists():
                # File was corrupted - show friendly notification
                self.mount_hint(
                    "⚠️ Previous session was corrupted and has been backed up. Starting fresh conversation."
                )
            return

        try:
            # Restore agent state
            agent_messages = conversation.get_agent_messages()
            ui_messages = conversation.get_ui_messages()

            # Create ConversationState for restoration
            state = ConversationState(
                agent_messages=agent_messages,
                ui_messages=ui_messages,
                agent_type=conversation.last_agent_model,
            )

            self.agent_manager.restore_conversation_state(state)

            # Update the current mode
            self.mode = AgentType(conversation.last_agent_model)
            self.deps.usage_manager.restore_usage_state()

        except Exception as e:  # pragma: no cover
            # If anything goes wrong during restoration, log it and continue
            logger.error("Failed to restore conversation state: %s", e)
            self.mount_hint(
                "⚠️ Could not restore previous session. Starting fresh conversation."
            )


def help_text_with_codebase(already_indexed: bool = False) -> str:
    return (
        "Howdy! Welcome to Shotgun - the context tool for software engineering. \n\n"
        "You can research, build specs, plan, create tasks, and export context to your "
        "favorite code-gen agents.\n\n"
        f"{'' if already_indexed else 'Once your codebase is indexed, '}I can help with:\n\n"
        "- Speccing out a new feature\n"
        "- Onboarding you onto this project\n"
        "- Helping with a refactor spec\n"
        "- Creating AGENTS.md file for this project\n"
    )


def help_text_empty_dir() -> str:
    return (
        "Howdy! Welcome to Shotgun - the context tool for software engineering.\n\n"
        "You can research, build specs, plan, create tasks, and export context to your "
        "favorite code-gen agents.\n\n"
        "What would you like to build? Here are some examples:\n\n"
        "- Research FastAPI vs Django\n"
        "- Plan my new web app using React\n"
        "- Create PRD for my planned product\n"
    )
