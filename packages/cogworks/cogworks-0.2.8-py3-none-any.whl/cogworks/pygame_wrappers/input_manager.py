import pygame
from cogworks.pygame_wrappers.event_manager import EventManager


class InputManager:
    _instance = None

    @staticmethod
    def get_instance():
        if InputManager._instance is None:
            InputManager()
        return InputManager._instance

    def __init__(self):
        if InputManager._instance is not None:
            raise Exception("InputManager is a singleton! Use get_instance() instead.")
        InputManager._instance = self

        self.keys_down = set()
        self.keys_pressed = set()
        self.keys_released = set()
        self.mouse_buttons_down = set()
        self.mouse_buttons_pressed = set()
        self.mouse_buttons_released = set()
        self.mouse_pos = (0, 0)
        self.mouse_rel = (0, 0)

        # Subscribe to the EventManager
        EventManager.get_instance().subscribe(self.handle_event)

    def handle_event(self, event):
        """Handle a single pygame event."""
        if event.type == pygame.KEYDOWN:
            if event.key not in self.keys_down:
                self.keys_pressed.add(event.key)
            self.keys_down.add(event.key)
        elif event.type == pygame.KEYUP:
            self.keys_down.discard(event.key)
            self.keys_released.add(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button not in self.mouse_buttons_down:
                self.mouse_buttons_pressed.add(event.button)
            self.mouse_buttons_down.add(event.button)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.mouse_buttons_down.discard(event.button)
            self.mouse_buttons_released.add(event.button)
        elif event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
            self.mouse_rel = event.rel

    def update(self):
        """Call at the start of each frame to reset 'pressed'/'released' states."""
        self.keys_pressed.clear()
        self.keys_released.clear()
        self.mouse_buttons_pressed.clear()
        self.mouse_buttons_released.clear()
        self.mouse_rel = (0, 0)

        # ---------------- Query Helpers ---------------- #

    def is_key_down(self, key):
        """Return True if the key is currently held down."""
        return key in self.keys_down

    def is_key_pressed(self, key):
        """Return True if the key was pressed this frame."""
        return key in self.keys_pressed

    def is_key_released(self, key):
        """Return True if the key was released this frame."""
        return key in self.keys_released

    def is_mouse_button_down(self, button):
        """Return True if the mouse button is currently held down."""
        return button in self.mouse_buttons_down

    def is_mouse_button_pressed(self, button):
        """Return True if the mouse button was pressed this frame."""
        return button in self.mouse_buttons_pressed

    def is_mouse_button_released(self, button):
        """Return True if the mouse button was released this frame."""
        return button in self.mouse_buttons_released

    def get_mouse_position(self):
        return self.mouse_pos

    def get_mouse_motion(self):
        return self.mouse_rel
