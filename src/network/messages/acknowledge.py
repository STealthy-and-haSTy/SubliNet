import struct

from .base import ProtocolMessage


### ---------------------------------------------------------------------------


class AcknowledgeMessage(ProtocolMessage):
    """
    Transmit an ACK or NACK to the remote end. This is used as the machine
    readable response to some queries, and may be followed up by a Message or
    Error that explains the result of the Acknowledge in a human readable way.
    """
    def __init__(self, message_id, positive=True):
        self.message_id = message_id
        self.positive = positive

    def __str__(self):
        return "<Acknowledge message_id={0} positive={1}>".format(
            self.message_id, self.positive)

    @classmethod
    def msg_id(cls):
        return 1

    @classmethod
    def decode(cls, data):
        _, message_id, positive = struct.unpack(">HH?", data)

        return AcknowledgeMessage(message_id, positive)

    def encode(self):
        return struct.pack(">IHH?",
            2 + 2 + 1,
            AcknowledgeMessage.msg_id(),
            self.message_id,
            self.positive)


### ---------------------------------------------------------------------------
