from cogworks.component import Component
from cogworks.pygame_wrappers.window import Window


class Camera(Component):
    """
    Represents a 2D camera component used to control view position and zoom level.

    The camera manages how world coordinates are transformed into screen coordinates,
    and vice versa. It supports zooming, centering, visibility checks, and world-space
    position queries for key points on the viewport.
    """

    def __init__(self) -> None:
        super().__init__()
        self.offset_x: float = 0
        self.offset_y: float = 0
        self.zoom: float = 1.0  # 1.0 = normal, <1.0 = zoom out, >1.0 = zoom in

    def move(self, dx: float, dy: float) -> None:
        """
        Move the camera by the specified deltas in world space.

        Args:
            dx (float): The change in the x-axis.
            dy (float): The change in the y-axis.
        """
        self.offset_x += dx
        self.offset_y += dy

    def get_world_position_of_point(self, point: str = "center") -> tuple[float, float]:
        """
        Get the world coordinates of a specific point on the camera's view.

        Args:
            point (str): The point on the camera view. Valid options include:
                'center', 'topleft', 'topright', 'topcenter',
                'bottomleft', 'bottomright', 'bottomcenter',
                'leftcenter', 'rightcenter'

        Returns:
            tuple[float, float]: The (x, y) position in world coordinates.

        Raises:
            ValueError: If an invalid point name is provided.
        """
        # Screen dimensions
        sw, sh = Window.get_instance().get_size()
        points = {
            "center": (sw / 2, sh / 2),
            "topleft": (0, 0),
            "topright": (sw, 0),
            "topcenter": (sw / 2, 0),
            "bottomleft": (0, sh),
            "bottomright": (sw, sh),
            "bottomcenter": (sw / 2, sh),
            "leftcenter": (0, sh / 2),
            "rightcenter": (sw, sh / 2),
        }

        if point not in points:
            raise ValueError(f"Invalid point '{point}' for camera. Valid options: {list(points.keys())}")

        screen_x, screen_y = points[point]
        # Convert from screen coordinates to world coordinates
        world_x, world_y = self.screen_to_world(float(screen_x), float(screen_y))

        return world_x, world_y

    def set_zoom(self, zoom: float) -> None:
        """
        Set the camera's zoom level.

        Args:
            zoom (float): The zoom factor. Values > 1 zoom in, < 1 zoom out.

        Raises:
            ValueError: If the zoom value is less than or equal to zero.
        """
        if zoom <= 0:
            raise ValueError("Zoom must be greater than 0")
        self.zoom = zoom

    def world_to_screen(self, x: float, y: float) -> tuple[float, float]:
        """
        Convert world coordinates to screen coordinates based on the current
        camera offset and zoom level.

        Args:
            x (float): World x-coordinate.
            y (float): World y-coordinate.

        Returns:
            tuple[float, float]: Corresponding (x, y) position on the screen.
        """
        screen_x = (x - self.offset_x) * self.zoom
        screen_y = (y - self.offset_y) * self.zoom
        return screen_x, screen_y

    def screen_to_world(self, screen_x: float, screen_y: float) -> tuple[float, float]:
        """
        Convert screen coordinates back to world coordinates, considering
        the current offset and zoom.

        Args:
            screen_x (float): Screen x-coordinate.
            screen_y (float): Screen y-coordinate.

        Returns:
            tuple[float, float]: The equivalent (x, y) world position.
        """
        world_x = screen_x / self.zoom + self.offset_x
        world_y = screen_y / self.zoom + self.offset_y
        return world_x, world_y

    def scale_length(self, length: float) -> float:
        """
        Scale a given length or size according to the current zoom level.

        Args:
            length (float): The value to scale.

        Returns:
            float: The scaled length.
        """
        return length * self.zoom

    def center_on(self, x: float, y: float, screen_width: float, screen_height: float) -> None:
        """
        Center the camera on a specific world position.

        Adjusts the offset so that the given point appears at the centre
        of the screen, factoring in zoom.

        Args:
            x (float): World x-coordinate to center on.
            y (float): World y-coordinate to center on.
            screen_width (float): Width of the screen in pixels.
            screen_height (float): Height of the screen in pixels.
        """
        self.offset_x = x - (screen_width / 2) / self.zoom
        self.offset_y = y - (screen_height / 2) / self.zoom

    def is_visible(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        tolerance: float = 500.0
    ) -> bool:
        """
        Determine whether a rectangular object is visible within the camera view.

        Args:
            x (float): World x-position of the object centre.
            y (float): World y-position of the object centre.
            width (float): Object width (after scaling or zoom).
            height (float): Object height (after scaling or zoom).
            tolerance (float): Extra margin for visibility checks (default: 500).

        Returns:
            bool: True if any part of the object is visible, False if it's completely outside.
        """
        top, bottom, left, right = self.get_bounds()

        obj_left = x - width / 2
        obj_right = x + width / 2
        obj_top = y - height / 2
        obj_bottom = y + height / 2

        return not (
            obj_right < left - tolerance
            or obj_left > right + tolerance
            or obj_bottom < top - tolerance
            or obj_top > bottom + tolerance
        )

    def get_bounds(self) -> tuple[float, float, float, float]:
        """
        Get the current camera bounds in world coordinates.

        Returns:
            tuple[float, float, float, float]: The (top, bottom, left, right)
            coordinates of the camera’s visible region.
        """
        w, h = Window.get_instance().get_size()
        left = self.offset_x
        top = self.offset_y
        right = self.offset_x + w / self.zoom
        bottom = self.offset_y + h / self.zoom
        return top, bottom, left, right
