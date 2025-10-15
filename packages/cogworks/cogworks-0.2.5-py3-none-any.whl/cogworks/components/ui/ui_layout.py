import pygame

from cogworks.component import Component
from cogworks.components.ui.ui_transform import UITransform


class UILayout(Component):
    """
    UILayout automatically arranges child UI elements inside a parent container.

    Features:
        - Supports both vertical and horizontal layouts.
        - Adds configurable spacing between child elements.
        - Applies padding from the parent’s edge.
        - Dynamically adjusts child positions whenever `update_layout` is called.
    """

    def __init__(self, vertical=True, spacing=5, padding=5):
        """
        Initialise a UILayout component.

        Args:
            vertical (bool, optional): If True, children are arranged top-to-bottom.
                                       If False, children are arranged left-to-right. (default: True)
            spacing (int, optional): Space (in pixels) between child elements. (default: 5)
            padding (int, optional): Space (in pixels) from the parent's edge before starting layout. (default: 5)
        """
        super().__init__()
        self.vertical = vertical
        self.spacing = spacing
        self.padding = padding

    def start(self) -> None:
        """
        Called when the component is first initialised.

        Behaviour:
            - Immediately triggers layout calculation for the children.
        """
        self.update_layout()

    def update_layout(self):
        """
        Update the positions and sizes of child UI elements based on the layout rules.

        Behaviour:
            - Retrieves the parent `UITransform` to define available space.
            - Iterates through all children of the parent GameObject.
            - If a child has a `UITransform`, its rectangle is recalculated:
                * In vertical mode: children are stacked top-to-bottom and horizontally centered.
                * In horizontal mode: children are lined up left-to-right and vertically centered.
            - Relative sizing is respected if defined in the child `UITransform`.
        """
        # Get children from the GameObject itself
        children = self.game_object.children
        if not children:
            return

        parent_transform = self.game_object.get_component(UITransform)
        if not parent_transform:
            return
        parent_rect = parent_transform.rect

        offset = self.padding
        for child in children:
            t = child.get_component(UITransform)
            if not t:
                continue

            # Calculate width and height relative to parent
            width = int(t._width * parent_rect.width) if t.relative else int(t._width)
            height = int(t._height * parent_rect.height) if t.relative else int(t._height)

            if self.vertical:
                # Place child in vertical stack
                t.rect = pygame.Rect(
                    parent_rect.left,
                    parent_rect.top + offset,
                    width,
                    height
                )
                # Center horizontally
                t.rect.centerx = parent_rect.centerx
                offset += height + self.spacing
            else:
                # Place child in horizontal row
                t.rect = pygame.Rect(
                    parent_rect.left + offset,
                    parent_rect.top,
                    width,
                    height
                )
                # Center vertically
                t.rect.centery = parent_rect.centery
                offset += width + self.spacing
