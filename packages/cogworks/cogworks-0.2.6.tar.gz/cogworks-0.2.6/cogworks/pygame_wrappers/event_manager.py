import pygame

class EventManager:
    _instance = None

    @staticmethod
    def get_instance():
        if EventManager._instance is None:
            EventManager()
        return EventManager._instance

    def __init__(self):
        if EventManager._instance is not None:
            raise Exception("EventManager is a singleton! Use get_instance() instead.")
        EventManager._instance = self
        self.subscribers = []

    def subscribe(self, callback):
        """Subscribe a callable to receive events."""
        if callback not in self.subscribers:
            self.subscribers.append(callback)

    def unsubscribe(self, callback):
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    def poll_events(self):
        """Poll events once per frame and notify subscribers."""
        for event in pygame.event.get():
            for callback in self.subscribers:
                callback(event)