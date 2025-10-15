from cogworks.component import Component

class UIRenderer(Component):
    def render(self, surface):
        raise NotImplementedError("UIRenderer subclasses must implement render()")
