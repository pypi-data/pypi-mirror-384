import pygame
from cogworks.components.ui.ui_transform import UITransform
from cogworks.components.ui.ui_renderer import UIRenderer
from cogworks.utils.asset_loader import load_engine_image, load_user_image


class UIImage(UIRenderer):
    """
    UIImage renders an image respecting UITransform's rect and anchor.
    Scales proportionally, preserving aspect ratio, and aligns to the anchor.
    """

    def __init__(self, image_path, load_engine=False):
        super().__init__()
        self.image = load_engine_image(image_path) if load_engine else load_user_image(image_path)

    def set_image(self, image_path, load_engine=False):
        self.image = load_engine_image(image_path) if load_engine else load_user_image(image_path)

    def render(self, surface):
        ui_transform = self.game_object.get_component(UITransform)
        rect = ui_transform.rect

        # Scale proportionally (fit inside rect)
        iw, ih = self.image.get_size()
        scale = min(rect.width / iw, rect.height / ih)
        new_size = (int(iw * scale), int(ih * scale))
        img = pygame.transform.scale(self.image, new_size)

        # Align based on UITransform anchor
        anchor = getattr(ui_transform, "anchor", "center")
        if anchor == "topleft":
            img_rect = img.get_rect(topleft=rect.topleft)
        elif anchor == "topright":
            img_rect = img.get_rect(topright=rect.topright)
        elif anchor == "bottomleft":
            img_rect = img.get_rect(bottomleft=rect.bottomleft)
        elif anchor == "bottomright":
            img_rect = img.get_rect(bottomright=rect.bottomright)
        else:  # default to center
            img_rect = img.get_rect(center=rect.center)

        surface.blit(img, img_rect)
