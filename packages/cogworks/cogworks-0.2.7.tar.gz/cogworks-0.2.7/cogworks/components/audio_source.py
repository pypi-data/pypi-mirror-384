import pygame
from cogworks.component import Component
from cogworks.utils.asset_loader import load_user_audio


class AudioSource(Component):
    """
    Represents a sound-emitting component that can play, stop, and spatially
    adjust audio based on its position relative to an active `AudioListener`.

    This component uses `pygame.mixer` for playback and supports features such as
    looping, distance-based attenuation, stereo panning, and one-shot effects.
    """

    def __init__(
        self,
        clip_path: str | None = None,
        loop: bool = False,
        volume: float = 1.0,
        position: tuple[float, float] = (0.0, 0.0),
        listener_position: tuple[float, float] = (0.0, 0.0),
        max_distance: float = 5000.0,
        auto_update_position: bool = True,
    ):
        """
        Initialise an AudioSource component.

        Args:
            clip_path (str | None): Optional path to the initial audio clip.
            loop (bool): Whether the clip should loop when played.
            volume (float): Base volume of the audio (0.0 - 1.0).
            position (tuple[float, float]): Initial world position of the source.
            listener_position (tuple[float, float]): Position of the listener.
            max_distance (float): Maximum distance for spatial attenuation.
            auto_update_position (bool): Whether to auto-update position from the game object.
        """
        super().__init__()
        self.clip_path: str | None = clip_path
        self.clip: pygame.mixer.Sound | None = None
        self.channel: pygame.mixer.Channel | None = None
        self.loop: bool = loop
        self.volume: float = volume
        self.position: tuple[float, float] = position
        self.listener_position: tuple[float, float] = listener_position
        self.max_distance: float = max_distance
        self.auto_update_position: bool = auto_update_position
        self._listener = None

        # Automatically load clip if path provided
        if self.clip_path:
            self.set_clip(self.clip_path)


    def start(self) -> None:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        listener = self.game_object.scene.get_active_audio_listener()
        if listener:
            listener.register_source(self)
            self._listener = listener

    def on_disabled(self) -> None:
        """
        Called when the component is disabled.

        Unregisters the source from its listener and stops any active playback.
        """
        if self._listener:
            self._listener.unregister_source(self)
            self._listener = None
        self.stop()

    def on_remove(self) -> None:
        """
        Called when the component is removed from its game object.

        Unregisters from the listener and stops all audio to prevent leaks or crashes.
        """
        if self._listener:
            self._listener.unregister_source(self)
            self._listener = None
        self.stop()

    def update(self, dt: float) -> None:
        """
        Called every frame to update the component.

        Automatically updates the audio source’s position based on the
        game object’s transform (if enabled) and applies spatial audio logic.

        Args:
            dt (float): Delta time since the last update (unused, for consistency).
        """
        if self.auto_update_position:
            self.position = self.game_object.transform.get_world_position()
        self.update_spatial_audio()

    def set_clip(self, relative_path: str) -> None:
        """
        Load an audio clip from the given relative path.

        Args:
            relative_path (str): Path to the audio file relative to the asset directory.
        """
        self.clip_path = relative_path
        self.clip = load_user_audio(relative_path)
        self.clip.set_volume(self.volume)

    def play(self, bypass_spatial: bool = False) -> None:
        """
        Play the currently assigned audio clip.

        Optionally bypasses spatial effects (distance attenuation and stereo panning)
        and plays the clip at full volume.

        Args:
            bypass_spatial (bool): If True, ignore spatial effects during playback.
        """
        if not self.clip:
            return

        loops = -1 if self.loop else 0
        self.channel = self.clip.play(loops=loops)
        if self.channel:
            if bypass_spatial:
                self.channel.set_volume(self.volume, self.volume)
        else:
            print(f"[AudioSource] Failed to play '{self.clip_path}'")

    def play_one_shot(self, relative_path: str, volume: float = 1.0, bypass_spatial: bool = False) -> None:
        """
        Play a one-shot (temporary) audio clip without affecting the main clip.

        Useful for short sound effects such as clicks, footsteps, or impacts.

        Args:
            relative_path (str): Path to the audio file.
            volume (float): Playback volume multiplier (0.0 - 1.0).
            bypass_spatial (bool): If True, ignore spatial attenuation and panning.
        """
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        try:
            clip = load_user_audio(relative_path)
            clip.set_volume(max(0.0, min(1.0, volume)))
            channel = clip.play()
            if channel:
                if bypass_spatial:
                    channel.set_volume(volume, volume)
            else:
                print(f"[AudioSource] Failed to PlayOneShot '{relative_path}'")
        except Exception as e:
            print(f"[AudioSource] Error playing one-shot '{relative_path}': {e}")

    def stop(self) -> None:
        """
        Stop playback of the current clip, if one is active.
        """
        if self.channel:
            self.channel.stop()
            self.channel = None

    def set_listener_position(self, pos: tuple[float, float]) -> None:
        """
        Update the listener’s position used for spatial calculations.

        Args:
            pos (tuple[float, float]): The (x, y) position of the listener.
        """
        self.listener_position = pos

    def update_spatial_audio(self) -> None:
        """
        Apply spatial audio effects such as distance attenuation and stereo panning.

        Calculates the volume and stereo balance based on the distance and
        direction of the audio source relative to the listener. Closer sounds
        play louder and more central; distant sounds fade and pan left/right.
        """
        if not self.channel:
            return

        sx, sy = self.position
        lx, ly = self.listener_position

        dx = sx - lx
        dy = sy - ly
        distance = (dx**2 + dy**2) ** 0.5

        attenuation = max(0.0, 1.0 - (distance / self.max_distance))
        total_volume = self.volume * attenuation

        pan = max(-1.0, min(1.0, dx / self.max_distance))
        left = total_volume * (1.0 - max(0, pan))
        right = total_volume * (1.0 + min(0, pan))

        self.channel.set_volume(left, right)
