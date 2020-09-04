import sublime

from Default.paste_from_history import g_clipboard_history

from .network import NetworkEvent, ConnectionManager, ClipboardMessage

from .utils import log


###----------------------------------------------------------------------------


class NetworkEventHandler():
    """
    This class represents the glue logic between the network code and the
    package proper, handling the network events raised by the manager to
    display text in the console and trigger other actions.
    """
    def __init__(self, manager):
        manager.add_handler('core', NetworkEvent.CONNECTING, self.connectionState)
        manager.add_handler('core', NetworkEvent.ACCEPTING, self.connectionState)
        manager.add_handler('core', NetworkEvent.CONNECTED, self.connectionState)
        manager.add_handler('core', NetworkEvent.CLOSED, self.connectionState)
        manager.add_handler('core', NetworkEvent.CONNECTION_FAILED, self.connectionState)

        manager.add_handler('core', NetworkEvent.MESSAGE, self.message)

    def connectionState(self, connection, event, extra):
        log(f'{event.name.title()}: {connection.host}:{connection.port}', panel=True)

    def message(self, connection, event, msg):
        if msg.msg_id() == ClipboardMessage.msg_id():
            return self.clipboard_message(connection, msg.text)

    def clipboard_message(self, connection, text):
        log(f'{connection.host}:{connection.port} updated the clipboard ({len(text)} characters)', panel=True)

        sublime.set_clipboard(text)
        g_clipboard_history.push_text(text)


###----------------------------------------------------------------------------
