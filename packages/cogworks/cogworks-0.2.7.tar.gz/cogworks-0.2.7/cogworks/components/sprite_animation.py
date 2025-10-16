import os
from dataclasses import dataclass, field
from typing import Callable
from cogworks import Component
from cogworks.components.sprite import Sprite
from cogworks.exceptions.missing_component_error import MissingComponentError


@dataclass
class Animation:
    """
    Represents a sprite-based animation sequence with optional frame events.
    """
    name: str
    sprite_path: str
    start_sprite_index: int = 1
    last_sprite_index: int = 1
    time_between_sprites: float = 0.1
    loop: bool = True
    events: dict[int, list[Callable]] = field(default_factory=dict)

    def add_event(self, index: int, callback: Callable):
        """Attach a callback for a specific sprite frame index."""
        if index not in self.events:
            self.events[index] = []
        self.events[index].append(callback)

    def trigger_events(self, index: int):
        """Trigger all callbacks for a specific frame index."""
        for callback in self.events.get(index, []):
            callback()


class SpriteAnimation(Component):
    """
    Component for managing sprite animations.
    """

    def __init__(self):
        super().__init__()
        self.animations: list[Animation] = []
        self.selected_animation: Animation | None = None

        self.sprite_index: int = 0
        self.animation_timer: float = 0.0
        self.sprite: Sprite | None = None

        self.is_playing: bool = False

    def start(self):
        """Initialise the component and fetch the Sprite component."""
        self.sprite_index = 0
        self.animation_timer = 0.0

        self.sprite = self.game_object.get_component(Sprite)
        if self.sprite is None:
            raise MissingComponentError(Sprite, self.game_object)

    def update(self, dt: float):
        """Advance the animation based on the delta time."""
        if not self.is_playing or self.selected_animation is None or self.sprite is None:
            return

        self.animation_timer += dt

        if self.animation_timer >= self.selected_animation.time_between_sprites:
            base, ext = os.path.splitext(self.selected_animation.sprite_path)
            new_path = f"{base}{self.sprite_index}{ext}"
            self.sprite.change_image(new_path)

            # Trigger frame events
            self.selected_animation.trigger_events(self.sprite_index)

            self.sprite_index += 1

            # Handle end of animation
            if self.sprite_index > self.selected_animation.last_sprite_index:
                if self.selected_animation.loop:
                    self.sprite_index = self.selected_animation.start_sprite_index
                else:
                    self.is_playing = False
                    self.sprite_index = self.selected_animation.last_sprite_index

            self.animation_timer = 0.0

    def clear_selected_animation(self):
        """Clear the currently selected animation."""
        self.selected_animation = None
        self.is_playing = False

    def set_animation(self, name: str, play: bool = True):
        """Select an animation by name."""
        self.selected_animation = next(
            (anim for anim in self.animations if anim.name == name), None
        )

        if self.selected_animation is None:
            print(f"[WARNING] Animation '{name}' not found.")
            return

        self.sprite_index = self.selected_animation.start_sprite_index
        self.is_playing = play
        self.animation_timer = 0.0

    def add_animation(
        self,
        name: str,
        sprite_path: str,
        start_sprite_index: int = 1,
        last_sprite_index: int = 1,
        time_between_sprites: float = 0.1,
        loop: bool = True,
    ) -> Animation:
        """
        Add a new sprite animation.

        Args:
            name (str): Name of the animation.
            sprite_path (str): Base path to sprite images (without index).
            start_sprite_index (int): Index of the first sprite.
            last_sprite_index (int): Index of the last sprite.
            time_between_sprites (float): Delay between frames (minimum 0.1).
            loop (bool): Whether the animation should loop.

        Returns:
            Animation: The created Animation object.
        """
        if time_between_sprites < 0.1:
            print("[WARNING] time_between_sprites should be at least 0.1.")
            time_between_sprites = 0.1

        animation = Animation(
            name=name,
            sprite_path=sprite_path,
            start_sprite_index=start_sprite_index,
            last_sprite_index=last_sprite_index,
            time_between_sprites=time_between_sprites,
            loop=loop,
        )

        self.animations.append(animation)
        return animation
