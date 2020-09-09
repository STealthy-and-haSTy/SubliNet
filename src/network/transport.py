from threading import Thread
from timeit import default_timer as timer

import socket
import select
import struct
import time

import textwrap

from .messages import ProtocolMessage, IntroductionMessage
from ..utils import sn_setting
from ..utils import log


### ---------------------------------------------------------------------------


class NetworkThread(Thread):
    """
    This background thread does all of our socket I/O for us, to ensure that
    we don't block anything and that our data flows no matter what else is
    happening.

    All of our sockets use non-blocking mode.
    """
    def __init__(self, manager, lock, connections, event):
        log("== Creating network thread")
        super().__init__()
        self.manager = manager
        self.conn_lock = lock
        self.connections = connections
        self.event = event
        self.discovery_socket = self.make_discovery_socket()
        self.server_socket = self.make_server_socket()

        # Create the message that we use to introduce ourselves; this is never
        # going to change so no need to make multiples of them.
        #
        # TODO: The tokens used here need to be configurable; in such a case
        #       we need either a way to signal the thread to change what it is
        #       broadcasting, or we need to quit and restart Sublime to make
        #       such a change take effect.
        self.broadcast_msg = IntroductionMessage('tmartin', 'password', sn_setting('stream_ip'), sn_setting('stream_port'))

    def __del__(self):
        log("== Destroying network thread")

    def make_discovery_socket(self):
        """
        Create and return a UDP socket configured to multicast to the
        configured group and port. This is used in our discovery service to
        announce our existence to other copies of us running on other machines.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setblocking(False)

        # Ensure that address and port reuse are enabled. Port reuse is not
        # available on all operating systems.
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, 'SO_REUSEPORT'):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        # Set the time to live for broadcasts.
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, sn_setting('discovery_ttl'))

        # Bind the socket now; this is required for us to get any data on this
        # port. We're binding to any IP available on this machine; on Linux we
        # can bind the multicast IP to further constrain where we get the data
        # from, but Windows doesn't allow that.
        #
        # TODO: Make this a configuration item for people that want to control
        #       what interface to use for discovery, in case they have a
        #       multihomed machine. This requires that the Introduction message
        #       be modified to include possibly many IP address and port
        #       combinations.
        sock.bind(('' , sn_setting('discovery_port')))

        # Join the multicast group.
        request = struct.pack("4sl", socket.inet_aton(sn_setting('discovery_group')), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, request)

        return sock

    def make_server_socket(self):
        """
        Create and return a TCP socket configured to listen to the configured
        discovery port. External instances of our package respond to the
        discovery messages we multicast by connecting to us via a TCP socket.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)

        # Ensure that address and port reuse are enabled. Port reuse is not
        # available on all operating systems.
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, 'SO_REUSEPORT'):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        sock.bind((sn_setting('stream_ip'), sn_setting('stream_port')))
        sock.listen(5)

        return sock

    def receive_discovery(self, conn):
        """
        Handle an incoming data read on our discovery socket. This gets called
        when the discovery UDP socket selects as readable.
        """
        data, addr = conn.recvfrom(10240)
        msg = ProtocolMessage.from_data(data, True)

        # log('Discovery from: {} : {}', repr(addr), str(msg))

        # If this message was broadcast by us, we don't need to handle it
        #
        # TODO: Should this compare the whole incoming message to the one we
        #       sent? Presumably nobody is crazy enough to configure multiple
        #       machines on the network with the same host, right?
        if msg.hostname == self.broadcast_msg.hostname:
            return

        # We don't want to try to connect to a remote host if they are using
        # a different protocol version than we are.
        #
        # In the future, we can respond to an older protocol by either refusing
        # to connect or by adapting our communications to the older protocol.
        if msg.protocol_version != 1:
            # log('Discovery host is running a different protocol: {}', addr)
            return

        # We don't want to try to connect to a remote host if we already have
        # a connection to them, say if they saw our broadcast first and
        # connected in. We only check IP because the port will be locally
        # assigned if they connected to us first.
        if len(self.manager.find_connection(msg.ip)) != 0:
            # log('Discovery host already connected: {}', addr)
            return

        # We should try to connect to this host; once we do, send an
        # introduction message to the other side so they know who we are.
        conn = self.manager.connect(msg.ip, msg.port)
        conn.hostname = msg.hostname
        conn.send(self.broadcast_msg)

    def handle_incoming_peer(self, conn):
        """
        Handle an incoming connection request for a peer. This gets called when
        the server socket selects as readable, indicating that a new connection
        is pending.
        """
        client, addr = conn.accept()
        conn = self.manager._add_connection(client, addr[0], addr[1])


    def run(self):
        """
        Execute our network tasks by selecting across all sockets, triggering
        the appropriate handlers as socket events occur. The main loop waits on
        a semaphore that tells if it it should terminate itself, at which point
        the loop will break.
        """
        log("== Entering network loop")

        # Start with no known broadcast so we do so right away; after that
        # we'll go timed.
        last_broadcast = None

        discovery = self.broadcast_msg.encode()
        broadcast_addr = (sn_setting('discovery_group'), sn_setting('discovery_port'))
        broadcast_delay = sn_setting('broadcast_time')

        while not self.event.is_set():
            tick = timer()

            with self.conn_lock:
                readable = [c for c in self.connections if c.connected]
                writable = [c for c in self.connections if c._is_writeable()]

            # Add in our server sockets so that we know when a broadcast
            # arrives or when someone is trying to connect to us.
            readable.extend([self.discovery_socket, self.server_socket])

            # This can't happen because of our server sockets, so this is a
            # reminder that if you select on nothing, the timeout expires
            # instantly. Goodbye, CPU...
            if not readable and not writable:
                log("*** Network thread has no connections to service")
                time.sleep(0.25)
                continue

            rset, wset, _ = select.select(readable, writable, [], 0.25)

            for conn in rset:
                # Was a broadcast seen?
                if conn == self.discovery_socket:
                    self.receive_discovery(conn)

                # Is there a new potential incoming connection?
                elif conn == self.server_socket:
                    self.handle_incoming_peer(conn)

                # It's just a regular connection
                else:
                    conn._receive()

            for conn in wset:
                conn._send()

            if last_broadcast is None or tick - last_broadcast > broadcast_delay:
                self.discovery_socket.sendto(discovery, broadcast_addr)
                last_broadcast = tick

        log("== Network thread is gracefully ending")


### ---------------------------------------------------------------------------
