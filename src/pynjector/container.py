from typing import Callable, TypeVar
from itertools import islice
import inspect

from .lifetime import DiLifetime
from .cell import DiCell, FORBIDDEN_TYPES
from .resolver import DiResolver


_T = TypeVar('_T', bound=object)
class DIContainer:
    """
    A simple dependency injection pynjector that automatically resolves dependencies
    based on constructor parameters using type hints.

    It allows you to bind classes and automatically resolve their dependencies
    when instantiating them.
    """

    def __init__(self):
        self.__bindings: dict[type, DiCell] = {
            DiResolver: DiCell.instance(DiResolver, DiResolver(self)),
        }

    def bind(self, class_type: type, factory: DiLifetime | Callable[[], any] | any | None = None):
        """
        Binds a class to the DI container. Supports:
        - A concrete instance (Singleton)
        - A factory function for creating instances
        - Direct instantiation using type constructor

        :param class_type: The class type to bind.
        :param factory: Can be an instance, a factory function, a lifetime type, or None.
        :raises ValueError: If the provided class type or factory is invalid.
        """
        if not isinstance(class_type, type):
            raise ValueError(f"Expected 'class_type' to be a class, but got {type(class_type)}.")

        if class_type in (DIContainer, DiCell, DiResolver):
            raise TypeError(f"Invalid type: {class_type.__name__} - injector types cannot be used.")

        if class_type in FORBIDDEN_TYPES:
            raise TypeError(f"Invalid type: {class_type.__name__} is a default immutable type and cannot be used.")

        if isinstance(factory, class_type):
            self.__bindings[class_type] = DiCell.instance(class_type, factory)
        elif callable(factory):
            constructor_params = inspect.signature(factory).parameters
            if len(constructor_params) != 0:
                raise ValueError(f"Initialize function parameters of class '{class_type.__name__}' should be empty.")
            self.__bindings[class_type] = DiCell.factory(class_type, factory)
        else:
            if factory and not isinstance(factory, DiLifetime):
                raise ValueError(
                    f"Expected 'factory' to be lifetime or callable or an instance of {class_type.__name__}, but got {type(factory).__name__}.")

            constructor_params = inspect.signature(class_type).parameters
            # Check that each constructor parameter is registered
            for param, param_details in islice(constructor_params.items(), 0, None):
                if param_details.annotation is inspect.Signature.empty:
                    raise ValueError(f"Constructor parameter '{param}' is missing a type annotation.")

                param_type = param_details.annotation
                if isinstance(param_type, type) and param_type not in self.__bindings:
                    raise ValueError(f"Constructor parameter '{param}' of class '{class_type.__name__}' "
                                     f"depends on unregistered type '{param_type.__name__}'.")

            self.__bindings[class_type] = DiCell.typed(class_type, factory)

    def is_registered(self, class_type: type) -> bool:
        """
        Check whether the requested class type is registered in the container.

        :param class_type: The class type to check.
        :return: True if `class_type` is registered, False otherwise.

        Notes
        -----
        - Only exact type matches are checked.
        - Does NOT follow subclass relationships.
        - Does NOT instantiate the provider; this is a pure lookup.
        """

        return class_type in self.__bindings

    def resolve(self, class_type: type[_T]) -> _T:
        """
        Resolves an instance of a class with its dependencies injected.

        - If the class is registered, it retrieves the instance from the container.
        - If the class is not registered, it attempts to resolve dependencies automatically.

        :param class_type: The class type to be instantiated.
        :return: An instance of the class with its dependencies injected.
        :raises ValueError: If a constructor parameter is missing a type annotation or cannot be resolved.
        """

        if not isinstance(class_type, type):
            raise ValueError(f"Expected 'class_type' to be a class, but got {type(class_type)}.")

        if class_type in FORBIDDEN_TYPES:
            raise TypeError(f"Invalid type: {class_type.__name__} is a default immutable type and cannot be used.")

        resolved_cell = self.__bindings.get(class_type, None)
        if resolved_cell is None:
            return DiCell.resolve_type(class_type, self.__bindings)

        return resolved_cell.get_instance(self.__bindings)
