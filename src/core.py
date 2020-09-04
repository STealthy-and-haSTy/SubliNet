import sublime
import sublime_plugin

from .network import ConnectionManager
from .handler import NetworkEventHandler


###----------------------------------------------------------------------------


# Our global instance of the ConnectionManager and the event handler.
_manager = None
_handler = None


###----------------------------------------------------------------------------


def loaded():
    """
    Initialize package state
    """
    global _manager, _handler

    _manager = ConnectionManager()
    _handler = NetworkEventHandler(_manager)

    _manager.startup()

def unloaded():
    """
    Clean up package state before unloading
    """
    global _manager, _handler

    if _manager is not None:
        _manager.shutdown()
        _manager = None
        _handler = None


###----------------------------------------------------------------------------
