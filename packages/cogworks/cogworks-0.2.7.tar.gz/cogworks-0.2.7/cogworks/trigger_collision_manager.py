import math
from collections import defaultdict

class TriggerCollisionManager:
    def __init__(self, cell_size=128):
        """
        Initialise the collision manager.

        Args:
            cell_size (int): Size of each spatial grid cell for collision partitioning.
        """
        self.colliders = set()
        self.spatial_grid = defaultdict(list)
        self.cell_size = cell_size

    def register(self, collider):
        """
        Register a collider to the collision manager.

        Args:
            collider (TriggerCollider): The collider to be tracked.
        """
        self.colliders.add(collider)

    def unregister(self, collider):
        """
        Unregister a collider from the collision manager.

        Args:
            collider (TriggerCollider): The collider to remove.
        """
        self.colliders.discard(collider)

    def _get_cells(self, collider):
        """
        Calculate which spatial grid cells a collider occupies.

        Args:
            collider (TriggerCollider): The collider to evaluate.

        Returns:
            set of (int, int): Set of (x, y) cell coordinates.
        """
        if collider.shape == "rect":
            left, top = collider.rect.left, collider.rect.top
            right, bottom = collider.rect.right, collider.rect.bottom
        else:  # circle
            if collider.center is None:
                # fallback: use transform position
                x, y = collider.transform.get_world_position()
                cx, cy = x, y
            else:
                cx, cy = collider.center
            r = collider.radius
            left, top = cx - r, cy - r
            right, bottom = cx + r, cy + r

        x1 = math.floor(left / self.cell_size)
        y1 = math.floor(top / self.cell_size)
        x2 = math.floor(right / self.cell_size)
        y2 = math.floor(bottom / self.cell_size)

        return {(x, y) for x in range(x1, x2 + 1) for y in range(y1, y2 + 1)}

    def update(self, dt):
        self.spatial_grid.clear()

        # Populate the grid
        for collider in self.colliders:
            for cell in self._get_cells(collider):
                self.spatial_grid[cell].append(collider)

        checked_pairs = set()

        # Check collisions only within each cell
        for cell_colliders in self.spatial_grid.values():
            for i, a in enumerate(cell_colliders):
                for j in range(i + 1, len(cell_colliders)):
                    b = cell_colliders[j]

                    # Layer mask filtering
                    if (a.layer_mask and b.layer not in a.layer_mask) or \
                       (b.layer_mask and a.layer not in b.layer_mask):
                        continue

                    pair_id = tuple(sorted((id(a), id(b))))
                    if pair_id in checked_pairs:
                        continue
                    checked_pairs.add(pair_id)

                    if a.intersects(b):
                        # Trigger enter event if collision started this frame
                        if b not in a._colliding_with:
                            a._colliding_with.add(b)
                            b._colliding_with.add(a)
                            self._call_event(a, "on_trigger_enter", b)
                            self._call_event(b, "on_trigger_enter", a)
                        else:
                            # Trigger stay event if collision persists
                            self._call_event(a, "on_trigger_stay", b)
                            self._call_event(b, "on_trigger_stay", a)
                    else:
                        # Trigger exit event if collision ended this frame
                        if b in a._colliding_with:
                            a._colliding_with.remove(b)
                            b._colliding_with.remove(a)
                            self._call_event(a, "on_trigger_exit", b)
                            self._call_event(b, "on_trigger_exit", a)

    def _call_event(self, collider, event_name, other):
        """
        Helper to call a collision event on all components of a game object.

        Args:
            collider (TriggerCollider): The collider whose game object will receive the event.
            event_name (str): Name of the event method to call.
            other (TriggerCollider): The other collider involved in the event.
        """
        for comp in collider.game_object.components:
            if hasattr(comp, event_name):
                getattr(comp, event_name)(other)

    def clear(self):
        """Completely clear all registered colliders and reset the spatial grid."""
        self.colliders.clear()
        self.spatial_grid.clear()