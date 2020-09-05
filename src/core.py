import sublime
import sublime_plugin

from .network import ConnectionManager
from .handler import NetworkEventHandler
from .utils import setup_log_panel


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

    for window in sublime.windows():
        setup_log_panel(window)

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


def broadcast_message(msg):
    """
    Transmit the message to all of the connections currently established with
    our network manager.
    """
    _manager.broadcast(msg)


###----------------------------------------------------------------------------
