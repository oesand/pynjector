import pytest
from inspect import signature
from pynjector.dependa import dependa, DiDependa, FORBIDDEN_TYPES
from pynjector import DIContainer, DiLifetime

# Helper classes for testing (non-forbidden)
class X: pass
class Y: pass
class Z: pass

# --------------------------------------------------
# Basic attribute injection
# --------------------------------------------------

def test_dependa_assigns_attributes():
    @dependa
    class A:
        x: X
        y: Y

    a = A(x=X(), y=Y())
    assert isinstance(a.x, X)
    assert isinstance(a.y, Y)

def test_dependa_missing_attributes_raises():
    @dependa
    class A:
        x: X
        y: Y

    with pytest.raises(ValueError) as exc:
        A(x=X())  # missing y
    assert "Missing required attributes" in str(exc.value)

def test_dependa_unexpected_attributes_raises():
    @dependa
    class A:
        x: X

    with pytest.raises(ValueError) as exc:
        A(x=X(), z=Z())
    assert "Unexpected attribute" in str(exc.value)

def test_dependa_type_checking():
    @dependa
    class A:
        x: X
        y: Y

    with pytest.raises(TypeError):
        A(x=Y(), y=Y())  # wrong type for x

# --------------------------------------------------
# Default values are ignored (not required)
# --------------------------------------------------

def test_dependa_default_values_ignored():
    @dependa
    class A:
        x: X = X()  # default value
        y: Y

    # Only y is required
    a = A(y=Y())
    assert isinstance(a.y, Y)
    # x keeps default
    assert isinstance(getattr(a, "x", None), X)

# --------------------------------------------------
# Class constants (ALL_CAPS) are ignored
# --------------------------------------------------

def test_dependa_constants_ignored():
    @dependa
    class A:
        X_CONST: X
        y: Y

    a = A(y=Y())
    assert isinstance(a.y, Y)
    assert not hasattr(a, "X_CONST") or getattr(a, "X_CONST") is None

# --------------------------------------------------
# Signature reflects only required attributes
# --------------------------------------------------

def test_dependa_signature_reflects_only_required_attributes():
    @dependa
    class A:
        x: X
        y: Y = Y()
        Z_CONST: Z

    sig = signature(A)
    params = list(sig.parameters.values())
    # Only x should appear
    assert len(params) == 1
    assert params[0].name == "x"

# --------------------------------------------------
# Forbidden types raise on class creation
# --------------------------------------------------

@pytest.mark.parametrize("typ", FORBIDDEN_TYPES)
def test_dependa_forbidden_types_raise(typ):
    with pytest.raises(ValueError):
        @dependa
        class A:
            x: typ

# --------------------------------------------------
# DiDependaMeta and DiDependa class usage
# --------------------------------------------------

def test_didependa_meta_auto_init():
    class A(DiDependa):
        x: X
        y: Y

    a = A(x=X(), y=Y())
    assert isinstance(a.x, X)
    assert isinstance(a.y, Y)

def test_didependa_meta_missing_attribute_raises():
    class A(DiDependa):
        x: X
        y: Y

    with pytest.raises(ValueError):
        A(x=X())

def test_didependa_meta_type_checking():
    class A(DiDependa):
        x: X
        y: Y

    with pytest.raises(TypeError):
        A(x=Y(), y=Y())

# --------------------------------------------------
# Simple DI injection for DiDependa subclass
# --------------------------------------------------

def test_di_container_injects_dependa_class():
    container = DIContainer()

    class A(DiDependa):
        x: X

    # Bind X in the container
    x_instance = X()
    container.bind(X, x_instance)

    # Bind A as typed
    container.bind(A, DiLifetime.MAYFLY)

    a = container.resolve(A)
    assert isinstance(a, A)
    assert isinstance(a.x, X)
    assert a.x is x_instance  # exact instance from container

def test_di_container_injects_nested_dependa_classes():
    container = DIContainer()

    class A(DiDependa):
        x: X

    class B(DiDependa):
        a: A
        y: Y

    # Bind dependencies
    x_instance = X()
    y_instance = Y()
    container.bind(X, x_instance)
    container.bind(Y, y_instance)
    container.bind(A, DiLifetime.SINGLETON)  # A is singleton
    container.bind(B, DiLifetime.MAYFLY)

    b1 = container.resolve(B)
    b2 = container.resolve(B)

    # B instances are different (mayfly)
    assert b1 is not b2

    # Nested A is singleton
    assert b1.a is b2.a

    # Nested attributes
    assert b1.a.x is x_instance
    assert b1.y is y_instance
    assert b2.y is y_instance

# --------------------------------------------------
# Type mismatch or missing dependency raises
# --------------------------------------------------

def test_missing_dependency_raises():
    container = DIContainer()

    class A(DiDependa):
        x: X

    # X is not bound
    with pytest.raises(ValueError):
        container.resolve(A)

def test_dependency_type_mismatch_raises():
    container = DIContainer()

    with pytest.raises(ValueError):
        container.bind(X, Y())

# --------------------------------------------------
# Factory bindings with DiDependa
# --------------------------------------------------

def test_factory_binding_for_dependa_class():
    container = DIContainer()

    class A(DiDependa):
        x: X

    x_instance = X()
    container.bind(X, x_instance)

    # Bind using factory
    container.bind(A, lambda: A(x=container.resolve(X)))

    a = container.resolve(A)
    assert isinstance(a, A)
    assert a.x is x_instance
