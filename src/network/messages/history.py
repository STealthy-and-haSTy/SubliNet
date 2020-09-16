import struct

from .base import ProtocolMessage


### ---------------------------------------------------------------------------


class ClipboardHistoryMessage(ProtocolMessage):
    """
    This message transmits a textual version of the clipboard contets.

    This is identical to ClipboardMessage, but is a different type so that the
    receiving end can filter them out if it so desires.
    """
    def __init__(self, index, total, text):
        self.index = index
        self.total = total
        self.text = text

    def __str__(self):
        return "<ClipboardHistory text='{0}' ({1}/{2})>".format(
            self.text, self.index, self.total)

    @classmethod
    def msg_id(cls):
        return 6

    @classmethod
    def decode(cls, data):
        pre_len = struct.calcsize(">HBBI")
        _, index, total, msg_len = struct.unpack(">HBBI", data[:pre_len])

        msg_str, = struct.unpack_from(">%ds" % msg_len, data, pre_len)

        return ClipboardHistoryMessage(index, total, msg_str.decode('utf-8'))

    def encode(self):
        msg_data = self.text.encode("utf-8")
        return struct.pack(">IHBBI%ds" % len(msg_data),
            2 + 4 + 1 + 1 + len(msg_data),
            ClipboardHistoryMessage.msg_id(),
            self.index,
            self.total,
            len(msg_data),
            msg_data)


### ---------------------------------------------------------------------------
