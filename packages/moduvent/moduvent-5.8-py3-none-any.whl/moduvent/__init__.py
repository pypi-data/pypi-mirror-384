from .async_moduvent import AsyncEventAwareBase, AsyncEventManager
from .common import subscribe_method
from .events import (
    DataEvent,
    DataEventFactory,
    Event,
    EventFactory,
    Signal,
    SignalFactory,
)
from .module_loader import ModuleLoader
from .moduvent import EventAwareBase, EventManager

event_manager = EventManager()
EventAwareBase.event_manager = event_manager
register = event_manager.register
subscribe = event_manager.subscribe
unsubscribe = event_manager.unsubscribe
emit = event_manager.emit
reset = event_manager.reset
halt = event_manager.halt

aevent_manager = AsyncEventManager()
AsyncEventAwareBase.event_manager = aevent_manager
aregister = aevent_manager.register
asubscribe = aevent_manager.subscribe
aunsubscribe = aevent_manager.unsubscribe
aemit = aevent_manager.emit
initialize = aevent_manager.initialize
areset = aevent_manager.reset
ahalt = aevent_manager.halt

module_loader = ModuleLoader()
discover_modules = module_loader.discover_modules
signal = SignalFactory.new
data_event = DataEventFactory.new

__all__ = [
    "EventAwareBase",
    "EventManager",
    "Event",
    "DataEvent",
    "ModuleLoader",
    "register",
    "subscribe",
    "subscribe_method",
    "unsubscribe",
    "emit",
    "AsyncEventManager",
    "AsyncEventAwareBase",
    "aevent_manager",
    "aregister",
    "asubscribe",
    "aunsubscribe",
    "module_loader",
    "discover_modules",
    "Signal",
    "signal",
    "DataEvent",
    "data_event",
    "initialize",
    "reset",
    "EventFactory",
    "halt",
    "ahalt",
]
