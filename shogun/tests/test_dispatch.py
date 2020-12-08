from operator import itemgetter

from shogun.dispatch.concrete.default import DispatcherDefault
from shogun.dispatch.registry import GlobalRegistry, TypeRegistry


def test_dispatch_priorities():
    dispatchers = [(d.priority, d) for d in GlobalRegistry.dispatchers()]
    reverse_sorted = sorted(dispatchers, key=itemgetter(0), reverse=True)
    assert dispatchers == reverse_sorted


def test_last_dispatcher_is_default():
    assert list(GlobalRegistry.dispatchers())[-1] is DispatcherDefault


def test_type_registry_manual_register():
    registry = TypeRegistry()
    registry.register(DispatcherDefault)
    dispatchers = list(registry.dispatchers())
    assert len(dispatchers) == 1
    assert dispatchers[0] is DispatcherDefault


def test_type_registry_manual_deregister():
    registry = TypeRegistry()
    registry.register(DispatcherDefault)
    registry.deregister(DispatcherDefault)
    assert len(list(registry.dispatchers())) == 0


def test_type_registry_manual_clear():
    registry = TypeRegistry()
    registry.register(DispatcherDefault)
    registry.register(DispatcherDefault)
    assert len(list(registry.dispatchers())) == 2

    registry.clear()
    assert len(list(registry.dispatchers())) == 0
