from typing import TYPE_CHECKING, TypeVar
if TYPE_CHECKING:
    from .container import DIContainer


_T = TypeVar('_T', bound=object)
class DiResolver:
    """
    A class responsible for resolving and instantiating dependencies
    by retrieving them from a dependency injection container.

    The resolver uses the provided DIContainer to retrieve instances
    of registered classes and automatically inject their dependencies.
    If a class is not registered, it will attempt to resolve its
    dependencies dynamically.
    """

    def __init__(self, container: 'DIContainer'):
        self.__container = container

    def resolve(self, class_type: type[_T]) -> _T:
        """
        Resolves an instance of a class with its dependencies injected.

        - If the class is registered, it retrieves the instance from the container.
        - If the class is not registered, it attempts to resolve dependencies automatically.

        :param class_type: The class type to be instantiated.
        :return: An instance of the class with its dependencies injected.
        :raises ValueError: If a constructor parameter is missing a type annotation or cannot be resolved.
        """
        return self.__container.resolve(class_type)
