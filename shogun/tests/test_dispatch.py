from operator import itemgetter

from shogun.dispatch import TypeRegistry
from shogun.dispatch.concrete.default import DispatcherDefault


def test_dispatch_priorities():
    dispatchers = [(d.priority, d) for d in TypeRegistry.dispatchers()]
    reverse_sorted = sorted(dispatchers, key=itemgetter(0), reverse=True)
    assert dispatchers == reverse_sorted


def test_last_dispatcher_is_default():
    assert list(TypeRegistry.dispatchers())[-1] is DispatcherDefault
