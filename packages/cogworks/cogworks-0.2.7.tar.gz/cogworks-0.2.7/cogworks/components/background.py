import pygame
from cogworks.component import Component
from cogworks.components.sprite import Sprite
from cogworks.components.transform import Transform
from cogworks.pygame_wrappers.event_manager import EventManager


class Background(Component):
    """
    Renders a background sprite that scales to fit the screen and stays centered.
    """

    def __init__(self):
        super().__init__()
        self.original_image: pygame.Surface | None = None
        self.scaled_image: pygame.Surface | None = None
        self.transform: Transform | None = None

    def on_enabled(self):
        EventManager.get_instance().subscribe(self._on_event)

    def on_disabled(self):
        EventManager.get_instance().unsubscribe(self._on_event)

    def on_remove(self):
        EventManager.get_instance().unsubscribe(self._on_event)

    def start(self):
        self.transform = self.game_object.get_component(Transform)
        self.original_image = self.game_object.get_component(Sprite).original_image

        self._scale_and_center()

    def _scale_and_center(self):
        if not self.original_image or not self.transform:
            return

        screen_width, screen_height = self.game_object.scene.get_window_size()
        img_width, img_height = self.original_image.get_size()

        # Calculate scale factor to cover the screen
        scale_x = screen_width / img_width
        scale_y = screen_height / img_height
        scale = max(scale_x, scale_y)

        new_width = int(img_width * scale)
        new_height = int(img_height * scale)

        # Scale the image
        self.scaled_image = pygame.transform.smoothscale(self.original_image, (new_width, new_height))

        # Center the image
        self.transform.local_x = (screen_width - new_width) // 2
        self.transform.local_y = (screen_height - new_height) // 2

    def render(self, surface):
        if self.scaled_image and self.transform:
            surface.blit(self.scaled_image, (self.transform.local_x, self.transform.local_y))

    def _on_event(self, event):
        if event.type == pygame.VIDEORESIZE:
            self._scale_and_center()