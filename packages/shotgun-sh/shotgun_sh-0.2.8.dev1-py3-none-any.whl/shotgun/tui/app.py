from collections.abc import Iterable
from typing import Any

from textual.app import App, SystemCommand
from textual.binding import Binding
from textual.screen import Screen

from shotgun.agents.config import ConfigManager, get_config_manager
from shotgun.logging_config import get_logger
from shotgun.tui.screens.splash import SplashScreen
from shotgun.utils.file_system_utils import get_shotgun_base_path
from shotgun.utils.update_checker import perform_auto_update_async

from .screens.chat import ChatScreen
from .screens.directory_setup import DirectorySetupScreen
from .screens.feedback import FeedbackScreen
from .screens.model_picker import ModelPickerScreen
from .screens.provider_config import ProviderConfigScreen
from .screens.welcome import WelcomeScreen

logger = get_logger(__name__)


class ShotgunApp(App[None]):
    SCREENS = {
        "chat": ChatScreen,
        "provider_config": ProviderConfigScreen,
        "model_picker": ModelPickerScreen,
        "directory_setup": DirectorySetupScreen,
        "feedback": FeedbackScreen,
    }
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit the app"),
    ]

    CSS_PATH = "styles.tcss"

    def __init__(
        self, no_update_check: bool = False, continue_session: bool = False
    ) -> None:
        super().__init__()
        self.config_manager: ConfigManager = get_config_manager()
        self.no_update_check = no_update_check
        self.continue_session = continue_session

        # Start async update check and install
        if not no_update_check:
            perform_auto_update_async(no_update_check=no_update_check)

    def on_mount(self) -> None:
        self.theme = "gruvbox"
        # Track TUI startup
        from shotgun.posthog_telemetry import track_event

        track_event("tui_started", {})

        self.push_screen(
            SplashScreen(), callback=lambda _arg: self.refresh_startup_screen()
        )

    def refresh_startup_screen(self) -> None:
        """Push the appropriate screen based on configured providers."""
        # Show welcome screen if no providers are configured OR if user hasn't seen it yet
        config = self.config_manager.load()
        if (
            not self.config_manager.has_any_provider_key()
            or not config.shown_welcome_screen
        ):
            if isinstance(self.screen, WelcomeScreen):
                return

            self.push_screen(
                WelcomeScreen(),
                callback=lambda _arg: self.refresh_startup_screen(),
            )
            return

        if not self.check_local_shotgun_directory_exists():
            if isinstance(self.screen, DirectorySetupScreen):
                return

            self.push_screen(
                DirectorySetupScreen(),
                callback=lambda _arg: self.refresh_startup_screen(),
            )
            return

        if isinstance(self.screen, ChatScreen):
            return
        # Pass continue_session flag to ChatScreen
        self.push_screen(ChatScreen(continue_session=self.continue_session))

    def check_local_shotgun_directory_exists(self) -> bool:
        shotgun_dir = get_shotgun_base_path()
        return shotgun_dir.exists() and shotgun_dir.is_dir()

    async def action_quit(self) -> None:
        """Quit the application."""
        # Shut down PostHog client to prevent threading errors
        from shotgun.posthog_telemetry import shutdown

        shutdown()
        self.exit()

    def get_system_commands(self, screen: Screen[Any]) -> Iterable[SystemCommand]:
        return [
            SystemCommand(
                "Feedback", "Send us feedback or report a bug", self.action_feedback
            )
        ]  # we don't want any system commands

    def action_feedback(self) -> None:
        """Open feedback screen and submit feedback."""
        from shotgun.posthog_telemetry import Feedback, submit_feedback_survey

        def handle_feedback(feedback: Feedback | None) -> None:
            if feedback is not None:
                submit_feedback_survey(feedback)
                self.notify("Feedback sent. Thank you!")

        self.push_screen(FeedbackScreen(), callback=handle_feedback)


def run(no_update_check: bool = False, continue_session: bool = False) -> None:
    """Run the TUI application.

    Args:
        no_update_check: If True, disable automatic update checks.
        continue_session: If True, continue from previous conversation.
    """
    # Clean up any corrupted databases BEFORE starting the TUI
    # This prevents crashes from corrupted databases during initialization
    import asyncio

    from shotgun.codebase.core.manager import CodebaseGraphManager
    from shotgun.utils import get_shotgun_home

    storage_dir = get_shotgun_home() / "codebases"
    manager = CodebaseGraphManager(storage_dir)

    try:
        removed = asyncio.run(manager.cleanup_corrupted_databases())
        if removed:
            logger.info(
                f"Cleaned up {len(removed)} corrupted database(s) before TUI startup"
            )
    except Exception as e:
        logger.error(f"Failed to cleanup corrupted databases: {e}")
        # Continue anyway - the TUI can still function

    app = ShotgunApp(no_update_check=no_update_check, continue_session=continue_session)
    app.run(inline_no_clear=True)


def serve(
    host: str = "localhost",
    port: int = 8000,
    public_url: str | None = None,
    no_update_check: bool = False,
    continue_session: bool = False,
) -> None:
    """Serve the TUI application as a web application.

    Args:
        host: Host address for the web server.
        port: Port number for the web server.
        public_url: Public URL if behind a proxy.
        no_update_check: If True, disable automatic update checks.
        continue_session: If True, continue from previous conversation.
    """
    # Clean up any corrupted databases BEFORE starting the TUI
    # This prevents crashes from corrupted databases during initialization
    import asyncio

    from textual_serve.server import Server

    from shotgun.codebase.core.manager import CodebaseGraphManager
    from shotgun.utils import get_shotgun_home

    storage_dir = get_shotgun_home() / "codebases"
    manager = CodebaseGraphManager(storage_dir)

    try:
        removed = asyncio.run(manager.cleanup_corrupted_databases())
        if removed:
            logger.info(
                f"Cleaned up {len(removed)} corrupted database(s) before TUI startup"
            )
    except Exception as e:
        logger.error(f"Failed to cleanup corrupted databases: {e}")
        # Continue anyway - the TUI can still function

    # Create a new event loop after asyncio.run() closes the previous one
    # This is needed for the Server.serve() method
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Build the command string based on flags
    command = "shotgun"
    if no_update_check:
        command += " --no-update-check"
    if continue_session:
        command += " --continue"

    # Create and start the server with hardcoded title and debug=False
    server = Server(
        command=command,
        host=host,
        port=port,
        title="The Shotgun",
        public_url=public_url,
    )

    # Set up graceful shutdown on SIGTERM/SIGINT
    import signal
    import sys

    def signal_handler(_signum: int, _frame: Any) -> None:
        """Handle shutdown signals gracefully."""
        from shotgun.posthog_telemetry import shutdown

        logger.info("Received shutdown signal, cleaning up...")
        # Restore stdout/stderr before shutting down
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        shutdown()
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Suppress the textual-serve banner by redirecting stdout/stderr
    import io

    # Capture and suppress the banner, but show the actual serving URL
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    captured_output = io.StringIO()
    sys.stdout = captured_output
    sys.stderr = captured_output

    try:
        # This will print the banner to our captured output
        import logging

        # Temporarily set logging to ERROR level to suppress INFO messages
        textual_serve_logger = logging.getLogger("textual_serve")
        original_level = textual_serve_logger.level
        textual_serve_logger.setLevel(logging.ERROR)

        # Print our own message to the original stdout
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        print(f"Serving Shotgun TUI at http://{host}:{port}")
        print("Press Ctrl+C to quit")

        # Now suppress output again for the serve call
        sys.stdout = captured_output
        sys.stderr = captured_output

        server.serve(debug=False)
    finally:
        # Restore original stdout/stderr
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        if "textual_serve_logger" in locals():
            textual_serve_logger.setLevel(original_level)


if __name__ == "__main__":
    run()
