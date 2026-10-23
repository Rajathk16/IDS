"""Policies screen for configuring alert thresholds, severity rules, and audit logs."""

from __future__ import annotations

from typing import List
from rich.markdown import Markdown
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, DataTable, Input, Label, RichLog, Select
from src.core.policies import AlertPolicy, get_policies, save_policies


class PoliciesScreenWidget(Widget):
    """Enables inspecting alert policies, toggling enable/disable, and reviewing the policy audit log."""

    DEFAULT_CSS = """
    PoliciesScreenWidget {
        height: 100%;
        layout: vertical;
    }
    #policy-actions-bar {
        height: auto;
        padding: 1;
        background: $panel;
    }
    #policy-actions-bar Button {
        margin-right: 1;
    }
    #policy-table-box {
        height: 3fr;
        border: solid $accent;
    }
    #policy-audit-box {
        height: 2fr;
        border: solid $secondary;
        background: $surface;
        padding: 1;
    }
    #policy-status-lbl {
        color: $accent;
        padding: 0 1;
    }
    """

    def __init__(self):
        super().__init__()
        self._cached_policies: List[AlertPolicy] = []
        self._selected_policy_id: str | None = None

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="policy-actions-bar"):
                yield Button("Toggle Enabled / Disabled", id="btn-toggle-policy", variant="primary")
                yield Button("Raise Confidence (+0.05)", id="btn-raise-conf")
                yield Button("Lower Confidence (-0.05)", id="btn-lower-conf")
                yield Button("🔄 Refresh Policies", id="btn-refresh-policies")
            yield Label("Select a policy row to adjust alert thresholds.", id="policy-status-lbl")

            with Container(id="policy-table-box"):
                yield DataTable(id="table-policies", cursor_type="row")

            with Container(id="policy-audit-box"):
                yield Label("[bold magenta]Policy Modification Audit History[/bold magenta]")
                yield RichLog(id="policy-audit-log", wrap=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#table-policies", DataTable)
        table.add_columns("Policy ID", "Policy Name", "Attack Category", "Min Conf", "Alert Severity", "Status")
        self.refresh_policies()

    def refresh_policies(self) -> None:
        pol_cfg = get_policies()
        self._cached_policies = pol_cfg.policies

        table = self.query_one("#table-policies", DataTable)
        table.clear()

        for i, p in enumerate(self._cached_policies):
            status_text = "[bold green]ENABLED[/bold green]" if p.enabled else "[dim red]DISABLED[/dim red]"
            sev_color = "red" if p.severity in ("HIGH", "CRITICAL") else ("yellow" if p.severity == "MEDIUM" else "green")
            table.add_row(
                p.policy_id,
                p.name,
                p.attack_category,
                f"{p.min_confidence:.2f}",
                f"[{sev_color}]{p.severity}[/{sev_color}]",
                status_text,
                key=str(i)
            )

        # Update audit log
        audit_log = self.query_one("#policy-audit-log", RichLog)
        audit_log.clear()
        for a in reversed(pol_cfg.audit_log[-20:]):
            audit_log.write(
                f"[dim]{a.timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/dim] "
                f"[bold cyan][{a.action}][/bold cyan] [yellow]{a.policy_id}[/yellow]: {a.details}"
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        try:
            idx = int(event.row_key.value)
            if 0 <= idx < len(self._cached_policies):
                p = self._cached_policies[idx]
                self._selected_policy_id = p.policy_id
                status = self.query_one("#policy-status-lbl", Label)
                status.update(f"Selected Policy: {p.policy_id} ('{p.name}') - Current Conf: {p.min_confidence:.2f}")
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        status = self.query_one("#policy-status-lbl", Label)

        if btn_id == "btn-refresh-policies":
            self.refresh_policies()
            return

        if not self._selected_policy_id:
            status.update("⚠️ Please select a policy from the table first.")
            return

        pol_cfg = get_policies()
        target_pol = next((p for p in pol_cfg.policies if p.policy_id == self._selected_policy_id), None)
        if not target_pol:
            return

        if btn_id == "btn-toggle-policy":
            new_state = not target_pol.enabled
            pol_cfg.toggle_policy(self._selected_policy_id, new_state)
            save_policies()
            status.update(f"✓ Policy {self._selected_policy_id} {'Enabled' if new_state else 'Disabled'}.")
            self.refresh_policies()

        elif btn_id == "btn-raise-conf":
            new_conf = min(0.95, round(target_pol.min_confidence + 0.05, 2))
            pol_cfg.update_confidence(self._selected_policy_id, new_conf)
            save_policies()
            status.update(f"✓ Policy {self._selected_policy_id} min confidence set to {new_conf:.2f}.")
            self.refresh_policies()

        elif btn_id == "btn-lower-conf":
            new_conf = max(0.10, round(target_pol.min_confidence - 0.05, 2))
            pol_cfg.update_confidence(self._selected_policy_id, new_conf)
            save_policies()
            status.update(f"✓ Policy {self._selected_policy_id} min confidence set to {new_conf:.2f}.")
            self.refresh_policies()
