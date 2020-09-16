import sublime

from Default.paste_from_history import g_clipboard_history

from .network import NetworkEvent, ConnectionManager
from .network import IntroductionMessage, ClipboardMessage, ClipboardHistoryMessage

from .utils import sn_setting, log, display_output_panel


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
        is_error = event in [NetworkEvent.CLOSED, NetworkEvent.CONNECTION_FAILED]
        log(f'{event.name.title()}: {connection.hostname}:{connection.port}', panel=True)
        display_output_panel(is_error)

    def message(self, connection, event, msg):
        if msg.msg_id() == ClipboardMessage.msg_id():
            return self.clipboard_message(connection, msg.text)
        elif msg.msg_id() == ClipboardHistoryMessage.msg_id():
            return self.clipboard_history(connection, msg)
        elif msg.msg_id() == IntroductionMessage.msg_id():
            return self.introduction_message(connection, msg)
        else:
            log(f'{str(msg)}', panel=True)

    def clipboard_message(self, connection, text):
        log(f'{connection.hostname} updated the clipboard ({len(text)} characters)', panel=True)
        display_output_panel(is_error=False)

        sublime.set_clipboard(text)
        g_clipboard_history.push_text(text)

    def clipboard_history(self, connection, msg):
        accept = sn_setting('sync_paste_history')
        if accept:
            g_clipboard_history.push_text(msg.text)

        if msg.index == msg.total:
            status = 'Received' if accept else 'Rejected'
            log(f'{status} {msg.total} clipboard history entries from {connection.hostname}', panel=True)
            display_output_panel(is_error=False)

    def introduction_message(self, connection, msg):
        connection.hostname = msg.hostname


###----------------------------------------------------------------------------
