from cogworks import Component
import pygame
import math

class LineRenderer(Component):
    """
    LineRenderer is a component that draws a line between two points in world space,
    with support for solid, dashed, and dotted styles. The line automatically converts
    world coordinates to screen coordinates using the scene's camera, ensuring it
    renders correctly relative to camera position and zoom. Dash and dot spacing
    can be customized, and the component updates each frame to reflect any movement
    of the points.
    """

    def __init__(
            self,
            point_a: tuple[float, float],
            point_b: tuple[float, float],
            color: tuple[int, int, int] = (255, 255, 255),
            width: int = 2,
            style: str = "solid",
            dash_length: float = 10,
            dot_radius: float = 2,
            alpha: int = 255
    ):
        """
        style: "solid", "dashed", or "dotted"
        dash_length: length of dashes for dashed lines
        dot_radius: radius of dots for dotted lines
        alpha: transparency value (0 = fully transparent, 255 = fully opaque)
        """
        super().__init__()
        self.point_a = point_a
        self.point_b = point_b
        self.color = color
        self.width = width
        self.style = style
        self.dash_length = dash_length
        self.dot_radius = dot_radius
        self.alpha = alpha
        self.camera = None

    def start(self) -> None:
        self.camera = self.game_object.scene.camera_component

    def render(self, surface) -> None:
        if not self.camera:
            return

        a_screen, b_screen = self.get_screen_points()

        # Create a temporary surface with per-pixel alpha
        line_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        rgba_color = (*self.color, self.alpha)

        if self.style == "solid":
            pygame.draw.line(line_surf, rgba_color, a_screen, b_screen, self.width)
        elif self.style == "dashed":
            self._draw_dashed_line(line_surf, a_screen, b_screen, rgba_color)
        elif self.style == "dotted":
            self._draw_dotted_line(line_surf, a_screen, b_screen, rgba_color)

        # Blit the temporary surface onto the main surface
        surface.blit(line_surf, (0, 0))

    def _draw_dashed_line(self, surface, start_pos, end_pos, color):
        x1, y1 = start_pos
        x2, y2 = end_pos
        dx = x2 - x1
        dy = y2 - y1
        distance = math.hypot(dx, dy)
        if distance == 0:
            return

        dash_count = max(int(distance // self.dash_length), 1)
        for i in range(dash_count + 1):
            start_ratio = i / dash_count
            end_ratio = min((i + 0.5) / dash_count, 1)
            sx = x1 + dx * start_ratio
            sy = y1 + dy * start_ratio
            ex = x1 + dx * end_ratio
            ey = y1 + dy * end_ratio
            pygame.draw.line(surface, color, (sx, sy), (ex, ey), self.width)

    def _draw_dotted_line(self, surface, start_pos, end_pos, color):
        x1, y1 = start_pos
        x2, y2 = end_pos
        dx = x2 - x1
        dy = y2 - y1
        distance = math.hypot(dx, dy)
        if distance == 0:
            return

        dot_count = max(int(distance // (self.dot_radius * 2)), 1)
        for i in range(dot_count + 1):
            t = i / dot_count
            cx = x1 + dx * t
            cy = y1 + dy * t
            pygame.draw.circle(surface, color, (int(cx), int(cy)), self.dot_radius)

    def get_screen_points(self):
        if not self.camera:
            return self.point_a, self.point_b
        a_screen = self.camera.world_to_screen(*self.point_a)
        b_screen = self.camera.world_to_screen(*self.point_b)
        return a_screen, b_screen
