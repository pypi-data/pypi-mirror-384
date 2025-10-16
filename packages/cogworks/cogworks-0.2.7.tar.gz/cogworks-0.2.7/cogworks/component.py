class Component:
    """
    Base class for all components.
    Components add specific behaviour to GameObjects (e.g., rendering, physics, input).
    """

    def __init__(self):
        """
        Initialise a new Component.
        The parent GameObject will be assigned automatically when the component is added.
        """
        self.game_object = None  # Set when attached to a GameObject
        self.active = True
        self.is_runtime = False
        self.has_started = False

    def start(self) -> None:
        """
        Called once when the component is first added to a GameObject
        or when the GameObject starts.
        Override in subclasses.
        """
        pass

    def update(self, dt: float) -> None:
        """
        Called every frame to update the component.

        Args:
            dt (float): Delta time since the last frame, in seconds.
        """
        pass

    def fixed_update(self, dt: float) -> None:
        """
        Called at a fixed timestep for deterministic updates,
        such as physics or AI logic.

        Args:
            dt (float): Fixed delta time.
        """
        pass

    def render(self, surface) -> None:
        """
        Called every frame to render visuals for this component.

        Args:
            surface: The pygame surface to render onto.
        """
        pass

    def on_remove(self) -> None:
        """
        Called when the component is removed from its GameObject.
        Override in subclasses for cleanup logic.
        """
        pass

    def on_enabled(self):
        """
        Called when the component is enabled.
        """
        pass

    def on_disabled(self):
        """
        Called when the component is disabled.
        """
        pass

    def exists(self):
        """Returns True if the GameObject exists in the scene"""
        return self.game_object.exists()