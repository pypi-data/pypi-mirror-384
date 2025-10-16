import random
from cogworks import Component
from cogworks.components.sprite import Sprite


class Particle(Component):
    """
    Represents a particle effect component for 2D games.

    Particles are small, short-lived objects that can move, scale, rotate,
    and fade over their lifetime. They can also be assigned a sprite for
    visual representation. The particle's behaviour is configurable through
    initial randomisation, gravity, direction, and lifetime properties.
    """

    def __init__(
        self,
        sprite_path: str | None = None,
        min_x: float = 0,
        max_x: float = 50,
        min_y: float = 0,
        max_y: float = 50,
        min_rotation: float = -180,
        max_rotation: float = 180,
        min_scale: float = 0.4,
        max_scale: float = 0.8,
        move_speed: float = 500,
        gravity: float = 500,
        min_direction: tuple[float, float] = (-1, -1),
        max_direction: tuple[float, float] = (1, 1),
        lifetime: float = 1.5,
        end_scale: float | None = None,
        scale_with_lifetime: bool = False,
        rotate_over_lifetime: bool = False,
        fade_over_lifetime: bool = False,
    ):
        """
        Initialise a Particle component with configurable properties.

        Args:
            sprite_path (str | None): Path to the sprite image. Optional.
            min_x (float): Minimum initial x-position.
            max_x (float): Maximum initial x-position.
            min_y (float): Minimum initial y-position.
            max_y (float): Maximum initial y-position.
            min_rotation (float): Minimum initial rotation in degrees.
            max_rotation (float): Maximum initial rotation in degrees.
            min_scale (float): Minimum initial scale factor.
            max_scale (float): Maximum initial scale factor.
            move_speed (float): Base movement speed of the particle.
            gravity (float): Gravity applied per second.
            min_direction (tuple[float, float]): Minimum direction vector components.
            max_direction (tuple[float, float]): Maximum direction vector components.
            lifetime (float): Time in seconds before the particle is destroyed.
            end_scale (float | None): Final scale at the end of the lifetime.
            scale_with_lifetime (bool): Whether to scale over time.
            rotate_over_lifetime (bool): Whether to rotate over time.
            fade_over_lifetime (bool): Whether to fade out over time.
        """
        super().__init__()
        self.sprite_path: str | None = sprite_path
        self.min_x: float = min_x
        self.max_x: float = max_x
        self.min_y: float = min_y
        self.max_y: float = max_y
        self.min_rotation: float = min_rotation
        self.max_rotation: float = max_rotation
        self.min_scale: float = min_scale
        self.max_scale: float = max_scale
        self.move_speed: float = move_speed
        self.gravity: float = gravity
        self.min_direction: tuple[float, float] = min_direction
        self.max_direction: tuple[float, float] = max_direction
        self.lifetime: float = lifetime
        self.end_scale: float = end_scale if end_scale is not None else max_scale
        self.scale_with_lifetime: bool = scale_with_lifetime
        self.rotate_over_lifetime: bool = rotate_over_lifetime
        self.fade_over_lifetime: bool = fade_over_lifetime

        # Runtime state
        self.age: float = 0.0
        self.initial_scale: float = 1.0
        self.initial_rotation: float = 0.0
        self.initial_alpha: int = 255
        self.sprite: Sprite | None = None

        # Movement state
        self.direction: list[float] = [0.0, 0.0]
        self.velocity: list[float] = [0.0, 0.0]

    def start(self) -> None:
        """
        Initialise particle properties at the start of its lifetime.

        Randomises position, rotation, scale, and movement direction/velocity.
        Attaches a sprite if provided.
        """
        # Randomise initial position
        random_x = random.uniform(self.min_x, self.max_x)
        random_y = random.uniform(self.min_y, self.max_y)
        self.game_object.transform.set_local_position(random_x, random_y)

        # Randomise initial rotation
        random_rotation = random.uniform(self.min_rotation, self.max_rotation)
        self.initial_rotation = random_rotation
        self.game_object.transform.set_local_rotation(random_rotation)

        # Randomise initial scale
        random_scale = random.uniform(self.min_scale, self.max_scale)
        self.initial_scale = random_scale
        self.game_object.transform.set_local_scale(random_scale, random_scale)

        # Randomise initial direction and velocity
        random_x_dir = random.uniform(self.min_direction[0], self.max_direction[0])
        random_y_dir = random.uniform(self.min_direction[1], self.max_direction[1])
        self.direction = [random_x_dir, random_y_dir]
        self.velocity = [
            self.direction[0] * self.move_speed,
            self.direction[1] * self.move_speed,
        ]

        # Add sprite if provided
        if self.sprite_path:
            self.sprite = Sprite(self.sprite_path)
            self.initial_alpha = self.sprite.alpha
            self.game_object.add_component(self.sprite)

    def update(self, dt: float) -> None:
        """
        Update the particle each frame.

        Handles lifetime progression, movement, gravity, scaling, rotation,
        and fading.

        Args:
            dt (float): Delta time since the last frame in seconds.
        """
        self.age += dt
        t = min(self.age / self.lifetime, 1.0)  # progress ratio (0 → 1)

        # Destroy particle after lifetime
        if self.age >= self.lifetime:
            self.game_object.destroy()
            return

        # Apply gravity
        self.velocity[1] += self.gravity * dt

        # Update position
        pos_x, pos_y = self.game_object.transform.get_local_position()
        new_x = pos_x + self.velocity[0] * dt
        new_y = pos_y + self.velocity[1] * dt
        self.game_object.transform.set_local_position(new_x, new_y)

        # Update scale over lifetime
        if self.scale_with_lifetime:
            new_scale = self.initial_scale + (self.end_scale - self.initial_scale) * t
            self.game_object.transform.set_local_scale(new_scale, new_scale)

        # Rotate over lifetime
        if self.rotate_over_lifetime:
            new_rotation = self.initial_rotation + 360 * t  # full rotation over lifetime
            self.game_object.transform.set_local_rotation(new_rotation)

        # Fade over lifetime
        if self.fade_over_lifetime and self.sprite is not None:
            alpha = self.initial_alpha * max(1.0 - t, 0.0)
            self.sprite.set_alpha(alpha)
