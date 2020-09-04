import struct

from .base import ProtocolMessage


### ---------------------------------------------------------------------------


class ErrorMessage(ProtocolMessage):
    """
    Transmit an error-based textual message to the remote end, with the
    implication that the message is an explanation for something that just went
    wrong.

    Like the Message message, internal protocol messages generally transmit a
    message of this type after they do something that signals a failure, so
    that both the code and the user can see what's happened.
    """
    def __init__(self, error_code, error_msg):
        self.error_code = error_code
        self.error_msg = error_msg

    def __str__(self):
        return "<Error code={0} msg='{1}'>".format(
            self.error_code, self.error_msg)

    @classmethod
    def msg_id(cls):
        return 3

    @classmethod
    def decode(cls, data):
        pre_len = struct.calcsize(">HII")
        _, code, msg_len = struct.unpack(">HII", data[:pre_len])

        msg_str, = struct.unpack_from(">%ds" % msg_len, data, pre_len)

        return ErrorMessage(code, msg_str.decode('utf-8'))

    def encode(self):
        msg_data = self.error_msg.encode("utf-8")
        return struct.pack(">IHII%ds" % len(msg_data),
            2 + 4 + 4 + len(msg_data),
            ErrorMessage.msg_id(),
            self.error_code,
            len(msg_data),
            msg_data)


### ---------------------------------------------------------------------------
