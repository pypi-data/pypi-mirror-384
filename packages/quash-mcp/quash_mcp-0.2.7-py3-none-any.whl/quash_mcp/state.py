"""
Session state manager for Quash MCP Server.
Maintains configuration and device state throughout a session.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict


@dataclass
class SessionState:
    """Manages session state for the MCP server."""

    # Device information
    device_serial: Optional[str] = None
    device_info: Optional[Dict[str, str]] = None
    portal_ready: bool = False

    # Agent configuration
    config: Dict[str, Any] = field(default_factory=lambda: {
        "model": "anthropic/claude-sonnet-4",
        "temperature": 0.2,
        "max_steps": 15,
        "vision": False,
        "reasoning": False,
        "reflection": False,
        "debug": False,
        "api_key": None  # Stores quash_api_key
    })

    # Latest suite execution
    latest_suite: Optional[Dict[str, Any]] = None

    # Storage path for persistent config
    _config_path: Path = field(default_factory=lambda: Path.home() / ".mahoraga" / "config.json")

    def __post_init__(self):
        """Load saved configuration after initialization"""
        self._load_config()

    def reset(self):
        """Reset all state to defaults."""
        self.device_serial = None
        self.device_info = None
        self.portal_ready = False
        self.config = {
            "model": "anthropic/claude-sonnet-4",
            "temperature": 0.2,
            "max_steps": 15,
            "vision": False,
            "reasoning": False,
            "reflection": False,
            "debug": False,
            "api_key": None
        }

    def is_device_connected(self) -> bool:
        """Check if a device is connected."""
        return self.device_serial is not None

    def is_configured(self) -> bool:
        """Check if configuration is set (at minimum mahoraga API key)."""
        return self.config.get("api_key") is not None

    def is_ready(self) -> bool:
        """Check if system is ready for execution."""
        return self.is_device_connected() and self.is_configured()

    def update_config(self, **kwargs):
        """Update configuration with provided parameters."""
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
        # Save to disk after updating
        self._save_config()

    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary without exposing sensitive data."""
        summary = self.config.copy()
        if summary.get("api_key"):
            summary["api_key_set"] = True
            summary["api_key"] = "***"
        else:
            summary["api_key_set"] = False
            summary["api_key"] = None
        return summary

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "device_serial": self.device_serial,
            "device_info": self.device_info,
            "portal_ready": self.portal_ready,
            "config": self.get_config_summary()
        }

    def _load_config(self):
        """Load configuration from disk if it exists"""
        try:
            if self._config_path.exists():
                with open(self._config_path, 'r') as f:
                    saved_config = json.load(f)
                    # Only load mahoraga API key (other settings are session-specific)
                    if "api_key" in saved_config and saved_config["api_key"]:
                        self.config["api_key"] = saved_config["api_key"]
        except Exception:
            pass  # Fail silently if can't load

    def _save_config(self):
        """Save configuration to disk"""
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            # Only save mahoraga API key (other settings are session-specific)
            config_to_save = {
                "api_key": self.config.get("api_key")
            }
            with open(self._config_path, 'w') as f:
                json.dump(config_to_save, f)
        except Exception:
            pass  # Fail silently if can't save


# Global session state instance
_session_state = SessionState()


def get_state() -> SessionState:
    """Get the global session state instance."""
    return _session_state


def reset_state():
    """Reset the global session state."""
    _session_state.reset()