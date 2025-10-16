__all__ = ["no_error"]


class NullContext:
    def __enter__(self, *args, **kwargs):
        pass

    def __exit__(self, *args, **kwargs):
        pass


no_error = NullContext()
