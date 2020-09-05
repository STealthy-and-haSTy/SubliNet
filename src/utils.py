import sublime

import textwrap


###----------------------------------------------------------------------------


def log(msg, *args, dialog=False, error=False, panel=False, **kwargs):
    """
    Generate a message to the console and optionally as either a message or
    error dialog. The message will be formatted and dedented before being
    displayed, and will be prefixed with its origin.
    """
    msg = textwrap.dedent(msg.format(*args, **kwargs)).strip()

    if error:
        print("SubliNet:")
        return sublime.error_message(msg)

    for line in msg.splitlines():
        print("SubliNet: {msg}".format(msg=line))

    if dialog:
        sublime.message_dialog(msg)

    if panel:
        for window in sublime.windows():
            view = window.find_output_panel("sublinet")
            view.run_command("append", {
                "characters": msg + "\n",
                "force": True,
                "scroll_to_end": True
            })

        sublime.active_window().run_command("show_panel", {"panel": "output.sublinet"})


###----------------------------------------------------------------------------


def setup_log_panel(window, src_window=None):
    """
    Set up an output panel for our logging in the given window.

    If a source window is provided, the content of the panel in that window
    will be copied into the panel created in this window to synchronize them.
    """
    view = window.create_output_panel("sublinet")
    view.set_read_only(True)
    view.settings().set("gutter", False)
    view.settings().set("rulers", [])
    view.settings().set("word_wrap", False)

    if src_window:
        src_view = src_window.find_output_panel("sublinet")
        if src_view:
            text = src_view.substr(sublime.Region(0, len(src_view)))
            view.run_command("append", {
                "characters": text,
                "force": True,
                "scroll_to_end": True
            })

            # Whatever scroll_to_end is supposed to do, scrolling to the end
            # does not appear to be it.
            view.run_command("move_to",  {"extend": False, "to": "eof"})


###----------------------------------------------------------------------------
