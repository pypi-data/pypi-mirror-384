from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, cast

from textual.command import DiscoveryHit, Hit, Provider

from shotgun.agents.models import AgentType
from shotgun.codebase.models import CodebaseGraph
from shotgun.tui.screens.model_picker import ModelPickerScreen
from shotgun.tui.screens.provider_config import ProviderConfigScreen

if TYPE_CHECKING:
    from shotgun.tui.screens.chat import ChatScreen


class AgentModeProvider(Provider):
    """Command provider for agent mode switching."""

    @property
    def chat_screen(self) -> "ChatScreen":
        from shotgun.tui.screens.chat import ChatScreen

        return cast(ChatScreen, self.screen)

    def set_mode(self, mode: AgentType) -> None:
        """Switch to research mode."""
        self.chat_screen.mode = mode

    async def discover(self) -> AsyncGenerator[DiscoveryHit, None]:
        """Provide default mode switching commands when palette opens."""
        yield DiscoveryHit(
            "Switch to Research Mode",
            lambda: self.set_mode(AgentType.RESEARCH),
            help="🔬 Research topics with web search and synthesize findings",
        )
        yield DiscoveryHit(
            "Switch to Specify Mode",
            lambda: self.set_mode(AgentType.SPECIFY),
            help="📝 Create detailed specifications and requirements documents",
        )
        yield DiscoveryHit(
            "Switch to Plan Mode",
            lambda: self.set_mode(AgentType.PLAN),
            help="📋 Create comprehensive, actionable plans with milestones",
        )
        yield DiscoveryHit(
            "Switch to Tasks Mode",
            lambda: self.set_mode(AgentType.TASKS),
            help="✅ Generate specific, actionable tasks from research and plans",
        )
        yield DiscoveryHit(
            "Switch to Export Mode",
            lambda: self.set_mode(AgentType.EXPORT),
            help="📤 Export artifacts and findings to various formats",
        )

    async def search(self, query: str) -> AsyncGenerator[Hit, None]:
        """Search for mode commands."""
        matcher = self.matcher(query)

        commands = [
            (
                "Switch to Research Mode",
                "🔬 Research topics with web search and synthesize findings",
                lambda: self.set_mode(AgentType.RESEARCH),
                AgentType.RESEARCH,
            ),
            (
                "Switch to Specify Mode",
                "📝 Create detailed specifications and requirements documents",
                lambda: self.set_mode(AgentType.SPECIFY),
                AgentType.SPECIFY,
            ),
            (
                "Switch to Plan Mode",
                "📋 Create comprehensive, actionable plans with milestones",
                lambda: self.set_mode(AgentType.PLAN),
                AgentType.PLAN,
            ),
            (
                "Switch to Tasks Mode",
                "✅ Generate specific, actionable tasks from research and plans",
                lambda: self.set_mode(AgentType.TASKS),
                AgentType.TASKS,
            ),
            (
                "Switch to Export Mode",
                "📤 Export artifacts and findings to various formats",
                lambda: self.set_mode(AgentType.EXPORT),
                AgentType.EXPORT,
            ),
        ]

        for title, help_text, callback, mode in commands:
            if self.chat_screen.mode == mode:
                continue
            score = matcher.match(title)
            if score > 0:
                yield Hit(score, matcher.highlight(title), callback, help=help_text)


class UsageProvider(Provider):
    """Command provider for agent mode switching."""

    @property
    def chat_screen(self) -> "ChatScreen":
        from shotgun.tui.screens.chat import ChatScreen

        return cast(ChatScreen, self.screen)

    async def discover(self) -> AsyncGenerator[DiscoveryHit, None]:
        """Provide default mode switching commands when palette opens."""
        yield DiscoveryHit(
            "Show usage",
            self.chat_screen.action_show_usage,
            help="Display usage information for the current session",
        )

    async def search(self, query: str) -> AsyncGenerator[Hit, None]:
        """Search for mode commands."""
        matcher = self.matcher(query)

        async for discovery_hit in self.discover():
            score = matcher.match(discovery_hit.text or "")
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(discovery_hit.text or ""),
                    discovery_hit.command,
                    help=discovery_hit.help,
                )


class ProviderSetupProvider(Provider):
    """Command palette entries for provider configuration."""

    @property
    def chat_screen(self) -> "ChatScreen":
        from shotgun.tui.screens.chat import ChatScreen

        return cast(ChatScreen, self.screen)

    def open_provider_config(self) -> None:
        """Show the provider configuration screen."""
        self.chat_screen.app.push_screen(ProviderConfigScreen())

    def open_model_picker(self) -> None:
        """Show the model picker screen."""
        self.chat_screen.app.push_screen(ModelPickerScreen())

    async def discover(self) -> AsyncGenerator[DiscoveryHit, None]:
        yield DiscoveryHit(
            "Open Provider Setup",
            self.open_provider_config,
            help="⚙️ Manage API keys for available providers",
        )
        yield DiscoveryHit(
            "Select AI Model",
            self.open_model_picker,
            help="🤖 Choose which AI model to use",
        )

    async def search(self, query: str) -> AsyncGenerator[Hit, None]:
        matcher = self.matcher(query)

        title = "Open Provider Setup"
        score = matcher.match(title)
        if score > 0:
            yield Hit(
                score,
                matcher.highlight(title),
                self.open_provider_config,
                help="⚙️ Manage API keys for available providers",
            )

        title = "Select AI Model"
        score = matcher.match(title)
        if score > 0:
            yield Hit(
                score,
                matcher.highlight(title),
                self.open_model_picker,
                help="🤖 Choose which AI model to use",
            )


class CodebaseCommandProvider(Provider):
    """Command palette entries for codebase management."""

    @property
    def chat_screen(self) -> "ChatScreen":
        from shotgun.tui.screens.chat import ChatScreen

        return cast(ChatScreen, self.screen)

    async def discover(self) -> AsyncGenerator[DiscoveryHit, None]:
        yield DiscoveryHit(
            "Codebase: Delete Codebase Index",
            self.chat_screen.delete_codebase_command,
            help="Delete an existing codebase index",
        )
        yield DiscoveryHit(
            "Codebase: Index Codebase",
            self.chat_screen.index_codebase_command,
            help="Index a repository into the codebase graph",
        )

    async def search(self, query: str) -> AsyncGenerator[Hit, None]:
        matcher = self.matcher(query)
        commands = [
            (
                "Codebase: Delete Codebase Index",
                self.chat_screen.delete_codebase_command,
                "Delete an existing codebase index",
            ),
            (
                "Codebase: Index Codebase",
                self.chat_screen.index_codebase_command,
                "Index a repository into the codebase graph",
            ),
        ]
        for title, callback, help_text in commands:
            score = matcher.match(title)
            if score > 0:
                yield Hit(score, matcher.highlight(title), callback, help=help_text)


class DeleteCodebasePaletteProvider(Provider):
    """Provider that lists indexed codebases for deletion."""

    @property
    def chat_screen(self) -> "ChatScreen":
        from shotgun.tui.screens.chat import ChatScreen

        return cast(ChatScreen, self.screen)

    async def _codebases(self) -> list[CodebaseGraph]:
        try:
            result = await self.chat_screen.codebase_sdk.list_codebases()
        except Exception as exc:  # pragma: no cover - defensive UI path
            self.chat_screen.notify(
                f"Unable to load codebases: {exc}", severity="error"
            )
            return []
        return result.graphs

    async def discover(self) -> AsyncGenerator[DiscoveryHit, None]:
        graphs = await self._codebases()
        for graph in graphs:
            title = f"Delete {graph.name}"
            help_text = f"{graph.graph_id} • {graph.repo_path}"
            yield DiscoveryHit(
                title,
                lambda graph_id=graph.graph_id: self.chat_screen.delete_codebase_from_palette(
                    graph_id
                ),
                help=help_text,
            )

    async def search(self, query: str) -> AsyncGenerator[Hit, None]:
        matcher = self.matcher(query)
        graphs = await self._codebases()
        for graph in graphs:
            display = f"{graph.name} ({graph.graph_id[:8]})"
            score = matcher.match(display)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(display),
                    lambda graph_id=graph.graph_id: self.chat_screen.delete_codebase_from_palette(
                        graph_id
                    ),
                    help=graph.repo_path,
                )


class UnifiedCommandProvider(Provider):
    """Unified command provider with all commands in alphabetical order."""

    @property
    def chat_screen(self) -> "ChatScreen":
        from shotgun.tui.screens.chat import ChatScreen

        return cast(ChatScreen, self.screen)

    def open_provider_config(self) -> None:
        """Show the provider configuration screen."""
        self.chat_screen.app.push_screen(ProviderConfigScreen())

    def open_model_picker(self) -> None:
        """Show the model picker screen."""
        self.chat_screen.app.push_screen(ModelPickerScreen())

    async def discover(self) -> AsyncGenerator[DiscoveryHit, None]:
        """Provide commands in alphabetical order when palette opens."""
        # Alphabetically ordered commands
        yield DiscoveryHit(
            "Codebase: Delete Codebase Index",
            self.chat_screen.delete_codebase_command,
            help="Delete an existing codebase index",
        )
        yield DiscoveryHit(
            "Codebase: Index Codebase",
            self.chat_screen.index_codebase_command,
            help="Index a repository into the codebase graph",
        )
        yield DiscoveryHit(
            "Open Provider Setup",
            self.open_provider_config,
            help="⚙️ Manage API keys for available providers",
        )
        yield DiscoveryHit(
            "Select AI Model",
            self.open_model_picker,
            help="🤖 Choose which AI model to use",
        )
        yield DiscoveryHit(
            "Show usage",
            self.chat_screen.action_show_usage,
            help="Display usage information for the current session",
        )

    async def search(self, query: str) -> AsyncGenerator[Hit, None]:
        """Search for commands in alphabetical order."""
        matcher = self.matcher(query)

        # Define all commands in alphabetical order
        commands = [
            (
                "Codebase: Delete Codebase Index",
                self.chat_screen.delete_codebase_command,
                "Delete an existing codebase index",
            ),
            (
                "Codebase: Index Codebase",
                self.chat_screen.index_codebase_command,
                "Index a repository into the codebase graph",
            ),
            (
                "Open Provider Setup",
                self.open_provider_config,
                "⚙️ Manage API keys for available providers",
            ),
            (
                "Select AI Model",
                self.open_model_picker,
                "🤖 Choose which AI model to use",
            ),
            (
                "Show usage",
                self.chat_screen.action_show_usage,
                "Display usage information for the current session",
            ),
        ]

        for title, callback, help_text in commands:
            score = matcher.match(title)
            if score > 0:
                yield Hit(score, matcher.highlight(title), callback, help=help_text)
