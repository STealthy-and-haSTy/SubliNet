import sublime
import sublime_plugin


from .utils import setup_log_panel


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


###----------------------------------------------------------------------------
