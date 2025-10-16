class MissingComponentError(Exception):
    def __init__(self, component_type, game_object):
        super().__init__(f"{game_object} is missing required component: {component_type.__name__}")