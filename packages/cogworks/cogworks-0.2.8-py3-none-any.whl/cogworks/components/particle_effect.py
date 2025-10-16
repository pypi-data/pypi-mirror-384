from cogworks import GameObject, Component
from cogworks.components.particle import Particle
from typing import Tuple


class ParticleEffect(Component):
    """
    A component that spawns multiple particles with configurable behaviour.

    This component allows you to define particle appearance, movement,
    lifetime, scaling, rotation, and fading. It spawns a set number of particles
    when started and each particle is an independent GameObject with its own Particle component.
    """

    def __init__(
        self,
        sprite_path: str,
        particle_amount: int = 3,
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
        min_direction: Tuple[float, float] = (-1, -1),
        max_direction: Tuple[float, float] = (1, 1),
        lifetime: float = 1.5,
        end_scale: float | None = None,
        scale_with_lifetime: bool = False,
        rotate_over_lifetime: bool = False,
        fade_over_lifetime: bool = False,
    ):
        """
        Initialise a ParticleEffect component.

        Args:
            sprite_path (str): Path to the sprite image for particles.
            particle_amount (int): Number of particles to spawn.
            min_x (float): Minimum X offset from parent GameObject.
            max_x (float): Maximum X offset from parent GameObject.
            min_y (float): Minimum Y offset from parent GameObject.
            max_y (float): Maximum Y offset from parent GameObject.
            min_rotation (float): Minimum initial rotation for particles.
            max_rotation (float): Maximum initial rotation for particles.
            min_scale (float): Minimum initial scale for particles.
            max_scale (float): Maximum initial scale for particles.
            move_speed (float): Base speed for particle movement.
            gravity (float): Gravity applied to particles per second.
            min_direction (tuple[float, float]): Minimum direction vector components.
            max_direction (tuple[float, float]): Maximum direction vector components.
            lifetime (float): Time in seconds before particle destruction.
            end_scale (float | None): Final scale at the end of particle lifetime.
            scale_with_lifetime (bool): Whether particles scale over time.
            rotate_over_lifetime (bool): Whether particles rotate over time.
            fade_over_lifetime (bool): Whether particles fade over time.
        """
        super().__init__()
        self.sprite_path: str = sprite_path
        self.particle_amount: int = particle_amount
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
        self.min_direction: Tuple[float, float] = min_direction
        self.max_direction: Tuple[float, float] = max_direction
        self.lifetime: float = lifetime
        self.end_scale: float | None = end_scale
        self.scale_with_lifetime: bool = scale_with_lifetime
        self.rotate_over_lifetime: bool = rotate_over_lifetime
        self.fade_over_lifetime: bool = fade_over_lifetime

    def start(self) -> None:
        """
        Called when the component starts.

        Automatically spawns the configured number of particles.
        """
        self.spawn_particles()

    def spawn_particles(self) -> None:
        """
        Instantiate particle GameObjects based on the configured properties.

        Each particle is assigned a Particle component with its own
        position, rotation, scale, movement, and lifetime behaviour.
        """
        x, y = self.game_object.transform.get_local_position()

        for i in range(self.particle_amount):
            particle = GameObject(f"Particle{i}", z_index=5)

            particle_component = Particle(
                sprite_path=self.sprite_path,
                min_x=x + self.min_x,
                max_x=x + self.max_x,
                min_y=y + self.min_y,
                max_y=y + self.max_y,
                min_rotation=self.min_rotation,
                max_rotation=self.max_rotation,
                min_scale=self.min_scale,
                max_scale=self.max_scale,
                move_speed=self.move_speed,
                gravity=self.gravity,
                min_direction=self.min_direction,
                max_direction=self.max_direction,
                lifetime=self.lifetime,
                end_scale=self.end_scale,
                scale_with_lifetime=self.scale_with_lifetime,
                rotate_over_lifetime=self.rotate_over_lifetime,
                fade_over_lifetime=self.fade_over_lifetime,
            )

            particle.add_component(particle_component)
            self.game_object.scene.instantiate_game_object(particle)
