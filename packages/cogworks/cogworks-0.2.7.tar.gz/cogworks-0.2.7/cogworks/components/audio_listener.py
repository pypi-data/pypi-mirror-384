from cogworks.component import Component
from cogworks.components.camera import Camera
from cogworks.components.audio_source import AudioSource


class AudioListener(Component):
    """
    Represents an audio listener component that processes audio sources
    relative to the active camera's position.

    This component keeps track of all active `AudioSource` instances,
    updates their perceived position based on the listener's location
    (typically tied to the camera), and handles registration and cleanup.
    """

    def __init__(self):
        super().__init__()
        self._sources = set()

    def register_source(self, source: AudioSource) -> None:
        """
        Register an AudioSource to be managed by this listener.

        This links the source with the listener, allowing positional
        audio updates based on the listener's location.

        Args:
            source (AudioSource): The audio source to register.
        """
        self._sources.add(source)
        source._listener = self

    def unregister_source(self, source: AudioSource) -> None:
        """
        Unregister an AudioSource from this listener.

        Removes the source from tracking and clears its listener reference.

        Args:
            source (AudioSource): The audio source to unregister.
        """
        self._sources.discard(source)
        source._listener = None

    def clear_sources(self) -> None:
        """
        Stop and remove all registered audio sources.

        This is typically called when the listener is destroyed or reset.
        Ensures all associated sources are stopped and detached safely.
        """
        for source in list(self._sources):
            source.stop()
            source._listener = None
        self._sources.clear()

    def update(self, dt: float) -> None:
        """
        Update all registered audio sources with the current listener position.

        The listener’s position is derived from the attached `Camera` component,
        ensuring spatial audio behaves correctly relative to the view.
        """
        cam = self.game_object.get_component(Camera)
        if cam:
            listener_pos = (cam.offset_x, cam.offset_y)
            for source in list(self._sources):
                source.set_listener_position(listener_pos)
