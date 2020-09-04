import struct

from .base import ProtocolMessage


### ---------------------------------------------------------------------------


class MessageMessage(ProtocolMessage):
    """
    Transmit a generic textual message to the remote end, with the implication
    that the message is informational in nature.

    Internal protocol messages are used to transmit information and state meant
    to be machine readable; messages of this type can be transmitted after such
    a message to provide a human readable version as well.
    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "<Message msg='{0}'>".format(self.msg)

    @classmethod
    def msg_id(cls):
        return 2

    @classmethod
    def decode(cls, data):
        pre_len = struct.calcsize(">HI")
        _, msg_len = struct.unpack(">HI", data[:pre_len])

        msg_str, = struct.unpack_from(">%ds" % msg_len, data, pre_len)

        return MessageMessage(msg_str.decode('utf-8'))

    def encode(self):
        msg_data = self.msg.encode("utf-8")
        return struct.pack(">IHI%ds" % len(msg_data),
            2 + 4 + len(msg_data),
            MessageMessage.msg_id(),
            len(msg_data),
            msg_data)


### ---------------------------------------------------------------------------
