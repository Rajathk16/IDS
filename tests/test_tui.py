"""Unit tests for the Textual TUI screens and tab navigation."""

import asyncio
import pytest
from src.tui.app import IoTIDSTuiApp


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_tui_app_initialization_and_tabs():
    """Verify that the TUI app initializes with all 6 operational tabs."""
    async def _run():
        app = IoTIDSTuiApp()
        async with app.run_test() as pilot:
            # Check tabs are present
            assert app.query_one("#tab-chat") is not None
            assert app.query_one("#tab-runs") is not None
            assert app.query_one("#tab-logs") is not None
            assert app.query_one("#tab-monitor") is not None
            assert app.query_one("#tab-policies") is not None
            assert app.query_one("#tab-settings") is not None

            # Test tab switching shortcut action
            app.action_switch_tab("tab-monitor")
            await pilot.pause()
            tabs = app.query_one("#main-tabs")
            assert tabs.active == "tab-monitor"

            app.action_switch_tab("tab-policies")
            await pilot.pause()
            assert tabs.active == "tab-policies"

    asyncio.run(_run())
