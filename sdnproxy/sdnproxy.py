#!/usr/bin/env python

# Copyright (c) 2015 Hassib Belhaj-Hassine <hassib.belhaj at tum.de>

"""
proxy for use with ditra
"""

import sys
import asyncore
import socket
import time


# ------------------ Configuration ------------------

LISTEN_PORT = 6633
LISTEN_ADDRESS = "0.0.0.0"
CONTROLLERS = {}

# ---------------------------------------------------


class ConnectionAcceptor(asyncore.dispatcher):
    def __init__(self, (address, port)):
        asyncore.dispatcher.__init__(self)
        self.port = port
        self.address = address
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind((address, port))
        self.listen(2)
        print "Listening on %s:%s" % (address, port)

    def handle_accept(self):
        pair = self.accept()
        if pair:
            sock, address = pair
            Hypervisor(sock)
            print "Connection from: ", address


class Hypervisor(asyncore.dispatcher):
    def __init__(self, sock):
        asyncore.dispatcher.__init__(self, sock=sock)
        self.controller = None
        self.buffer = ""

    def handle_read(self):
        packet = self.recv(4096)
        if packet == "":
            print "[WARNING] Socket closed by remote hypervisor!"
            self.close()
            return
        # Initiate controller
        if not self.controller:
            delimiter = packet.index(":")
            controller_address = packet[:delimiter]
            controller_port = int(packet[(delimiter+1):])
            pair = (controller_address, controller_port)
            if pair in CONTROLLERS:
                self.controller = CONTROLLERS[pair]
                self.controller.hypervisor.close()
                print "Controller switched"
            else:
                self.controller = Controller(pair)
                CONTROLLERS[pair] = self.controller
            self.controller.hypervisor = self
            time.sleep(0.1)
            return
        # If controller initiated, pass messages
        if self.controller and self.controller.hypervisor == self:
            self.controller.buffer += packet

    def handle_write(self):
        self.send(self.buffer)
        self.buffer = ""

    def writable(self):
        return bool(self.buffer)

    def close(self):
        if self.buffer:
            self.handle_write()
        print "Closing connection to Ditra"
        asyncore.dispatcher.close(self)


class Controller(asyncore.dispatcher):
    def __init__(self, (address, port)):
        asyncore.dispatcher.__init__(self)
        self.port = port
        self.address = address
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((address, port))
        self.hypervisor = None
        self.buffer = ""
        print "controller started on: %s:%s" % (address, port)

    def handle_read(self):
        packet = self.recv(4096)
        if packet == "":
            print "[WARNING] Socket closed by remote controller!"
            self.close()
            return
        self.hypervisor.buffer += packet

    def handle_write(self):
        self.send(self.buffer)
        self.buffer = ""

    def writable(self):
        return bool(self.buffer)


def main():
    acceptor = ConnectionAcceptor((LISTEN_ADDRESS, LISTEN_PORT))
    asyncore.loop()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "Interrupted by user. (Ctrl-C)"
        sys.exit(1)
    except Exception as err:
        print err
        sys.exit(1)