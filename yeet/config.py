"""
Yeet - Configuration Manager
App ID: gay.geeks.Yeet
"""

import os
import json
import logging
from typing import List, Dict, Any, Callable
from .models import Target, ThrowableItem, PhysicsConfig, ServerConfig, WebhookConfig, get_default_targets, get_default_items

logger = logging.getLogger("yeet.config")

class ConfigManager:
    def __init__(self, config_path: str = None):
        if config_path:
            self.config_path = config_path
        else:
            xdg_config_home = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
            yeet_config_dir = os.path.join(xdg_config_home, "yeet")
            os.makedirs(yeet_config_dir, exist_ok=True)
            self.config_path = os.path.join(yeet_config_dir, "config.json")

        self.targets: List[Target] = []
        self.items: Dict[str, ThrowableItem] = {}
        self.physics: PhysicsConfig = PhysicsConfig()
        self.server: ServerConfig = ServerConfig()
        self.webhooks: WebhookConfig = WebhookConfig()
        self._change_listeners: List[Callable[[], None]] = []

        self.load()

    def add_change_listener(self, callback: Callable[[], None]):
        self._change_listeners.append(callback)

    def notify_changes(self):
        for cb in self._change_listeners:
            try:
                cb()
            except Exception as e:
                logger.error(f"Error in config change listener: {e}")

    def load(self):
        if not os.path.exists(self.config_path):
            logger.info(f"Configuration file not found at {self.config_path}, creating defaults.")
            self.targets = get_default_targets()
            self.items = get_default_items()
            self.physics = PhysicsConfig()
            self.server = ServerConfig()
            self.save()
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.targets = [Target.from_dict(t) for t in data.get("targets", [])]
            if not self.targets:
                self.targets = get_default_targets()

            items_data = data.get("items", {})
            self.items = {k: ThrowableItem.from_dict(v) for k, v in items_data.items()}
            if not self.items:
                self.items = get_default_items()
            else:
                # Merge any newly added default items (e.g. beachball)
                for k, v in get_default_items().items():
                    if k not in self.items:
                        self.items[k] = v

            self.physics = PhysicsConfig.from_dict(data.get("physics", {}))
            self.server = ServerConfig.from_dict(data.get("server", {}))
            self.webhooks = WebhookConfig.from_dict(data.get("webhooks", {}))
            logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}. Falling back to defaults.")
            self.targets = get_default_targets()
            self.items = get_default_items()
            self.physics = PhysicsConfig()
            self.server = ServerConfig()
            self.webhooks = WebhookConfig()

    def save(self):
        data = {
            "targets": [t.to_dict() for t in self.targets],
            "items": {k: v.to_dict() for k, v in self.items.items()},
            "physics": self.physics.to_dict(),
            "server": self.server.to_dict(),
            "webhooks": self.webhooks.to_dict(),
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved configuration to {self.config_path}")
            self.notify_changes()
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    def to_client_dict(self) -> Dict[str, Any]:
        """JSON-serializable payload sent to OBS overlay over WebSocket."""
        return {
            "targets": [t.to_dict() for t in self.targets],
            "items": {k: v.to_dict() for k, v in self.items.items()},
            "physics": self.physics.to_dict(),
        }
