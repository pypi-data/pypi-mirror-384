from cogworks.component import Component


class ScriptComponent(Component):
    """
    Base class for user-defined logic components.
    Inherit from this to add custom behaviour
    to GameObjects.
    """

    def start(self) -> None:
        """
        Called once when the component is first added to a GameObject
        or when the GameObject starts.
        Override this in subclasses.
        """
        super().start()

    def update(self, dt: float) -> None:
        """
        Called every frame to update the component.
        Override this in subclasses.
        """
        super().update(dt)

    def fixed_update(self, dt: float) -> None:
        """
        Called at a fixed timestep for deterministic updates
        such as physics or AI logic.
        Override this in subclasses.
        """
        super().fixed_update(dt)

    def render(self, surface) -> None:
        """
        Called every frame to render visuals for this component.
        Override this in subclasses.
        """
        super().render(surface)

    def on_remove(self) -> None:
        """
        Called when the component is removed from its GameObject.
        Override this in subclasses for cleanup logic.
        """
        super().on_remove()
