import os
import pygame
import importlib.resources as res

def load_engine_audio(relative_path: str) -> pygame.mixer.Sound:
    """
    Load an audio file bundled inside the cogworks package.
    Example: load_engine_audio("sounds/click.wav")
    """
    _ensure_pygame_mixer()

    with res.files("cogworks.engine_assets").joinpath(relative_path).open("rb") as f:
        # Pygame mixer cannot load directly from file-like objects,
        # so we must write to a temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(f.read())
            tmp_path = tmp.name

    sound = pygame.mixer.Sound(tmp_path)
    os.remove(tmp_path)
    return sound


def load_user_audio(relative_path: str) -> pygame.mixer.Sound:
    """
    Load an audio file from the user's project 'assets' folder.
    Example: load_user_audio("sounds/jump.wav")
    """
    _ensure_pygame_mixer()

    project_root = os.getcwd()
    assets_dir = os.path.join(project_root, "assets")
    abs_path = os.path.join(assets_dir, relative_path)

    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"User audio asset not found: {abs_path}")

    return pygame.mixer.Sound(abs_path)


def _ensure_pygame_mixer():
    if not pygame.get_init():
        pygame.init()
    if not pygame.mixer.get_init():
        pygame.mixer.init()

def load_engine_image(relative_path: str) -> pygame.Surface:
    """
    Load an image bundled inside the cogworks package.
    Example: load_engine_image("images/default.png")
    """
    with res.files("cogworks.engine_assets").joinpath(relative_path).open("rb") as f:
        img = pygame.image.load(f).convert_alpha()
    _ensure_pygame_display()
    return img


def load_user_image(relative_path: str) -> pygame.Surface:
    """
    Load an image from the user's project 'assets' folder.
    Example: load_user_image("images/player.png")
    """
    project_root = os.getcwd()
    assets_dir = os.path.join(project_root, "assets")
    abs_path = os.path.join(assets_dir, relative_path)

    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"User asset not found: {abs_path}")

    img = pygame.image.load(abs_path).convert_alpha()
    _ensure_pygame_display()
    return img


def _ensure_pygame_display():
    if not pygame.get_init():
        pygame.init()
    if not pygame.display.get_init():
        pygame.display.set_mode((1, 1))
