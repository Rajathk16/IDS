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


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_tui_chat_commands_and_dispatch():
    """Verify chat commands like /help and /status dispatch without error."""
    async def _run():
        app = IoTIDSTuiApp()
        async with app.run_test() as pilot:
            chat_screen = app.query_one("ChatScreenWidget")
            log = chat_screen.query_one("#chat-log")
            
            # Dispatch help
            chat_screen._dispatch_query("/help", log)
            await pilot.pause()

            # Dispatch status
            chat_screen._dispatch_query("/status", log)
            await pilot.pause()

            # Dispatch clear
            chat_screen._dispatch_query("/clear", log)
            await pilot.pause()

    asyncio.run(_run())


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_tui_settings_reset():
    """Verify settings screen resets form values on reset defaults button."""
    from textual.widgets import Button, Input
    async def _run():
        app = IoTIDSTuiApp()
        async with app.run_test() as pilot:
            app.action_switch_tab("tab-settings")
            await pilot.pause()
            settings_screen = app.query_one("SettingsScreenWidget")
            inp = settings_screen.query_one("#inp-max-features", Input)
            inp.value = "99"
            
            # Click reset button
            btn_reset = settings_screen.query_one("#btn-reset-defaults", Button)
            btn_reset.press()
            await pilot.pause()

            # Should be restored to factory default (15)
            assert inp.value == "15"

    asyncio.run(_run())
