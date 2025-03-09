from typing import Callable
from itertools import islice
from threading import Lock
from enum import Enum
import inspect

from .lifetime import DiLifetime


FORBIDDEN_TYPES = (int, float, str, bool, bytes, tuple, frozenset, complex, Enum)


class DiCellKind(Enum):
    """
    Enum representing different kinds of dependency injection (DI) cells.
    """
    TYPED = 1  # A class type that should be instantiated when needed
    FACTORY = 2  # A callable factory function that returns an instance
    INSTANCE = 3  # A pre-instantiated object


class DiCell:
    def __init__(self):
        """
        Private constructor to prevent direct instantiation.
        Use class methods `typed`, `factory`, or `instance` instead.
        """
        raise Exception("This constructor is invalid, use the provided factory functions.")

    @classmethod
    def __default_factory(cls, kind: DiCellKind, class_type: type):
        """
        Internal factory method to create a DiCell instance with a given kind and class type.
        """
        self = super().__new__(cls)  # Properly create a new instance
        self._kind = kind
        self._class_type = class_type
        return self

    @classmethod
    def typed(cls, class_type: type, lifetime: DiLifetime | None = None):
        """
        Registers a class type with an lifetime policy.

        :param class_type: The class type to be instantiated.
        :param lifetime: The lifetime policy (default: SINGLETON).
        """
        self = cls.__default_factory(DiCellKind.TYPED, class_type)
        self._lifetime = lifetime or DiLifetime.MAYFLY
        if self._lifetime == DiLifetime.SINGLETON:
            self._lock = Lock()
        return self

    @classmethod
    def factory(cls, class_type: type, initializer: Callable[[], any]):
        """
        Registers a factory function that will create an instance when needed.

        :param class_type: The class type that the factory will produce.
        :param initializer: A callable that returns an instance of the class.
        """
        self = cls.__default_factory(DiCellKind.FACTORY, class_type)
        self._initializer = initializer
        return self

    @classmethod
    def instance(cls, class_type: type, instance: any):
        """
        Registers a pre-instantiated object.

        :param class_type: The type of the instance.
        :param instance: The already created instance.
        """
        self = cls.__default_factory(DiCellKind.INSTANCE, class_type)
        self._instance = instance
        return self

    @staticmethod
    def resolve_type(class_type: type, bindings: dict[type, 'DiCell']):
        """
        Resolves dependencies for a given class by inspecting its constructor parameters.

        :param class_type: The class type to be instantiated.
        :param bindings: The dictionary of registered types.
        :return: An instance of the class with its dependencies injected.
        """
        constructor_params = inspect.signature(class_type).parameters
        resolved_params = {}

        for param, param_details in islice(constructor_params.items(), 0, None):
            param_type = param_details.annotation
            if param_type is inspect.Signature.empty:
                raise ValueError(f"Constructor parameter '{param}' of class '{class_type.__name__}'"
                                 f" is missing a type annotation.")

            resolved_cell = bindings.get(param_type, None)
            if resolved_cell is None:
                raise ValueError(f"Constructor parameter '{param}' of class '{class_type.__name__}' "
                                 f"depends on unregistered type '{param_type.__name__}'.")

            resolved_params[param] = resolved_cell.get_instance(bindings)
        return class_type(**resolved_params)

    def get_instance(self, bindings: dict[type, 'DiCell']) -> any:
        """
        Retrieves an instance of the registered type, handling different DI cell kinds accordingly.

        :param bindings: The dictionary of registered dependencies.
        :return: An instance of the required type.
        """
        if self._kind == DiCellKind.TYPED:
            if self._lifetime == DiLifetime.SINGLETON:
                with self._lock:
                    if hasattr(self, '_instance'):
                        return self._instance
                    self._instance = self.resolve_type(self._class_type, bindings)
                    return self._instance

            elif self._lifetime == DiLifetime.MAYFLY:
                return self.resolve_type(self._class_type, bindings)

            raise Exception(f"Invalid lifetime policy of type '{self._class_type.__name__}'.")

        elif self._kind == DiCellKind.FACTORY:
            return self._initializer()

        elif self._kind == DiCellKind.INSTANCE:
            return self._instance

        raise Exception(f"Unknown DI cell kind of type '{self._class_type.__name__}'.")
