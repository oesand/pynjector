import pytest

from pynjector.container import DIContainer
from pynjector.cell import DiCell, DiCellKind, FORBIDDEN_TYPES
from pynjector.lifetime import DiLifetime
from pynjector.resolver import DiResolver


# ------------------------------------------------------------------------------
# Helper classes for tests
# ------------------------------------------------------------------------------

class A:
    pass

class B:
    def __init__(self, a: A):
        self.a = a

class C:
    def __init__(self, a: A, b: B):
        self.a = a
        self.b = b

class NoAnnotation:
    def __init__(self, x):
        pass

class NeedUnregistered:
    def __init__(self, x: int):   # int is forbidden/unregistered
        pass


# ------------------------------------------------------------------------------
# DIContainer.bind tests
# ------------------------------------------------------------------------------

def test_bind_wrong_type():
    c = DIContainer()
    with pytest.raises(ValueError):
        c.bind(123)


def test_bind_forbidden_type():
    c = DIContainer()
    for t in FORBIDDEN_TYPES:
        with pytest.raises(TypeError):
            c.bind(t)


def test_bind_injector_type_disallowed():
    c = DIContainer()
    with pytest.raises(TypeError):
        c.bind(DIContainer)
    with pytest.raises(TypeError):
        c.bind(DiCell)
    with pytest.raises(TypeError):
        c.bind(DiResolver)


def test_bind_instance():
    c = DIContainer()
    a = A()
    c.bind(A, a)
    assert c.resolve(A) is a


def test_bind_factory_with_non_empty_constructor():
    class K:
        def __init__(self, x: A): pass

    c = DIContainer()
    with pytest.raises(ValueError):
        c.bind(K, lambda x: K(0))


def test_bind_factory_success():
    class K:
        def __init__(self): pass

    c = DIContainer()
    c.bind(K, lambda: K())
    assert isinstance(c.resolve(K), K)


def test_bind_typed_requires_annotations():
    class K:
        def __init__(self, x): pass

    c = DIContainer()
    with pytest.raises(ValueError):
        c.bind(K)


def test_bind_typed_unregistered_dependency():
    class K:
        def __init__(self, x: A): pass

    c = DIContainer()
    with pytest.raises(ValueError):
        c.bind(K)


def test_bind_typed_mayfly_default():
    class K:
        def __init__(self): pass

    c = DIContainer()
    c.bind(K)
    i1 = c.resolve(K)
    i2 = c.resolve(K)
    assert i1 is not i2


def test_bind_typed_singleton():
    class K:
        def __init__(self): pass

    c = DIContainer()
    c.bind(K, DiLifetime.SINGLETON)
    a = c.resolve(K)
    b = c.resolve(K)
    assert a is b


# ------------------------------------------------------------------------------
# DIContainer.resolve tests
# ------------------------------------------------------------------------------

def test_resolve_forbidden_type():
    c = DIContainer()
    with pytest.raises(TypeError):
        c.resolve(int)


def test_resolve_dynamic_unregistered():
    c = DIContainer()
    c.bind(A)
    c.bind(B)
    obj = c.resolve(B)
    assert isinstance(obj, B)


def test_resolve_missing_annotation():
    c = DIContainer()
    with pytest.raises(ValueError):
        c.resolve(NoAnnotation)


def test_resolve_unregistered_dependency():
    c = DIContainer()
    with pytest.raises(ValueError):
        c.resolve(B)


def test_resolver_injected():
    c = DIContainer()
    resolver = c.resolve(DiResolver)
    assert isinstance(resolver, DiResolver)
    assert resolver.resolve(A)  # dynamic resolve works


# ------------------------------------------------------------------------------
# Lifetime behavior integration
# ------------------------------------------------------------------------------

def test_mayfly_integration():
    c = DIContainer()
    c.bind(A)
    i1 = c.resolve(A)
    i2 = c.resolve(A)
    assert i1 is not i2


def test_singleton_integration():
    c = DIContainer()
    c.bind(A, DiLifetime.SINGLETON)
    i1 = c.resolve(A)
    i2 = c.resolve(A)
    assert i1 is i2


def test_complex_dependency_graph():
    c = DIContainer()
    c.bind(A)
    c.bind(B)
    c.bind(C)
    c_instance = c.resolve(C)
    assert isinstance(c_instance, C)
    assert isinstance(c_instance.a, A)
    assert isinstance(c_instance.b, B)
    assert isinstance(c_instance.b.a, A)

# ------------------------------------------------------------------------------
# Registered checks
# ------------------------------------------------------------------------------

def test_is_registered_true():
    container = DIContainer()

    class A: pass

    container.bind(A, lambda: A())
    assert container.is_registered(A) is True


def test_is_registered_false():
    container = DIContainer()

    class A: pass
    class B: pass

    container.bind(A, lambda: A())
    assert container.is_registered(B) is False


def test_is_registered_does_not_instantiate():
    """
    is_registered must NOT create objects or call providers.
    """
    container = DIContainer()
    called = False

    class A: pass

    def provider():
        nonlocal called
        called = True
        return A()

    container.bind(A, provider)

    assert container.is_registered(A) is True
    assert called is False, "is_registered() must not call provider()"


def test_is_registered_exact_match_only():
    """
    Registry must check for exact types — no subclass fallback.
    """
    container = DIContainer()

    class A: pass
    class B(A): pass

    container.bind(A, lambda: A())

    assert container.is_registered(A) is True
    assert container.is_registered(B) is False
