import sublime

import queue
import struct
import socket

from .messages import ProtocolMessage

from .events import NetworkEvent
from ..utils import log


### ---------------------------------------------------------------------------


class Connection():
    """
    This class wraps the core logic for dealing with a connection to a remote
    server instance. Their creation and destruction are controlled by an
    external management class, and the underlying network code invokes methods
    in our class to determine when and in any network actions are needed.

    Connections wrap TCP sockets operating in a non-blocking manner.

    Each connection contains its own internal queue for messages it has been
    asked to send or that it has received, which it will handle automatically
    based on being called by the underlying network code.
    """
    def __init__(self, mgr, socket, ip, port, callback, accepted=False):
        """
        Create a new connection to the provided ip and port combination.
        This should only be called by the connection manager, which will hold
        onto the connection.
        """
        self.manager = mgr
        self.send_queue = queue.Queue()
        # TODO: As currently implemented, the receive queue is not needed as we
        #       are using an event scheme that allows for more than one thing
        #       to register, so we need to trigger those per message instead of
        #       holding them in a queue.
        #
        #       Keep this here until we decide if that's needed or if we should
        #       remove that in favor of the previous scheme that involves a
        #       single handler.
        self.recv_queue = queue.Queue()

        self.ip = ip;
        self.hostname = ip
        self.port = port

        self.socket = socket
        self.connected = False

        self.send_data = None
        self.receive_data = bytearray()
        self.expected_length = None

        self.callback = callback

        # We get created as either the result of initiating an output going
        # connection or accepting an incoming connection from a peer; trigger
        # the appropriate notification now.
        self._raise(NetworkEvent.CONNECTING if not accepted else NetworkEvent.ACCEPTING)

        # log("  -- Creating connection: {}", self)

    def __del__(self):
        # don't close here; assume the manager will close us before it goes
        # away.
        # self.close()
        # log("  -- Destroying connection: {}", self)
        pass

    def __str__(self):
        return "<Connection ip='{0}:{1} ({6})' socket={2} out={3} in={4}{5}>".format(
            self.ip, self.port, self.socket.fileno() if self.socket else None,
            self.send_queue.qsize(),
            self.recv_queue.qsize(),
            " CONNECTED" if self.connected else "",
            self.hostname)

    def __repr__(self):
        return str(self)

    def send(self, protocolMsgInstance):
        """
        Queue the provided protocol message up for sending to the other end of
        the connection. It will be sent at the next available opportunity.
        """
        self.send_queue.put(protocolMsgInstance.encode())

    # TODO: This is currently not needed because our receive queue is always
    #       empty; see the note in the constructor.
    def receive(self):
        """
        Remove an item from the incoming queue, or None if there are no
        messages waiting.
        """
        try:
            return self.recv_queue.get_nowait()
        except queue.Empty:
            return None

    # TODO: Should we defer closing into all queued messages have been
    #       transmitted out, and reject any addition outgoing messages during
    #       the close grace period?
    def close(self):
        """
        Close this connection by requesting our manager close us. This will
        shut down the connection in an orderly manner and drop the connection
        from the managed list.

        Any messages that are currently queued for transmission will be lost
        when the connection closes.
        """
        self.manager._remove(self)
        self._raise(NetworkEvent.CLOSED)


    def fileno(self):
        """
        For allowing us to use this connection in a call to select(); this
        should return the socket handle for the select() call to select on. It
        comes from our socket.
        """
        if self.socket:
            return self.socket.fileno()

        return None

    def _raise(self, event, extra=None):
        """
        If there is a registered listener, trigger a callback to let the other
        end know that there is a change in state. The callback is triggered in
        the main thread in Sublime.

        Events get invoked with the connection that is raising the event, the
        event itself and some optional extra data (which differs based on the
        event).

        Note: The events here are raised in the owner of the connection, which
        is the connection manager; user facing events are registered for and
        triggered from there.
        """
        if self.callback:
            sublime.set_timeout(lambda: self.callback(self, event, extra))
        else:
            # This should not be seen unless there's a programmer error.
            log('Unhandled Event: {} {} {}', event, extra, self)

    def _is_writeable(self):
        """
        Returns True if this connection is write-able; that is, that it has
        something to write.

        This returns True if the input queue has items in it or if we are
        currently sending a message and didn't send it all in one shot.

        The network thread uses this to know if this connection cares to know
        if it is write-able or not.
        """
        if self.socket:
            return (not self.connected or
                    self.send_queue.qsize() > 0 or
                    self.send_data is not None)

        return False

    def _send(self):
        """
        Called by the network thread in response to a select() call if this
        connection selected as write-able.

        This tries to send as many messages from the outgoing queue as possible
        with a sanity check to ensure that another thread can't starve other
        connection I/O by pumping messages into our queue while we're sending.
        """
        # Since sends happen after receives, it's possible that the connection
        # broke during the receive, in which case we should do nothing here.
        if self.socket is None:
            return

        if not self.connected:
            code = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            if code == 0:
                self.connected = True
                self._raise(NetworkEvent.CONNECTED)
            else:
                self._raise(NetworkEvent.CONNECTION_FAILED)
                return self.close()

        try:
            for _ in range(10):
                if self.send_data is None:
                    self.send_data = self.send_queue.get_nowait()

                sent = self.socket.send(self.send_data)
                # sent = self.socket.send(self.send_data[:1])
                self.send_data = self.send_data[sent:]
                if not self.send_data:
                    self.send_data = None
                else:
                    break

        except queue.Empty:
            pass

        except BlockingIOError:
            pass

        except Exception as e:
            self._raise(NetworkEvent.SEND_ERROR, str(e))
            log("Send Error: {}:{}: {}",
                self.ip, self.port, e)
            self.close()

    # TODO: This is currently triggering notifications for each incoming
    #       message instead of queuing them up; see the constructor for
    #       details.
    def _receive(self):
        """
        Called by the network thread in response to a select() call if this
        connection selected as readable.

        This reads as many incoming messages as possible from the socket and
        queues them up, raising a notification to tell the handler that a new
        message has been received.
        """
        try:
            new_data = self.socket.recv(4096)
            if not new_data:
                return self.close()

            self.receive_data.extend(new_data)

            while True:
                if self.expected_length is None:
                    if len(self.receive_data) >= 4:
                        self.expected_length, = struct.unpack_from(">I", self.receive_data)
                        self.receive_data = self.receive_data[4:]
                    else:
                        break

                if len(self.receive_data) >= self.expected_length:
                    msg_data = self.receive_data[:self.expected_length]
                    self.receive_data = self.receive_data[self.expected_length:]
                    self.expected_length = None

                    # TODO: In order to facilitate our new event model and the
                    #       notion that more than one listener might want the
                    #       message, don't put received messages in the queue.
                    #
                    #       We probably don't need this any more if we decide
                    #       we like/need this model and not the standard single
                    #       handler we previously used.
                    new_msg = ProtocolMessage.from_data(msg_data)
                    # self.recv_queue.put(ProtocolMessage.from_data(msg_data))
                    self._raise(NetworkEvent.MESSAGE, new_msg)

                else:
                    break

        except BlockingIOError:
            pass

        except Exception as e:
            self._raise(NetworkEvent.RECV_ERROR, str(e))
            log("Recv Error: {}:{}: {}",
                self.ip, self.port, e)
            self.close()


### ---------------------------------------------------------------------------
