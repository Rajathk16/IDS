"""Policy configuration, alert threshold rules, and policy audit tracking."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AlertPolicy(BaseModel):
    """An alert policy rule for matching intrusion detection events."""

    policy_id: str
    name: str
    enabled: bool = True
    attack_category: str = Field(
        default="All",
        description="Target attack category: 'All', 'DDoS', 'DoS', 'Recon', 'Web', 'BruteForce', 'Spoofing', 'Mirai'"
    )
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    severity: str = Field(
        default="MEDIUM",
        description="Assigned severity: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'"
    )
    description: str


class PolicyAuditRecord(BaseModel):
    """Record of a policy configuration modification."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    action: str  # e.g., "ENABLE", "DISABLE", "UPDATE_THRESHOLD", "CREATE"
    policy_id: str
    details: str


class PolicyConfig(BaseModel):
    """Collection of alert policies and audit records."""

    policies: List[AlertPolicy] = Field(default_factory=list)
    audit_log: List[PolicyAuditRecord] = Field(default_factory=list)

    @classmethod
    def default_policies(cls) -> PolicyConfig:
        """Create factory default policies for IoT network security."""
        policies = [
            AlertPolicy(
                policy_id="POL-001",
                name="Critical Mirai Botnet Activity",
                enabled=True,
                attack_category="Mirai",
                min_confidence=0.6,
                severity="CRITICAL",
                description="Immediately flag Mirai greeth/greip/udpplain botnet traffic as CRITICAL."
            ),
            AlertPolicy(
                policy_id="POL-002",
                name="High Volume DDoS Flood",
                enabled=True,
                attack_category="DDoS",
                min_confidence=0.7,
                severity="HIGH",
                description="Elevate confirmed distributed denial of service attack floods to HIGH severity."
            ),
            AlertPolicy(
                policy_id="POL-003",
                name="Web & Command Injection Exploit",
                enabled=True,
                attack_category="Web",
                min_confidence=0.65,
                severity="HIGH",
                description="Flag SQLi, XSS, and remote command injection IoT attacks as HIGH severity."
            ),
            AlertPolicy(
                policy_id="POL-004",
                name="Reconnaissance & Port Scanning",
                enabled=True,
                attack_category="Recon",
                min_confidence=0.6,
                severity="MEDIUM",
                description="Flag port sweeps, host discovery, and vulnerability scans as MEDIUM severity."
            ),
            AlertPolicy(
                policy_id="POL-005",
                name="Denial of Service (DoS)",
                enabled=True,
                attack_category="DoS",
                min_confidence=0.6,
                severity="MEDIUM",
                description="Flag single-source DoS flooding as MEDIUM severity."
            ),
            AlertPolicy(
                policy_id="POL-006",
                name="Spoofing & Man-In-The-Middle",
                enabled=True,
                attack_category="Spoofing",
                min_confidence=0.6,
                severity="MEDIUM",
                description="Flag ARP spoofing and DNS cache poisoning as MEDIUM severity."
            ),
            AlertPolicy(
                policy_id="POL-007",
                name="Brute Force Password Guessing",
                enabled=True,
                attack_category="BruteForce",
                min_confidence=0.7,
                severity="LOW",
                description="Flag dictionary and brute force attempts on IoT credentials as LOW severity."
            ),
        ]
        return cls(
            policies=policies,
            audit_log=[
                PolicyAuditRecord(
                    action="INITIALIZE",
                    policy_id="SYSTEM",
                    details="Initialized default IoT network alert policies."
                )
            ]
        )

    def evaluate(self, attack_category: str, confidence: float) -> tuple[str, Optional[str]]:
        """
        Evaluate an event against enabled policies.
        Returns (severity, triggered_policy_name).
        Does not alter the ML classification itself.
        """
        if attack_category.lower() == "benign":
            return "INFO", None

        # Check category-specific policies first, highest severity match wins
        severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}
        highest_sev = "LOW"
        matched_policy = None

        for pol in self.policies:
            if not pol.enabled:
                continue
            if pol.attack_category.lower() in (attack_category.lower(), "all"):
                if confidence >= pol.min_confidence:
                    if severity_order.get(pol.severity, 0) >= severity_order.get(highest_sev, 0):
                        highest_sev = pol.severity
                        matched_policy = pol.name

        return highest_sev, matched_policy

    def toggle_policy(self, policy_id: str, enabled: bool) -> bool:
        """Enable or disable a policy and log to audit history."""
        for pol in self.policies:
            if pol.policy_id == policy_id:
                old = pol.enabled
                pol.enabled = enabled
                self.audit_log.append(
                    PolicyAuditRecord(
                        action="ENABLE" if enabled else "DISABLE",
                        policy_id=policy_id,
                        details=f"Policy '{pol.name}' enabled state changed from {old} to {enabled}."
                    )
                )
                return True
        return False

    def update_confidence(self, policy_id: str, min_confidence: float) -> bool:
        """Update confidence threshold and log to audit history."""
        for pol in self.policies:
            if pol.policy_id == policy_id:
                old = pol.min_confidence
                pol.min_confidence = min_confidence
                self.audit_log.append(
                    PolicyAuditRecord(
                        action="UPDATE_THRESHOLD",
                        policy_id=policy_id,
                        details=f"Policy '{pol.name}' min confidence changed from {old:.2f} to {min_confidence:.2f}."
                    )
                )
                return True
        return False

    def save_to_file(self, config_path: Path = Path("config/policies.json")) -> None:
        """Save policy configuration to file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(mode="json"), f, indent=2)

    @classmethod
    def load_from_file(cls, config_path: Path = Path("config/policies.json")) -> PolicyConfig:
        """Load from file or return factory defaults."""
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls(**data)
            except Exception:
                pass
        cfg = cls.default_policies()
        cfg.save_to_file(config_path)
        return cfg


_policies_instance: Optional[PolicyConfig] = None


def get_policies() -> PolicyConfig:
    """Return the global PolicyConfig singleton."""
    global _policies_instance
    if _policies_instance is None:
        _policies_instance = PolicyConfig.load_from_file()
    return _policies_instance


def save_policies() -> None:
    """Persist the global PolicyConfig."""
    global _policies_instance
    if _policies_instance is not None:
        _policies_instance.save_to_file()
