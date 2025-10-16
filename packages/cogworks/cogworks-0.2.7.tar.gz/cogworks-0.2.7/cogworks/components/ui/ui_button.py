import pygame
from cogworks.components.ui.ui_transform import UITransform
from cogworks.components.ui.ui_renderer import UIRenderer
from cogworks.pygame_wrappers.event_manager import EventManager

class UIButton(UIRenderer):
    """
    UIButton is a simple interactive UI element that can be rendered on screen,
    respond to mouse hover, and trigger an action when clicked.

    Features:
        - Renders a rectangular button with text centered inside.
        - Highlights (brightens background) when hovered.
        - Supports a callback function to be executed on click.
    """

    def __init__(
        self,
        text,
        on_click=None,
        font_size=24,
        text_color=(255, 255, 255),
        bg_color=(0, 0, 255),
        border_radius=0
    ):
        """
        Initialise a UIButton component.

        Args:
            text (str): The text displayed on the button.
            on_click (callable, optional): Function to call when the button is clicked.
            font_size (int, optional): Size of the text font (default: 24).
            text_color (tuple[int,int,int], optional): RGB colour of the text (default: white).
            bg_color (tuple[int,int,int], optional): RGB background colour of the button (default: blue).
            border_radius (int, optional): Radius of button corners for rounded edges (default: 0, sharp corners).
        """
        super().__init__()
        self.text = text
        self.on_click = on_click
        self.font = pygame.font.Font(None, font_size)
        self.text_color = text_color
        self.bg_color = bg_color
        self.border_radius = border_radius
        self.hovered = False


    def on_enabled(self):
        # Subscribe to global event manager to handle mouse events
        EventManager.get_instance().subscribe(self.handle_event)

    def on_remove(self):
        EventManager.get_instance().unsubscribe(self.handle_event)

    def on_disabled(self):
        EventManager.get_instance().unsubscribe(self.handle_event)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.hovered:
            self.on_click(self.game_object)

    def render(self, surface):
        rect = self.game_object.get_component(UITransform).rect
        mouse_pos = pygame.mouse.get_pos()
        self.hovered = rect.collidepoint(mouse_pos)

        rect = self.game_object.get_component(UITransform).rect
        color = tuple(min(c + 50, 255) if self.hovered else c for c in self.bg_color)
        pygame.draw.rect(surface, color, rect, border_radius=self.border_radius)
        text_surf = self.font.render(self.text, True, self.text_color)
        surface.blit(text_surf, text_surf.get_rect(center=rect.center))