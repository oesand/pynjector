from enum import Enum


class DiLifetime(Enum):
    """
    Represents the lifetime of an object or instance.
    """

    SINGLETON = 1  # A single instance that persists throughout the application's lifetime.
    MAYFLY = 2  # A new instance is created each time it is needed (transient behavior).
