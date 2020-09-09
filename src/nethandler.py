import sublime

from Default.paste_from_history import g_clipboard_history

from .network import NetworkEvent, ConnectionManager
from .network import IntroductionMessage, ClipboardMessage

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
        log(f'{event.name.title()}: {connection.hostname}:{connection.port}', panel=True)

    def message(self, connection, event, msg):
        if msg.msg_id() == ClipboardMessage.msg_id():
            return self.clipboard_message(connection, msg.text)
        elif msg.msg_id() == IntroductionMessage.msg_id():
            return self.introduction_message(connection, msg)

    def clipboard_message(self, connection, text):
        log(f'{connection.hostname} updated the clipboard ({len(text)} characters)', panel=True)

        sublime.set_clipboard(text)
        g_clipboard_history.push_text(text)

    def introduction_message(self, connection, msg):
        connection.hostname = msg.hostname


###----------------------------------------------------------------------------
