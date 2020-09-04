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
        window = sublime.active_window()
        if "output.sublinet" not in window.panels():
            view = window.create_output_panel("sublinet")
            view.set_read_only(True)
            view.settings().set("gutter", False)
            view.settings().set("rulers", [])
            view.settings().set("word_wrap", False)

        view = window.find_output_panel("sublinet")
        view.run_command("append", {
            "characters": msg + "\n",
            "force": True,
            "scroll_to_end": True})

        window.run_command("show_panel", {"panel": "output.sublinet"})


###----------------------------------------------------------------------------
