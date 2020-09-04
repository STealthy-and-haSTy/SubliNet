import socket
from threading import Event, Lock

from ..core import log
from .connection import Connection
from .transport import NetworkThread


### ---------------------------------------------------------------------------


class ConnectionManager():
    """
    This class manages all of our connections for us, and acts as a mediator
    between the Connection class instances and the NetworkThread that handles
    our I/O.

    There should be only a single global instance of this class created, and
    all public facing access to the intenals of the network code go through the
    methods in this class.

    We maintain a threadsafe list of connections and have the ability for
    external code to register an interest in socket events.
    """
    def __init__(self):
        self.conn_lock = Lock()
        self.connections = list()
        self.thr_event = Event()
        self.handlers = dict()
        self.net_thread = NetworkThread(self, self.conn_lock, self.connections,
                                        self.thr_event)

    def startup(self):
        """
        Start up the networking system. This intializes the client list and
        starts the network thread running. That will start our discovery
        broadcasts.

        This must be called from plugin_loaded()
        """
        log("=> Connection Manager Initializing")
        self.net_thread.start()

    def shutdown(self):
        """
        Gracefully shut down the network system. This asks all connections to
        shut down gracefully, closes the sockets, and then asks the network
        thread to terminate itself.

        This should be called from plugin_unloaded().
        """
        log("=> Connection Manager Shutting Down")
        self.thr_event.set()
        self.net_thread.join(0.25)

        with self.conn_lock:
            for connection in self.connections:
                self._close_connection(connection)

    def add_handler(self, key, event, handler):
        """
        Add an event handler for the given event, which will trigger the
        handler whenever that event is raised by a connection.

        The key is used to uniquely identify the registration on the handler,
        so that it can be removed later via a call to remove_handler.
        """
        notify_list = self.handlers.get(event, None)
        if notify_list is None:
            notify_list = dict()
            self.handlers[event] = notify_list

        notify_list[key] = handler

    def remove_handler(self, key, event):
        """
        Remove the event handler for the provided event on the given key. If
        there is no such event, nothing happens.
        """
        notify_list = self.handlers.get(event, None)
        if notify_list is not None:
            if key in notify_list:
                del notify_list[key]

    def find_connection(self, host=None, port=None):
        """
        Find and return all connections matching the provided criteria; can
        find all connections to a host, all connections to a port, or just all
        connections period.

        The returned list may be empty.
        """
        retcons = list()
        with self.conn_lock:
            for connection in self.connections:
                if host is not None and host != connection.host:
                    continue

                if port is not None and port != connection.port:
                    continue

                retcons.append(connection)

        return retcons

    def connect(self, host, port):
        """
        Start an outgoing connection to the provided host and port.

        The new connection object will be returned, but it will not yet be
        connected. An event will be raised when the connection attempt finishes
        (regardless of whether it succeeded or not).
        """
        with self.conn_lock:
            connection = self._open_connection(host, port)
            self.connections.append(connection)

        return connection

    def broadcast(self, protocolMsgInstance):
        """
        Broadcast the given protocol message over all of the current
        connections. This silently does nothing if there are not any
        connection.

        This is a convenience method for using find_connections() to find every
        connection and calling their send() methods in turn.
        """
        with self.conn_lock:
            for connection in self.connections:
                connection.send(protocolMsgInstance)

    def _add_connection(self, sock, host, port):
        """
        Add a new connection directly from a socket, once a connection is
        actually made. This is called by the network thread to add in the
        new connection after it accepts a connection successfully.
        """
        with self.conn_lock:
            connection = Connection(self, sock, host, port, self._handle_event, accepted=True)
            self.connections.append(connection)

        return connection

    def _open_connection(self, host, port):
        """
        Do the underlying work of actually opening up a brand new connection
        to the provided host and port.
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setblocking(False)
            sock.connect((host, port))
        except BlockingIOError:
            pass

        connection = Connection(self, sock, host, port, self._handle_event)

        return connection

    def _close_connection(self, connection):
        """
        Given a connection object, attempt to gracefully close it.
        """
        if connection.socket:
            try:
                connection.socket.shutdown(socket.SHUT_RDWR)
                connection.socket.close()

            except:
                pass

            finally:
                connection.socket = None
                connection.connected = False

    def _remove(self, connection):
        """
        Remove the provided connection from the list of connections that we
        are currently storing.
        """
        with self.conn_lock:
            self._close_connection(connection)
            self.connections[:] = [conn for conn in self.connections
                                        if conn is not connection]

    def _handle_event(self, connection, event, extra):
        """
        This handles events for all of our connections, allowing us to know
        when they're created, destroyed or receiving messages, so that we can
        act on them as needed.

        All events raised by connections go through here, although only those
        that have been registered will do anything.
        """
        log(f'_handle_event({event}, {connection})')

        handlers = self.handlers.get(event,{})
        for handler in handlers.values():
            handler(connection, event, extra)


### ---------------------------------------------------------------------------
