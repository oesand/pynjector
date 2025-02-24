from typing import Type, Callable, Dict, Any
import inspect


class DIContainer:
    """
    A simple dependency injection container that automatically resolves dependencies
    based on constructor parameters using type hints.

    It allows you to bind classes and automatically resolve their dependencies
    when instantiating them.
    """

    def __init__(self):
        """
        Initializes the DI container.
        """
        self._bindings: Dict[Type, Callable[[], Any]] = {}

    def bind(self, class_type: Type, factory: Callable[[], Any] | Any | None = None):
        """
        Binds a class to the container. You can optionally provide a factory function or an already created instance.
        If no factory is provided, the default constructor of the class is used.

        If no factory is provided, the class's constructor must not have any parameters,
        and all parameters must be registered classes.

        If an instance is provided, it will be used as the singleton instance of the class.

        :param class_type: The class type that should be bound in the container.
        :param factory: A function or lambda that creates an instance of the class, or an already created instance.
                        If not provided, the class will be instantiated using its constructor.
        """
        if not isinstance(class_type, type):
            raise ValueError(f"Expected 'class_type' to be a class, but got {type(class_type)}.")

        if factory and not (callable(factory) or isinstance(factory, class_type)):
            raise ValueError(
                f"Expected 'factory' to be callable or an instance of {class_type.__name__}, but got {type(factory).__name__}.")

        # If factory is an instance, treat it as a singleton
        if isinstance(factory, class_type):
            self._bindings[class_type] = factory
        elif callable(factory):
            # Register the callable to create instances of the class
            self._bindings[class_type] = factory
        elif not factory:
            constructor_params = inspect.signature(class_type).parameters
            if len(constructor_params) > 1:  # More than just 'self'
                # Check that each constructor parameter is registered
                for param, param_details in constructor_params.items():
                    if param != 'self':
                        if param_details.annotation is inspect.Signature.empty:
                            raise ValueError(f"Constructor parameter '{param}' is missing a type annotation.")
                        param_type = param_details.annotation
                        if isinstance(param_type, type) and param_type not in self._bindings:
                            raise ValueError(f"Constructor parameter '{param}' of class '{class_type.__name__}' "
                                             f"depends on unregistered type '{param_type.__name__}'.")
            # Register the class with the default constructor
            self._bindings[class_type] = class_type

    def resolve(self, class_type: Type) -> Any:
        """
        Resolves a dependency and returns an instance of the class.
        Automatically resolves constructor dependencies based on type annotations.
        It resolves registered classes and unregistered classes by analyzing constructor annotations.

        :param class_type: The class type to be instantiated.
        :return: An instance of the specified class with its dependencies injected.
        :raises ValueError: If a constructor parameter is missing a type annotation or cannot be resolved.
        """

        if not isinstance(class_type, type):
            raise ValueError(f"Expected 'class_type' to be a class, but got {type(class_type)}.")

        return self._resolve_dependencies(class_type)

    def _resolve_dependencies(self, class_type: Type) -> Any:
        initializer = self._bindings.get(class_type, class_type)
        if not callable(initializer):
            return initializer

        constructor_params = inspect.signature(initializer).parameters
        resolved_params = {}

        # Resolve dependencies for each constructor parameter with type annotations
        for param, param_details in constructor_params.items():
            if param == 'self':
                continue

            if param_details.annotation is inspect.Signature.empty:
                raise ValueError(f"Constructor parameter '{param}' of class '{class_type.__name__}'"
                                 f" is missing a type annotation.")

            param_type = param_details.annotation
            if param_type not in self._bindings:
                raise ValueError(f"Constructor parameter '{param}' of class '{class_type.__name__}' "
                                 f"depends on unregistered type '{param_type.__name__}'.")

            resolved_params[param] = self._resolve_dependencies(param_type)

        # Instantiate the class with resolved dependencies
        return class_type(**resolved_params)
