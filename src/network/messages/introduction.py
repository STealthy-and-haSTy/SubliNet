import sublime

import struct
import socket

from .base import ProtocolMessage


### ---------------------------------------------------------------------------


def _get_local_ip():
    """
    Return the local IP of this machine. On multihomed machines, this will
    return the IP of the interface that has the default route. If this fails,
    then use localhost as a fallback.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(('10.255.255.255', 1))
        ip = sock.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        sock.close()

    return ip


### ---------------------------------------------------------------------------


class IntroductionMessage(ProtocolMessage):
    """
    This message provides an introduction of ourselves to a remote instance,
    and conveys information about us and what protocol version we're using to
    interact.

    These are transmitted via the discovery service using UDP to advertise
    what IP and port we're listening on, as well as other information.

    Currently the user and password is unused (and taken from another) but the
    notion is that they would provide a minimal level of access control in
    cases where multiple users on the same local network are available and it's
    not desirable for them to intermingle traffic.
    """
    protocol_version = 1

    def __init__(self, user, password, ip=None, port=None, hostname=None, platform=None):
        self.user = user
        self.password = password
        self.ip = ip or _get_local_ip()
        self.port = port or 4377
        self.hostname = hostname or socket.getfqdn()
        self.platform = platform or sublime.platform()

    def __str__(self):
        return "<Introduction user={0} ip={1}:{2} host={3} platform={4} version={5}>".format(
            self.user, self.ip, self.port, self.hostname, self.platform, self.protocol_version)

    @classmethod
    def msg_id(cls):
        return 0

    @classmethod
    def decode(cls, data):
        _, version, user, password, ip, port, hostname, platform = struct.unpack(">HB64s64s39sH64s8s", data)

        msg = IntroductionMessage(
            user.decode("utf-8").rstrip("\000"),
            password.decode("utf-8").rstrip("\000"),
            ip.decode("utf-8").rstrip("\000"),
            port,
            hostname.decode("utf-8").rstrip("\000"),
            platform.decode("utf-8").rstrip("\000"))
        msg.protocol_version = version

        return msg

    def encode(self):
        return struct.pack(">IHB64s64s39sH64s8s",
            2 + 1 + 64 + 64 + 39 + 2 + 64 + 8,
            IntroductionMessage.msg_id(),
            self.protocol_version,
            self.user.encode("utf-8"),
            self.password.encode("utf-8"),
            self.ip.encode("utf=8"),
            self.port,
            self.hostname.encode("utf-8"),
            self.platform.encode("utf-8"))


### ---------------------------------------------------------------------------
