import pytest

from threading import Lock
from pynjector.cell import DiCell, DiCellKind
from pynjector.lifetime import DiLifetime

class A:
    pass

class B:
    def __init__(self, a: A):
        self.a = a

def test_dicell_constructor_forbidden():
    with pytest.raises(Exception):
        DiCell()


def test_dicell_typed_mayfly():
    cell = DiCell.typed(A, DiLifetime.MAYFLY)
    assert cell._kind == DiCellKind.TYPED
    assert cell._lifetime == DiLifetime.MAYFLY
    assert not hasattr(cell, "_instance")
    inst1 = cell.get_instance({})
    inst2 = cell.get_instance({})
    assert inst1 is not inst2


def test_dicell_typed_singleton():
    cell = DiCell.typed(A, DiLifetime.SINGLETON)
    assert hasattr(cell, "_lock")
    inst1 = cell.get_instance({})
    inst2 = cell.get_instance({})
    assert inst1 is inst2


def test_dicell_factory():
    cell = DiCell.factory(A, lambda: A())
    assert cell._kind == DiCellKind.FACTORY
    inst1 = cell.get_instance({})
    inst2 = cell.get_instance({})
    assert inst1 is not inst2


def test_dicell_instance():
    obj = A()
    cell = DiCell.instance(A, obj)
    assert cell._kind == DiCellKind.INSTANCE
    assert cell.get_instance({}) is obj


def test_dicell_resolve_type_success():
    bindings = {A: DiCell.instance(A, A())}
    b_instance = DiCell.resolve_type(B, bindings)
    assert isinstance(b_instance, B)
    assert isinstance(b_instance.a, A)


def test_dicell_resolve_missing_annotation():
    class NoAnnotation:
        def __init__(self, x):
            pass

    bindings = {}
    with pytest.raises(ValueError):
        DiCell.resolve_type(NoAnnotation, bindings)


def test_dicell_resolve_unregistered_dependency():
    bindings = {}
    with pytest.raises(ValueError):
        DiCell.resolve_type(B, bindings)
