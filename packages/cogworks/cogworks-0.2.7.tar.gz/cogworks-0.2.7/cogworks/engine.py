import pygame

from cogworks.pygame_wrappers.window import Window
from cogworks.pygame_wrappers.input_manager import InputManager
from cogworks.pygame_wrappers.event_manager import EventManager
from cogworks.scene_manager import Scene, SceneManager


class Engine:
    """
    The main cogworks class that manages the game/application loop.
    Provides update, render, event handling, and scene management.
    """

    def __init__(self, width: int = 500, height: int = 500, caption: str = "CogWorks Engine", fps: int = 60, world_bound_x: float = 5000, world_bound_y: float = 5000):
        """
        Initialise the cogworks with a window, scene manager, and runtime state.

        Args:
            width (int, optional): Initial width of the window. Defaults to 500.
            height (int, optional): Initial height of the window. Defaults to 500.
            caption (str, optional): The window caption. Defaults to "CogWorks Engine".
            fps (int, optional): Frames per second. Defaults to 60.
            world_bound_x (float, optional): World boundary x position for GameObject, if passes it, it gets destroyed
            world_bound_y (float, optional): World boundary y position for GameObject, if passes it, it gets destroyed
        """
        self.window = Window(pygame, width, height, caption, resizable=True)
        self.running = True
        self.clock = pygame.time.Clock()
        self.fps = fps  # Target frames per second
        self.world_bound_x = world_bound_x
        self.world_bound_y = world_bound_y

        self._next_frame_queue = []  # Queue of functions to run next frame

        # Scene manager
        self.scene_manager = SceneManager()

        # Input manager
        self.input = InputManager.get_instance()

        # Event manager
        self.event_manager = EventManager.get_instance()
        self.event_manager.subscribe(self.handle_event)
        self.window.subscribe_events(self.event_manager)

    # ---------------- Scene Management ---------------- #

    def set_active_scene(self, scene_name: str) -> None:
        """Change the currently active scene by name, deferred until next frame."""

        def change_scene():
            if self.scene_manager.active_scene is None:
                self.scene_manager.set_active_scene(scene_name)
            else:
                self.scene_manager.change_active_scene(scene_name)

        # Schedule the scene change for the next frame
        self.schedule_next_frame(change_scene)

    def create_scene(self, scene_name: str, gravity=(0, 900)) -> Scene:
        """Create a new scene and add it to scene manager."""
        new_scene = Scene(scene_name, gravity)
        self.scene_manager.add_scene(new_scene, self)
        return new_scene

    def restart_active_scene(self):
        if self.scene_manager.active_scene:
            self.scene_manager.active_scene.restart()

    # ---------------- Event Handling ---------------- #

    def handle_event(self, event):
        """Handle cogworks-specific events like QUIT."""
        if event.type == pygame.QUIT:
            self.quit()

    # ---------------- Engine Loop ---------------- #

    def schedule_next_frame(self, callback):
        """
        Schedule a function to run at the start of the next frame.
        Useful for deferred actions like scene changes.
        """
        self._next_frame_queue.append(callback)

    def render(self):
        """
        Render/draw content to the screen and the active scene.
        """
        self.window.render()

        self.scene_manager.render(self.window.screen)

        # FPS display, throttled to once per second
        if pygame.time.get_ticks() % 1000 < 16:
            pygame.display.set_caption(f"{self.window.caption} - FPS: {self.clock.get_fps():.2f}")

        pygame.display.flip()

    def quit(self):
        """Stop the cogworks loop and quit pygame."""
        self.running = False

    def run(self):
        """
        Run the main cogworks loop with a fixed timestep for physics.
        """
        fixed_dt = 1 / 60.0  # 60 FPS physics step
        accumulator = 0.0

        # Start the active scene
        self.scene_manager.start_active_scene()

        while self.running:
            # Execute scheduled callbacks from the previous frame
            for callback in self._next_frame_queue:
                callback()
            self._next_frame_queue.clear()

            # Get frame time in seconds, clamp huge spikes
            frame_time = self.clock.tick(self.fps) / 1000.0
            frame_time = min(frame_time, 0.25)  # cap max 250ms

            accumulator += frame_time

            # Poll events and update input once per frame
            self.event_manager.poll_events()
            self.input.update()

            # Fixed timestep updates (physics / stable simulation)
            max_updates = 5
            updates = 0
            while accumulator >= fixed_dt and updates < max_updates:
                self.scene_manager.fixed_update(fixed_dt)
                accumulator -= fixed_dt
                updates += 1

            # Variable timestep updates (animations, UI, effects)
            self.scene_manager.update(frame_time)

            # Render the scene
            self.render()

