
SubliNet
========

SubliNet is a package for Sublime Text builds >= 4050 that connects all
instances of Sublime running on the same local network (which have the package
installed) together for the purposes of sharing information between them.

This package is still under active development, but at the current time the
desired proof of concept functionality of sharing the clipboard between
multiple hosts has been implemented.

In use, the package multicasts a discovery message on a set interval,
advertising to other instances of Sublime Text also running on the same local network
(and running this package) that we exist and are ready to communicate.

Whenever another instance sees the discovery message, it will connect back to
the broadcast machine. All machines connect to each other like a mesh, and can
freely transmit messages to each other. There is no explicit reconnect-on-
disconnect; instead, connections will be re- established when the next
discovery message is seen from the disconnected host.

This allows for the list of running hosts to grow or shrink on the network as
needed without any prior configuration of known hosts and without annoying
messages about not being able to reconnect if a host goes down or is otherwise
available. Similarly, when new hosts are added, they are seamlessly integrated
with the existing mesh.

Currently, low level protocol messages are exchanged, along with:

- the contents of the clipboard whenever a copy or cut operation happens; on
  the receiving end, this text is placed on the clipboard and also added to the
  paste history.

- on connect, the clipboard history is synced to the remote end (if enabled).

This could be extended to other information as well, such as gathering file
names, file contents or even controlling remote aspects of Sublime.


# Networking

In order to work, all instances of Sublime that you want to connect together
need to be on the same subnet and connected to a switch or router that allows
multicast UDP broadcasts.

Currently, the network setup is hard coded to the following values (but for the
technically minded, they can be modified in `transport.py`):

 * Discovery messages are multicast to group 224.1.1.1 on port 4377; the same
   port is used for the TCP connections between hosts.
 * The Multicast TTL is set to 1
 * Discovery broadcasts occur every 30 seconds



# TODO

In no particular order and as a non-exhaustive list, things that are planned or
should be done include:

 * Detect changes in configuration and signal the network thread so that it can
   potentially update its network configuration on the fly.
 * Logging to the output panel should be less spoopy (syntax highlighting too?)
 * Implement a proper token ring in the `Introduction` message so that multiple
   users running the package on the same SubNet can control which instances they
   talk to; the `Introduction` message has provisions for this, but they are
   currently not enforced.
 * Replace the message classes we're using with something more Pythonic.

