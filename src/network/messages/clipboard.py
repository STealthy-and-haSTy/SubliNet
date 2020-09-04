import struct

from .base import ProtocolMessage


### ---------------------------------------------------------------------------


class ClipboardMessage(ProtocolMessage):
    """
    This message transmits a textual version of the clipboard contets.

    This message is structured similarly to the Message and Error messages, but
    has a specific purpose for the information that it conveys.
    """
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return "<Clipboard text='{0}'>".format(self.text)

    @classmethod
    def msg_id(cls):
        return 4

    @classmethod
    def decode(cls, data):
        pre_len = struct.calcsize(">HI")
        _, msg_len = struct.unpack(">HI", data[:pre_len])

        msg_str, = struct.unpack_from(">%ds" % msg_len, data, pre_len)

        return ClipboardMessage(msg_str.decode('utf-8'))

    def encode(self):
        msg_data = self.text.encode("utf-8")
        return struct.pack(">IHI%ds" % len(msg_data),
            2 + 4 + len(msg_data),
            ClipboardMessage.msg_id(),
            len(msg_data),
            msg_data)


### ---------------------------------------------------------------------------
