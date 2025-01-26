from typing import Dict, Callable, Optional, List
import keyboard
import threading
import logging
from dataclasses import dataclass
from enum import Enum


class KeyAction(Enum):
    PRESS = 'press'
    RELEASE = 'release'
    HOLD = 'hold'


@dataclass
class KeyBinding:
    key: str
    action: KeyAction
    callback: Callable
    description: str
    enabled: bool = True


class KeyboardHandler:
    def __init__(self):
        self.logger = logging.getLogger("nexus.keyboard")
        self.bindings: Dict[str, KeyBinding] = {}
        self.is_listening = False
        self.listener_thread: Optional[threading.Thread] = None
        self._setup_default_bindings()

    def _setup_default_bindings(self):
        """Setup default key bindings"""
        self.register_binding(
            'ctrl+c',
            KeyAction.PRESS,
            self.handle_exit,
            'Exit application'
        )

        self.register_binding(
            'ctrl+p',
            KeyAction.PRESS,
            self.toggle_pause,
            'Pause/Resume scan'
        )

        self.register_binding(
            'ctrl+h',
            KeyAction.PRESS,
            self.show_help,
            'Show help menu'
        )

    def register_binding(self,
                         key: str,
                         action: KeyAction,
                         callback: Callable,
                         description: str):
        """Register a new key binding"""
        binding = KeyBinding(
            key=key,
            action=action,
            callback=callback,
            description=description
        )

        self.bindings[key] = binding
        if self.is_listening:
            self._add_hotkey(binding)

    def unregister_binding(self, key: str):
        """Remove a key binding"""
        if key in self.bindings:
            if self.is_listening:
                keyboard.remove_hotkey(key)
            del self.bindings[key]

    def start_listening(self):
        """Start keyboard listener"""
        if not self.is_listening:
            self.is_listening = True
            self._register_all_hotkeys()
            self.listener_thread = threading.Thread(
                target=self._keyboard_listener,
                daemon=True
            )
            self.listener_thread.start()

    def stop_listening(self):
        """Stop keyboard listener"""
        if self.is_listening:
            self.is_listening = False
            keyboard.unhook_all()
            if self.listener_thread:
                self.listener_thread.join()
                self.listener_thread = None

    def _keyboard_listener(self):
        """Main keyboard listener loop"""
        try:
            keyboard.wait()
        except Exception as e:
            self.logger.error(f"Keyboard listener error: {str(e)}")
            self.stop_listening()

    def _register_all_hotkeys(self):
        """Register all key bindings as hotkeys"""
        for binding in self.bindings.values():
            if binding.enabled:
                self._add_hotkey(binding)

    def _add_hotkey(self, binding: KeyBinding):
        """Add single hotkey"""
        if binding.action == KeyAction.PRESS:
            keyboard.add_hotkey(
                binding.key,
                binding.callback,
                suppress=True
            )
        elif binding.action == KeyAction.HOLD:
            keyboard.on_press_key(
                binding.key,
                lambda _: binding.callback(),
                suppress=True
            )

    def handle_exit(self):
        """Handle application exit"""
        self.logger.info("Exit requested via keyboard")
        self.stop_listening()
        raise KeyboardInterrupt

    def toggle_pause(self):
        """Toggle scan pause state"""
        self.logger.info("Scan pause toggled via keyboard")
        # Implementation specific to scan control

    def show_help(self):
        """Display help menu"""
        help_text = "\nAvailable Key Bindings:\n"
        for binding in self.bindings.values():
            if binding.enabled:
                help_text += f"{binding.key}: {binding.description}\n"
        print(help_text)

    def get_active_bindings(self) -> List[KeyBinding]:
        """Get list of active key bindings"""
        return [b for b in self.bindings.values() if b.enabled]

    def enable_binding(self, key: str):
        """Enable a key binding"""
        if key in self.bindings:
            self.bindings[key].enabled = True
            if self.is_listening:
                self._add_hotkey(self.bindings[key])

    def disable_binding(self, key: str):
        """Disable a key binding"""
        if key in self.bindings:
            self.bindings[key].enabled = False
            if self.is_listening:
                keyboard.remove_hotkey(key)

    def is_binding_enabled(self, key: str) -> bool:
        """Check if a key binding is enabled"""
        return key in self.bindings and self.bindings[key].enabled
