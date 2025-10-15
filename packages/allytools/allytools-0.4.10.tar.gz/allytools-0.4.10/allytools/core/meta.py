class IterableConstants(type):
    def __iter__(cls):
        for attr in dir(cls):
            if not attr.startswith("_") and not callable(getattr(cls, attr)):
                yield getattr(cls, attr)