import pygame
from cogworks.component import Component
from cogworks.pygame_wrappers.event_manager import EventManager


class UITransform(Component):
    """
    UITransform defines the position, size, and anchor of a UI element.

    Now takes camera position and zoom into account, so UI elements
    can follow world-space movement or adjust correctly to zoom.
    """

    def __init__(self, x=0, y=0, width=1, height=1, anchor="topleft", relative=True, world_space=False, debug=False):
        """
        Args:
            x, y (float | int): Position (fractional or absolute).
            width, height (float | int): Size (fractional or absolute).
            anchor (str): Position anchor: 'topleft', 'center', etc.
            relative (bool): Whether to treat coordinates as fractions of screen size.
            world_space (bool): If True, interpret x/y as world coordinates affected by camera.
        """
        super().__init__()
        self.anchor = anchor
        self.relative = relative
        self.world_space = world_space
        self._x, self._y = x, y
        self._width, self._height = width, height
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.debug = debug

    def on_enabled(self):
        self.game_object.is_ui_object = True
        EventManager.get_instance().subscribe(self._on_event)

    def on_disabled(self):
        self.game_object.is_ui_object = False
        EventManager.get_instance().unsubscribe(self._on_event)

    def on_remove(self):
        self.game_object.is_ui_object = False
        EventManager.get_instance().unsubscribe(self._on_event)

    def start(self):
        self.game_object.is_ui_object = True
        if self.world_space and self.relative:
            self.relative = False
        self.update_rect()

    def update_rect(self):
        parent_go = self.game_object.parent
        parent_transform = parent_go.get_component("UITransform") if parent_go else None

        if parent_go and parent_go.has_component("UILayout"):
            return

        screen_width, screen_height = pygame.display.get_window_size()
        camera = self.game_object.scene.camera_component

        # --- Determine Base Dimensions ---
        if parent_transform and self.relative:
            width = int(self._width * parent_transform.rect.width)
            height = int(self._height * parent_transform.rect.height)
        elif self.relative:
            width = int(self._width * screen_width)
            height = int(self._height * screen_height)
        else:
            width, height = int(self._width), int(self._height)

        # --- Determine Base Position ---
        if self.world_space and camera:
            # Treat _x/_y as world coordinates directly
            x, y = camera.world_to_screen(float(self._x), float(self._y))
            width = camera.scale_length(width)
            height = camera.scale_length(height)
        elif parent_transform and self.relative:
            px, py = self._get_parent_anchor_origin(parent_transform)
            x = px + int(self._x * parent_transform.rect.width)
            y = py + int(self._y * parent_transform.rect.height)
        elif self.relative:
            x = int(self._x * screen_width)
            y = int(self._y * screen_height)
        else:
            x, y = int(self._x), int(self._y)

        # --- Apply This Element's Own Anchor ---
        if self.anchor == "center":
            x -= width // 2
            y -= height // 2
        elif self.anchor == "topright":
            x -= width
        elif self.anchor == "bottomleft":
            y -= height
        elif self.anchor == "bottomright":
            x -= width
            y -= height

        self.rect = pygame.Rect(x, y, width, height)

    def _get_parent_anchor_origin(self, parent_transform):
        rect = parent_transform.rect
        anchor = parent_transform.anchor
        if anchor == "topleft":
            return rect.left, rect.top
        elif anchor == "topright":
            return rect.right, rect.top
        elif anchor == "bottomleft":
            return rect.left, rect.bottom
        elif anchor == "bottomright":
            return rect.right, rect.bottom
        elif anchor == "center":
            return rect.centerx, rect.centery
        else:
            return rect.topleft

    def set_position(self, x, y):
        self._x, self._y = x, y
        self.update_rect()

    def set_size(self, width, height):
        self._width, self._height = width, height
        self.update_rect()

    def set_anchor(self, anchor):
        self.anchor = anchor
        self.update_rect()

    def _on_event(self, event):
        if event.type == pygame.VIDEORESIZE:
            self.update_rect()
            layout = self.game_object.get_component("UILayout")
            if layout:
                layout.update_layout()

    def render(self, surface):
        if not self.debug:
            return
        colour = (0, 255, 0) if not self.game_object.parent else (255, 255, 0)
        pygame.draw.rect(surface, colour, self.rect, 1)

        # Small anchor marker
        pygame.draw.circle(surface, (255, 0, 0), self.rect.topleft, 3)