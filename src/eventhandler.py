import sublime
import sublime_plugin


from .utils import setup_log_panel, log
from .core import broadcast_message
from .network import ClipboardMessage


###----------------------------------------------------------------------------


class SubliNetEventListener(sublime_plugin.EventListener):
    """
    This handles Sublime Text events (as opposed to network events, which are
    separate and handled elsewhere).
    """
    def on_new_window(self, window):
        for existing in sublime.windows():
            if existing.id() != window.id():
                return setup_log_panel(window, existing)

    # TODO: Realistically, this should not log to the panel in a way that opens
    #       it or we might want to kill ourselves. So maybe make it
    #       configurable or give the log command a way to log to the panel
    #       without opening it as well.
    def on_post_text_command(self, view, name, args):
        if name == 'copy' or name == 'cut':
            text = sublime.get_clipboard()
            broadcast_message(ClipboardMessage(text))
            log(f'Transmitting {text.len()} clipboard characters')


###----------------------------------------------------------------------------
