import pygame


class _EventObj:
    def __init__(self, event: pygame.event.Event):
        self.event = event
        for prop, value in event.__dict__.items():
            setattr(self, prop, value)

    def __bool__(self):
        return not self.event is None

    def __str__(self):
        return str(self.event)


class _EventManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if not self.initialized:
            self.initialized = True
            self._events = []

    def _init(self):
        self._quit = False
        self._window_close = None

    def update(self):
        self._init()

        self._events = pygame.event.get()

    def get(self, key):
        for event in self._events:
            if event.type == key:
                return _EventObj(event)

        return None


class EventFinder:
    @staticmethod
    def init() -> bool:
        pygame.init()
        _EventManager()
        return True

    @staticmethod
    def update() -> None:
        _EventManager().update()

    @staticmethod
    def get(key) -> _EventObj:
        return _EventManager().get(key)
