from cogworks.utils.asset_loader import load_engine_image


class Window:
    """
    A wrapper class around pygame's display window handling.
    Provides convenient methods for creating and resizing the window.
    """

    _instance = None

    @staticmethod
    def get_instance():
        if not Window._instance:
            raise Exception("Window has not been created yet!")
        return Window._instance

    def __init__(self, pygame, width: int, height: int, caption: str, resizable: bool = False, fullscreen: bool = False, background_color: tuple = (30, 30, 30)):
        """
        Initialise a window with the given dimensions and caption.

        Args:
            pygame: The pygame module instance.
            width (int): The initial width of the window.
            height (int): The initial height of the window.
            caption (str): The caption/title of the window.
            resizable (bool, optional): If True, allows the window to be resizable. Defaults to False.
            fullscreen (bool, optional): If True, starts the window in fullscreen mode. Defaults to False.
            background_color (tuple, optional): Background color of the window. Defaults to (30, 30, 30).
        """
        if Window._instance is not None:
            raise Exception("Window is a singleton! Use Window.get_instance().")
        Window._instance = self

        self.pygame = pygame
        self.width = width
        self.height = height
        self.caption = caption
        self.resizable = resizable
        self.fullscreen = fullscreen
        self.background_color = background_color
        self.event_manager = None

        pygame.init()
        self.screen = self._create_window()

    def _create_window(self):
        """Internal helper to create the pygame window with the current settings."""
        flags = 0
        if self.resizable:
            flags |= self.pygame.RESIZABLE
        if self.fullscreen:
            flags |= self.pygame.FULLSCREEN

        self.pygame.display.set_caption(self.caption)
        screen = self.pygame.display.set_mode((self.width, self.height), flags)
        icon = load_engine_image("images/cog_works_icon_2.png")
        self.pygame.display.set_icon(icon)
        return screen

    def configure(self, width: int = None, height: int = None, resizable: bool = None, fullscreen: bool = None, background_color: tuple = None):
        """
        Reconfigure the window size or settings.

        Args:
            width (int, optional): New width of the window. If None, keeps current width.
            height (int, optional): New height of the window. If None, keeps current height.
            resizable (bool, optional): Update whether the window should be resizable.
            fullscreen (bool, optional): Update whether the window should be fullscreen.
            background_color (tuple, optional): Background color of the window.
        """
        if width:
            self.width = width
        if height:
            self.height = height
        if resizable is not None:
            self.resizable = resizable
        if fullscreen is not None:
            self.fullscreen = fullscreen
        if background_color is not None:
            self.background_color = background_color

        self.screen = self._create_window()

    def toggle_fullscreen(self):
        """Toggle fullscreen mode on or off."""
        self.fullscreen = not self.fullscreen
        self.screen = self._create_window()

    def resize(self, width: int, height: int):
        """"
        Resize the window to the given dimensions.

        Args:
            width (int): The new width.
            height (int): The new height.
        """
        self.configure(width=width, height=height)

    def get_size(self):
        """
        Get the current size of the window.

        Returns:
            tuple: (width, height)
        """
        return self.screen.get_size()

    def render(self):
        """Render the window with background color."""
        self.screen.fill(self.background_color)

    def handle_event(self, event):
        """Handle pygame events."""
        if event.type == self.pygame.VIDEORESIZE:
            self.resize(event.w, event.h)

    def subscribe_events(self, event_manager):
        self.event_manager = event_manager
        event_manager.subscribe(self.handle_event)