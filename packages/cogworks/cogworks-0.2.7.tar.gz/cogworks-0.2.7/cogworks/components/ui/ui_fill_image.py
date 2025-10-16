import pygame
from cogworks.components.ui.ui_transform import UITransform
from cogworks.components.ui.ui_image import UIImage


class UIFillImage(UIImage):
    """
    UIImage with fill capability and optional smooth fill animation.

    Attributes:
        fill_amount (float): Current fill amount (0.0 to 1.0)
        target_fill (float): Target fill amount for smooth animation
        fill_direction (str): 'horizontal' or 'vertical'
        fill_origin (str): 'left'/'right' for horizontal, 'top'/'bottom' for vertical
        fill_speed (float): How fast to animate fill per second (0 = instant)
    """

    def __init__(self, image_path, load_engine=False, fill_amount=1.0,
                 fill_direction='horizontal', fill_origin=None, fill_speed=2.0):
        super().__init__(image_path, load_engine)
        self.start_fill_amount = max(0.0, min(fill_amount, 1.0))
        self.fill_amount = self.start_fill_amount
        self.target_fill = self.fill_amount
        self.fill_direction = fill_direction.lower()
        if self.fill_direction not in ('horizontal', 'vertical'):
            raise ValueError("fill_direction must be 'horizontal' or 'vertical'")

        # Set default origin based on direction if not provided
        if fill_origin is None:
            self.fill_origin = 'left' if self.fill_direction == 'horizontal' else 'top'
        else:
            self.fill_origin = fill_origin.lower()
        self._validate_origin()

        self.fill_speed = fill_speed  # Fill units per second

    def start(self):
        self.fill_amount = self.start_fill_amount

    def _validate_origin(self):
        if self.fill_direction == 'horizontal' and self.fill_origin not in ('left', 'right'):
            raise ValueError("For horizontal fill, fill_origin must be 'left' or 'right'")
        if self.fill_direction == 'vertical' and self.fill_origin not in ('top', 'bottom'):
            raise ValueError("For vertical fill, fill_origin must be 'top' or 'bottom'")

    def set_fill(self, amount, smooth=True):
        """Set a new fill amount, optionally animated."""
        amount = max(0.0, min(amount, 1.0))
        if smooth:
            self.target_fill = amount
        else:
            self.fill_amount = amount
            self.target_fill = amount

    def set_direction(self, direction, origin=None):
        self.fill_direction = direction.lower()
        if self.fill_direction not in ('horizontal', 'vertical'):
            raise ValueError("fill_direction must be 'horizontal' or 'vertical'")
        if origin:
            self.fill_origin = origin.lower()
        self._validate_origin()

    def update(self, dt):
        if self.fill_amount != self.target_fill:
            diff = self.target_fill - self.fill_amount
            step = self.fill_speed * dt
            if abs(diff) <= step:
                self.fill_amount = self.target_fill
            else:
                self.fill_amount += step if diff > 0 else -step

    def render(self, surface):
        rect = self.game_object.get_component(UITransform).rect

        # Scale image to fit rect without stretching
        iw, ih = self.image.get_size()
        scale = min(rect.width / iw, rect.height / ih)
        img = pygame.transform.scale(self.image, (int(iw * scale), int(ih * scale)))

        # Determine filled area
        if self.fill_direction == 'horizontal':
            filled_width = int(img.get_width() * self.fill_amount)
            if self.fill_origin == 'left':
                img = img.subsurface(pygame.Rect(0, 0, filled_width, img.get_height()))
                img_rect = img.get_rect(topleft=rect.topleft)
            else:  # right
                img = img.subsurface(pygame.Rect(img.get_width() - filled_width, 0, filled_width, img.get_height()))
                img_rect = img.get_rect(topright=rect.topright)
        else:  # vertical
            filled_height = int(img.get_height() * self.fill_amount)
            if self.fill_origin == 'top':
                img = img.subsurface(pygame.Rect(0, 0, img.get_width(), filled_height))
                img_rect = img.get_rect(topleft=rect.topleft)
            else:  # bottom
                img = img.subsurface(pygame.Rect(0, img.get_height() - filled_height, img.get_width(), filled_height))
                img_rect = img.get_rect(bottomleft=rect.bottomleft)

        surface.blit(img, img_rect)
