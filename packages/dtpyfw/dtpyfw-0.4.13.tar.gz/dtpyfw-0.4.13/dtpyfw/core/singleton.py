__all__ = (
    "singleton_class",
    "singleton_class_by_args",
)


def singleton_class(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


def singleton_class_by_args(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        # Create a unique key based on the arguments
        key = (args, frozenset(kwargs.items()))
        if key not in instances:
            instances[key] = cls(*args, **kwargs)
        return instances[key]

    return get_instance
