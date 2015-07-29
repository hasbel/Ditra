#!/usr/bin/env python

# Copyright (c) 2015 Hassib Belhaj-Hassine <hassib.belhaj at tum.de>

"""
SDN proxy for use with ditra
"""

import sys
import asyncore
import socket


# ------------------ Configuration ------------------

LISTEN_PORT = 6633
LISTEN_ADDRESS = "0.0.0.0"

# ---------------------------------------------------

controllers = {}

class ConnectionAcceptor(asyncore.dispatcher):
    """Responsible for binding to a port and accepting connections

    Upon instantiation, we bind to a local port and start
    listening for incoming connections. Connection are assumed
    to be from ditra hypervisor instances and are accepted.
    A Hypervisor object is then instantiated for each accepted
    connection and the resulting socket is passed to it.
    """
    def __init__(self, (address, port)):
        asyncore.dispatcher.__init__(self)
        self.port = port
        self.address = address
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bind((address, port))
        self.listen(2)
        print "Listening on %s:%s" % (address, port)

    def handle_accept(self):
        """Accept connections and create a Hypervisor object for each"""
        pair = self.accept()
        if pair:
            sock, address = pair
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
            Hypervisor(sock)
            print "Connection from: ", address


class Hypervisor(asyncore.dispatcher):
    """Handles the connection to the Ditra hypervisor

    This class is responsible for all communication to and from the
    Ditra hypervisors, including the handshake.
    This Class will instantiate a new Controller object if needed.
    """
    def __init__(self, sock):
        asyncore.dispatcher.__init__(self, sock=sock)
        self.controller = None
        self.buffer = ""

    def handle_read(self):
        """Called by asyncore when a packet is received

        During the initiate handshake with the connecting Ditra,
        a table check is performed to see if a Controller object
        already exists for the controller address received from Ditra.
        If that is the case, it is linked to the new Hypervisor Object.
        If not, a new Controller object will be created.
        After The handshake, everything is passed to the controller
        as is.
        """
        packet = self.recv(8192)
        if packet == "":
            print "[WARNING] Socket closed by remote hypervisor", self.addr
            print "Closing connection to Ditra"
            self.close()
            return
        # Initiate controller: Ditra 3-way handshake
        if not self.controller:
            delimiter = packet.index(":")
            controller_address = packet[:delimiter]
            # Assume port number has 4 digits
            controller_port = int(packet[(delimiter+1):(delimiter+5)])
            packet = packet[(delimiter+5):]
            pair = (controller_address, controller_port)
            if pair in controllers:
                self.controller = controllers[pair]
                print "Controller switched"
            else:
                self.controller = Controller(pair)
                controllers[pair] = self.controller
            self.controller.hypervisor = self
            self.buffer += "\x03\x00\x00\x08\x00\x00\x00\x01" # of_hello
            if packet == "":
                return
        # If controller initiated, pass messages
        if self.controller:
            self.controller.buffer += packet

    def handle_write(self):
        """Called by asyncore when the socket is ready to send"""
        self.send(self.buffer)
        self.buffer = ""

    def writable(self):
        """Only try to send when there is something to send"""
        return bool(self.buffer)


class Controller(asyncore.dispatcher):
    """Handles the connection to an SDN Controller

    This class is responsible for all communication to and from the
    controller, including the hello.
    """
    def __init__(self, (address, port)):
        asyncore.dispatcher.__init__(self)
        self.port = port
        self.address = address
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        self.connect((address, port))
        self.hypervisor = None
        self.buffer = ""
        print "controller started on: %s:%s" % (address, port)

    def handle_read(self):
        packet = self.recv(8192)
        if packet == "":
            print "[WARNING] Socket closed by remote controller!"
            print "Closing connection to controller and associated Ditra."
            self.close()
            self.hypervisor.close()
            # de-register from controllers list
            del controllers[(self.address, self.port)]
            return
        self.hypervisor.buffer += packet

    def handle_write(self):
        self.send(self.buffer)
        self.buffer = ""

    def writable(self):
        return bool(self.buffer)


def main():
    """Listen for incoming connection, and start the asyncore loop"""
    ConnectionAcceptor((LISTEN_ADDRESS, LISTEN_PORT))
    asyncore.loop()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "Interrupted by user. (Ctrl-C)"
        sys.exit(1)
