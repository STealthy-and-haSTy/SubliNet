import struct
from os.path import dirname, basename, join

from .base import ProtocolMessage


### ---------------------------------------------------------------------------


# TODO: This should allow for spooling of files in partial chunks by including
#       a total chunk count and a current chunk indicator, allowing both ends
#       to handle large files without exploding memory usage.
#
#       This could also be enhanced to allow for sending the buffer in place
#       of reading the current file content from disk first.
class FileContentMessage(ProtocolMessage):
    """
    This message transmits file information to the remote end; the name of a
    file and optionally also its content.

    Currently this is a rather crude implementation; the whole file will be
    read into memory and transmitted at once. A more robust implementation
    would allow for spooling chunks of the file in sucessive messages so that
    the memory load is not of concern in the general case.
    """
    def __init__(self, root_path, relative_name, read_file=True):
        self.root_path = root_path
        self.relative_name = relative_name

        if read_file:
            with open(join(root_path, relative_name), "rb") as file:
                self.file_content = file.read()

    def __str__(self):
        return "<FileContent root='{0}' name='{1}' size={2}>".format(
            self.root_path, self.relative_name, len(self.file_content))

    @classmethod
    def msg_id(cls):
        return 5

    @classmethod
    def decode(cls, data):
        pre_len = struct.calcsize(">H256s256sI")
        _, root, name, file_length = struct.unpack(">H256s256sI", data[:pre_len])

        msg = FileContentMessage(root.decode('utf-8').rstrip("\000"),
                                 name.decode('utf-8').rstrip("\000"),
                                 read_file=False)
        content, = struct.unpack_from(">%ds" % file_length, data, pre_len)

        msg.file_content = content.decode('utf-8')

        return msg

    def encode(self):
        return struct.pack(">IH256s256sI%ds" % len(self.file_content),
            2 + 256 + 256 + 4 + len(self.file_content),
            FileContentMessage.msg_id(),
            self.root_path.encode('utf-8'),
            self.relative_name.encode('utf-8'),
            len(self.file_content),
            self.file_content)


### ---------------------------------------------------------------------------
