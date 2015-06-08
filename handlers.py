# Copyright (c) 2015 Hassib Belhaj-Hassine <hassib.belhaj at tum.de>

"""
module containing the ditra handlers
"""

import asyncore
import socket

import messages


class BasicDispatcher(asyncore.dispatcher):
    """a parent class for switches and controllers to inherit from

    This class wraps the asyncore dispatcher class, and provides the
    handling functionality that is common to both switches and
    controllers. Both the controller and the switch classes inherit
    from this class.
    """
    def __init__(self, (address, port)):
        asyncore.dispatcher.__init__(self)
        self.port = port
        self.address = address
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((address, port))
        self.buffer = ""

    def handle_message(self, message):
        pass

    def handle_read(self):
        message= self.recv(1024)
        parsed_message = messages.parse(message)
        print "From %s:%s received: " % (self.address, self.port), \
               messages.get_type(parsed_message)
        if parsed_message.type == 2:
            self.buffer += messages.of_echo_reply.pack()
        else:
            self.handle_message(message)

    def handle_write(self):
        if self.buffer:
            self.send(self.buffer)
            print "To %s:%s sent: " % (self.address, self.port), \
                   messages.get_type(self.buffer)
            self.buffer = ""

    def writable(self):
        return bool(self.buffer)


class Switch(BasicDispatcher):
    """Switch handling functionality, understandable by asyncore"""
    def __init__(self, (address, port)):
        BasicDispatcher.__init__(self, (address, port))
        self.controller = None
        print "Switch initiated on: %s:%s" % (address, port)

    def set_controller(self, controller):
        self.controller = controller

    def handle_connect(self):
        pass
        #self.send(of_hello)
        #self.send(of_features_request)
        #self.send(of_role_request)
        #self.send(of_set_config)

    def handle_message(self, message):
        self.controller.buffer += message


class Controller(BasicDispatcher):
    """Controller handling functionality, understandable by asyncore"""
    def __init__(self, (address, port)):
        BasicDispatcher.__init__(self, (address, port))
        self.switch = None
        print "Controller initiated on: %s:%s" % (address, port)

    def set_switch(self, switch):
        self.switch = switch

    def handle_connect(self):
        pass

    def handle_message(self, message):
        self.switch.buffer += message
