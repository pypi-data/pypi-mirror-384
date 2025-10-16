import pymunk
from operator import attrgetter

from cogworks.components.audio_listener import AudioListener
from cogworks.components.camera import Camera
from cogworks.game_object import GameObject
from cogworks.trigger_collision_manager import TriggerCollisionManager


class Scene:
    """
    A Scene represents a collection of GameObjects.
    Scenes handle updating, fixed updates, and rendering all their GameObjects.
    Each Scene has its own camera GameObject by default.
    """

    def __init__(self, name: str = "Scene", gravity=(0, 900)):
        """
        Initialize a Scene with a name and default camera.

        Args:
            name (str): The name of the scene.
        """
        self.has_started = False
        self.start_states = None
        self.name = name

        self.engine = None

        # Default camera setup
        self.camera = GameObject("Camera")
        self.camera_component = Camera()
        self.camera.add_component(self.camera_component)
        self.camera.add_component(AudioListener())
        self.camera.scene = self

        self.initial_objects: list[GameObject] = [self.camera]
        self.runtime_objects: list[GameObject] = []

        # Cache combined sorted list for updates and rendering
        self.sorted_objects: list[GameObject] = self.initial_objects + self.runtime_objects

        self.physics_space = pymunk.Space()
        self.gravity = gravity
        self.physics_space.gravity = self.gravity
        self.trigger_collision_manager = TriggerCollisionManager()

    def start(self):
        self.has_started = True
        # Start each initial game object
        for go in self.initial_objects:
            go.enable()
            go.start()
        self._sort_objects()

    def stop(self):
        self._cleanup()
        self.has_started = False

    def _cleanup(self):
        self.camera.get_component(AudioListener).clear_sources()

        # Create a new physics space
        self.physics_space = pymunk.Space()
        self.physics_space.gravity = self.gravity

        # Destroy and cleanup runtime GameObjects
        for go in self.runtime_objects:
            go.destroy()
            go.cleanup()
        self.runtime_objects.clear()

        # Disable and clean up initial GameObjects
        for go in self.initial_objects:
            go.cleanup()
            go.disable()

        # Clear collision manager
        self.trigger_collision_manager.clear()

        self._sort_objects()  # refresh sorted_objects

    def restart(self):
        self.stop()
        self.start()

    def add_game_object(self, game_object: GameObject) -> None:
        """
        Add a *initial GameObject to the scene

        Args:
            game_object (GameObject): The GameObject to add.
        """
        if self.has_started:
            raise RuntimeError("Scene already started, use instantiate_game_object instead")
        game_object.scene = self
        self.initial_objects.append(game_object)
        self._sort_objects()

    def instantiate_game_object(self, game_object: GameObject) -> None:
        """
        Instantiate a *runtime GameObject to the scene, set its scene reference, and call its start method.

        Args:
            game_object (GameObject): The GameObject to add.
        """
        if not self.has_started:
            raise RuntimeError("Scene hasn't started, use add_game_object instead")
        game_object.scene = self
        game_object.start()
        self.runtime_objects.append(game_object)
        self._sort_objects()

    def remove_game_object(self, game_object: GameObject) -> None:
        """
        Remove a *runtime GameObject from the scene and call `on_remove` on its components.

        Args:
            game_object (GameObject): The GameObject to remove.
        """
        if game_object in self.runtime_objects:
            for comp in game_object.components:
                if hasattr(comp, "on_remove"):
                    comp.on_remove()
            self.runtime_objects.remove(game_object)
            del game_object
            self._sort_objects()

    def get_all_components_of_type(self, component_type):
        components = []
        for go in self.sorted_objects:
            components = components + go.get_all_components_of_type(component_type)
        return components

    def update(self, dt: float) -> None:
        """
        Update all GameObjects (initial and runtime) and CollisionManagers in the scene.

        Args:
            dt (float): Delta time since last frame.
        """
        for obj in self.sorted_objects:
            obj.update(dt)

        self.trigger_collision_manager.update(dt)

    def fixed_update(self, dt: float) -> None:
        """
        Fixed timestep update for physics or deterministic logic.
        Calls `fixed_update` on all GameObjects (initial and runtime).

        Args:
            dt (float): Fixed delta time.
        """
        self.physics_space.step(dt)

        for obj in self.sorted_objects:
            obj.fixed_update(dt)

    def render(self, surface) -> None:
        """
        Render all GameObjects in the scene to the given surface in order of z_index.

        Args:
            surface: The pygame surface to render onto.
        """
        for obj in self.sorted_objects:
            obj.render(surface)

    def _sort_objects(self):
        # Sort game objects by z_index (default 0)
        self.sorted_objects = self.initial_objects + self.runtime_objects
        self.sorted_objects.sort(key=attrgetter("z_index"))

    def get_window_size(self) -> tuple[int, int]:
        """
        Get the current window size from the cogworks.

        Returns:
            tuple[int, int]: Width and height of the window.
        """
        return self.engine.window.get_size()

    def get_active_audio_listener(self):
        return self.camera.get_component(AudioListener)

    def __repr__(self):
        return f"<Scene name='{self.name}', objects={len(self.sorted_objects)}>"


class SceneManager:
    """
    SceneManager handles adding, switching, and updating the currently active scene.
    """

    def __init__(self):
        self.scenes: dict[str, Scene] = {}
        self.active_scene: Scene | None = None

    def add_scene(self, scene: Scene, engine) -> None:
        """
        Add a scene to the manager and assign it an engine reference.

        Args:
            scene (Scene): The scene to add.
            engine: The game cogworks instance.
        """
        scene.engine = engine
        self.scenes[scene.name] = scene

    def set_active_scene(self, scene_name: str) -> None:
        """
        Set a scene as the active scene by name.

        Args:
            scene_name (str): Name of the scene to activate.

        Raises:
            ValueError: If the scene name is not found in the manager.
        """
        if scene_name in self.scenes:
            self.active_scene = self.scenes[scene_name]
            self.active_scene.start()
        else:
            raise ValueError(f"Scene '{scene_name}' not found in SceneManager.")

    def start_active_scene(self):
        if self.active_scene:
            self.active_scene.start()

    def change_active_scene(self, scene_name: str) -> None:
        """Change the currently active scene by name."""
        if self.active_scene:
            self.active_scene.stop()
        self.set_active_scene(scene_name)

    def update(self, dt: float) -> None:
        """
        Update the active scene.

        Args:
            dt (float): Delta time since last frame.
        """
        if self.active_scene:
            self.active_scene.update(dt)

    def fixed_update(self, dt: float) -> None:
        """
        Call fixed_update on the active scene.

        Args:
            dt (float): Fixed delta time.
        """
        if self.active_scene:
            self.active_scene.fixed_update(dt)

    def render(self, surface) -> None:
        """
        Render the active scene to the given surface.

        Args:
            surface: The surface to render onto.
        """
        if self.active_scene:
            self.active_scene.render(surface)
