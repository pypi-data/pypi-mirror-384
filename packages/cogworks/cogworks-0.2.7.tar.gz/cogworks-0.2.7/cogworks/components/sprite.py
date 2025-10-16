import pygame
from cogworks.component import Component
from cogworks.components.transform import Transform
from cogworks.components.rigidbody2d import Rigidbody2D
from cogworks.utils.asset_loader import load_user_image


class Sprite(Component):
    """
    Sprite component for rendering images attached to a GameObject with support
    for scaling, rotation, flipping, pixel-art mode, transparency, and camera visibility.
    """

    def __init__(
        self,
        image_path: str,
        offset_x: float = 0,
        offset_y: float = 0,
        scale_factor: float = 1.0,
        alpha: int = 255,
        flip_x: bool = False,
        flip_y: bool = False,
        pixel_art_mode: bool = False
    ):
        """
        Initialise a Sprite component.

        Args:
            image_path (str): Path to the image file (inside 'assets' folder).
            offset_x (float): X-axis offset relative to the Transform.
            offset_y (float): Y-axis offset relative to the Transform.
            scale_factor (float): Multiplier for scaling the sprite.
            alpha (int): Transparency (0 = invisible, 255 = opaque).
            flip_x (bool): Flip horizontally.
            flip_y (bool): Flip vertically.
            pixel_art_mode (bool): If True, disables smoothing for crisp pixel art.
        """
        super().__init__()
        self.image_path: str = image_path
        self.original_image: pygame.Surface = load_user_image(image_path).convert_alpha()
        self.image: pygame.Surface = self.original_image
        self.rect: pygame.Rect = self.image.get_rect()

        self.transform: Transform | None = None
        self._last_transform_state: tuple | None = None
        self.camera = None
        self._scaled_image_cache: dict = {}

        self.offset_x: float = offset_x
        self.offset_y: float = offset_y
        self.scale_factor: float = scale_factor
        self.alpha: int = alpha
        self.flip_x: bool = flip_x
        self.flip_y: bool = flip_y
        self.pixel_art_mode: bool = pixel_art_mode

    def start(self):
        """Initialise transform and camera references, and apply starting transform."""
        self.transform = self.game_object.get_component(Transform)
        self.camera = self.game_object.scene.camera_component
        if not self.transform:
            self.transform = Transform()
            self.game_object.add_component(self.transform)

        self._apply_transform()

    def _apply_transform(self):
        """Apply scaling, rotation, flipping, alpha, and update rect."""
        sx, sy = self.transform.get_local_scale()
        angle = self.transform.local_rotation

        sx *= self.scale_factor
        sy *= self.scale_factor
        avg_scale = (sx + sy) / 2 if sx != sy else sx

        # Scale and rotate image
        if self.pixel_art_mode:
            w, h = int(self.original_image.get_width() * sx), int(self.original_image.get_height() * sy)
            scaled_image = pygame.transform.scale(self.original_image, (w, h))
            if angle != 0:
                scaled_image = pygame.transform.rotate(scaled_image, angle)
            self.image = scaled_image
        else:
            self.image = pygame.transform.rotozoom(self.original_image, angle, avg_scale)

        # Apply flips
        if self.flip_x or self.flip_y:
            self.image = pygame.transform.flip(self.image, self.flip_x, self.flip_y)

        # Apply transparency
        self.image.set_alpha(self.alpha)

        # Update rect based on transform
        final_x = self.transform.local_x + self.offset_x * self.scale_factor
        final_y = self.transform.local_y + self.offset_y * self.scale_factor
        self.rect = self.image.get_rect(center=(final_x, final_y))

        self._last_transform_state = (sx, sy, self.transform.local_rotation, self.flip_x, self.flip_y, self.pixel_art_mode)
        self._scaled_image_cache.clear()

    def update(self, dt: float):
        """Update sprite transform if scale or rotation changed."""
        if not self.transform:
            return

        sx, sy = self.transform.get_local_scale()
        state = (sx, sy, self.transform.local_rotation, self.flip_x, self.flip_y, self.pixel_art_mode)
        if state != self._last_transform_state:
            self._apply_transform()

    def render(self, surface: pygame.Surface):
        """Render sprite to the given surface, respecting camera and visibility."""
        if not self.transform or not self.image:
            return

        x, y = self.transform.get_world_position()
        x += self.offset_x * self.scale_factor
        y += self.offset_y * self.scale_factor

        img = self.image
        w, h = img.get_size()
        zoom = self.camera.zoom if self.camera else 1.0

        cache_key = (w, h, zoom, self.scale_factor, self.alpha, self.flip_x, self.flip_y, self.pixel_art_mode)
        if cache_key in self._scaled_image_cache:
            img_scaled = self._scaled_image_cache[cache_key]
        else:
            w_scaled, h_scaled = int(w * zoom), int(h * zoom)
            img_scaled = pygame.transform.scale(img, (w_scaled, h_scaled)) if self.pixel_art_mode else pygame.transform.smoothscale(img, (w_scaled, h_scaled))
            img_scaled.set_alpha(self.alpha)
            self._scaled_image_cache[cache_key] = img_scaled

        if self.camera and not self.camera.is_visible(x=x, y=y, width=img_scaled.get_width(), height=img_scaled.get_height()):
            return

        if self.camera:
            screen_x, screen_y = self.camera.world_to_screen(x, y)
            surface.blit(img_scaled, (screen_x - img_scaled.get_width() // 2, screen_y - img_scaled.get_height() // 2))
        else:
            surface.blit(img_scaled, img_scaled.get_rect(center=(x, y)).topleft)

    def change_image(self, new_image_path: str):
        """Change the sprite image at runtime."""
        self.image_path = new_image_path
        self.original_image = load_user_image(new_image_path).convert_alpha()
        self._apply_transform()

    def set_alpha(self, alpha: int):
        """Set sprite transparency at runtime."""
        self.alpha = max(0, min(255, alpha))
        if self.image:
            self.image.set_alpha(self.alpha)
        self._scaled_image_cache.clear()

    def get_width(self) -> float:
        """Return the scaled width of the sprite."""
        return self.image.get_width()

    def get_height(self) -> float:
        """Return the scaled height of the sprite."""
        return self.image.get_height()

    def _get_scale(self, transform: Transform | None, axis: str) -> float:
        """
        Internal helper to get scale along a specific axis.

        Args:
            transform (Transform | None): Optional transform reference.
            axis (str): 'x' or 'y'.

        Returns:
            float: Scale factor along the axis.

        Raises:
            ReferenceError: If no transform is available.
            ValueError: If axis is invalid.
        """
        if transform is None:
            if self.transform is None:
                raise ReferenceError("Sprite does not have a Transform yet. Call in start()/update().")
            transform = self.transform

        if axis == "x":
            return transform.local_scale_x
        elif axis == "y":
            return transform.local_scale_y
        else:
            raise ValueError("Axis must be 'x' or 'y'.")
