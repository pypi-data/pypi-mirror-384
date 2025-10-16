import pygame
from cogworks.components.ui.ui_transform import UITransform
from cogworks.components.ui.ui_renderer import UIRenderer


class UILabel(UIRenderer):
    """
    UILabel is a simple UI element for displaying text on the screen.

    Features:
        - Renders text with alignment (anchor) relative to the UITransform's rect.
        - Supports custom font size, text colour, and optional background colour.
        - Can update text dynamically at runtime via `set_text`.
        - Supports optional rounded corners for the background.
        - Anchor options: 'center', 'topleft', 'topright', 'bottomleft', 'bottomright',
                          'midtop', 'midbottom', 'midleft', 'midright'.
    """

    def __init__(
        self,
        text: str,
        font_size: int = 24,
        color: tuple[int, int, int] = (255, 255, 255),
        bg_color: tuple[int, int, int] | None = None,
        border_radius: int = 0,
        anchor: str = "center",
    ):
        """
        Initialise a UILabel component.

        Args:
            text (str): The text displayed by the label.
            font_size (int, optional): Font size (default: 24).
            color (tuple[int,int,int], optional): Text colour (default: white).
            bg_color (tuple[int,int,int] | None, optional): Background colour.
            border_radius (int, optional): Rounded corner radius for background (default: 0).
            anchor (str, optional): Text alignment anchor (default: 'center').
                                    Options include:
                                    'center', 'topleft', 'topright', 'bottomleft', 'bottomright',
                                    'midtop', 'midbottom', 'midleft', 'midright'.
        """
        super().__init__()
        self.start_text = text
        self.text = self.start_text
        self.font = pygame.font.Font(None, font_size)
        self.color = color
        self.bg_color = bg_color
        self.border_radius = border_radius
        self.anchor = anchor.lower().strip()

    def start(self):
        self.text = self.start_text

    def set_text(self, new_text: str) -> None:
        """Update the label's text."""
        self.text = new_text

    def render(self, surface) -> None:
        rect = self.game_object.get_component(UITransform).rect
        text_surf = self.font.render(self.text, True, self.color)

        # Draw background if needed
        if self.bg_color:
            pygame.draw.rect(surface, self.bg_color, rect, border_radius=self.border_radius)

        # Get the text rect and position based on the chosen anchor
        text_rect = text_surf.get_rect()

        # Map anchor keywords to rect attributes dynamically
        if hasattr(rect, self.anchor):
            setattr(text_rect, self.anchor, getattr(rect, self.anchor))
        else:
            # Default fallback to center if anchor is invalid
            text_rect.center = rect.center

        # Blit text at anchored position
        surface.blit(text_surf, text_rect)
