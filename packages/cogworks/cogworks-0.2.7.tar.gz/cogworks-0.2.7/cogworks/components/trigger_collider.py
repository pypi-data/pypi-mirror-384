import pygame
from typing import Optional, List, Set
from cogworks.component import Component

class TriggerCollider(Component):
    """
    Trigger collider component for detecting overlaps with other colliders.

    Supports rectangular and circular shapes with optional layer filtering.
    """

    def __init__(
            self,
            shape: str = "rect",
            width: int = 0,
            height: int = 0,
            radius: int = 0,
            offset_x: float = 0,
            offset_y: float = 0,
            layer: str = "Default",
            debug: bool = False,
            layer_mask: Optional[List[str]] = None
    ):
        """
        Initialize a TriggerCollider component.

        Args:
            shape (str): Type of the collider. Either "rect" for rectangle or "circle". Default is "rect".
            width (int): Width of the rectangle collider (ignored if shape is "circle"). Default is 0.
            height (int): Height of the rectangle collider (ignored if shape is "circle"). Default is 0.
            radius (int): Radius of the circle collider (ignored if shape is "rect"). Default is 0.
            offset_x (float): X-axis offset relative to the GameObject's Transform. Default is 0.
            offset_y (float): Y-axis offset relative to the GameObject's Transform. Default is 0.
            layer (str): Layer name used for collision filtering. Default is "Default".
            debug (bool): If True, the collider will render debug visuals. Default is False.
            layer_mask (Optional[List[str]]): List of layers this collider can interact with.
                None means it interacts with all layers. Default is None.
        """
        super().__init__()
        self.transform = None
        self.shape: str = shape
        self.width: int = width
        self.height: int = height
        self.radius: int = radius
        self.offset_x: float = offset_x
        self.offset_y: float = offset_y
        self.rect: Optional[pygame.Rect] = None
        self.center: Optional[tuple[float, float]] = None
        self._colliding_with: Set["TriggerCollider"] = set()
        self.layer: str = layer
        self.debug: bool = debug
        self.layer_mask: Optional[List[str]] = layer_mask

    def start(self):
        """Initialise collider dimensions and register with collision manager."""
        self.transform = self.game_object.transform

        sprite = self.game_object.get_component("Sprite")

        if self.shape == "rect" and (self.width == 0 or self.height == 0):
            if sprite:
                self.width = sprite.image.get_width()
                self.height = sprite.image.get_height()

        if self.shape == "circle" and self.radius == 0:
            if sprite:
                self.radius = max(sprite.image.get_width(), sprite.image.get_height()) // 2

        self.update_shape()

        self.game_object.scene.trigger_collision_manager.register(self)

    def update_shape(self):
        """Update collider position based on Transform and offset."""
        x, y = self.transform.get_world_position()
        x += self.offset_x
        y += self.offset_y

        if self.shape == "rect":
            self.rect = pygame.Rect(x - self.width // 2, y - self.height // 2, self.width, self.height)
            self.center = self.rect.center
        elif self.shape == "circle":
            self.center = (x, y)

    def update(self, dt: float):
        self.update_shape()

    def on_remove(self):
        self.game_object.scene.trigger_collision_manager.unregister(self)

    def intersects(self, other: "TriggerCollider") -> bool:
        """Check if this collider intersects with another, respecting layer masks."""
        if self.layer_mask and other.layer not in self.layer_mask:
            return False
        if other.layer_mask and self.layer not in other.layer_mask:
            return False

        if self.shape == "rect" and other.shape == "rect":
            return self.rect.colliderect(other.rect)
        elif self.shape == "circle" and other.shape == "circle":
            dx = self.center[0] - other.center[0]
            dy = self.center[1] - other.center[1]
            return dx * dx + dy * dy < (self.radius + other.radius) ** 2
        elif self.shape == "rect" and other.shape == "circle":
            return TriggerCollider._circle_rect_intersects(other, self)
        elif self.shape == "circle" and other.shape == "rect":
            return TriggerCollider._circle_rect_intersects(self, other)
        return False

    def render(self, surface: pygame.Surface):
        """Render collider shape for debugging if debug is enabled."""
        if not self.debug:
            return

        camera = self.game_object.scene.camera_component

        if self.shape == "rect":
            screen_x, screen_y = camera.world_to_screen(self.rect.x, self.rect.y)
            screen_width = self.rect.width * camera.zoom
            screen_height = self.rect.height * camera.zoom
            screen_rect = pygame.Rect(screen_x, screen_y, screen_width, screen_height)
            pygame.draw.rect(surface, (255, 0, 0), screen_rect, 1)
        else:
            screen_center = camera.world_to_screen(*self.center)
            screen_radius = int(self.radius * camera.zoom)
            pygame.draw.circle(surface, (255, 0, 0), (int(screen_center[0]), int(screen_center[1])), screen_radius, 1)

    @staticmethod
    def _circle_rect_intersects(circle: "TriggerCollider", rect_collider: "TriggerCollider") -> bool:
        """Check collision between a circle and rectangle collider."""
        rect = rect_collider.rect
        cx, cy = circle.center
        closest_x = max(rect.left, min(cx, rect.right))
        closest_y = max(rect.top, min(cy, rect.bottom))
        dx = cx - closest_x
        dy = cy - closest_y
        return dx * dx + dy * dy < circle.radius * circle.radius
