class EventManager:
    def __init__(self):
        self.events = {}

    def subscribe(self, event_name, callback):
        if event_name not in self.events:
            self.events[event_name] = []
        self.events[event_name].append(callback)

    def unsubscribe(self, event_name, callback):
        if event_name in self.events:
            self.events[event_name].remove(callback)
            if not self.events[event_name]:
                del self.events[event_name]

    def emit(self, event_name, *args, **kwargs):
        if event_name in self.events:
            for callback in self.events[event_name]:
                callback(*args, **kwargs)