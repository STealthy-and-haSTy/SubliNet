from enum import Enum


### ---------------------------------------------------------------------------


class NetworkEvent(Enum):
    """
    This enumeration represents the various event notifications that the network
    code can raise to provide an indication of state changes.
    """
    # The connection was closed (either gracefully or due to an error).
    CLOSED=0

    # A new connection attempt is being made on the connection; the connection
    # is starting but not yet established.
    CONNECTING=1

    # A new incoming connection is being established; the attempt is starting
    # but not yet established.
    ACCEPTING=2

    # A connection has successfully connected.
    CONNECTED=3

    # The connection attempt to the remote host failed.
    CONNECTION_FAILED=4

    # An error occured while sending data to the server
    SEND_ERROR=5

    # An error occured while receiving data from the server
    RECV_ERROR=6

    # A message has been received from the other end of the connection.
    MESSAGE=7


### ---------------------------------------------------------------------------
