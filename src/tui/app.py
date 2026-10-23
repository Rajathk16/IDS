"""Interactive Terminal User Interface (TUI) for DevRakshak IoT Intrusion & DDoS Defense System."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widget import Widget
from textual.widgets import Static, TabbedContent, TabPane
from src.core.engine import IDSEngine
from src.core.logging_config import setup_logging
from src.tui.screens.chat import ChatScreenWidget
from src.tui.screens.logs import LogsScreenWidget
from src.tui.screens.monitor import MonitorScreenWidget
from src.tui.screens.policies import PoliciesScreenWidget
from src.tui.screens.runs import RunsScreenWidget
from src.tui.screens.settings import SettingsScreenWidget


class TopControlBar(Widget):
    """Custom top header bar matching the DevRakshak cyberpunk control plane style."""

    DEFAULT_CSS = """
    TopControlBar {
        height: 1;
        layout: horizontal;
        background: #090d1a;
        padding: 0 1;
    }
    #top-left-title {
        width: 1fr;
    }
    #top-right-meta {
        width: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(
            "[bold cyan]DEVRAKSHAK[/bold cyan] [bold magenta]//[/bold magenta] [bold white]AI IOT INTRUSION & DDOS DEFENSE[/bold white]",
            id="top-left-title"
        )
        yield Static(
            "[bold green]ENGINE[/bold green] [bold cyan]•[/bold cyan] "
            "[bold white]CICIoT2023[/bold white] [bold cyan]•[/bold cyan] "
            "[bold yellow][OFFLINE][/bold yellow] [dim]MODEL:[/dim] [bold cyan]Random Forest[/bold cyan] [dim]v1.0.0[/dim]",
            id="top-right-meta"
        )


class BottomStatusBar(Widget):
    """Custom status bar footer with path, model metadata, and keybindings."""

    DEFAULT_CSS = """
    BottomStatusBar {
        height: 1;
        background: #090d1a;
        padding: 0 1;
        color: #94a3b8;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(
            "[dim]d:\\mini project[/dim]  [dim]MODEL:[/dim] [bold cyan]Random Forest[/bold cyan]  "
            "[dim]DATASET:[/dim] [bold cyan]CICIoT2023[/bold cyan]  [bold yellow][OFFLINE PROTOTYPE][/bold yellow]  "
            "[dim]|  ↵ Submit   /help Commands   1-6 Switch Tabs   Ctrl+Q Quit[/dim]"
        )


class DevRakshakApp(App):
    """DevRakshak Terminal User Interface for IoT Intrusion and DDoS Detection."""

    TITLE = "DEVRAKSHAK // AI IoT Intrusion & DDoS Defense"
    SUB_TITLE = "CICIoT2023 Real-Time Offline Telemetry"

    CSS = """
    Screen {
        background: #070a13;
        color: #e2e8f0;
    }
    TabbedContent {
        height: 1fr;
        background: #070a13;
    }
    ContentSwitcher {
        height: 1fr;
    }
    TabPane {
        height: 1fr;
        padding: 0;
        background: #070a13;
    }
    ContentTab {
        background: #090d1a;
        color: #94a3b8;
        padding: 0 2;
        border: none;
    }
    ContentTab:hover {
        background: #0f172a;
        color: #38bdf8;
    }
    ContentTab.-active {
        background: #111c35;
        color: #00f0ff;
        text-style: bold;
        border-bottom: tall #00f0ff;
    }
    Tabs {
        background: #090d1a;
        border-bottom: solid #1e293b;
    }
    """

    BINDINGS = [
        Binding("1", "switch_tab('tab-chat')", "1:Chat", show=True),
        Binding("2", "switch_tab('tab-runs')", "2:Runs", show=True),
        Binding("3", "switch_tab('tab-logs')", "3:Logs", show=True),
        Binding("4", "switch_tab('tab-monitor')", "4:Monitor", show=True),
        Binding("5", "switch_tab('tab-policies')", "5:Policies", show=True),
        Binding("6", "switch_tab('tab-settings')", "6:Settings", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.engine = IDSEngine()

    def compose(self) -> ComposeResult:
        yield TopControlBar()
        with TabbedContent(initial="tab-chat", id="main-tabs"):
            with TabPane("⚡ [1] CHAT", id="tab-chat"):
                yield ChatScreenWidget(self.engine)
            with TabPane("📄 [2] RUNS", id="tab-runs"):
                yield RunsScreenWidget(self.engine)
            with TabPane("📜 [3] LOGS", id="tab-logs"):
                yield LogsScreenWidget()
            with TabPane("📊 [4] MONITOR", id="tab-monitor"):
                yield MonitorScreenWidget(self.engine)
            with TabPane("🛡️ [5] POLICIES", id="tab-policies"):
                yield PoliciesScreenWidget()
            with TabPane("⚙️ [6] SETTINGS", id="tab-settings"):
                yield SettingsScreenWidget()
        yield BottomStatusBar()

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch active tab by keyboard shortcut."""
        tabs = self.query_one("#main-tabs", TabbedContent)
        tabs.active = tab_id


# Alias for backward-compatibility with tests and CLI
IoTIDSTuiApp = DevRakshakApp


def run_tui() -> None:
    """Launch the interactive DevRakshak terminal interface."""
    setup_logging()
    app = DevRakshakApp()
    app.run()


if __name__ == "__main__":
    run_tui()
