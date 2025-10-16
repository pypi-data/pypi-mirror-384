import math
import pygame
from cogworks.component import Component

class Transform(Component):
    """
    Transform component to track position, rotation, and scale of a GameObject.

    Supports both local (relative to parent) and world (absolute) transforms.

    Attributes:
        local_x (float): Local X position relative to parent.
        local_y (float): Local Y position relative to parent.
        local_rotation (float): Local rotation in degrees relative to parent.
        local_scale_x (float): Local scale along X axis.
        local_scale_y (float): Local scale along Y axis.
    """

    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        rotation: float = 0,
        scale_x: float = 1,
        scale_y: float | None = None,
        debug: bool = False,
        z_index: int = 1
    ):
        super().__init__()
        self.start_x = x
        self.start_y = y
        self.local_x = x
        self.local_y = y

        self.start_rotation = rotation
        self.local_rotation = rotation

        self.start_scale_x = scale_x
        self.local_scale_x = scale_x
        self.start_scale_y = scale_y if scale_y is not None else scale_x
        self.local_scale_y = self.start_scale_y

        self.debug = debug
        self.z_index = z_index

        self.world_bound_x: float = math.inf
        self.world_bound_y: float = math.inf

    def start(self):
        """Initialise world bounds and reset transform to start values."""
        self.local_x = self.start_x
        self.local_y = self.start_y
        self.local_rotation = self.start_rotation
        self.local_scale_x = self.start_scale_x
        self.local_scale_y = self.start_scale_y

        self.world_bound_x = self.game_object.scene.engine.world_bound_x
        self.world_bound_y = self.game_object.scene.engine.world_bound_y

    # --- Local setters / getters ---
    def set_local_position(self, x: float, y: float):
        self.local_x = x
        self.local_y = y

    def get_local_position(self) -> tuple[float, float]:
        return self.local_x, self.local_y

    def set_local_rotation(self, degrees: float):
        self.local_rotation = degrees % 360

    def get_local_rotation(self, radians: bool = True) -> float:
        return math.radians(self.local_rotation) if radians else self.local_rotation

    def set_local_scale(self, sx: float, sy: float | None = None):
        self.local_scale_x = sx
        self.local_scale_y = sy if sy is not None else sx

    def get_local_scale(self) -> tuple[float, float]:
        return self.local_scale_x, self.local_scale_y

    # --- World setters ---
    def set_world_position(self, x: float, y: float):
        if self.game_object and self.game_object.parent:
            px, py = self.game_object.parent.transform.get_world_position()
            self.local_x = x - px
            self.local_y = y - py
        else:
            self.local_x = x
            self.local_y = y

    def set_world_rotation(self, degrees: float):
        if self.game_object and self.game_object.parent:
            parent_rotation = self.game_object.parent.transform.get_world_rotation(radians=False)
            self.local_rotation = (degrees - parent_rotation) % 360
        else:
            self.local_rotation = degrees % 360

    def set_world_scale(self, sx: float, sy: float | None = None):
        if self.game_object and self.game_object.parent:
            psx, psy = self.game_object.parent.transform.get_world_scale()
            self.local_scale_x = sx / psx
            self.local_scale_y = (sy / psy) if sy is not None else (sx / psx)
        else:
            self.local_scale_x = sx
            self.local_scale_y = sy if sy is not None else sx

    def rotate(self, delta_degrees: float):
        self.local_rotation = (self.local_rotation + delta_degrees) % 360

    # --- World getters ---
    def get_world_position(self) -> tuple[float, float]:
        if self.game_object and self.game_object.parent:
            px, py = self.game_object.parent.transform.get_world_position()
            return px + self.local_x, py + self.local_y
        return self.local_x, self.local_y

    def get_world_rotation(self, radians: bool = True) -> float:
        angle = self.local_rotation
        if self.game_object and self.game_object.parent:
            angle += self.game_object.parent.transform.get_world_rotation(radians=False)
        return math.radians(angle) if radians else angle

    def get_world_scale(self) -> tuple[float, float]:
        sx, sy = self.local_scale_x, self.local_scale_y
        if self.game_object and self.game_object.parent:
            psx, psy = self.game_object.parent.transform.get_world_scale()
            return sx * psx, sy * psy
        return sx, sy

    # --- Direction helpers ---
    def get_forward(self) -> tuple[float, float]:
        angle = self.get_world_rotation(radians=True)
        return math.cos(angle), math.sin(angle)

    def get_back(self) -> tuple[float, float]:
        fx, fy = self.get_forward()
        return -fx, -fy

    def get_right(self) -> tuple[float, float]:
        angle = self.get_world_rotation(radians=True)
        return math.cos(angle + math.pi / 2), math.sin(angle + math.pi / 2)

    def get_left(self) -> tuple[float, float]:
        rx, ry = self.get_right()
        return -rx, -ry

    # --- Bounds check ---
    def check_bounds(self) -> None:
        x, y = self.get_world_position()
        if x < -self.world_bound_x or x > self.world_bound_x or y < -self.world_bound_y or y > self.world_bound_y:
            self.game_object.destroy()

    # --- Debug rendering ---
    def render(self, surface: pygame.Surface):
        if not self.debug:
            return

        camera = self.game_object.scene.camera_component
        x, y = camera.world_to_screen(*self.get_world_position()) if camera else self.get_world_position()
        fx, fy = self.get_forward()
        rx, ry = self.get_right()

        length = 30  # Visual length of direction vectors
        forward_end = (x + fx * length, y + fy * length)
        right_end = (x + rx * length, y + ry * length)

        # Draw position
        pygame.draw.circle(surface, (255, 255, 0), (int(x), int(y)), 5)
        # Draw forward
        pygame.draw.line(surface, (0, 255, 0), (x, y), forward_end, 2)
        # Draw right
        pygame.draw.line(surface, (255, 0, 0), (x, y), right_end, 2)
