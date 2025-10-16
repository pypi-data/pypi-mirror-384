import uuid

from cogworks.components.transform import Transform


class GameObject:
    """
    A base class representing any entity in the game world.
    GameObjects can hold components that define their behaviour,
    such as rendering, physics, or custom logic.
    """

    _id_counter = 0  # class-level counter for incremental IDs

    def __init__(self, name: str = "GameObject", z_index: int = 0, x: float = 0, y: float = 0, scale_x: float = 1, scale_y: float = 1, rotation: float = 0):
        """
        Initialise a new GameObject with a unique identifier.
        Automatically adds a Transform component.
        """
        # Assign unique IDs
        self.uuid = uuid.uuid4()          # Globally unique identifier
        self.id = GameObject._id_counter  # Local incremental ID
        GameObject._id_counter += 1

        # Meta information
        self.name = name
        self._active = True
        self.z_index = z_index
        self.is_ui_object = False

        # Scene
        self.scene = None
        self.camera = None

        # Component storage
        self.initial_components: list = []
        self._sorted_components: list = []
        self.runtime_components: list = []

        # Add default Transform component
        self.transform = Transform(x=x, y=y, scale_x=scale_x, scale_y=scale_y, rotation=rotation)
        self.add_component(self.transform)

        # ---------------- Hierarchy ----------------
        self.parent: "GameObject | None" = None  # Parent GameObject
        self.initial_children: list["GameObject"] = []
        self.runtime_children: list["GameObject"] = []

    # ---------------- Component Management ----------------
    def add_component(self, component) -> None:
        """
        Attach a component to the GameObject.
        Ensures only one component of each type exists.
        Prevents adding Rigidbody2D to a child GameObject.
        """
        component_type = type(component)

        # Only allow one Transform
        if component_type is Transform and self.get_component(Transform):
            raise ValueError("GameObject already has a Transform component")

        # Prevent duplicate components
        if self.get_component(component_type) is not None:
            raise ValueError(f"GameObject already has a component of type {component_type.__name__}")

        # Prevent adding Rigidbody2D to child objects
        if component_type.__name__ == "Rigidbody2D" and self.parent is not None:
            raise ValueError("Cannot add Rigidbody2D to a child GameObject")

        component.game_object = self
        target_list = self.runtime_components if self.scene and self.scene.has_started else self.initial_components

        target_list.append(component)
        if self.scene and self.scene.has_started:
            component.start()
            component.has_started = True

        self._sort_components()

    def remove_component(self, component_type) -> bool:
        """
        Remove the first component of the given type from the GameObject.
        """
        # Do not allow removing Transform
        if component_type is Transform and self in getattr(self.scene, "initial_components", []):
            print("Cannot remove Transform component from GameObject.")
            return False

        components = self.runtime_components if self.scene and self.scene.has_started else self.initial_components

        for i, comp in enumerate(components):
            if isinstance(comp, component_type):
                if hasattr(comp, "on_remove"):
                    comp.on_remove()
                components.pop(i)
                del comp
                self._sort_components()
                return True
        return False

    def get_component(self, component_type):
        """
        Retrieve the first component of a given type.
        Accepts either the class type or a string with the class name.
        """
        # Cache concatenation to avoid repeated list creation
        components = self._all_components
        if isinstance(component_type, str):
            for comp in components:
                if comp.__class__.__name__ == component_type:
                    return comp
        else:
            for comp in components:
                if isinstance(comp, component_type):
                    return comp
        return None

    def has_component(self, component) -> bool:
        """
        Check if the GameObject has a component of the given type or class name.
        Accepts either a class type or a string with the component's class name.
        """
        return self.get_component(component) is not None

    def _sort_components(self):
        """Maintain a sorted list of components by z_index."""
        self._sorted_components = sorted(
            self._all_components,
            key=lambda c: getattr(c, "z_index", 0)
        )

    @property
    def _all_components(self):
        """Cache for faster access instead of concatenating repeatedly"""
        return self.initial_components + self.runtime_components

    @property
    def components(self):
        return self._all_components

    # ---------------- Hierarchy Management ----------------
    def add_child(self, child: "GameObject") -> None:
        """
        Add a child GameObject to this GameObject.
        Automatically removes child from previous parent if needed
        and propagates this GameObject's scene to the child hierarchy.
        """
        if child.parent:
            child.parent.remove_child(child)
        child.parent = self
        child.scene = self.scene

        target_list = self.runtime_children if self.scene and self.scene.has_started else self.initial_children
        target_list.append(child)

        if self.scene:
            child._set_scene_recursive(self.scene)  # propagate scene to child and descendants

        if self.scene and self.scene.has_started:
            child.start()

    def _set_scene_recursive(self, scene):
        self.scene = scene
        for child in self._all_children:
            child._set_scene_recursive(scene)

    def remove_child(self, child: "GameObject") -> None:
        """
        Remove a child GameObject from this GameObject and clear its scene.
        """
        target_list = self.runtime_children if self.scene and self.scene.has_started else self.initial_children
        if child in target_list:
            target_list.remove(child)
            child.parent = None

    def get_children(self) -> list["GameObject"]:
        """
        Return a list of child GameObjects.
        """
        return self.children

    @property
    def _all_children(self):
        """Cache for faster access instead of concatenating repeatedly"""
        return self.initial_children + self.runtime_children

    @property
    def children(self):
        return self._all_children

    # ---------------- Lifecycle ----------------
    def start(self) -> None:
        """
        Call start() on all components and children.
        """
        self.camera = self.scene.camera_component
        self._sort_components()
        for comp in self.initial_components:
            if not comp.has_started:
                comp.start()
                comp.has_started = True
        for child in self.initial_children:
            child.enable()
            child.start()

    def update(self, dt: float) -> None:
        """
        Update all components and children.
        """
        if not self._active:
            return

        if not self.is_ui_object: self.transform.check_bounds()

        x, y = self.transform.get_world_position()
        if not self.is_ui_object and not self.camera.is_visible(x=x, y=y, width=0, height=0, tolerance=2000):
            return

        components = self._all_components
        children = self._all_children

        for comp in components:
            if comp.has_started:
                comp.update(dt)
        for child in children:
            child.update(dt)

    def fixed_update(self, dt: float) -> None:
        """
        Fixed timestep update for physics or deterministic logic.
        Calls fixed_update on all components that implement it, including children.
        """
        if not self._active:
            return

        components = self._all_components
        children = self._all_children

        for comp in components:
            if comp.has_started:
                comp.fixed_update(dt)
        for child in children:
            child.fixed_update(dt)

    def render(self, surface) -> None:
        if not self._active:
            return

        sorted_components = self._sorted_components
        children = self._all_children

        for comp in sorted_components:
            comp.render(surface)

        for child in children:
            child.render(surface)

    def cleanup(self) -> None:
        for comp in list(self.runtime_components):
            self.remove_component(type(comp))
        for child in list(self.runtime_children):
            self.remove_child(child)
            child.cleanup()
        for comp in self.initial_components:
            comp.has_started = False
        self.runtime_components = []
        self.runtime_children = []
        self._sort_components()

    def destroy(self):
        """Remove the GameObject from its parent or scene, or deactivate if it's a starting object."""

        # Helper function to decide whether to deactivate or remove
        def deactivate_or_remove(container, start_list, remove_func):
            if self in start_list:
                self.disable()
            else:
                remove_func(self)

        if self.parent:
            deactivate_or_remove(
                container=self.parent,
                start_list=self.parent.initial_children,
                remove_func=self.parent.remove_child
            )
        else:
            deactivate_or_remove(
                container=self.scene,
                start_list=getattr(self.scene, "initial_objects", []),
                remove_func=self.scene.remove_game_object
            )

    def enable(self):
        """Enable the GameObject"""
        self._active = True
        self.on_enabled()

    def disable(self):
        """Disable the GameObject"""
        self._active = False
        self.on_disabled()

    def on_enabled(self):
        """
        Called when the GameObject is enabled
        """
        for comp in self._all_components:
            comp.on_enabled()
        for child in self._all_children:
            child.on_enabled()

    def on_disabled(self):
        """
        Called when the GameObject is disabled
        """
        for comp in self._all_components:
            comp.on_disabled()
            comp.has_started = False
        for child in self._all_children:
            child.on_disabled()

    def exists(self):
        """Returns True if the GameObject exists in the scene"""
        return self._active

    def get_all_components_of_type(self, component_type):
        components = []
        for comp in self.components:
            if type(comp) == component_type:
                components.append(comp)
        for child in self.children:
            components = components + child.get_all_components_of_type(component_type)
        return components

    # ---------------- Utilities ----------------
    def get_world_position(self):
        return self.transform.get_world_position()

    def __repr__(self):
        return f"<GameObject id={self.id}, uuid={self.uuid}, name='{self.name}' child_count={len(self._all_children)} active={self._active}>"
