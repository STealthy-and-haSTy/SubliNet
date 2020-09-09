import sublime

import textwrap


###----------------------------------------------------------------------------


def loaded():
    """
    Initialize package state
    """
    sn_setting.obj = sublime.load_settings("SubliNet.sublime-settings")
    sn_setting.default = {
        'broadcast_time': 30,
        'discovery_group': '224.1.1.1',
        'discovery_port': 4377,
        'discovery_ttl': 1,
        'stream_ip': '',
        'stream_port': 4377,
    }


def unloaded():
    """
    Clean up package state before unloading
    """
    pass


###----------------------------------------------------------------------------


# TODO: For logs where panel is True, this should only automatically open the
#       panel if a configuation item says so. There should be an additional
#       config item that indicates if the panel should auto-close or not. See
#       the SFTP package, which does the same thing.
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

    # Output to the console if this is a regular log or a message dialog; if
    # we're going to log to the panel, then we don't need to reundantly log to
    # the console as well.
    if not panel:
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

        window = sublime.active_window()
        window.run_command("show_panel", {"panel": "output.sublinet"})
        close_panel_after_delay(window, 5000)


###----------------------------------------------------------------------------


def sn_setting(key):
    """
    Get a SubliNet setting from a cached settings object.
    """
    default = sn_setting.default.get(key, None)
    return sn_setting.obj.get(key, default)


###----------------------------------------------------------------------------


def close_panel_after_delay(window, delay):
    """
    After the provided delay, close the SubliNet panel in the window provided.

    This call debounces other calls for the same window within the given delay
    to ensure that if more logs appear, the panel will remain open long enough
    to see them.
    """
    w_id = window.id()

    # If this is the first call for this window, add a new entry to the tracking
    # map; otherwise increment the existing value.
    if w_id not in close_panel_after_delay.map:
        close_panel_after_delay.map[w_id] = 1
    else:
        close_panel_after_delay.map[w_id] += 1

    def close_panel(window):
        # Decrement the call count for this window; if this is not the last
        # call, then we can leave.
        close_panel_after_delay.map[w_id] -= 1
        if close_panel_after_delay.map[w_id] != 0:
            return

        # Stop tracking this window now, and perform the close in it
        del close_panel_after_delay.map[w_id]

        if window.active_panel() == 'output.sublinet':
            window.run_command('hide_panel')

    sublime.set_timeout(lambda: close_panel(window), delay)

close_panel_after_delay.map = {}


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
