import inspect
import struct


### ---------------------------------------------------------------------------


class ProtocolMessage():
    """
    This class represents the base class for all messages to be sent between
    Sublime Text instances.  It also acts as an intermediate that  can defer
    decode requests to the appropriate class based on pulling the id value out
    of the message.
    """
    _registry = {}
    _size_width = struct.calcsize(">I")

    @classmethod
    def register(cls, classObj):
        """
        Register the provided class object with the system so that messages
        of that type can be decoded. The provided object needs to be a class
        that is a subclass of this class, which has implemented all of the
        abstract methods and ensures that it has a unique message ID.
        """
        if not inspect.isclass(classObj):
            raise ValueError('Need to provide a subclass of ProtocolMessage')

        if not issubclass(classObj, ProtocolMessage):
            raise ValueError('Can only register Protocol Messages (got %s)' % classObj.__name__)

        msg_id = classObj.msg_id()
        if msg_id in cls._registry:
            raise ValueError('Duplicate message type detected (%d, %s)' % (msg_id, classObj.__name__))

        cls._registry[msg_id] = classObj

    @classmethod
    def from_data(cls, data, udp=False):
        """
        Takes a block of data (bytes) that contains an encoded protocol
        message. If the block is for a known protocol message (based on the
        encoded type ID), an instance of that message will be returned
        containing the decoded data. Otherwise a ValueError exception will be
        raised.

        Encoded messages store their length for use in reception via TCP; for
        UDP messages, they will all arrive via a single datagram, where the
        length prefix on the transmission isn't required.
        """
        if udp: data = data[cls._size_width:]

        msg_id, = struct.unpack_from(">H", data)
        msg_class = cls._registry.get(msg_id)
        if msg_class is None:
            raise ValueError('Unknown message type (%d)' % msg_id)

        return msg_class.decode(data)

    @classmethod
    def msg_id(cls):
        """
        Provide a unique numeric id that represents this message. This needs to
        be implemented by subclasses; this version will throw an exception.
        """
        raise NotImplementedError('abstract base method should be overridden')

    @classmethod
    def decode(cls, data):
        """
        Takes a byte object and return back an instance of this class based on
        that data. The data provided will be exactly the data that was returned
        from a prior call to encode().
        """
        raise NotImplementedError('abstract base method should be overridden')

    def encode(self):
        """
        Return a bytes object that represents this message in a way that the
        decode() method can use to restore this object state. The first field
        in the encoded message needs to be the message type code so that the
        decoder knows what class to use to do the decoding.
        """
        raise NotImplementedError('abstract base method should be overridden')


### ---------------------------------------------------------------------------
